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

        # Display results
        st.success("✅ Analysis Complete!")
        st.markdown("---")

        # Birth Information Summary
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Solar Date", f"{birth_date.strftime('%Y-%m-%d')}")
            st.metric("Solar Time", f"{birth_time.strftime('%H:%M:%S')}")

        with col2:
            st.metric(
                "Lunar Date", f"{lunar.getYear()}-{abs(lunar.getMonth())}-{lunar.getDay()}"
            )
            lunar_time_str = f"{lunar.getHour():02d}:{lunar.getMinute():02d}"
            st.metric("Lunar Time", lunar_time_str)

        with col3:
            st.metric("Gender", "Female" if gender == 0 else "Male")
            st.metric("Location", f"{latitude:.4f}°, {longitude:.4f}°")

        st.markdown("---")

        # LLM Analysis Tabs
        tab1, tab2, tab3 = st.tabs(
            [
                "👤 Life Overview",
                "💕 Romance",
                "💼 Career",
            ]
        )

        with tab1:
            st.subheader("👤 Life Overview")
            if llm_response.life_overview:
                st.markdown(llm_response.life_overview)
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

    except Exception as e:
        logger.error(f"❌ Error during analysis: {str(e)}", exc_info=True)
        st.error(f"❌ Error during analysis: {str(e)}")
        st.info("Please check your input values and try again.")
        with st.expander("View Error Details"):
            st.code(str(e))

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
