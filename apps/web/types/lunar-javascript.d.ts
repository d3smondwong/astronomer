declare module 'lunar-javascript/index.js' {
  interface SolarDate {
    getLunar(): LunarDate;
    getYear(): number;
    getMonth(): number;
    getDay(): number;
    getHour(): number;
    getMinute(): number;
    getSecond(): number;
  }

  interface LunarDate {
    getYear(): number;
    getMonth(): number;
    getDay(): number;
    getHour(): number;
    getEightChar(): EightChar;
    getYearInGanZhi(): string;
    getMonthInGanZhi(): string;
    getDayInGanZhi(): string;
    getTimeInGanZhi(): string;
  }

  interface EightChar {
    getYear(): string;
    getYearGan(): string;
    getYearZhi(): string;
    getYearHideGan(): string[];
    getMonth(): string;
    getMonthGan(): string;
    getMonthZhi(): string;
    getMonthHideGan(): string[];
    getDay(): string;
    getDayGan(): string;
    getDayZhi(): string;
    getDayHideGan(): string[];
    getTime(): string;
    getTimeGan(): string;
    getTimeZhi(): string;
    getTimeHideGan(): string[];
  }

  interface SolarStatic {
    fromYmd(year: number, month: number, day: number): SolarDate;
    fromYmdHms(year: number, month: number, day: number, hour: number, minute: number, second: number): SolarDate;
  }

  export const Solar: SolarStatic;
  export const Lunar: unknown;
  export const EightChar: unknown;
  export const NineStar: unknown;
}
