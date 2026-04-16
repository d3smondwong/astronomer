"""
十二长生 Twelve Life Stages (Di Shi)

Two values per pillar (年柱, 月柱, 日柱, 时柱):
  - library_stage:     raw Chinese string from the lunar-python library
                       (bazi.getYearDiShi() etc.) — referenced against the Day Master.
  - self_seated_stage: 自坐 — computed from the pillar's OWN 天干 against its own 地支,
                       using the same Chang Sheng offset algorithm as twelveLifeStages.ts.

Self-seated algorithm:
  offset = CHANG_SHENG_OFFSET[天干]
  index  = (offset + zhi_index)  for yang stems (甲丙戊庚壬)
           (offset - zhi_index)  for yin stems  (乙丁己辛癸)
  stage  = CHANG_SHENG_ORDER[index % 12]
"""

# 12 stages in index order (mirrors LunarUtil.CHANG_SHENG)
_CHANG_SHENG_ORDER = [
    '长生', '沐浴', '冠带', '临官', '帝旺',
    '衰',   '病',   '死',   '墓',   '绝',   '胎', '养',
]

# Starting offset per Heavenly Stem
# Earth stems (戊/己) share Fire stems' offsets — standard BaZi rule
_CHANG_SHENG_OFFSET = {
    '甲': 1,  '丙': 10, '戊': 10, '庚': 7, '壬': 4,
    '乙': 6,  '丁':  9, '己':  9, '辛': 0, '癸': 3,
}

# Earthly Branch → 0-based index (子=0 … 亥=11)
_ZHI_INDEX = {
    '子': 0, '丑': 1, '寅': 2, '卯': 3, '辰': 4,  '巳': 5,
    '午': 6, '未': 7, '申': 8, '酉': 9, '戌': 10, '亥': 11,
}

_YANG_STEMS = {'甲', '丙', '戊', '庚', '壬'}


def _self_seated_stage(stem: str, branch: str) -> str | None:
    """Compute the 自坐 (self-seated) life stage using the pillar's own 天干 and 地支."""
    offset = _CHANG_SHENG_OFFSET.get(stem)
    zhi_index = _ZHI_INDEX.get(branch)
    if offset is None or zhi_index is None:
        return None
    raw = offset + (zhi_index if stem in _YANG_STEMS else -zhi_index)
    return _CHANG_SHENG_ORDER[raw % 12]


def get_twelve_life_stages(bazi, pillars: dict) -> dict:
    """
    Return the two Di Shi life-stage values for each of the Four Pillars.

    Args:
        bazi:    EightChar object from lunar_birthday.getEightChar()
        pillars: Output of get_bazi_pillars() — provides 天干 and 地支 for self-seated calculation.

    Returns:
        dict keyed by 年柱, 月柱, 日柱, 时柱.
        Each contains: library_stage (str), self_seated_stage (str | None).
    """
    def make_stage(library_fn, pillar_key: str) -> dict:
        stem   = pillars[pillar_key]["天干"]
        branch = pillars[pillar_key]["地支"]
        return {
            "星运":     library_fn(),
            "自坐": _self_seated_stage(stem, branch),
        }

    return {
        "年柱": make_stage(bazi.getYearDiShi,  "年柱"),
        "月柱": make_stage(bazi.getMonthDiShi, "月柱"),
        "日柱": make_stage(bazi.getDayDiShi,   "日柱"),
        "时柱": make_stage(bazi.getTimeDiShi,  "时柱"),
    }
