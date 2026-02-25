"""
Solar to True Solar Time Conversion Module

This module converts standard clock time (standard time) to True Solar Time (TST),
accounting for timezone differences, Equation of Time (EoT) variations, and longitude-based
solar time discrepancies.

True Solar Time is essential for accurate BaZi calculations as it represents the actual
position of the sun relative to the observer's location, which is critical for determining
the correct Earthly Branch of the Hour Pillar.

Key Calculations:
1. Equation of Time (EoT): Accounts for the elliptical orbit of Earth and axial tilt
   causing the sun's apparent motion to vary throughout the year (±14-16 minutes)
2. Longitude Correction: Adjusts for the fact that 15° of longitude = 1 hour of time
   (4 minutes per degree of longitude)
3. Standard Meridian: Determined by the UTC offset of the location

Key Function:
    get_true_solar_time(dt, latitude, longitude): Converts standard time to True Solar Time

    Args:
        dt (datetime): Birth datetime in standard/wall clock time
        latitude (float): Birth location latitude (-90 to 90)
        longitude (float): Birth location longitude (-180 to 180)

    Returns:
        tuple: (Solar object with TST, dict with calculation details)

Reference:
- Equation of Time: Accounts for Earth's elliptical orbit and obliquity
- Standard Meridian: UTC offset × 15° per hour
- Longitude Correction: 4 minutes per degree from standard meridian
"""

from lunar_python import Solar, Lunar
import math
from timezonefinder import TimezoneFinder
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta
import json


def get_true_solar_time(datetime_obj, latitude, longitude):
    """
    Convert standard clock time to True Solar Time (TST).

    Args:
        datetime_obj (datetime): Birth datetime in standard/wall clock time
        latitude (float): Birth location latitude in decimal degrees
        longitude (float): Birth location longitude in decimal degrees

    Returns:
        tuple: (Solar object with TST, dict with calculation details)
    """
    # Step 1: Get timezone and UTC offset
    tf = TimezoneFinder()
    tz_name = tf.timezone_at(lat=latitude, lng=longitude)
    tz = ZoneInfo(tz_name)

    # Localize datetime to correct timezone for accurate offset
    dt_localized = datetime_obj.replace(tzinfo=tz)
    utc_offset = dt_localized.utcoffset().total_seconds() / 3600

    # Calculate Standard Meridian (in degrees)
    # Each hour of UTC offset corresponds to 15° of longitude
    standard_meridian = utc_offset * 15

    # Step 2: Calculate day of year (more robust than manual calculation)
    n = datetime_obj.timetuple().tm_yday

    # Step 3: Calculate Equation of Time (EoT)
    # B represents the day angle in the Earth's orbit
    B = (2 * math.pi / 365) * (n - 81)  # Radians

    # EoT formula (accurate to within ~1 minute)
    eot_minutes = 9.87 * math.sin(2 * B) - 7.53 * math.cos(B) - 1.5 * math.sin(B)

    # Step 4: Calculate Longitude Correction
    # 4 minutes for each degree away from standard meridian
    longitude_correction = 4 * (longitude - standard_meridian)

    # Step 5: Calculate total adjustment to standard time
    total_adjustment_minutes = longitude_correction + eot_minutes

    # Step 6: Apply adjustment using timedelta (handles calendar overflow/underflow)
    naive_dt = datetime_obj.replace(tzinfo=None)
    solar_dt = naive_dt + timedelta(minutes=total_adjustment_minutes)

    # Create Solar object with adjusted time
    adjusted_solar = Solar.fromYmdHms(
        solar_dt.year,
        solar_dt.month,
        solar_dt.day,
        solar_dt.hour,
        solar_dt.minute,
        solar_dt.second,
    )

    return adjusted_solar, {
        "original_datetime": datetime_obj,
        "latitude": latitude,
        "longitude": longitude,
        "timezone": tz_name,
        "utc_offset_hours": utc_offset,
        "standard_meridian": standard_meridian,
        "day_of_year": n,
        "equation_of_time_minutes": eot_minutes,
        "longitude_correction_minutes": longitude_correction,
        "total_adjustment_minutes": total_adjustment_minutes,
        "true_solar_datetime": solar_dt,
    }


# --- EXECUTION ---

if __name__ == "__main__":
    # python -m src.astronomer_calculations.solar_lunar_time

    print("=" * 80)
    print("☀️  Solar to True Solar Time Conversion Test")
    print("=" * 80)

    try:
        # Desmond's birthday example
        solar_birthday = Solar.fromYmdHms(1985, 11, 25, 17, 7, 0)

        # Create datetime object directly from known values
        datetime_birthday = datetime(1985, 11, 25, 17, 7, 0)

        # Location: Singapore (Changi area)
        latitude = 1.3253
        longitude = 103.8415

        print(f"\n📍 Birth Information:")
        print(f"   Solar Date: {solar_birthday.toYmdHms()}")
        print(f"   Location: Latitude {latitude}°N, Longitude {longitude}°E")

        # Convert to True Solar Time
        print(f"\n⏳ Converting to True Solar Time...")
        tst_birthday, details = get_true_solar_time(
            datetime_birthday, latitude, longitude
        )

        print(f"\n✅ Conversion Complete:")
        print(f"   Standard Time: {solar_birthday.toYmdHms()}")
        print(f"   True Solar Time: {tst_birthday.toYmdHms()}")

        # Show conversion to lunar calendar
        lunar_birthday = tst_birthday.getLunar()
        print(
            f"   Lunar Date: {lunar_birthday.getYear()}-{lunar_birthday.getMonth():02d}-{lunar_birthday.getDay():02d} {lunar_birthday.getHour():02d}:{lunar_birthday.getMinute():02d}"
        )

        # Display detailed calculations
        print(f"\n📊 Calculation Breakdown:")
        print(f"   Timezone: {details['timezone']}")
        print(f"   UTC Offset: {details['utc_offset_hours']:+.1f} hours")
        print(f"   Standard Meridian: {details['standard_meridian']:.1f}°")
        print(f"   Day of Year: {details['day_of_year']}")
        print(
            f"   Equation of Time: {details['equation_of_time_minutes']:+.2f} minutes"
        )
        print(
            f"   Longitude Correction: {details['longitude_correction_minutes']:+.2f} minutes"
        )
        print(
            f"   Total Adjustment: {details['total_adjustment_minutes']:+.2f} minutes"
        )

        print(f"\n--- Full JSON Output ---")
        print(json.dumps(details, ensure_ascii=False, indent=2, default=str))

        print("\n" + "=" * 80)
        print("✨ Test Completed Successfully!")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback

        traceback.print_exc()
