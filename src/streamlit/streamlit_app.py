"""
Streamlit Frontend for Astronomer BaZi Analysis Application
"""

import streamlit as st
import sys
from datetime import datetime
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.bazi_service import BaziService
from src.astronomer_calculations.solar_lunar_time import get_true_solar_time
from src.utils.logging import configure_logging, get_logger
from lunar_python import Solar

# To run it
# streamlit run src/streamlit/streamlit_app.py

# Initialize logging
configure_logging()
logger = get_logger(__name__)

# Page configuration
st.set_page_config(
    page_title="BaZi Analysis",
    page_icon="🌟",
    layout="wide",
    initial_sidebar_state="expanded",
)

logger.info("BaZi Analysis Streamlit app loaded")

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
st.title("🌟 BaZi Analysis")
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

            # Initialize BaZi service and analyze
            service = BaziService()
            analysis_result = service.analyze_bazi(
                lunar,
                birth_datetime=birth_datetime,
                latitude=latitude,
                longitude=longitude,
                gender=gender,
            )

        logger.info("✅ BaZi analysis completed successfully")

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
                "Lunar Date", f"{lunar.getYear()}-{lunar.getMonth()}-{lunar.getDay()}"
            )
            lunar_time_str = f"{lunar.getHour():02d}:{lunar.getMinute():02d}"
            st.metric("Lunar Time", lunar_time_str)

        with col3:
            st.metric("Gender", "Female" if gender == 0 else "Male")
            st.metric("Location", f"{latitude:.4f}°, {longitude:.4f}°")

        st.markdown("---")

        # Results Tabs
        (
            tab0,
            tab1,
            tab2,
            tab3,
            tab4,
            tab5,
            tab6,
            tab7,
            tab8,
            tab9,
            tab10,
            tab11,
            tab12,
            tab13,
        ) = st.tabs(
            [
                "基本信息",
                "八字",
                "出生环境",
                "五行",
                "神煞",
                "旬空",
                "三垣",
                "胦息",
                "作用",
                "袁天罡称骨歌",
                "十神",
                "纳音",
                "地势",
                "能量系统",
            ]
        )

        with tab0:
            st.subheader("基本信息 (Basic Information)")
            if "basic_info" in analysis_result and analysis_result["basic_info"]:
                st.json(analysis_result["basic_info"])
            else:
                st.info("No basic information available")

        with tab1:
            st.subheader("八字 (BaZi - Four Pillars)")
            if "bazi" in analysis_result and analysis_result["bazi"]:
                st.json(analysis_result["bazi"])
            else:
                st.info("No BaZi data available")

        with tab2:
            st.subheader("🌌 出生环境 (Birth Environment)")
            if (
                "birth_environment" in analysis_result
                and analysis_result["birth_environment"]
            ):
                st.json(analysis_result["birth_environment"])
            else:
                st.info("No Birth Environment data available")

        with tab3:
            st.subheader("五行 (Five Elements)")
            if "wu_xing" in analysis_result and analysis_result["wu_xing"]:
                st.json(analysis_result["wu_xing"])
            else:
                st.info("No Five Elements data available")

        with tab4:
            st.subheader("🌙 神煞 (Shen Sha - Gods & Evils)")
            if "shen_sha" in analysis_result and analysis_result["shen_sha"]:
                st.json(analysis_result["shen_sha"])
            else:
                st.info("No Shen Sha data available")

        with tab5:
            st.subheader("✨ 旬空 (Xun Kong - Void Branches)")
            if "xun_kong" in analysis_result and analysis_result["xun_kong"]:
                st.json(analysis_result["xun_kong"])
            else:
                st.info("No Xun Kong data available")

        with tab6:
            st.subheader("👑 三垣 (San Yuan - Three Palaces)")
            if "san_yuan" in analysis_result and analysis_result["san_yuan"]:
                st.json(analysis_result["san_yuan"])
            else:
                st.info("No Three Palaces data available")

        with tab7:
            st.subheader("🐟 胦息 (Tai Xi - Embryonic Breath)")
            if "tai_xi" in analysis_result and analysis_result["tai_xi"]:
                st.json(analysis_result["tai_xi"])
            else:
                st.info("No Embryonic Breath data available")

        with tab8:
            st.subheader("⚡ 作用 (Gan Zhi Interactions)")
            if "interactions" in analysis_result and analysis_result["interactions"]:
                st.json(analysis_result["interactions"])
            else:
                st.info("No Interaction data available")

        with tab9:
            st.subheader("⚖️ 袁天罡称骨歌 (Yuan Tian Gang Bone Weight)")
            if "bone_weight" in analysis_result and analysis_result["bone_weight"]:
                st.json(analysis_result["bone_weight"])
            else:
                st.info("No Bone Weight data available")

        with tab10:
            st.subheader("🔯 十神 (Ten Gods)")
            if "shi_shen" in analysis_result and analysis_result["shi_shen"]:
                st.json(analysis_result["shi_shen"])
            else:
                st.info("No Ten Gods data available")

        with tab11:
            st.subheader("🎵 纳音 (Na Yin - Five Elements)")
            if "na_yin" in analysis_result and analysis_result["na_yin"]:
                st.json(analysis_result["na_yin"])
            else:
                st.info("No Na Yin data available")

        with tab12:
            st.subheader("🌍 地势 (Di Shi - Earthly Position)")
            if "di_shi" in analysis_result and analysis_result["di_shi"]:
                st.json(analysis_result["di_shi"])
            else:
                st.info("No Di Shi data available")

        with tab13:
            st.subheader("⚡ 能量系统 (Branch Energy)")
            if "branch_energy" in analysis_result and analysis_result["branch_energy"]:
                st.json(analysis_result["branch_energy"])
            else:
                st.info("No Branch Energy data available")

        # Raw JSON (for debugging)
        with st.expander("📊 View Raw Analysis Data (JSON)"):
            st.json(analysis_result)

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
        ### Welcome to BaZi Analysis! 👋

        Enter your birth information in the left sidebar and click **"Analyze BaZi Chart"** to begin your analysis.

        **Required Information:**
        - Birth Date & Time
        - Birth Location (Latitude & Longitude)
        - Gender

        Your birth information will be converted from solar to lunar calendar and analyzed using traditional BaZi principles.
        """
        )
