/**
 * True Solar Time Conversion Module
 *
 * Converts standard clock time to True Solar Time (TST), accounting for:
 * - Timezone lookup via GPS coordinates (parallel to Python's TimezoneFinder)
 * - Equation of Time variations
 * - Longitude-based solar time discrepancies
 *
 * Returns lunar calendar date for BaZi extraction.
 */

'use client';

let Solar: any = null;
let initAttempted = false;

async function initSolar() {
  if (!Solar && !initAttempted) {
    initAttempted = true;
    const lunarModule = await import('lunar-javascript/index.js');

    if (lunarModule.Solar) {
      Solar = lunarModule.Solar;
    } else if ((lunarModule as any).default?.Solar) {
      Solar = (lunarModule as any).default.Solar;
    } else {
      throw new Error('Solar not found in lunar-javascript module');
    }

    if (typeof Solar.fromYmdHms !== 'function') {
      throw new Error('Solar.fromYmdHms is not a function');
    }
  }
  return Solar;
}

export interface TrueSolarTimeResult {
  originalDateTime: Date;
  trueSolarDateTime: Date;
  lunarDate: any;
}

function calculateEquationOfTime(dayOfYear: number): number {
  const B = (2 * Math.PI / 365) * (dayOfYear - 81);
  return 9.87 * Math.sin(2 * B) - 7.53 * Math.cos(B) - 1.5 * Math.sin(B);
}

/**
 * Resolve the UTC offset (hours) for given coordinates at a given date,
 * using geo-tz for timezone lookup — parallel to Python's TimezoneFinder + ZoneInfo.
 */
async function getUTCOffsetFromCoordinates(
  latitude: number,
  longitude: number,
  date: Date,
): Promise<number> {
  const tzlookup = (await import('tz-lookup')).default;
  const tzName = tzlookup(latitude, longitude);

  // Use Intl to resolve the actual UTC offset including DST —
  // parallel to Python's dt_localized.utcoffset().total_seconds() / 3600
  const formatter = new Intl.DateTimeFormat('en', {
    timeZone: tzName,
    timeZoneName: 'shortOffset',
  });
  const parts = formatter.formatToParts(date);
  const offsetStr = parts.find(p => p.type === 'timeZoneName')?.value ?? 'GMT+0';

  // Parse "GMT+8" or "GMT+5:30" into decimal hours
  const match = offsetStr.match(/GMT([+-])(\d+)(?::(\d+))?/);
  if (!match) return 0;
  const sign  = match[1] === '+' ? 1 : -1;
  const hours = parseInt(match[2], 10);
  const mins  = parseInt(match[3] ?? '0', 10);
  return sign * (hours + mins / 60);
}

export async function getTrueSolarTime(
  standardDateTime: Date,
  latitude: number,
  longitude: number,
): Promise<TrueSolarTimeResult> {
  const SolarClass = await initSolar();

  // Step 1: Resolve real UTC offset from coordinates
  const utcOffsetHours   = await getUTCOffsetFromCoordinates(latitude, longitude, standardDateTime);
  const standardMeridian = utcOffsetHours * 15;

  // Step 2: Day of year
  const startOfYear = new Date(standardDateTime.getFullYear(), 0, 0);
  const dayOfYear   = Math.floor(
    (standardDateTime.getTime() - startOfYear.getTime()) / (1000 * 60 * 60 * 24)
  );

  // Step 3: Equation of Time + Longitude Correction
  const equationOfTimeMinutes      = calculateEquationOfTime(dayOfYear);
  const longitudeCorrectionMinutes = 4 * (longitude - standardMeridian);
  const totalAdjustmentMinutes     = longitudeCorrectionMinutes + equationOfTimeMinutes;

  // Step 4: Apply adjustment in naive (timezone-free) space —
  // mirrors Python's: naive_dt = datetime_obj.replace(tzinfo=None)
  //                              solar_dt = naive_dt + timedelta(minutes=total_adjustment)
  //
  // Extract the user-intended local wall-clock values, treat them as UTC
  // to create a timezone-free timestamp, apply the adjustment, then read back
  // with UTC getters. This avoids machine-timezone contamination entirely.
  const naiveMs = Date.UTC(
    standardDateTime.getFullYear(),
    standardDateTime.getMonth(),
    standardDateTime.getDate(),
    standardDateTime.getHours(),
    standardDateTime.getMinutes(),
    standardDateTime.getSeconds(),
  );
  const adjustedNaive  = new Date(naiveMs + totalAdjustmentMinutes * 60 * 1000);

  const tst = {
    year:   adjustedNaive.getUTCFullYear(),
    month:  adjustedNaive.getUTCMonth() + 1,
    day:    adjustedNaive.getUTCDate(),
    hour:   adjustedNaive.getUTCHours(),
    minute: adjustedNaive.getUTCMinutes(),
    second: adjustedNaive.getUTCSeconds(),
  };

  const solar     = SolarClass.fromYmdHms(tst.year, tst.month, tst.day, tst.hour, tst.minute, tst.second);
  const lunarDate = solar.getLunar();

  return {
    originalDateTime:  standardDateTime,
    trueSolarDateTime: adjustedNaive,
    lunarDate,
  };
}
