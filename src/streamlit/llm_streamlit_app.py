"""
Streamlit Frontend for Astronomer BaZi LLM Analysis Application
"""

import streamlit as st
import sys
from datetime import datetime
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src.services.astronomer_data_aggregator import AstroDataAggregator
from src.services.astronomer_data_llm_formatter import AstroDataLLMFormatter
from src.astronomer_calculations.solar_lunar_time import get_true_solar_time
from src.utils.logging import configure_logging, get_logger
from src.llm.llm_service import analyse_bazi, LLMError
from lunar_python import Solar

# To run it
# streamlit run src/streamlit/llm_streamlit_app.py

# Initialize logging
configure_logging()
logger = get_logger(__name__)

# Page configuration
st.set_page_config(
    page_title="BaZi LLM Analysis",
    page_icon="🌟",
    layout="wide",
    initial_sidebar_state="expanded",
)

logger.info("BaZi LLM Analysis Streamlit app loaded")


def _save_report(
    sections: list[tuple[str, str]],
    llm_input_data: dict,
    birth_date,
    gender: int,
    longitude: float,
    latitude: float,
) -> Path:
    """Save markdown report and LLM input JSON to reports/YYYY-MM-DD/HH-MM-SS/."""
    import json as _json
    now = datetime.now()
    gender_label = "Male" if gender == 1 else "Female"
    stem = f"{birth_date.strftime('%Y-%m-%d')}_{gender_label}_{longitude}_{latitude}"
    report_dir = (
        Path(__file__).parent.parent.parent
        / "reports"
        / now.strftime("%Y-%m-%d")
        / now.strftime("%H-%M-%S")
    )
    report_dir.mkdir(parents=True, exist_ok=True)

    md_lines = ["# BaZi Report\n"]
    for header, content in sections:
        if content:
            md_lines.append(f"## {header}\n\n{content}\n")
    (report_dir / f"{stem}.md").write_text("\n---\n\n".join(md_lines), encoding="utf-8")

    (report_dir / f"{stem}.json").write_text(
        _json.dumps(llm_input_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    return report_dir / f"{stem}.md"


# Styling
st.markdown(
    """
    <style>
    .main {
        padding: 2rem;
    }
    .stTitle {
        text-align: center;
        color: #1f77b4;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header
st.title("🌟 BaZi LLM Analysis")
st.markdown("---")

# Sidebar for input
with st.sidebar:
    st.header("📋 Birth Information")

    # Birth Date
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Birth Date**")
        birth_date = st.date_input(
            " ",
            value=datetime(1985, 11, 25),
            min_value=datetime(1940, 1, 1),
            max_value=datetime.now(),
            help="Select your birth date",
        )

    with col2:
        st.markdown("**Birth Time**")
        col_hour, col_min = st.columns(2)
        with col_hour:
            birth_hour = st.number_input(
                "Hour",
                min_value=0,
                max_value=23,
                value=17,
                step=1,
            )
        with col_min:
            birth_minute = st.number_input(
                "Minute",
                min_value=0,
                max_value=59,
                value=7,
                step=1,
            )
        birth_time = datetime.min.time().replace(
            hour=int(birth_hour), minute=int(birth_minute)
        )

    # Location Information
    st.subheader("📍 Location")

    col3, col4 = st.columns(2)
    with col3:
        latitude = st.number_input(
            "Latitude",
            min_value=-90.0,
            max_value=90.0,
            value=1.3521,  # Singapore default
            step=0.0001,
            help="Decimal degrees (N is positive)",
        )

    with col4:
        longitude = st.number_input(
            "Longitude",
            min_value=-180.0,
            max_value=180.0,
            value=103.8198,  # Singapore default
            step=0.0001,
            help="Decimal degrees (E is positive)",
        )

    # Gender
    st.subheader("👤 Gender")
    gender = st.radio(
        "Select Gender",
        options=[0, 1],
        index=1,
        format_func=lambda x: "Female" if x == 0 else "Male",
        horizontal=True,
    )

    # Analyze Button
    st.markdown("---")
    analyze_button = st.button(
        "🔍 Analyze BaZi Chart", use_container_width=True, type="primary"
    )
    has_result = "_result" in st.session_state
    save_button = st.button(
        "💾 Save Report",
        use_container_width=True,
        disabled=not has_result,
        help="Run an analysis first to enable saving." if not has_result else "Save the full report to the reports folder.",
    )

# Main content area
if analyze_button:
    try:
        logger.info(
            f"Analysis requested - Date: {birth_date}, Time: {birth_time}, "
            f"Location: ({latitude}, {longitude}), Gender: {gender}"
        )
        with st.spinner("🔄 Processing your birth information..."):
            # Combine date and time
            birth_datetime = datetime.combine(birth_date, birth_time)

            # Convert solar to lunar time
            tst, conversion_details = get_true_solar_time(
                birth_datetime, latitude, longitude
            )
            lunar = tst.getLunar()

            # Initialize data aggregator and collect raw data
            aggregator = AstroDataAggregator()
            raw_data = aggregator.collect_data(
                lunar,
                birth_datetime=birth_datetime,
                latitude=latitude,
                longitude=longitude,
                gender=gender,
            )

            # Format data for LLM
            formatter = AstroDataLLMFormatter(raw_data)
            llm_friendly_data = formatter.format_for_llm()

        logger.info("✅ BaZi analysis completed successfully")

        try:
            with st.spinner("🤖 Consulting the LLM..."):
                llm_response = analyse_bazi(llm_friendly_data)
        except LLMError as e:
            logger.error("LLM analysis failed: %s", e)
            st.error(f"LLM error: {e}")
            st.stop()

        # Persist results so the page survives button re-runs
        st.session_state["_result"] = {
            "llm_response": llm_response,
            "llm_friendly_data": llm_friendly_data,
            "raw_data": raw_data,
            "conversion_details": conversion_details,
            "solar_date": birth_date.strftime("%Y-%m-%d"),
            "solar_time": birth_time.strftime("%H:%M:%S"),
            "lunar_date": f"{lunar.getYear()}-{abs(lunar.getMonth())}-{lunar.getDay()}",
            "lunar_time": f"{lunar.getHour():02d}:{lunar.getMinute():02d}",
            "birth_date": birth_date,
            "gender": gender,
            "latitude": latitude,
            "longitude": longitude,
        }
        st.rerun()

    except Exception as e:
        logger.error(f"❌ Error during analysis: {str(e)}", exc_info=True)
        st.error(f"❌ Error during analysis: {str(e)}")
        st.info("Please check your input values and try again.")
        with st.expander("View Error Details"):
            st.code(str(e))

# Display results (renders on every rerun as long as session state has data)
if "_result" in st.session_state:
    r = st.session_state["_result"]
    llm_response = r["llm_response"]
    llm_friendly_data = r["llm_friendly_data"]
    raw_data = r["raw_data"]
    conversion_details = r["conversion_details"]

    st.success("✅ Analysis Complete!")
    st.markdown("---")

    # Birth Information Summary
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Solar Date", r["solar_date"])
        st.metric("Solar Time", r["solar_time"])
    with col2:
        st.metric("Lunar Date", r["lunar_date"])
        st.metric("Lunar Time", r["lunar_time"])
    with col3:
        st.metric("Gender", "Female" if r["gender"] == 0 else "Male")
        st.metric("Location", f"{r['latitude']:.4f}°, {r['longitude']:.4f}°")

    st.markdown("---")

    # Handle Save Report (button lives in sidebar)
    ov = llm_response.life_overview
    all_sections = [
        ("👤 Life Overview — ✨ A Poem About You", ov.poem),
        ("👤 Life Overview — 🔍 Do We Understand You?", ov.self_verification),
        ("👤 Life Overview — 🧬 Core Identity", ov.core_identity),
        ("👤 Life Overview — 📖 Your Life So Far", ov.life_so_far),
        ("👤 Life Overview — ⚡ 3 Defining Moments", ov.defining_moments),
        ("👤 Life Overview — 🔭 The Future", ov.the_future),
        ("👤 Life Overview — ⚖️ The Destiny Balance Sheet", ov.destiny_balance_sheet),
        ("👤 Life Overview — 🌿 Living in Alignment", ov.living_in_alignment),
        ("💕 Romance", llm_response.romance),
        ("💼 Career", llm_response.career),
    ]
    if save_button:
        saved_path = _save_report(
            all_sections, llm_friendly_data,
            r["birth_date"], r["gender"], r["longitude"], r["latitude"],
        )
        project_root = Path(__file__).parent.parent.parent
        st.success(f"Report saved to `{saved_path.relative_to(project_root)}`")

    # LLM Analysis Tabs
    tab1, tab2, tab3 = st.tabs(
        [
            "👤 Life Overview",
            "💕 Romance",
            "💼 Career",
        ]
    )

    with tab1:
        ov = llm_response.life_overview
        sections = [
            ("✨ A Poem About You", ov.poem),
            ("🔍 Do We Understand You?", ov.self_verification),
            ("🧬 Core Identity", ov.core_identity),
            ("📖 Your Life So Far", ov.life_so_far),
            ("⚡ 3 Defining Moments", ov.defining_moments),
            ("🔭 The Future", ov.the_future),
            ("⚖️ The Destiny Balance Sheet", ov.destiny_balance_sheet),
            ("🌿 Living in Alignment", ov.living_in_alignment),
        ]
        has_content = any(content for _, content in sections)
        if has_content:
            for header, content in sections:
                if content:
                    st.subheader(header)
                    st.markdown(content)
        else:
            st.warning("No Life Overview returned from the LLM.")

    with tab2:
        st.subheader("💕 Romance")
        if llm_response.romance:
            st.markdown(llm_response.romance)
        else:
            st.warning("No Romance section returned from the LLM.")

    with tab3:
        st.subheader("💼 Career")
        if llm_response.career:
            st.markdown(llm_response.career)
        else:
            st.warning("No Career section returned from the LLM.")

    st.markdown("---")

    # JSON Data Viewer
    with st.expander("📊 View JSON Data"):
        st.subheader("LLM-Formatted Analysis Data")
        st.json(llm_friendly_data)

    # Raw Analysis Data (for debugging)
    with st.expander("🔧 View Raw Analysis Data (Debug)"):
        st.json(raw_data)

    # Conversion Details
    with st.expander("📐 View Time Conversion Details"):
        st.json(conversion_details)

else:
    # Welcome message
    st.empty()
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.info(
            """
        ### Welcome to BaZi LLM Analysis! 👋

        Enter your birth information in the left sidebar and click **"Analyze BaZi Chart"** to begin your analysis.

        **Required Information:**
        - Birth Date & Time
        - Birth Location (Latitude & Longitude)
        - Gender

        Your birth information will be converted from solar to lunar calendar and analyzed using traditional BaZi principles with AI-powered insights.

        **Tabs Available:**
        - **👤 Life Overview** — General life path and destiny insights
        - **💕 Romance** — Relationship and romantic prospects
        - **💼 Career** — Professional development and opportunities
        """
        )
