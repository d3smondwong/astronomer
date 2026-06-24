"""
Applies classical BaZi texts to a computed natal chart.

Covers San Ming Tong Hui interpretations across volumes 3–7:
  v3 — 禄神, 驿马, 天乙贵人, 三奇, 天月德, 太极贵人, 学堂, 正印, 贵气, 空亡
  v4 — 天干日干, 月日天干, 五行组合
  v5 — 官杀
  v7 — 论六亲, 论女命, 论小儿, 卷流

  Adding a new topic     → one analyzer fn  + one entry in ANALYZERS
  Adding a new condition → one evaluator fn + one entry in CONDITION_EVALUATORS

Public gateway: get_natal_interpretations(natal_chart: dict) -> dict


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 RULE SCHEMA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  {
    "逻辑名称":  str,
    "适用性别": "男" | "女" | "通用",
    "判定模式": "AND" | "OR" | "NOT" | "阈值",
    "判定逻辑": [ <condition>, ... ],
    "断语":     str,
    "现代解读": str   # optional
  }

Each <condition> is a leaf or a nested block:

  Leaf:
  {
    "位置":     { "柱": <pillar_spec>, "部分": <section> },
    "证据前缀": str,          # optional — prefixes all evidence keys with "<前缀>_"
    "判定目标": { "类型": str, ... }
  }

  Nested block (recursive):
  { "判定模式": "AND"|"OR"|"NOT", "判定逻辑": [ <condition>, ... ] }

  <pillar_spec>  = "全局" | "年柱" | "月柱" | "日柱" | "时柱" | [str, ...]
  <section>      = "天干" | "地支" | "藏干" | "十神" | "十神计数" |
                   "天干计数" | "地支计数" |
                   "交互" | "神煞" | "五行" | "十神_五行状态"

  位置 special key:
    "同柱": True  — resolves 柱 at runtime to the pillar captured by 前提条件's 宫位
                    evidence. Requires 前提条件 whose evaluator returns "宫位" in its
                    evidence dict. Passes that pillar name as pos["柱"] to the evaluator.


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 CONDITION EVALUATORS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 ── Ten-god (十神) ─────────────────────────────────────────────

  "十神"
    部分: "天干"|"地支"|"藏干"|"十神"|"十神计数" (omit = all)
    { "类型": "十神", "值": [str],
      "来源柱": str?,       # ten-god must also appear in this pillar
      "月令秉令": bool? }   # month-branch 本气 must match 值

  "十神_集合"
    { "类型": "十神_集合", "值": [str] }   # ALL listed must appear

  "十神_无"
    { "类型": "十神_无",  "值": [str] }   # NONE may appear

  "十神_克"
    { "类型": "十神_克",
      "克方":   [str], "被克方": [str],
      "范围": "全局"|"同柱"|"相邻柱" }   # default: "全局"

  "十神_生"
    { "类型": "十神_生",
      "生方":   [str], "被生方": [str],
      "范围": "全局"|"同柱"|"相邻柱" }

  "十神_同柱"
    { "类型": "十神_同柱", "主神": [str], "配神": [str] }
    # same pillar contains ≥1 from 主神 AND ≥1 from 配神

  "十神_五行状态"
    { "类型": "十神_五行状态", "目标十神": [str],
      "值": [str] }         # seasonal states: 旺/相/休/囚/死

  "十神_阶段在支"
    { "类型": "十神_阶段在支", "十神": str | [str], "阶段": "长生" | "墓" }
    # Checks whether the ten-god's element occupies the given 十二长生 stage at a branch.
    # Without 柱 in pos: chart-wide — ten-god stem and its stage branch may be on different pillars.
    # With 柱 in pos (e.g. 同柱: True): same-pillar — both must be on the scoped pillar.
    # "阶段" is required; supported values: "长生" (uses _CHANG_SHENG_MAP), "墓" (uses _MU_MAP).

  "十神_长生阶段"
    { "类型": "十神_长生阶段", "十神": str | [str], "阶段": [str], "参考柱": str? }
    # Checks whether a ten-god's stem placed against a reference pillar's branch falls in
    # one of the specified 十二长生 stages (e.g. ["死", "绝", "墓"]).
    # pos.柱 scopes which pillars are scanned for the ten-god (default: all four).
    # "参考柱" selects which pillar supplies the reference branch (default: "月柱").

 ── Five-elements (五行) ───────────────────────────────────────

  "五行有"
    部分: "五行"
    { "类型": "五行有", "值": [str],
      "强度": [str]? }      # e.g. ["旺","相"] — filters by seasonal state

  "五行全"
    { "类型": "五行全" }    # all five elements present globally

  "五行计数差"
    { "类型": "五行计数差", "五行A": str, "五行B": str,
      "阈值": int, "比较": "≥"|"≤"|"=" }
    # count(五行A) − count(五行B) vs threshold (stems+branches only, not 藏干)

  "五行生克"
    柱: exactly two pillars
    { "类型": "五行生克", "值": "相生"|"相克" }

  "五行交战"
    { "类型": "五行交战", "克方": str, "被克方": str }
    # globally: both elements present and ke relationship valid

  "同柱_五行克"
    { "类型": "同柱_五行克", "克方五行": str, "被克方五行": str }
    # within each specified pillar (天干 + all 藏干): both elements present

 ── Counts (计数) ──────────────────────────────────────────────

  "计数"
    部分: "十神"|"十神计数" etc.
    { "类型": "计数", "十神": [str], "阈值": int, "比较": "≥"|"≤"|"=" }

  "计数_状态"
    { "类型": "计数_状态", "十神": [str], "值": [str],
      "阈值": int, "比较": "≥"|"≤"|"=" }
    # counts ten-gods whose element has one of the given seasonal states

  "计数_差"
    { "类型": "计数_差",
      "减数十神": [str], "被减数十神": [str],
      "阈值": int, "比较": "≥"|"≤"|"=" }

  "计数_神煞"
    { "类型": "计数_神煞", "神煞": [str], "阈值": int, "比较": "≥"|"≤"|"=" }

  "计数_天干合"
    { "类型": "计数_天干合", "阈值": int, "比较": "≥"|"≤"|"=" }

  "计数_五行"
    { "类型": "计数_五行", "五行": [str], "阈值": int, "比较": "≥"|"≤"|"=" }

  "空亡计数"
    { "类型": "空亡计数", "阈值": int, "比较": "≥"|"≤"|"=" }

 ── Interactions (交互) ────────────────────────────────────────

  "交互"
    { "类型": "交互", "值": [str], "形态"?: str }
    # 值: interaction types, e.g. ["天干合"]
    # 形态 (optional): filter by sub-form, e.g. "化气格", "合绊 - 妒合"

  "交互_无"
    { "类型": "交互_无", "值": [str] }

 ── Branches & stems (地支 / 天干) ─────────────────────────────

  "地支值"
    { "类型": "地支值", "值": [str],
      "数量": int?,  "比较": "≥"|"≤"|"="? }   # omit 数量 = any-match mode

  "地支全部相同"
    { "类型": "地支全部相同" }   # all four pillars share the same branch

  "天干值"
    { "类型": "天干值", "值": [str] }

  "天干阴阳"
    { "类型": "天干阴阳", "值": "阳"|"阴" }

  "天干全部相同"
    { "类型": "天干全部相同" }   # all four pillars share the same stem

  "天干相同_跨柱"
    柱: exactly two pillars (list)
    { "类型": "天干相同_跨柱" }   # the two specified pillars share the same stem

  "地支相同_跨柱"
    柱: exactly two pillars (list)
    { "类型": "地支相同_跨柱" }   # the two specified pillars share the same branch

  "特定组合"
    部分: "干支"
    { "类型": "特定组合", "值": [str] }
    # pillar's stem+branch combo (e.g. "甲子") is in the allowed list

  "干禄在支"
    柱: target pillar to check; 来源柱: pillar whose stem's 禄 is checked (default "日柱")
    { "类型": "干禄在支", "来源柱": "时柱" }
    # specified pillar's branch equals the 来源柱 stem's 禄位 (via _LU_WEI_MAP)

 ── Stars (神煞) ────────────────────────────────────────────────

  "神煞"
    { "类型": "神煞", "值": [str], "来源": [str]? }
    # 来源 is optional — omit to match any source.
    # Valid 来源: 日干, 年干, 月支, 年支, 日支, 日柱, 时柱, 自柱, 组合, 纳音, 节气, 年纳音

  "神煞_地支相生"
    { "类型": "神煞_地支相生", "神煞A": [str], "神煞B": [str],
      "来源A": [str]?, "来源B": [str]? }
    # 地支 of 神煞A-host sheng 地支 of 神煞B-host (must be different pillars)

  "同柱_神煞"
    { "类型": "同柱_神煞", "神煞A": [str], "神煞B": [str] }
    # same pillar contains ≥1 from A AND ≥1 from B

 ── Strength & void (强弱 / 空亡) ──────────────────────────────

  "日主强弱"
    { "类型": "日主强弱", "值": [str] }   # e.g. ["身强","身弱"]

  "月令强弱"
    { "类型": "月令强弱", "值": [str] }   # checks day master's 得令 state

  "空亡"
    { "类型": "空亡", "键": str | [str] }
    # Void key(s) to check — must be explicit (no default).
    # Year/month/hour pillars: "被日柱空"
    # Day pillar only:         "被年柱空" | "被月柱空" | "被时柱空"
    # Day pillar (any):        ["被年柱空", "被月柱空", "被时柱空"]
    # Any pillar (all types):  ["被日柱空", "被年柱空", "被月柱空", "被时柱空"]

  "互换空亡"
    { "类型": "互换空亡", "键": str }
    # Mutual void key on the day pillar: "年日互换空亡" | "月日互换空亡" | "日时互换空亡"

  "空亡支_同类冲"
    { "类型": "空亡支_同类冲" }
    # Void pillar clashed by another pillar sharing the same heavenly stem.
    # Checks all void types (被日柱空, 被年/月/时柱空). Chart-wide when no 位置 given.

 ── Miscellaneous ───────────────────────────────────────────────

  "十二长生"
    { "类型": "十二长生", "子属性": "自坐"|"日干", "值": [str] }
    # 子属性 defaults to "自坐" if omitted. e.g. ["长生","帝旺"]

  "重元星"
    { "类型": "重元星" }                  # month-branch repeats in year/day/hour

  "地支三合"
    { "类型": "地支三合" }               # deferred — requires spouse chart

  "冲出藏干十神"
    { "类型": "冲出藏干十神",
      "来源柱": str,     # pillar whose branch is the clash weapon (default "日柱")
      "值": [str] }     # ten-gods to find in the clashed branch's 藏干
    # Looks up the 六冲 partner of 来源柱's branch, then checks if that partner's
    # 藏干 elements map to any of the wanted ten-gods (relative to the day master).
    # Used for 飞财格: repeated branch clashes out opposite palace's hidden wealth.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Callable

from apps.backend.astronomer_logic.twelve_life_stages import _self_seated_stage

from apps.backend.data.san_ming_tong_hui_v2 import (
    volume_2_tian_gan_predictions,
    volume_2_di_zhi_prediction,
    volume_2_di_zhi_geography_predictions,
    volume_2_nian_yue_ri_shi_predictions,
    volume_2_shi_gan_he_predictions,
    volume_2_jin_jiao_tui_fu_predictions,
    volume_2_hua_qi_predictions,
    volume_2_zhi_yuan_liu_he_predictions,
    volume_2_san_he_predictions,
    volume_2_jiang_xing_hua_gai_predictions,
    volume_2_xian_chi_predictions,
    volume_2_liu_hai_predictions,
    volume_2_san_xing_predictions,
    volume_2_chong_ji_predictions,
)
from apps.backend.data.san_ming_tong_hui_v1 import (
    volume_1_liu_shi_jiazi_predictions,
    volume_1_nayin_ge_ju_predictions,
)
from apps.backend.data.san_ming_tong_hui_v3 import (
    volume_3_lu_shen_prediction,
    volume_3_horse_star_predictions,
    volume_3_horse_fortune_predictions,
    volume_3_noble_star_predictions,
    volume_3_3_wonders_predictions,
    volume_3_heavenly_monthly_virtues_predictions,
    volume_3_tai_ji_noble_predictions,
    volume_3_academy_predictions,
    volume_3_direct_resource_predictions,
    volume_3_noble_virtue_and_elegance_predictions,
    volume_3_plundering_star_predictions,
    volume_3_sheep_blade_predictions,
    volume_3_empty_void_predictions,
    volume_3_seperation_and_discord_star_predictions,
    volume_3_hidden_gold_predictions,
    volume_3_calamity_star_predictions,
    volume_3_six_adversities_predictions,
    volume_3_hook_twist_predictions,
    volume_3_ten_great_failures_predictions,
    volume_3_heavenly_earthly_net_predictions,
    volume_3_lonely_widow_star_predictions,
    volume_3_zi_yi_sha_predictions,
    volume_3_gua_jian_sha_predictions,
    volume_3_tian_huo_sha_predictions,
    volume_3_po_sha_predictions,
    volume_3_shui_ni_sha_predictions,
    volume_3_yin_yang_sha_predictions,
    volume_3_yin_yang_cha_cuo_predictions,
    volume_3_ba_zhuan_jiu_chou_predictions,
    volume_3_gu_luan_predictions,
    volume_3_bing_fu_predictions,
    volume_3_sang_men_diao_ke_predictions,
    volume_3_tao_hua_predictions,
    volume_3_hong_yan_predictions,
    volume_3_tian_tu_sha_predictions,
    volume_3_jian_feng_sha_predictions,
    # volume_3_guan_fu_sha_predictions,
    # volume_3_si_fu_sha_predictions,
    # volume_3_zhai_mu_sha_predictions,
    # volume_3_lei_ting_sha_predictions,
    # volume_3_ri_xing_sha_predictions,
    # volume_3_liu_xue_sha_predictions,
    # volume_3_ji_feng_sha_predictions,
    # volume_3_fu_chen_sha_predictions,
    # volume_3_tun_xian_sha_predictions,
)
from apps.backend.data.san_ming_tong_hui_v6 import special_patterns_卷六
from apps.backend.data.san_ming_tong_hui_v7 import (
    family_prediction_论六亲,
    female_prediction_论女命,
    children_predictions_论小儿,
)
from apps.backend.data.san_ming_tong_hui_v4 import (
    volume_4_stems_prediction,
    volume_4_month_day_stem_prediction,
    volume_4_elements_combo_prediction,
)
from apps.backend.data.san_ming_tong_hui_v5 import volume_5_rules
from apps.backend.data.key_rules import key_rules_predictions

_ALL_PILLARS = ["年柱", "月柱", "日柱", "时柱"]
_YANG_REN_XIANG_SHI_PAIRS: frozenset[tuple[str, str]] = frozenset([
    # 甲 series → blade 乙卯
    ("甲寅", "乙卯"), ("甲辰", "乙卯"), ("甲午", "乙卯"), ("甲申", "乙卯"), ("甲戌", "乙卯"),
    # 丙 series → blade 丁午 / 连珠 → 丁未
    ("丙辰", "丁午"), ("丙戌", "丁午"), ("丙丑", "丁午"), ("丙未", "丁午"), ("丙午", "丁未"),
    # 戊 series → blade 己午 / 连珠 → 己未
    ("戊辰", "己午"), ("戊戌", "己午"), ("戊丑", "己午"), ("戊未", "己午"), ("戊午", "己未"),
    # 庚 series → blade 辛酉
    ("庚辰", "辛酉"), ("庚戌", "辛酉"), ("庚丑", "辛酉"), ("庚未", "辛酉"),
    # 壬 series → blade 癸子 / 连珠 → 癸丑
    ("壬辰", "癸子"), ("壬戌", "癸子"), ("壬丑", "癸子"), ("壬未", "癸子"), ("壬子", "癸丑"),
])
_ADJACENT_PAIRS: list[tuple[str, str]] = [
    ("年柱", "月柱"),
    ("月柱", "日柱"),
    ("日柱", "时柱"),
]


# ── ChartContext ──────────────────────────────────────────────────────────────


@dataclass
class ChartContext:
    gender: str
    pillars: dict  # 四柱实体: pillar_name → full pillar dict
    shen_sha: dict  # 神煞: pillar_name → list[{"名称": str, ...}]
    interactions: list  # 作用.柱位动态 flat list
    five_elements: dict  # 五行: element → {"状态": str, ...}
    day_master: dict  # 日主: {"天干": ..., "五行": ..., "强弱": ..., ...}
    lunar_birthday: Any | None = field(default=None)
    vault_states: list = field(default_factory=list)  # 作用.库位状态
    tai_yuan_branch: str = field(default="")  # 地支 of 胎元 conception palace


def build_chart_context(natal_chart: dict) -> ChartContext:
    return ChartContext(
        gender=natal_chart["性别"],
        pillars=natal_chart["四柱实体"],
        shen_sha=natal_chart.get("神煞", {}),
        interactions=[
            # Only material-strength interactions matter for classical text rules;
            # 轻微/极弱 interactions are filtered to avoid false rule matches.
            item
            for item in natal_chart.get("作用", {}).get("柱位动态", [])
            if item.get("强度", "强势主流") in {"强势主流", "显著影响", "中等衰减"}
        ],
        five_elements=natal_chart.get("五行", {}),
        day_master=natal_chart.get("日主", {}),
        lunar_birthday=natal_chart.get("_lunar_birthday"),
        vault_states=natal_chart.get("作用", {}).get("库位状态", []),
        tai_yuan_branch=(
            natal_chart.get("胎命身", {}).get("胎元", {}).get("干支", "")[1:][:1]
        ),
    )


# ── Constants ─────────────────────────────────────────────────────────────────

TEN_GOD_ELEMENT: dict[str, dict[str, str]] = {
    "木": {
        "比肩": "木",
        "劫财": "木",
        "食神": "火",
        "伤官": "火",
        "正财": "土",
        "偏财": "土",
        "正官": "金",
        "七杀": "金",
        "偏官": "金",
        "正印": "水",
        "偏印": "水",
    },
    "火": {
        "比肩": "火",
        "劫财": "火",
        "食神": "土",
        "伤官": "土",
        "正财": "金",
        "偏财": "金",
        "正官": "水",
        "七杀": "水",
        "偏官": "水",
        "正印": "木",
        "偏印": "木",
    },
    "土": {
        "比肩": "土",
        "劫财": "土",
        "食神": "金",
        "伤官": "金",
        "正财": "水",
        "偏财": "水",
        "正官": "木",
        "七杀": "木",
        "偏官": "木",
        "正印": "火",
        "偏印": "火",
    },
    "金": {
        "比肩": "金",
        "劫财": "金",
        "食神": "水",
        "伤官": "水",
        "正财": "木",
        "偏财": "木",
        "正官": "火",
        "七杀": "火",
        "偏官": "火",
        "正印": "土",
        "偏印": "土",
    },
    "水": {
        "比肩": "水",
        "劫财": "水",
        "食神": "木",
        "伤官": "木",
        "正财": "火",
        "偏财": "火",
        "正官": "土",
        "七杀": "土",
        "偏官": "土",
        "正印": "金",
        "偏印": "金",
    },
}

_WU_XING_SHENG: dict[str, str] = {
    "木": "火",
    "火": "土",
    "土": "金",
    "金": "水",
    "水": "木",
}
_WU_XING_KE: dict[str, str] = {
    "木": "土",
    "土": "水",
    "水": "火",
    "火": "金",
    "金": "木",
}

_LU_WEI_MAP: dict[str, str] = {
    "甲": "寅", "乙": "卯",
    "丙": "巳", "丁": "午",
    "戊": "巳", "己": "午",
    "庚": "申", "辛": "酉",
    "壬": "亥", "癸": "子",
}

_SAN_HE_GROUPS: tuple = (
    frozenset({"寅", "午", "戌"}),
    frozenset({"申", "子", "辰"}),
    frozenset({"巳", "酉", "丑"}),
    frozenset({"亥", "卯", "未"}),
)

_LIU_HE_MAP: dict[str, str] = {
    "子": "丑", "丑": "子",
    "寅": "亥", "亥": "寅",
    "卯": "戌", "戌": "卯",
    "辰": "酉", "酉": "辰",
    "巳": "申", "申": "巳",
    "午": "未", "未": "午",
}

# 天干五合 pairs: 甲↔己, 乙↔庚, 丙↔辛, 丁↔壬, 戊↔癸
_WU_HE_STEM_MAP: dict[str, str] = {
    "甲": "己", "己": "甲",
    "乙": "庚", "庚": "乙",
    "丙": "辛", "辛": "丙",
    "丁": "壬", "壬": "丁",
    "戊": "癸", "癸": "戊",
}

# 地支相害 (Six Harms) map
_HAI_MAP: dict[str, str] = {
    "子": "未", "未": "子",
    "丑": "午", "午": "丑",
    "寅": "巳", "巳": "寅",
    "卯": "辰", "辰": "卯",
    "申": "亥", "亥": "申",
    "酉": "戌", "戌": "酉",
}

# 年支 → 驿马支: San He bureau horse branch
_YEAR_BRANCH_TO_MA: dict[str, str] = {
    "申": "寅", "子": "寅", "辰": "寅",
    "亥": "巳", "卯": "巳", "未": "巳",
    "寅": "申", "午": "申", "戌": "申",
    "巳": "亥", "酉": "亥", "丑": "亥",
}

# 地支五行: earthly branch → wu xing element
_ZHI_ELEMENT: dict[str, str] = {
    "子": "水", "亥": "水",
    "寅": "木", "卯": "木",
    "巳": "火", "午": "火",
    "申": "金", "酉": "金",
    "辰": "土", "戌": "土", "丑": "土", "未": "土",
}

# 天干五行: heavenly stem → wu xing element
_GAN_ELEMENT: dict[str, str] = {
    "甲": "木", "乙": "木",
    "丙": "火", "丁": "火",
    "戊": "土", "己": "土",
    "庚": "金", "辛": "金",
    "壬": "水", "癸": "水",
}

# 地支六冲: earthly branch ↔ its clashing partner
_LIU_CHONG_ZHI: dict[str, str] = {
    "子": "午", "午": "子",
    "丑": "未", "未": "丑",
    "寅": "申", "申": "寅",
    "卯": "酉", "酉": "卯",
    "辰": "戌", "戌": "辰",
    "巳": "亥", "亥": "巳",
}

# 地支藏干五行: earthly branch → list of hidden stem elements (main first)
_ZHI_CANG_GAN_ELEMENTS: dict[str, list[str]] = {
    "子": ["水"],
    "丑": ["土", "水", "金"],
    "寅": ["木", "火", "土"],
    "卯": ["木"],
    "辰": ["土", "木", "水"],
    "巳": ["火", "金", "土"],
    "午": ["火", "土"],
    "未": ["土", "火", "木"],
    "申": ["金", "水", "土"],
    "酉": ["金"],
    "戌": ["土", "金", "火"],
    "亥": ["水", "木"],
}

# Chang Sheng offset constants for 空亡支_长生 evaluator
# (mirrors twelve_life_stages._CHANG_SHENG_OFFSET / _ORDER / _ZHI_INDEX)
_CS_ORDER: list[str] = [
    "长生", "沐浴", "冠带", "临官", "帝旺",
    "衰",   "病",   "死",   "墓",   "绝",   "胎", "养",
]
_CS_OFFSET: dict[str, int] = {
    "甲": 1,  "丙": 10, "戊": 10, "庚": 7, "壬": 4,
    "乙": 6,  "丁":  9, "己":  9, "辛": 0, "癸": 3,
}
_CS_ZHI_IDX: dict[str, int] = {
    "子": 0, "丑": 1, "寅": 2, "卯": 3, "辰": 4,  "巳": 5,
    "午": 6, "未": 7, "申": 8, "酉": 9, "戌": 10, "亥": 11,
}
_YANG_STEMS_SET: frozenset[str] = frozenset({"甲", "丙", "戊", "庚", "壬"})

# 五行墓库支: wu xing element → its tomb (墓/库) branch
_WU_XING_MU_BRANCH: dict[str, str] = {
    "木": "未",
    "火": "戌",
    "金": "丑",
    "水": "辰",
    "土": "辰",  # 己土墓辰; 戊土墓戌 — 辰 used as canonical single value
}

# 纳音元素长生支: nayin element → its 长生 branch (yang-stem cycle)
_NA_YIN_ELEM_CHANG_SHENG: dict[str, str] = {
    "金": "巳",   # 庚金长生巳
    "木": "亥",   # 甲木长生亥
    "水": "申",   # 壬水长生申
    "火": "寅",   # 丙火长生寅
    "土": "寅",   # 戊土长生寅 (土随火)
}

# 纳音元素临官支: nayin element → its 临官 branch (yang-stem cycle)
_NA_YIN_ELEM_LIN_GUAN: dict[str, str] = {
    "金": "申",   # 庚金临官申
    "木": "寅",   # 甲木临官寅
    "水": "亥",   # 壬水临官亥
    "火": "巳",   # 丙火临官巳
    "土": "巳",   # 戊土临官巳 (土随火)
}

# 五虎遁: year-stem → starting heavenly stem for 寅月
_WU_HU_DUN_START: dict[str, str] = {
    "甲": "丙", "己": "丙",
    "乙": "戊", "庚": "戊",
    "丙": "庚", "辛": "庚",
    "丁": "壬", "壬": "壬",
    "戊": "甲", "癸": "甲",
}

# Month-branch offset from 寅 (index 0) through 丑 (index 11)
_MONTH_BRANCHES: tuple = ("寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑")

# 天乙贵人 branches per stem (combined 昼/夜)
_TIAN_YI_BRANCHES: dict[str, frozenset] = {
    "甲": frozenset({"丑", "未"}),
    "乙": frozenset({"子", "申"}),
    "丙": frozenset({"酉", "亥"}),
    "丁": frozenset({"酉", "亥"}),
    "戊": frozenset({"丑", "未"}),
    "己": frozenset({"子", "申"}),
    "庚": frozenset({"丑", "未"}),
    "辛": frozenset({"寅", "午"}),
    "壬": frozenset({"卯", "巳"}),
    "癸": frozenset({"卯", "巳"}),
}


# ── Pillar helpers ────────────────────────────────────────────────────────────


def _resolve_pillars(pos_zhu: str | list | None) -> list[str]:
    if not pos_zhu or pos_zhu == "全局":
        return _ALL_PILLARS
    if isinstance(pos_zhu, str):
        return [pos_zhu]
    return list(pos_zhu)


def _get_ten_gods_in_part(pillar: dict, bu_fen: str | None) -> list[str]:
    """Extract ten-god strings from a pillar's specified section.

    部分 semantics:
      "天干"              — stem only
      "地支"              — 本气 only (月令 dominant energy)
      "藏干"              — 本气 + 中气 (余气 excluded — too weak for pattern matching)
      "十神"|"柱"|None    — stem + 本气 + 中气
      "全藏干"            — all three tiers: 本气 + 中气 + 余气 (explicit rooting checks)
    """
    result: list[str] = []
    if bu_fen in ("柱", "十神", "十神计数", None, ""):
        tg = pillar.get("天干", {}).get("十神")
        if tg:
            result.append(tg)
        for role, info in pillar.get("藏干", {}).items():
            if role == "余气":
                continue
            tg = info.get("十神")
            if tg:
                result.append(tg)
    elif bu_fen == "天干":
        tg = pillar.get("天干", {}).get("十神")
        if tg:
            result.append(tg)
    elif bu_fen == "地支":
        # Branch's dominant ten-god = 藏干 本气 only
        tg = pillar.get("藏干", {}).get("本气", {}).get("十神")
        if tg:
            result.append(tg)
    elif bu_fen == "藏干":
        for role, info in pillar.get("藏干", {}).items():
            if role == "余气":
                continue
            tg = info.get("十神")
            if tg:
                result.append(tg)
    elif bu_fen == "全藏干":
        # Explicit: all three tiers including 余气 (use for rooting/通根 checks)
        for info in pillar.get("藏干", {}).values():
            tg = info.get("十神")
            if tg:
                result.append(tg)
    return result


def _get_ten_gods_with_source(pillar: dict, bu_fen: str | None) -> list[tuple[str, str]]:
    """Like _get_ten_gods_in_part but returns (ten_god, source_section) pairs."""
    result: list[tuple[str, str]] = []
    if bu_fen in ("柱", "十神", "十神计数", None, ""):
        tg = pillar.get("天干", {}).get("十神")
        if tg:
            result.append((tg, "天干"))
        for role, info in pillar.get("藏干", {}).items():
            if role == "余气":
                continue
            tg = info.get("十神")
            if tg:
                result.append((tg, f"藏干_{role}"))
    elif bu_fen == "天干":
        tg = pillar.get("天干", {}).get("十神")
        if tg:
            result.append((tg, "天干"))
    elif bu_fen == "地支":
        tg = pillar.get("藏干", {}).get("本气", {}).get("十神")
        if tg:
            result.append((tg, "藏干_本气"))
    elif bu_fen in ("藏干", "全藏干"):
        for role, info in pillar.get("藏干", {}).items():
            if bu_fen == "藏干" and role == "余气":
                continue
            tg = info.get("十神")
            if tg:
                result.append((tg, f"藏干_{role}"))
    return result


def _interaction_matches_pillars(item: dict, pillars: list[str]) -> bool:
    combo = item.get("组合明细", {})
    return any(p in combo for p in pillars)


def _compare_threshold(value: int, threshold: int, op: str) -> bool:
    if op in ("≥", ">="): return value >= threshold
    if op in ("≤", "<="): return value <= threshold
    if op == "=": return value == threshold
    return False


# ── Condition evaluators ──────────────────────────────────────────────────────
# Each fn: (ctx, pos, target) → (bool, evidence_dict)


def eval_ten_god(ctx: ChartContext, pos: dict, target: dict) -> tuple[bool, dict]:
    pillar_spec = pos.get("柱")
    bu_fen = pos.get("部分")
    wanted = set(target.get("值", []))

    # 天干合 / 六合: find interactions of that type; check if any participating
    # pillar's stem ten-god is in wanted. For 六合 this links the branch
    # interaction back to the stem ten-god of the same pillar.
    if bu_fen in ("天干合", "六合"):
        wanted_form: str | None = target.get("形态")  # optional: e.g. "化气格"
        for item in ctx.interactions:
            if item.get("类型") == bu_fen:
                if wanted_form and item.get("形态") != wanted_form:
                    continue
                for p_name in item.get("组合明细", {}):
                    tg = ctx.pillars.get(p_name, {}).get("天干", {}).get("十神")
                    if tg in wanted:
                        ev = {f"{bu_fen}_匹配": p_name, "十神": tg}
                        if wanted_form:
                            ev["形态"] = wanted_form
                        return True, ev
        return False, {}

    pillars_to_check = _resolve_pillars(pillar_spec)
    for p in pillars_to_check:
        pillar = ctx.pillars.get(p, {})
        for tg, source in _get_ten_gods_with_source(pillar, bu_fen):
            if tg not in wanted:
                continue
            # Optional: 来源柱 — ten-god must also appear in the source pillar
            lai_yuan = target.get("来源柱")
            if lai_yuan:
                src_tgs = _get_ten_gods_in_part(ctx.pillars.get(lai_yuan, {}), None)
                if tg not in src_tgs:
                    continue
            # Optional: 月令秉令 — month branch 本气 must be in wanted
            if target.get("月令秉令"):
                ben_qi_tg = (
                    ctx.pillars.get("月柱", {})
                    .get("藏干", {})
                    .get("本气", {})
                    .get("十神")
                )
                if ben_qi_tg not in wanted:
                    continue
            return True, {"宫位": p, "十神": tg, "来源": source}
    return False, {}


def eval_ten_god_set(ctx: ChartContext, pos: dict, target: dict) -> tuple[bool, dict]:
    """ALL listed ten-gods must appear somewhere in the union of specified pillars."""
    required = set(target.get("值", []))
    pillars_to_check = _resolve_pillars(pos.get("柱"))
    bu_fen = pos.get("部分")
    found: set[str] = set()
    for p in pillars_to_check:
        found.update(_get_ten_gods_in_part(ctx.pillars.get(p, {}), bu_fen))
    if required.issubset(found):
        return True, {"十神_集合": sorted(required)}
    return False, {}


def eval_ten_god_absent(
    ctx: ChartContext, pos: dict, target: dict
) -> tuple[bool, dict]:
    """None of the listed ten-gods appear in the specified scope (default: all four pillars).

    When 部分 is "天干合" or "六合", checks interaction participants instead of pillars.
    """
    excluded = set(target.get("值", []))
    bu_fen = pos.get("部分")

    if bu_fen in ("天干合", "六合"):
        for item in ctx.interactions:
            if item.get("类型") == bu_fen:
                for p_name in item.get("组合明细", {}):
                    tg = ctx.pillars.get(p_name, {}).get("天干", {}).get("十神")
                    if tg in excluded:
                        return False, {}
        return True, {"十神_无": sorted(excluded)}

    pillars = _resolve_pillars(pos.get("柱")) if pos.get("柱") else _ALL_PILLARS
    for p in pillars:
        for tg in _get_ten_gods_in_part(ctx.pillars.get(p, {}), bu_fen):
            if tg in excluded:
                return False, {}
    return True, {"十神_无": sorted(excluded)}


def eval_di_shi(ctx: ChartContext, pos: dict, target: dict) -> tuple[bool, dict]:
    wanted = set(target.get("值", []))
    sub = target.get("子属性", "自坐")
    for p in _resolve_pillars(pos.get("柱")):
        value = ctx.pillars.get(p, {}).get("十二长生", {}).get(sub)
        if value in wanted:
            return True, {"宫位": p, f"十二长生_{sub}": value}
    return False, {}


def eval_di_shi_absent(ctx: ChartContext, pos: dict, target: dict) -> tuple[bool, dict]:
    """十二长生_无: none of the listed 十二长生 phases appear on the resolved pillar(s)."""
    excluded = set(target.get("值", []))
    sub = target.get("子属性", "自坐")
    for p in _resolve_pillars(pos.get("柱")):
        value = ctx.pillars.get(p, {}).get("十二长生", {}).get(sub)
        if value in excluded:
            return False, {}
    return True, {"十二长生_无": sorted(excluded)}


def eval_shen_sha(ctx: ChartContext, pos: dict, target: dict) -> tuple[bool, dict]:
    shen_sha = set(target.get("值", []))
    shen_sha_sources = set(target.get("来源", []))
    allowed_states: list[str] | None = target.get("强度")
    for p in _resolve_pillars(pos.get("柱")):
        for star in ctx.shen_sha.get(p, []):
            if star.get("名称") not in shen_sha:
                continue
            if shen_sha_sources and star.get("来源") not in shen_sha_sources:
                continue
            if allowed_states is not None:
                branch_elem = ctx.pillars.get(p, {}).get("地支", {}).get("五行")
                if not branch_elem or ctx.five_elements.get(branch_elem, {}).get("状态") not in allowed_states:
                    continue
            return True, {"宫位": p, "神煞": star["名称"], "来源": star.get("来源")}
    return False, {}


def eval_shen_sha_absent(ctx: ChartContext, pos: dict, target: dict) -> tuple[bool, dict]:
    ok, _ = eval_shen_sha(ctx, pos, target)
    if ok:
        return False, {}
    return True, {"神煞_无": sorted(target.get("值", []))}


def eval_shen_sha_dizhi_sheng(
    ctx: ChartContext, pos: dict, target: dict
) -> tuple[bool, dict]:
    """地支相生 between the host pillars of two shen sha groups.
    Returns False when both shen sha land in the same pillar (self-generation).
    """
    sha_a = set(target.get("神煞A", []))
    sha_b = set(target.get("神煞B", []))
    shen_sha_sources_a = set(target.get("来源A", []))
    shen_sha_sources_b = set(target.get("来源B", []))
    pillars = _resolve_pillars(pos.get("柱"))

    def find_hosts(names: set, sources: set) -> list[tuple[str, str]]:
        out = []
        for p in pillars:
            if any(
                s.get("名称") in names
                and (not sources or s.get("来源") in sources)
                for s in ctx.shen_sha.get(p, [])
            ):
                elem = ctx.pillars.get(p, {}).get("地支", {}).get("五行")
                if elem:
                    out.append((p, elem))
        return out

    for p_a, e_a in find_hosts(sha_a, shen_sha_sources_a):
        for p_b, e_b in find_hosts(sha_b, shen_sha_sources_b):
            if p_a == p_b:
                continue
            if _WU_XING_SHENG.get(e_a) == e_b or _WU_XING_SHENG.get(e_b) == e_a:
                gen = e_a if _WU_XING_SHENG.get(e_a) == e_b else e_b
                return True, {"神煞A宫位": p_a, "神煞B宫位": p_b, "生方五行": gen}
    return False, {}


def eval_shen_sha_same_pillar(
    ctx: ChartContext, pos: dict, target: dict
) -> tuple[bool, dict]:
    sha_a = set(target.get("神煞A", []))
    sha_b = set(target.get("神煞B", []))
    shen_sha_sources = set(target.get("来源", []))
    for p in _resolve_pillars(pos.get("柱")):
        pillar_stars = ctx.shen_sha.get(p, [])
        if shen_sha_sources:
            pillar_stars = [s for s in pillar_stars if s.get("来源") in shen_sha_sources]
        names = {s.get("名称") for s in pillar_stars}
        matched_a = names & sha_a
        matched_b = names & sha_b
        if matched_a and matched_b:
            return True, {"宫位": p, "神煞A": next(iter(matched_a)), "神煞B": next(iter(matched_b))}
    return False, {}


_ONEWAY_VOID_KEYS = ("被年柱空", "被月柱空", "被时柱空")
_ALL_VOID_KEYS    = ("被日柱空", "被年柱空", "被月柱空", "被时柱空")
_MUTUAL_VOID_KEYS = ("年日互换空亡", "月日互换空亡", "日时互换空亡")


def eval_kong_wang(ctx: ChartContext, pos: dict, target: dict) -> tuple[bool, dict]:
    raw = target.get("键", "被日柱空")
    keys: list[str] = [raw] if isinstance(raw, str) else raw
    for p in _resolve_pillars(pos.get("柱")):
        void_dict = ctx.pillars.get(p, {}).get("空亡", {})
        for k in keys:
            val = void_dict.get(k, "无")
            if val and val != "无":
                return True, {"宫位": p, k: val}
    return False, {}


def eval_kong_wang_zhi_wuxing(ctx: ChartContext, pos: dict, target: dict) -> tuple[bool, dict]:
    """空亡支_五行: check 五行 element of the void BRANCH (the pillar's own 地支 that is void).

    Used with 同柱: True so the pillar is already bound to one that 前提条件 confirmed is void.
    Checks the pillar's 地支 element — NOT 本柱旬空 (which lists both branches of the pillar's
    own 旬 and would match two different elements, causing spurious multi-rule firing).
    """
    wanted = set(target.get("值", []))
    _void_keys = ("被日柱空", "被年柱空", "被月柱空", "被时柱空")
    for p in _resolve_pillars(pos.get("柱")):
        void_dict = ctx.pillars.get(p, {}).get("空亡", {})
        if not any(void_dict.get(k, "无") != "无" for k in _void_keys):
            continue
        branch_char = ctx.pillars.get(p, {}).get("地支", {}).get("地支", "")
        elem = _ZHI_ELEMENT.get(branch_char)
        if elem in wanted:
            return True, {"宫位": p, "空亡支": branch_char, "空亡支五行": elem}
    return False, {}


def eval_kong_wang_zhi_value(ctx: ChartContext, pos: dict, target: dict) -> tuple[bool, dict]:
    """空亡支_地支值: check if any void BRANCH character is in the wanted list (e.g. 四孟真空亡)."""
    wanted = set(target.get("值", []))
    for p in _resolve_pillars(pos.get("柱")):
        void_str = ctx.pillars.get(p, {}).get("空亡", {}).get("本柱旬空", "")
        if not void_str:
            continue
        for ch in void_str:
            if ch in wanted:
                return True, {"宫位": p, "空亡支": ch}
    return False, {}


def eval_rizhu_ke_kongwang(ctx: ChartContext, pos: dict, target: dict) -> tuple[bool, dict]:
    """日主克空亡支: day master element克s the void branch (the pillar's own 地支) main element
    or any of its hidden stem elements.

    Uses the pillar's 地支 (the branch that IS void), not 本柱旬空, for the same reason as
    eval_kong_wang_zhi_wuxing: 本柱旬空 is the pillar's own 旬's two void branches, not the
    specific branch that is void in this chart.
    """
    dm_element = ctx.day_master.get("五行")
    if not dm_element:
        return False, {}
    overcomes = _WU_XING_KE.get(dm_element)
    _void_keys = ("被日柱空", "被年柱空", "被月柱空", "被时柱空")
    for p in _resolve_pillars(pos.get("柱")):
        void_dict = ctx.pillars.get(p, {}).get("空亡", {})
        if not any(void_dict.get(k, "无") != "无" for k in _void_keys):
            continue
        branch_char = ctx.pillars.get(p, {}).get("地支", {}).get("地支", "")
        if not branch_char:
            continue
        elements_to_check = [_ZHI_ELEMENT.get(branch_char)] + _ZHI_CANG_GAN_ELEMENTS.get(branch_char, [])
        if overcomes in elements_to_check:
            return True, {"宫位": p, "日主五行": dm_element, "空亡支": branch_char, "克制五行": overcomes}
    return False, {}


def eval_kong_wang_zhi_changsheng(ctx: ChartContext, pos: dict, target: dict) -> tuple[bool, dict]:
    """空亡支_长生: compute day master's 十二长生 stage IN the void branch on-the-fly."""
    wanted = set(target.get("值", []))
    dm_stem = ctx.day_master.get("天干")
    if not dm_stem or dm_stem not in _CS_OFFSET:
        return False, {}
    offset = _CS_OFFSET[dm_stem]
    for p in _resolve_pillars(pos.get("柱")):
        void_str = ctx.pillars.get(p, {}).get("空亡", {}).get("本柱旬空", "")
        if not void_str:
            continue
        for ch in void_str:
            zhi_idx = _CS_ZHI_IDX.get(ch)
            if zhi_idx is None:
                continue
            if dm_stem in _YANG_STEMS_SET:
                idx = (offset + zhi_idx) % 12
            else:
                idx = (offset - zhi_idx) % 12
            stage = _CS_ORDER[idx]
            if stage in wanted:
                return True, {"宫位": p, "空亡支": ch, "日主长生": stage}
    return False, {}


def eval_kong_wang_tongwei_chong(ctx: ChartContext, pos: dict, target: dict) -> tuple[bool, dict]:
    """空亡支_同类冲: void pillar clashed by another pillar sharing the same stem → void locked, most toxic."""
    for p in _resolve_pillars(pos.get("柱")):
        void_dict = ctx.pillars.get(p, {}).get("空亡", {})
        if not any(void_dict.get(k, "无") != "无" for k in _ALL_VOID_KEYS):
            continue
        p_stem = ctx.pillars.get(p, {}).get("天干", {}).get("天干")
        p_branch = ctx.pillars.get(p, {}).get("地支", {}).get("地支")
        if not p_stem or not p_branch:
            continue
        clash_partner = _LIU_CHONG_ZHI.get(p_branch)
        for other_p, other_data in ctx.pillars.items():
            if other_p == p:
                continue
            other_stem = other_data.get("天干", {}).get("天干")
            other_branch = other_data.get("地支", {}).get("地支")
            if other_stem == p_stem and other_branch == clash_partner:
                return True, {"空亡柱": p, "同类冲柱": other_p}
    return False, {}


def eval_huhuan_kong_wang(ctx: ChartContext, pos: dict, target: dict) -> tuple[bool, dict]:
    """互换空亡: check if a pillar carries a specific mutual void key (年日互换空亡 etc.)."""
    key = target.get("键", "")
    if not key:
        return False, {}
    for p in _resolve_pillars(pos.get("柱")):
        val = ctx.pillars.get(p, {}).get("空亡", {}).get(key)
        if val:
            return True, {"宫位": p, key: val}
    return False, {}


def eval_interaction(ctx: ChartContext, pos: dict, target: dict) -> tuple[bool, dict]:
    wanted = set(target.get("值", []))
    wanted_form: str | None = target.get("形态")  # optional sub-form filter, e.g. "化气格"
    wanted_strength: set | None = set(target["强度"]) if "强度" in target else None
    pillar_spec = pos.get("柱")

    def _item_matches(item: dict) -> bool:
        if item.get("类型") not in wanted:
            return False
        if wanted_form and item.get("形态") != wanted_form:
            return False
        if wanted_strength and item.get("强度") not in wanted_strength:
            return False
        return True

    if pillar_spec == "全局":
        for item in ctx.interactions:
            if _item_matches(item):
                ev: dict = {"交互类型": item.get("类型")}
                if wanted_form:
                    ev["形态"] = item.get("形态")
                if wanted_strength:
                    ev["强度"] = item.get("强度")
                return True, ev
        return False, {}
    pillars_to_check = _resolve_pillars(pillar_spec)
    for item in ctx.interactions:
        if _item_matches(item) and _interaction_matches_pillars(item, pillars_to_check):
            ev = {"交互类型": item.get("类型"), "涉及柱": pillars_to_check}
            if wanted_form:
                ev["形态"] = item.get("形态")
            if wanted_strength:
                ev["强度"] = item.get("强度")
            return True, ev
    return False, {}


def eval_interaction_absent(
    ctx: ChartContext, pos: dict, target: dict
) -> tuple[bool, dict]:
    """No harmonizing interaction of specified types exists between the specified pillars."""
    wanted_types = set(target.get("值", []))
    check_sheng = "五行相生" in wanted_types or "五行生克" in wanted_types
    check_ke = "五行相克" in wanted_types or "五行生克" in wanted_types
    interaction_types = wanted_types - {"五行生克", "五行相生", "五行相克"}
    pillars_to_check = _resolve_pillars(pos.get("柱"))

    for item in ctx.interactions:
        if item.get("类型") in interaction_types and _interaction_matches_pillars(
            item, pillars_to_check
        ):
            return False, {}

    if (check_sheng or check_ke) and len(pillars_to_check) == 2:
        p1, p2 = pillars_to_check
        e1 = ctx.pillars.get(p1, {}).get("天干", {}).get("五行")
        e2 = ctx.pillars.get(p2, {}).get("天干", {}).get("五行")
        if e1 and e2:
            if check_sheng and (
                _WU_XING_SHENG.get(e1) == e2 or _WU_XING_SHENG.get(e2) == e1
            ):
                return False, {}
            if check_ke and (_WU_XING_KE.get(e1) == e2 or _WU_XING_KE.get(e2) == e1):
                return False, {}

    return True, {"交互_无": sorted(wanted_types), "涉及柱": pillars_to_check}


def eval_counter(ctx: ChartContext, pos: dict, target: dict) -> tuple[bool, dict]:
    bu_fen = pos.get("部分")
    threshold: int = target.get("阈值", 0)
    comparator: str = target.get("比较", "≥")

    if bu_fen == "天干计数":
        wanted = set(target.get("天干", []))
        if not wanted:
            return False, {}
        matches = [
            {"宫位": p, "天干": ctx.pillars.get(p, {}).get("天干", {}).get("天干")}
            for p in _ALL_PILLARS
            if ctx.pillars.get(p, {}).get("天干", {}).get("天干") in wanted
        ]
        ok = _compare_threshold(len(matches), threshold, comparator)
        return (ok, {"天干计数": sorted(wanted), "计数": len(matches), "匹配": matches}) if ok else (False, {})

    if bu_fen == "地支计数":
        wanted = set(target.get("地支", []))
        if not wanted:
            return False, {}
        matches = [
            {"宫位": p, "地支": ctx.pillars.get(p, {}).get("地支", {}).get("地支")}
            for p in _ALL_PILLARS
            if ctx.pillars.get(p, {}).get("地支", {}).get("地支") in wanted
        ]
        ok = _compare_threshold(len(matches), threshold, comparator)
        return (ok, {"地支计数": sorted(wanted), "计数": len(matches), "匹配": matches}) if ok else (False, {})

    ten_shen_spec = target.get("十神")
    if not ten_shen_spec:
        return False, {}
    wanted = {ten_shen_spec} if isinstance(ten_shen_spec, str) else set(ten_shen_spec)
    matches = []
    for p in _ALL_PILLARS:
        for tg, source in _get_ten_gods_with_source(ctx.pillars.get(p, {}), bu_fen):
            if tg in wanted:
                matches.append({"宫位": p, "十神": tg, "来源": source})

    ok = _compare_threshold(len(matches), threshold, comparator)
    return (ok, {"十神计数": sorted(wanted), "计数": len(matches), "匹配": matches}) if ok else (False, {})


def eval_ten_god_count_by_state(ctx: ChartContext, _pos: dict, target: dict) -> tuple[bool, dict]:
    """Count ten-gods whose five-element has one of the wanted seasonal states, compare to threshold."""
    ten_shen_spec = target.get("十神")
    if not ten_shen_spec:
        return False, {}
    wanted_tgs = (
        {ten_shen_spec} if isinstance(ten_shen_spec, str) else set(ten_shen_spec)
    )
    wanted_states = set(target.get("值", []))
    threshold: int = target.get("阈值", 0)
    comparator: str = target.get("比较", "≥")
    dm_element = ctx.day_master.get("五行")
    if not dm_element:
        return False, {}
    tg_to_element = TEN_GOD_ELEMENT.get(dm_element, {})

    matches = []
    for p in _ALL_PILLARS:
        for tg, source in _get_ten_gods_with_source(ctx.pillars.get(p, {}), None):
            if tg not in wanted_tgs:
                continue
            element = tg_to_element.get(tg)
            if not element:
                continue
            state = ctx.five_elements.get(element, {}).get("状态")
            if state in wanted_states:
                matches.append({"宫位": p, "十神": tg, "来源": source, "状态": state})

    ok = _compare_threshold(len(matches), threshold, comparator)
    return (
        (ok, {"计数_状态": sorted(wanted_tgs), "状态": sorted(wanted_states), "计数": len(matches), "匹配": matches})
        if ok
        else (False, {})
    )


def eval_ten_god_count_diff(ctx: ChartContext, pos: dict, target: dict) -> tuple[bool, dict]:
    """count(减数十神) - count(被减数十神) compared to threshold."""
    minuend = set(target.get("减数十神", []))
    subtrahend = set(target.get("被减数十神", []))
    threshold: int = target.get("阈值", 0)
    comparator: str = target.get("比较", "≥")
    matches_a: list[dict] = []
    matches_b: list[dict] = []
    for p in _ALL_PILLARS:
        for tg, source in _get_ten_gods_with_source(ctx.pillars.get(p, {}), None):
            if tg in minuend:
                matches_a.append({"宫位": p, "十神": tg, "来源": source})
            if tg in subtrahend:
                matches_b.append({"宫位": p, "十神": tg, "来源": source})
    diff = len(matches_a) - len(matches_b)
    ok = _compare_threshold(diff, threshold, comparator)
    return (
        (ok, {
            "计数_差": diff,
            "减数十神": sorted(minuend), "减数匹配": matches_a,
            "被减数十神": sorted(subtrahend), "被减数匹配": matches_b,
        })
        if ok
        else (False, {})
    )


def eval_shen_sha_count(
    ctx: ChartContext, _pos: dict, target: dict
) -> tuple[bool, dict]:
    wanted = set(target.get("神煞", []))
    if not wanted:
        return False, {}
    shen_sha_sources = set(target.get("来源", []))
    threshold: int = target.get("阈值", 0)
    comparator: str = target.get("比较", "≥")
    count = sum(
        1
        for p in _ALL_PILLARS
        for star in ctx.shen_sha.get(p, [])
        if star.get("名称") in wanted
        and (not shen_sha_sources or star.get("来源") in shen_sha_sources)
    )
    ok = _compare_threshold(count, threshold, comparator)
    return (ok, {"神煞计数": sorted(wanted), "计数": count}) if ok else (False, {})


def eval_shen_sha_count_diff(ctx: ChartContext, _pos: dict, target: dict) -> tuple[bool, dict]:
    """计数_神煞_差: count(神煞A) - count(神煞B) compared against threshold."""
    sha_a = set(target.get("神煞A", []))
    sha_b = set(target.get("神煞B", []))
    threshold: int = target.get("阈值", 1)
    comparator: str = target.get("比较", "≥")
    if not sha_a or not sha_b:
        return False, {}

    def _count(names: set) -> int:
        return sum(
            1
            for p in _ALL_PILLARS
            for star in ctx.shen_sha.get(p, [])
            if star.get("名称") in names
        )

    count_a = _count(sha_a)
    count_b = _count(sha_b)
    diff = count_a - count_b
    ok = _compare_threshold(diff, threshold, comparator)
    return (ok, {"神煞A": sorted(sha_a), "神煞B": sorted(sha_b), "差值": diff}) if ok else (False, {})


def eval_stem_harmony_count(
    ctx: ChartContext, _pos: dict, target: dict
) -> tuple[bool, dict]:
    threshold: int = target.get("阈值", 0)
    comparator: str = target.get("比较", "≥")
    count = sum(1 for item in ctx.interactions if item.get("类型") == "天干合")
    ok = _compare_threshold(count, threshold, comparator)
    return (ok, {"天干合_计数": count}) if ok else (False, {})


def _check_ten_god_element_pair(
    ctx: ChartContext,
    pos: dict,
    agent_group: set,
    patient_group: set,
    relation_map: dict,
    agent_key: str,
    patient_key: str,
    fan_wei: str,
) -> tuple[bool, dict]:
    """Check if any ten-god in agent_group has a relation_map link to any in patient_group.

    Respects fan_wei scope (全局 / 同柱 / 相邻柱). When pos contains a 柱 constraint it
    overrides fan_wei and narrows the search to those pillars only.
    """
    dm_element = ctx.day_master.get("五行")
    if not dm_element:
        return False, {}
    tg_to_element = TEN_GOD_ELEMENT.get(dm_element, {})

    def _hits(pillars: list[str], wanted: set) -> list[tuple[str, str, str]]:
        return [
            (p, tg, tg_to_element[tg])
            for p in pillars
            for tg in _get_ten_gods_in_part(ctx.pillars.get(p, {}), None)
            if tg in wanted and tg_to_element.get(tg)
        ]

    pillar_constraint = pos.get("柱")
    if pillar_constraint:
        search_pillars = _resolve_pillars(pillar_constraint)
        for p1, tg1, e1 in _hits(search_pillars, agent_group):
            for p2, tg2, e2 in _hits(search_pillars, patient_group):
                if relation_map.get(e1) == e2:
                    return True, {agent_key: tg1, f"{agent_key}宫位": p1, patient_key: tg2, f"{patient_key}宫位": p2}
        return False, {}

    if fan_wei == "全局":
        for p1, tg1, e1 in _hits(_ALL_PILLARS, agent_group):
            for p2, tg2, e2 in _hits(_ALL_PILLARS, patient_group):
                if relation_map.get(e1) == e2:
                    return True, {agent_key: tg1, f"{agent_key}宫位": p1, patient_key: tg2, f"{patient_key}宫位": p2}
    elif fan_wei == "同柱":
        for p in _ALL_PILLARS:
            for _, tg1, e1 in _hits([p], agent_group):
                for _, tg2, e2 in _hits([p], patient_group):
                    if relation_map.get(e1) == e2:
                        return True, {agent_key: tg1, patient_key: tg2, "宫位": p}
    elif fan_wei == "相邻柱":
        for p1, p2 in _ADJACENT_PAIRS:
            for _, tg1, e1 in _hits([p1], agent_group):
                for _, tg2, e2 in _hits([p2], patient_group):
                    if relation_map.get(e1) == e2:
                        return True, {agent_key: tg1, f"{agent_key}宫位": p1, patient_key: tg2, f"{patient_key}宫位": p2}
    return False, {}


def eval_ten_god_ke(ctx: ChartContext, pos: dict, target: dict) -> tuple[bool, dict]:
    """Ten-god controlling (克) relationship. Supports 全局 / 同柱 / 相邻柱 scope."""
    return _check_ten_god_element_pair(
        ctx, pos,
        agent_group=set(target.get("克方", [])),
        patient_group=set(target.get("被克方", [])),
        relation_map=_WU_XING_KE,
        agent_key="克方",
        patient_key="被克方",
        fan_wei=target.get("范围", "全局"),
    )


def eval_ten_god_sheng(ctx: ChartContext, pos: dict, target: dict) -> tuple[bool, dict]:
    """Ten-god generating (生) relationship. Supports 全局 / 同柱 / 相邻柱 scope."""
    return _check_ten_god_element_pair(
        ctx, pos,
        agent_group=set(target.get("生方", [])),
        patient_group=set(target.get("被生方", [])),
        relation_map=_WU_XING_SHENG,
        agent_key="生方",
        patient_key="被生方",
        fan_wei=target.get("范围", "全局"),
    )


def eval_sha_zhi_wu_xing_relation(ctx: ChartContext, _pos: dict, target: dict) -> tuple[bool, dict]:
    """Wu-xing ke/sheng between a shen sha's branch element and any pillar's stem or branch element.

    The sha's element is the five-element of the earthly branch on which it sits —
    the classical basis for '身克煞' / '煞克身' judgements.

    Schema:
      { "类型": "神煞支_五行关系",
        "关系": "克" | "被克" | "生" | "被生",  # direction relative to 柱/部分
        "神煞": [str],   # shen sha names whose branch element is used
        "柱":   str,     # required: 年柱 | 月柱 | 日柱 | 时柱
        "部分": str      # required: 天干 | 地支
      }
    Semantics of 关系 (reference = 柱/部分 element, sha = sha branch element):
      克   → reference 克s sha   (e.g., 身克煞)
      被克 → sha 克s reference   (e.g., 煞克身)
      生   → reference 生s sha
      被生 → sha 生s reference   (e.g., 煞生身)
    """
    sha_names = set(target.get("神煞", []))
    relation = target.get("关系")
    ref_pillar = target.get("柱")
    ref_part = target.get("部分")
    if not sha_names or not relation or not ref_pillar or not ref_part:
        return False, {}

    ref_pillar_data = ctx.pillars.get(ref_pillar, {})
    if ref_part == "天干":
        ref_elem = ref_pillar_data.get("天干", {}).get("五行")
    else:
        ref_elem = ref_pillar_data.get("地支", {}).get("五行")
    if not ref_elem:
        return False, {}

    for p in _ALL_PILLARS:
        if not any(s.get("名称") in sha_names for s in ctx.shen_sha.get(p, [])):
            continue
        sha_elem = ctx.pillars.get(p, {}).get("地支", {}).get("五行")
        if not sha_elem:
            continue
        if relation == "克" and _WU_XING_KE.get(ref_elem) == sha_elem:
            return True, {"宫位": p, "参考柱": ref_pillar, "参考五行": ref_elem, "神煞地支五行": sha_elem}
        if relation == "被克" and _WU_XING_KE.get(sha_elem) == ref_elem:
            return True, {"宫位": p, "参考柱": ref_pillar, "参考五行": ref_elem, "神煞地支五行": sha_elem}
        if relation == "生" and _WU_XING_SHENG.get(ref_elem) == sha_elem:
            return True, {"宫位": p, "参考柱": ref_pillar, "参考五行": ref_elem, "神煞地支五行": sha_elem}
        if relation == "被生" and _WU_XING_SHENG.get(sha_elem) == ref_elem:
            return True, {"宫位": p, "参考柱": ref_pillar, "参考五行": ref_elem, "神煞地支五行": sha_elem}
    return False, {}


def eval_sha_zhi_wu_xing_relation_absent(ctx: ChartContext, pos: dict, target: dict) -> tuple[bool, dict]:
    """Negation of 神煞支_五行关系 — true when the specified relationship does NOT hold.

    Schema: same as 神煞支_五行关系, type key is "神煞支_五行关系_无".
    """
    matched, _ = eval_sha_zhi_wu_xing_relation(ctx, pos, target)
    return (not matched), {}


def eval_ten_god_same_pillar(
    ctx: ChartContext, pos: dict, target: dict
) -> tuple[bool, dict]:
    """Check if 主神 and 配神 ten-god groups co-exist in the same pillar."""
    zhu_shen = set(target.get("主神", []))
    pei_shen = set(target.get("配神", []))
    pillars = _resolve_pillars(pos.get("柱"))

    for p in pillars:
        tgs = set(_get_ten_gods_in_part(ctx.pillars.get(p, {}), None))
        found_zhu = tgs & zhu_shen
        found_pei = tgs & pei_shen
        if found_zhu and found_pei:
            return True, {
                "宫位": p,
                "主神": next(iter(found_zhu)),
                "配神": next(iter(found_pei)),
            }
    return False, {}


def eval_wu_xing_relation(
    ctx: ChartContext, pos: dict, target: dict
) -> tuple[bool, dict]:
    """Five-element generating or controlling relationship between stems of two pillars."""
    pillars_to_check = _resolve_pillars(pos.get("柱"))
    if len(pillars_to_check) != 2:
        return False, {}
    relation = target.get("值")  # "相生" | "相克"
    p1, p2 = pillars_to_check
    e1 = ctx.pillars.get(p1, {}).get("天干", {}).get("五行")
    e2 = ctx.pillars.get(p2, {}).get("天干", {}).get("五行")
    if not e1 or not e2:
        return False, {}
    if relation == "相生":
        ok = _WU_XING_SHENG.get(e1) == e2 or _WU_XING_SHENG.get(e2) == e1
    elif relation == "相克":
        ok = _WU_XING_KE.get(e1) == e2 or _WU_XING_KE.get(e2) == e1
    else:
        ok = False
    return (ok, {"五行生克": relation, p1: e1, p2: e2}) if ok else (False, {})


def eval_ten_god_wu_xing_state(
    ctx: ChartContext, pos: dict, target: dict
) -> tuple[bool, dict]:
    """Check that a target ten-god's element has the specified seasonal state."""
    target_tgs = set(target.get("目标十神", []))
    wanted_states = set(target.get("值", []))
    dm_element = ctx.day_master.get("五行")
    if not dm_element:
        return False, {}
    tg_to_element = TEN_GOD_ELEMENT.get(dm_element, {})

    for p in _resolve_pillars(pos.get("柱")):
        for tg in _get_ten_gods_in_part(ctx.pillars.get(p, {}), None):
            if tg not in target_tgs:
                continue
            element = tg_to_element.get(tg)
            if not element:
                continue
            state = ctx.five_elements.get(element, {}).get("状态")
            if state in wanted_states:
                return True, {"宫位": p, "十神": tg, "五行": element, "状态": state}
    return False, {}


def eval_ten_god_element_attribute(
    ctx: ChartContext, pos: dict, target: dict
) -> tuple[bool, dict]:
    """Generic evaluator: finds stems/藏干 with specified ten-gods, checks their 五行 attribute.

    Condition target fields:
        "十神"       list[str]   — ten-gods to scan for (default: ["正官"])
        "值"         list[str]   — expected element values (e.g. ["金"])
        "读取来源"   list[str]   — "天干" | "藏干" | both (default: both)

    Pillar scope is controlled by the "位置" key in the parent condition dict.
    """
    wanted_elements = set(target.get("值", []))
    wanted_tg = set(target.get("十神", ["正官"]))
    sources = set(target.get("读取来源", ["天干", "藏干"]))

    for p in _resolve_pillars(pos.get("柱")):
        pillar = ctx.pillars.get(p, {})

        if "天干" in sources:
            tg_info = pillar.get("天干", {})
            if tg_info.get("十神") in wanted_tg:
                element = tg_info.get("五行")
                if element in wanted_elements:
                    return True, {"宫位": p, "来源": "天干",
                                  "十神": tg_info.get("十神"), "五行": element}

        if "藏干" in sources:
            for role, cg_info in pillar.get("藏干", {}).items():
                if not isinstance(cg_info, dict):
                    continue
                if cg_info.get("十神") in wanted_tg:
                    element = cg_info.get("五行")
                    if element in wanted_elements:
                        return True, {"宫位": p, "来源": f"藏干_{role}",
                                      "十神": cg_info.get("十神"), "五行": element}

    return False, {}


def eval_ri_zhu_strength(
    ctx: ChartContext, pos: dict, target: dict
) -> tuple[bool, dict]:
    wanted = set(target.get("值", []))
    strength = ctx.day_master.get("强弱")
    if strength in wanted:
        return True, {"日主强弱": strength}
    return False, {}


def eval_wu_gen(
    ctx: ChartContext, pos: dict, _target: dict
) -> tuple[bool, dict]:
    """无根: the source pillar's element does not appear in any branch's hidden stems (chart-wide).
    pos keys: 柱 (default 日柱), 部分 (default 天干).
    """
    pillar_name = pos.get("柱", "日柱")
    part = pos.get("部分", "天干")
    source_elem = ctx.pillars.get(pillar_name, {}).get(part, {}).get("五行")
    if not source_elem:
        return False, {}
    for p in _ALL_PILLARS:
        for stem_info in ctx.pillars.get(p, {}).get("藏干", {}).values():
            if isinstance(stem_info, dict) and stem_info.get("五行") == source_elem:
                return False, {}
    return True, {"柱": pillar_name, "部分": part, "五行": source_elem}


def eval_branch_value(ctx: ChartContext, pos: dict, target: dict) -> tuple[bool, dict]:
    wanted = set(target.get("值", []))
    pillars = _resolve_pillars(pos.get("柱"))

    if "数量" in target:
        threshold: int = target["数量"]
        comparator: str = target.get("比较", "≥")
        found = {
            ctx.pillars.get(p, {}).get("地支", {}).get("地支") for p in pillars
        } & wanted
        count = len(found)
        ok = _compare_threshold(count, threshold, comparator)
        return (ok, {"地支_匹配": sorted(found), "计数": count}) if ok else (False, {})

    for p in pillars:
        branch = ctx.pillars.get(p, {}).get("地支", {}).get("地支")
        if branch in wanted:
            return True, {"宫位": p, "地支": branch}
    return False, {}


# 外部_ conditions require the spouse's chart — deferred
def eval_branch_triple(ctx: ChartContext, pos: dict, target: dict) -> tuple[bool, dict]:
    return False, {}


def eval_stem_value(ctx: ChartContext, pos: dict, target: dict) -> tuple[bool, dict]:
    wanted = set(target.get("值", []))
    for p in _resolve_pillars(pos.get("柱")):
        stem = ctx.pillars.get(p, {}).get("天干", {}).get("天干")
        if stem in wanted:
            return True, {"宫位": p, "天干": stem}
    return False, {}


def eval_yue_ling_strength(
    ctx: ChartContext, _pos: dict, target: dict
) -> tuple[bool, dict]:
    wanted = set(target.get("值", []))
    state_full = ctx.day_master.get("得令", {}).get("状态", "")
    state = state_full.split(" ")[0] if state_full else ""
    if state in wanted:
        return True, {"月令强弱": state}
    return False, {}


def eval_stem_yinyang(
    ctx: ChartContext, pos: dict, target: dict
) -> tuple[bool, dict]:
    wanted = target.get("值")
    for p in _resolve_pillars(pos.get("柱")):
        tian_gan = ctx.pillars.get(p, {}).get("天干", {})
        stem = tian_gan.get("天干")
        yinyang = tian_gan.get("阴阳")
        if stem and yinyang == wanted:
            return True, {"宫位": p, "天干": stem, "阴阳": yinyang}
    return False, {}


def eval_kong_wang_count(
    ctx: ChartContext, _pos: dict, target: dict
) -> tuple[bool, dict]:
    threshold: int = target.get("阈值", 0)
    comparator: str = target.get("比较", "≥")
    count = 0
    for p in _ALL_PILLARS:
        void_dict = ctx.pillars.get(p, {}).get("空亡", {})
        if void_dict.get("被日柱空", "无") != "无":
            count += 1
    ok = _compare_threshold(count, threshold, comparator)
    return (ok, {"空亡计数": count}) if ok else (False, {})


def eval_wu_xing_present(
    ctx: ChartContext, _pos: dict, target: dict
) -> tuple[bool, dict]:
    wanted = set(target.get("值", []))
    allowed_states: list[str] | None = target.get("强度")
    for p in _ALL_PILLARS:
        pillar = ctx.pillars.get(p, {})
        for source, part in (("天干", pillar.get("天干", {})), ("地支", pillar.get("地支", {}))):
            element = part.get("五行")
            if element not in wanted:
                continue
            if allowed_states is not None:
                if ctx.five_elements.get(element, {}).get("状态") not in allowed_states:
                    continue
            return True, {"宫位": p, "来源": source, "五行": element}
    return False, {}


def eval_na_yin_wu_xing_present(
    ctx: ChartContext, _pos: dict, target: dict
) -> tuple[bool, dict]:
    """纳音_五行有: checks if any pillar's 纳音 last character matches the wanted elements."""
    wanted = set(target.get("值", []))
    for p in _ALL_PILLARS:
        nayin = ctx.pillars.get(p, {}).get("纳音", "")
        if nayin and nayin[-1] in wanted:
            return True, {"宫位": p, "纳音": nayin, "五行": nayin[-1]}
    return False, {}


_ALL_WU_XING = {"木", "火", "土", "金", "水"}


def eval_wu_xing_complete(
    ctx: ChartContext, _pos: dict, _target: dict
) -> tuple[bool, dict]:
    found: set[str] = set()
    for p in _ALL_PILLARS:
        pillar = ctx.pillars.get(p, {})
        e = pillar.get("天干", {}).get("五行")
        if e:
            found.add(e)
        e = pillar.get("地支", {}).get("五行")
        if e:
            found.add(e)
    if found >= _ALL_WU_XING:
        return True, {"五行全": sorted(found)}
    return False, {}


def eval_stems_all_same(
    ctx: ChartContext, _pos: dict, target: dict
) -> tuple[bool, dict]:
    stems = [ctx.pillars.get(p, {}).get("天干", {}).get("天干") for p in _ALL_PILLARS]
    if len(set(stems)) == 1 and stems[0]:
        allowed = target.get("值")
        if allowed and stems[0] not in allowed:
            return False, {}
        return True, {"天干": stems[0]}
    return False, {}


def eval_branches_all_same(
    ctx: ChartContext, _pos: dict, target: dict
) -> tuple[bool, dict]:
    branches = [ctx.pillars.get(p, {}).get("地支", {}).get("地支") for p in _ALL_PILLARS]
    if len(set(branches)) == 1 and branches[0]:
        allowed = target.get("值")
        if allowed and branches[0] not in allowed:
            return False, {}
        return True, {"地支": branches[0]}
    return False, {}


def eval_tian_gan_same_cross_pillar(
    ctx: ChartContext, pos: dict, _target: dict
) -> tuple[bool, dict]:
    specs = pos.get("柱", [])
    if not isinstance(specs, list) or len(specs) != 2:
        return False, {}
    stems = [ctx.pillars.get(p, {}).get("天干", {}).get("天干") for p in specs]
    if stems[0] and stems[0] == stems[1]:
        return True, {"天干": stems[0], "柱A": specs[0], "柱B": specs[1]}
    return False, {}


def eval_di_zhi_same_cross_pillar(
    ctx: ChartContext, pos: dict, _target: dict
) -> tuple[bool, dict]:
    specs = pos.get("柱", [])
    if not isinstance(specs, list) or len(specs) != 2:
        return False, {}
    branches = [ctx.pillars.get(p, {}).get("地支", {}).get("地支") for p in specs]
    if branches[0] and branches[0] == branches[1]:
        return True, {"地支": branches[0], "柱A": specs[0], "柱B": specs[1]}
    return False, {}


def eval_di_zhi_offset(
    ctx: ChartContext, pos: dict, _target: dict
) -> tuple[bool, dict]:
    """地支偏移: target pillar's branch is exactly 步数 positions forward from base pillar's branch (mod 12)."""
    base_pillar = pos.get("基准柱", "年柱")
    target_pillar = pos.get("目标柱", "月柱")
    steps: int = pos.get("步数", 3)
    base_branch = ctx.pillars.get(base_pillar, {}).get("地支", {}).get("地支")
    target_branch = ctx.pillars.get(target_pillar, {}).get("地支", {}).get("地支")
    if not base_branch or not target_branch:
        return False, {}
    try:
        expected = _BRANCHES_SEQ[(_BRANCHES_SEQ.index(base_branch) + steps) % 12]
    except ValueError:
        return False, {}
    if expected == target_branch:
        return True, {"基准柱": base_pillar, "基准支": base_branch, "目标柱": target_pillar, "目标支": target_branch, "步数": steps}
    return False, {}


def eval_tian_gan_wu_he_cross_pillar(
    ctx: ChartContext, pos: dict, _target: dict
) -> tuple[bool, dict]:
    """天干五合_柱间: two pillars' stems form a 五合 pair (structural check, ignores interaction strength)."""
    pillar_a = pos.get("柱A", "年柱")
    pillar_b = pos.get("柱B", "月柱")
    stem_a = ctx.pillars.get(pillar_a, {}).get("天干", {}).get("天干")
    stem_b = ctx.pillars.get(pillar_b, {}).get("天干", {}).get("天干")
    if not stem_a or not stem_b:
        return False, {}
    try:
        if abs(_STEMS_SEQ.index(stem_a) - _STEMS_SEQ.index(stem_b)) == 5:
            return True, {"柱A": pillar_a, "天干A": stem_a, "柱B": pillar_b, "天干B": stem_b}
    except ValueError:
        pass
    return False, {}


def eval_ten_god_wu_he(
    ctx: ChartContext, _pos: dict, target: dict
) -> tuple[bool, dict]:
    """十神五合: two chart stems whose ten-gods match the specified pair form a 五合.
    target keys: 十神 (list of exactly 2 ten-god names, e.g. ["七杀", "劫财"]).
    Structural check — reads ten-gods from pillar data, ignores interaction filtering.
    """
    wanted = target.get("十神", [])
    if len(wanted) != 2:
        return False, {}
    wanted_sorted = sorted(wanted)
    # Collect (pillar, stem, ten-god) for every pillar's heavenly stem
    chart_stems: list[tuple[str, str, str]] = []
    for p in _ALL_PILLARS:
        pillar = ctx.pillars.get(p, {})
        stem = pillar.get("天干", {}).get("天干")
        ten_god = pillar.get("天干", {}).get("十神")
        if stem and ten_god:
            chart_stems.append((p, stem, ten_god))
    # Check all unordered pairs — order-independent, handles duplicate ten-gods
    for i in range(len(chart_stems)):
        for j in range(i + 1, len(chart_stems)):
            p_a, stem_a, tg_a = chart_stems[i]
            p_b, stem_b, tg_b = chart_stems[j]
            if sorted([tg_a, tg_b]) != wanted_sorted:
                continue
            try:
                if abs(_STEMS_SEQ.index(stem_a) - _STEMS_SEQ.index(stem_b)) == 5:
                    return True, {
                        "柱A": p_a, "天干A": stem_a, "十神A": tg_a,
                        "柱B": p_b, "天干B": stem_b, "十神B": tg_b,
                    }
            except ValueError:
                pass
    return False, {}


def eval_ten_god_you_he(
    ctx: ChartContext, _pos: dict, target: dict
) -> tuple[bool, dict]:
    """十神有合: any stem with the specified ten-god participates in a 天干合 interaction.
    target keys: 十神 — list of ten-god names e.g. ["正官"].
    """
    wanted = set(target.get("十神", []))
    for item in ctx.interactions:
        if item.get("类型") == "天干合":
            for p_name in item.get("组合明细", {}):
                tg = ctx.pillars.get(p_name, {}).get("天干", {}).get("十神")
                if tg in wanted:
                    return True, {"宫位": p_name, "十神": tg}
    return False, {}


def eval_ten_god_jie_duan_zai_zhi(
    ctx: ChartContext, pos: dict, target: dict
) -> tuple[bool, dict]:
    """十神_阶段在支: checks whether a ten-god's element occupies a specified 十二长生 stage at an earthly branch.

    Registered as: "十神_阶段在支"

    target keys (both required):
      十神  — ten-god name (str) or list of names, e.g. "七杀" or ["正印", "偏印"]
      阶段  — 十二长生 stage to check; must be explicit (no default).
              Supported values: "长生" | "墓". Returns False if omitted.

    Behaviour depends on whether a pillar is scoped via pos:

    Chart-wide (no 柱 in pos):
      Scans all four pillars for the ten-god's stem, resolves that stem's stage branch
      from the appropriate map, then checks whether that branch appears on ANY pillar.
      Use this when the ten-god and its stage branch may be on different pillars.

    Same-pillar (柱 provided, e.g. via 同柱: True):
      Checks only the scoped pillar. Both the ten-god AND its element's stage branch
      must be present on that exact pillar (branch = stage branch of that ten-god's stem).
      Use this to verify, e.g., that a Seal star resides at its own element's tomb branch.
    """
    ten_god_raw = target.get("十神")
    wanted: set[str] = {ten_god_raw} if isinstance(ten_god_raw, str) else set(ten_god_raw or [])
    stage = target.get("阶段")
    if not stage:
        return False, {}
    stage_map = _MU_MAP if stage == "墓" else _CHANG_SHENG_MAP
    pillar_spec = pos.get("柱")

    if not pillar_spec:
        # Original chart-wide behaviour preserved exactly
        sha_stem: str | None = None
        found_tg: str | None = None
        for p in _ALL_PILLARS:
            pillar = ctx.pillars.get(p, {})
            tg = pillar.get("天干", {}).get("十神")
            if tg in wanted:
                sha_stem = pillar.get("天干", {}).get("天干")
                found_tg = tg
                if sha_stem:
                    break
            for stem_info in pillar.get("藏干", {}).values():
                if isinstance(stem_info, dict) and stem_info.get("十神") in wanted:
                    sha_stem = stem_info.get("天干")
                    found_tg = stem_info.get("十神")
                    break
            if sha_stem:
                break
        if not sha_stem:
            return False, {}
        stage_branch = stage_map.get(sha_stem)
        if not stage_branch:
            return False, {}
        for p in _ALL_PILLARS:
            branch = ctx.pillars.get(p, {}).get("地支", {}).get("地支")
            if branch == stage_branch:
                return True, {"十神": found_tg, "天干": sha_stem, f"{stage}支": stage_branch, "所在柱": p}
        return False, {}

    # Same-pillar behaviour: ten-god and stage branch must both be on the scoped pillar
    for p in _resolve_pillars(pillar_spec):
        pillar = ctx.pillars.get(p, {})
        branch = pillar.get("地支", {}).get("地支")
        if not branch:
            continue
        sha_stem = None
        found_tg = None
        tg = pillar.get("天干", {}).get("十神")
        if tg in wanted:
            sha_stem = pillar.get("天干", {}).get("天干")
            found_tg = tg
        if not sha_stem:
            for stem_info in pillar.get("藏干", {}).values():
                if isinstance(stem_info, dict) and stem_info.get("十神") in wanted:
                    sha_stem = stem_info.get("天干")
                    found_tg = stem_info.get("十神")
                    break
        if not sha_stem:
            continue
        stage_branch = stage_map.get(sha_stem)
        if stage_branch == branch:
            return True, {"宫位": p, "十神": found_tg, "天干": sha_stem, f"{stage}支": stage_branch}
    return False, {}


def eval_ten_god_stage_at_pillar_branch(
    ctx: ChartContext, pos: dict, target: dict
) -> tuple[bool, dict]:
    """十神_长生阶段: checks whether a ten-god's stem placed against a reference
    pillar's branch falls in one of the specified 十二长生 stages.

    target keys:
        十神    — str or list of ten-god names to scan for
        阶段    — list of 十二长生 stage names, e.g. ["死", "绝", "墓"]
        参考柱  — pillar whose branch is the reference point (default: "月柱")

    pos.柱 scopes which pillars are scanned for the ten-god (default: all four).
    Returns True if ANY matching ten-god's stem resolves to one of the wanted
    stages at the reference branch.
    """
    ten_god_raw = target.get("十神")
    wanted_gods: set[str] = (
        {ten_god_raw} if isinstance(ten_god_raw, str) else set(ten_god_raw or [])
    )
    wanted_stages: set[str] = set(target.get("阶段", []))
    ref_pillar = target.get("参考柱", "月柱")

    if not wanted_gods or not wanted_stages:
        return False, {}

    ref_branch = ctx.pillars.get(ref_pillar, {}).get("地支", {}).get("地支")
    if not ref_branch:
        return False, {}

    scan_pillars = _resolve_pillars(pos.get("柱")) if pos.get("柱") else _ALL_PILLARS

    for p in scan_pillars:
        pillar = ctx.pillars.get(p, {})
        tg = pillar.get("天干", {}).get("十神")
        stem = pillar.get("天干", {}).get("天干")
        if tg in wanted_gods and stem:
            stage = _self_seated_stage(stem, ref_branch)
            if stage in wanted_stages:
                return True, {"十神": tg, "天干": stem, "参考柱": ref_pillar, "参考支": ref_branch, "长生阶段": stage}
        for stem_info in pillar.get("藏干", {}).values():
            if not isinstance(stem_info, dict):
                continue
            tg = stem_info.get("十神")
            stem = stem_info.get("天干")
            if tg in wanted_gods and stem:
                stage = _self_seated_stage(stem, ref_branch)
                if stage in wanted_stages:
                    return True, {"十神": tg, "天干": stem, "参考柱": ref_pillar, "参考支": ref_branch, "长生阶段": stage, "藏干": True}

    return False, {}


def eval_specific_stem_branch_combo(
    ctx: ChartContext, pos: dict, target: dict
) -> tuple[bool, dict]:
    wanted = set(target.get("值", []))
    for p in _resolve_pillars(pos.get("柱")):
        pillar = ctx.pillars.get(p, {})
        stem = pillar.get("天干", {}).get("天干", "")
        branch = pillar.get("地支", {}).get("地支", "")
        combo = f"{stem}{branch}"
        if combo in wanted:
            return True, {"宫位": p, "组合": combo}
    return False, {}


_PILLAR_ORDER = ["年柱", "月柱", "日柱", "时柱"]


def eval_xian_hou_xu(ctx: ChartContext, _pos: dict, target: dict) -> tuple[bool, dict]:
    """Check that jiazi 先 appears at an earlier pillar index than jiazi 后."""
    xian = target.get("先")
    hou = target.get("后")
    if not xian or not hou:
        return False, {}
    xian_idx: int | None = None
    hou_idx: int | None = None
    for i, key in enumerate(_PILLAR_ORDER):
        pillar = ctx.pillars.get(key, {})
        gan = pillar.get("天干", {}).get("天干", "")
        zhi = pillar.get("地支", {}).get("地支", "")
        jiazi = gan + zhi
        if jiazi == xian and xian_idx is None:
            xian_idx = i
        if jiazi == hou and hou_idx is None:
            hou_idx = i
    if xian_idx is not None and hou_idx is not None and xian_idx < hou_idx:
        return True, {"先": xian, "后": hou, "先柱": _PILLAR_ORDER[xian_idx], "后柱": _PILLAR_ORDER[hou_idx]}
    return False, {}


def eval_gan_lu_zai_zhi(
    ctx: ChartContext, pos: dict, target: dict
) -> tuple[bool, dict]:
    """Checks that the specified target pillar's branch equals the Lu of target["来源柱"]'s stem.
    "来源柱" is required — omitting it returns False.
    """
    source_pillar = target.get("来源柱")
    if not source_pillar:
        return False, {}
    stem = ctx.pillars.get(source_pillar, {}).get("天干", {}).get("天干")
    if not stem:
        return False, {}
    lu_branch = _LU_WEI_MAP.get(stem)
    if not lu_branch:
        return False, {}
    for p in _resolve_pillars(pos.get("柱")):
        branch = ctx.pillars.get(p, {}).get("地支", {}).get("地支")
        if branch == lu_branch:
            return True, {"宫位": p, "来源柱": source_pillar, "天干": stem, "禄支": lu_branch}
    return False, {}



def eval_wu_xing_battle(
    ctx: ChartContext, _pos: dict, target: dict
) -> tuple[bool, dict]:
    ke_fang = target.get("克方")
    bei_ke = target.get("被克方")
    if not ke_fang or not bei_ke or _WU_XING_KE.get(ke_fang) != bei_ke:
        return False, {}
    elements_present: set[str] = set()
    for p in _ALL_PILLARS:
        pillar = ctx.pillars.get(p, {})
        e = pillar.get("天干", {}).get("五行")
        if e:
            elements_present.add(e)
        e = pillar.get("地支", {}).get("五行")
        if e:
            elements_present.add(e)
    if ke_fang in elements_present and bei_ke in elements_present:
        return True, {"克方": ke_fang, "被克方": bei_ke}
    return False, {}


def eval_wu_xing_ke_same_pillar(
    ctx: ChartContext, pos: dict, target: dict
) -> tuple[bool, dict]:
    ke_fang = target.get("克方五行")
    bei_ke = target.get("被克方五行")
    if not ke_fang or not bei_ke or _WU_XING_KE.get(ke_fang) != bei_ke:
        return False, {}
    for p in _resolve_pillars(pos.get("柱")):
        pillar = ctx.pillars.get(p, {})
        elements: set[str] = set()
        stem_elem = pillar.get("天干", {}).get("五行")
        if stem_elem:
            elements.add(stem_elem)
        for info in pillar.get("藏干", {}).values():
            e = info.get("五行")
            if e:
                elements.add(e)
        if ke_fang in elements and bei_ke in elements:
            return True, {"宫位": p, "克方": ke_fang, "被克方": bei_ke}
    return False, {}


def eval_wu_xing_count(
    ctx: ChartContext, _pos: dict, target: dict
) -> tuple[bool, dict]:
    wanted = set(target.get("五行", []))
    if not wanted:
        return False, {}
    threshold: int = target.get("阈值", 0)
    comparator: str = target.get("比较", "≥")
    count = 0
    for p in _ALL_PILLARS:
        pillar = ctx.pillars.get(p, {})
        if pillar.get("天干", {}).get("五行") in wanted:
            count += 1
        if pillar.get("地支", {}).get("五行") in wanted:
            count += 1
    ok = _compare_threshold(count, threshold, comparator)
    return (ok, {"五行计数": sorted(wanted), "计数": count}) if ok else (False, {})


def eval_wu_xing_count_diff(
    ctx: ChartContext, _pos: dict, target: dict
) -> tuple[bool, dict]:
    elem_a = target.get("五行A")
    elem_b = target.get("五行B")
    threshold: int = target.get("阈值", 0)
    comparator: str = target.get("比较", "≥")
    if not elem_a or not elem_b:
        return False, {}

    def _count(elem: str) -> int:
        n = 0
        for p in _ALL_PILLARS:
            pillar = ctx.pillars.get(p, {})
            if pillar.get("天干", {}).get("五行") == elem:
                n += 1
            if pillar.get("地支", {}).get("五行") == elem:
                n += 1
        return n

    diff = _count(elem_a) - _count(elem_b)
    ok = _compare_threshold(diff, threshold, comparator)
    return (ok, {"五行A": elem_a, "五行B": elem_b, "差值": diff}) if ok else (False, {})


def eval_di_zhi_count(
    ctx: ChartContext, _pos: dict, target: dict
) -> tuple[bool, dict]:
    """计数_地支: count how many of the four pillars carry a branch in 值.

    Schema: { "类型": "计数_地支", "值": ["戌", "亥"], "阈值": 3, "比较": "≥" }

    Each pillar contributes at most 1 to the count (its branch).
    Useful for grading 天罗/地网 severity by occurrence count.
    """
    wanted: set[str] = set(target.get("值", []))
    threshold: int = target.get("阈值", 0)
    comparator: str = target.get("比较", "≥")
    count = 0
    matched: list[str] = []
    for p in _ALL_PILLARS:
        branch = ctx.pillars.get(p, {}).get("地支", {}).get("地支")
        if branch in wanted:
            count += 1
            matched.append(f"{p}:{branch}")
    ok = _compare_threshold(count, threshold, comparator)
    return (ok, {"地支计数": count, "匹配": matched}) if ok else (False, {})


def eval_wu_xing_position_relation(
    ctx: ChartContext, pos: dict, target: dict
) -> tuple[bool, dict]:
    """五行_位置关系: exactly 数量 pillars carry the target element in specified 部分,
    and their positions satisfy 模式 ('非相邻': no two adjacent; '相邻': all contiguous)."""
    wanted = set(target.get("五行", []))
    if not wanted:
        return False, {}
    required: int = target.get("数量", 2)
    mode: str = target.get("模式", "非相邻")
    bu_fen: str = pos.get("部分", "天干")

    matched: list[int] = []
    for i, p in enumerate(_ALL_PILLARS):
        pillar = ctx.pillars.get(p, {})
        if bu_fen == "天干":
            if pillar.get("天干", {}).get("五行") in wanted:
                matched.append(i)
        elif bu_fen == "地支":
            if pillar.get("地支", {}).get("五行") in wanted:
                matched.append(i)
        elif bu_fen == "藏干":
            if any(
                isinstance(v, dict) and v.get("五行") in wanted
                for v in pillar.get("藏干", {}).values()
            ):
                matched.append(i)

    if len(matched) != required:
        return False, {}

    if mode == "非相邻":
        if any(matched[j + 1] - matched[j] == 1 for j in range(len(matched) - 1)):
            return False, {}
    elif mode == "相邻":
        if any(matched[j + 1] - matched[j] != 1 for j in range(len(matched) - 1)):
            return False, {}

    return True, {"五行": sorted(wanted), "位置": [_ALL_PILLARS[i] for i in matched], "模式": mode}


def eval_zhong_yuan_xing(
    ctx: ChartContext, _pos: dict, _target: dict
) -> tuple[bool, dict]:
    year = ctx.pillars.get("年柱", {})
    year_stem = year.get("天干", {}).get("天干")
    year_branch = year.get("地支", {}).get("地支")
    if not year_stem and not year_branch:
        return False, {}
    for p in ["月柱", "日柱", "时柱"]:
        pillar = ctx.pillars.get(p, {})
        if year_stem and pillar.get("天干", {}).get("天干") == year_stem:
            return True, {"重元星": "天干重复", "宫位": p, "天干": year_stem}
        if year_branch and pillar.get("地支", {}).get("地支") == year_branch:
            return True, {"重元星": "地支重复", "宫位": p, "地支": year_branch}
    return False, {}


# ── Volume 5 (论正官 / 论七煞) evaluators ─────────────────────────────────────

# 正官 stem for each day master (opposite yin-yang element that controls it)
_ZHENG_GUAN_STEM: dict[str, str] = {
    "甲": "辛", "乙": "庚",
    "丙": "癸", "丁": "壬",
    "戊": "乙", "己": "甲",
    "庚": "丁", "辛": "丙",
    "壬": "己", "癸": "戊",
}

_BRANCHES_SEQ = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
_STEMS_SEQ = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
# 天干合化气: indexed by the smaller stem's _STEMS_SEQ index (甲=0..戊=4)
# 甲己→土, 乙庚→金, 丙辛→水, 丁壬→木, 戊癸→火
_WU_HE_HUA_QI = ["土", "金", "水", "木", "火"]
# 天干长生支: stem → its 长生 earthly branch in the twelve growth phases
_CHANG_SHENG_MAP: dict[str, str] = {
    "甲": "亥", "乙": "午", "丙": "寅", "丁": "酉",
    "戊": "寅", "己": "酉", "庚": "巳", "辛": "子",
    "壬": "申", "癸": "卯",
}
# 天干临官支: stem → its 临官 earthly branch (长生 + 3 forward for yang; + 3 backward for yin)
_LIN_GUAN_MAP: dict[str, str] = {
    "甲": "寅", "乙": "卯", "丙": "巳", "丁": "午",
    "戊": "巳", "己": "午", "庚": "申", "辛": "酉",
    "壬": "亥", "癸": "子",
}
# 天干墓支: stem → its 墓 (tomb) earthly branch in the twelve growth phases
_MU_MAP: dict[str, str] = {
    "甲": "未", "乙": "戌", "丙": "戌", "丁": "丑",
    "戊": "戌", "己": "丑", "庚": "丑", "辛": "辰",
    "壬": "辰", "癸": "未",
}


def eval_yue_ling_zheng_qi(
    ctx: ChartContext, _pos: dict, target: dict
) -> tuple[bool, dict]:
    """月令正气: any hidden stem (本气/中气/余气) of the month branch matches target 十神."""
    wanted = set(target.get("值", []))
    cang_gan = ctx.pillars.get("月柱", {}).get("藏干", {})
    for role, stem_info in cang_gan.items():
        if not isinstance(stem_info, dict):
            continue
        ten_god = stem_info.get("十神")
        if ten_god and ten_god in wanted:
            return True, {"月令藏干": role, "十神": ten_god}
    return False, {}


def eval_san_he_guan_ju(
    ctx: ChartContext, _pos: dict, _target: dict
) -> tuple[bool, dict]:
    """三合官局: A 三合 forms the element that controls the day master (正官 element)."""
    dm_element = ctx.day_master.get("五行")
    if not dm_element:
        return False, {}
    for item in ctx.interactions:
        if item.get("类型") == "三合" and _WU_XING_KE.get(item.get("元素")) == dm_element:
            return True, {"三合元素": item.get("元素"), "三合组合": item.get("组合明细", {})}
    return False, {}


def eval_san_he_branches(
    ctx: ChartContext, _pos: dict, target: dict
) -> tuple[bool, dict]:
    """三合特定: all specified branches appear across the four chart pillars.
    target keys: 值 — list of individual branch strings e.g. ["亥", "卯", "未"].
    """
    required = set(target.get("值", []))
    if not required:
        return False, {}
    chart_branches = {
        ctx.pillars.get(p, {}).get("地支", {}).get("地支")
        for p in _ALL_PILLARS
    } - {None}
    if required <= chart_branches:
        return True, {"三合组合": "".join(sorted(required, key=_BRANCHES_SEQ.index)), "命盘地支": sorted(chart_branches, key=_BRANCHES_SEQ.index)}
    return False, {}


def eval_guan_xing_zuo_lu(
    ctx: ChartContext, _pos: dict, _target: dict
) -> tuple[bool, dict]:
    """官星坐禄: day master's 正官 stem's 禄 branch appears in any pillar's 地支."""
    day_stem = ctx.day_master.get("天干")
    if not day_stem:
        return False, {}
    zheng_guan_stem = _ZHENG_GUAN_STEM.get(day_stem)
    if not zheng_guan_stem:
        return False, {}
    lu_branch = _LU_WEI_MAP.get(zheng_guan_stem)
    if not lu_branch:
        return False, {}
    for p in _ALL_PILLARS:
        branch = ctx.pillars.get(p, {}).get("地支", {}).get("地支")
        if branch == lu_branch:
            return True, {"官星": zheng_guan_stem, "禄支": lu_branch, "宫位": p}
    return False, {}


def eval_wu_xing_ke_cross_pillar(
    ctx: ChartContext, pos: dict, _target: dict
) -> tuple[bool, dict]:
    """五行克_柱间: pillar A's part element controls pillar B's part element.

    pos keys: 克方柱 (default 月柱), 克方部分 (default 天干),
              被克方柱 (default 年柱), 被克方部分 (default 天干).
    """
    agent_pillar = pos.get("克方柱", "月柱")
    agent_part = pos.get("克方部分", "天干")
    patient_pillar = pos.get("被克方柱", "年柱")
    patient_part = pos.get("被克方部分", "天干")

    def _elem(pillar_name: str, part: str) -> str | None:
        pillar = ctx.pillars.get(pillar_name, {})
        return pillar.get(part, {}).get("五行")

    agent_elem = _elem(agent_pillar, agent_part)
    patient_elem = _elem(patient_pillar, patient_part)
    if not agent_elem or not patient_elem:
        return False, {}
    if _WU_XING_KE.get(agent_elem) == patient_elem:
        return True, {
            "克方": agent_pillar, "克方部分": agent_part, "克方五行": agent_elem,
            "被克方": patient_pillar, "被克方部分": patient_part, "被克方五行": patient_elem,
        }
    return False, {}


def eval_gan_ke_guanxi(
    ctx: ChartContext, _pos: dict, target: dict
) -> tuple[bool, dict]:
    """干克关系: stem of the pillar holding 施克支 controls stem of the pillar holding 受克支.

    target keys:
        施克支: branch that provides the controlling stem
        受克支: branch that provides the controlled stem

    Iterates all pillar pairs — the branch can land anywhere in the four pillars.
    """
    agent_branch = target.get("施克支")
    patient_branch = target.get("受克支")
    if not agent_branch or not patient_branch:
        return False, {}

    def _stem_elem(branch: str) -> list[tuple[str, str]]:
        return [
            (p, ctx.pillars[p]["天干"]["五行"])
            for p in _ALL_PILLARS
            if ctx.pillars.get(p, {}).get("地支", {}).get("地支") == branch
            and ctx.pillars.get(p, {}).get("天干", {}).get("五行")
        ]

    for agent_pillar, agent_elem in _stem_elem(agent_branch):
        for patient_pillar, patient_elem in _stem_elem(patient_branch):
            if _WU_XING_KE.get(agent_elem) == patient_elem:
                return True, {
                    "施克柱": agent_pillar, "施克支": agent_branch, "施克干五行": agent_elem,
                    "受克柱": patient_pillar, "受克支": patient_branch, "受克干五行": patient_elem,
                }
    return False, {}


def eval_tian_gan_he_hua_qi_ke_na_yin(
    ctx: ChartContext, pos: dict, _target: dict
) -> tuple[bool, dict]:
    """天干合化气克纳音: any 天干合 pair's 化气 controls the target pillar's 纳音 element.
    pos keys: 纳音柱 (default 年柱). Structural check — ignores interaction strength filtering.
    """
    na_yin_pillar = pos.get("纳音柱", "年柱")
    na_yin_str = ctx.pillars.get(na_yin_pillar, {}).get("纳音", "")
    if not na_yin_str:
        return False, {}
    na_yin_elem = na_yin_str[-1]

    stems: list[tuple[str, str, int]] = []
    for p in _ALL_PILLARS:
        stem = ctx.pillars.get(p, {}).get("天干", {}).get("天干")
        if not stem:
            continue
        try:
            stems.append((p, stem, _STEMS_SEQ.index(stem)))
        except ValueError:
            pass

    for i in range(len(stems)):
        for j in range(i + 1, len(stems)):
            _p_a, stem_a, idx_a = stems[i]
            _p_b, stem_b, idx_b = stems[j]
            if abs(idx_a - idx_b) == 5:
                hua_elem = _WU_HE_HUA_QI[min(idx_a, idx_b)]
                if _WU_XING_KE.get(hua_elem) == na_yin_elem:
                    return True, {
                        "天干合": f"{stem_a}{stem_b}",
                        "化气五行": hua_elem,
                        "纳音柱": na_yin_pillar,
                        "纳音": na_yin_str,
                        "纳音五行": na_yin_elem,
                    }
    return False, {}


def eval_jie_qi_yue_nei_position(
    ctx: ChartContext, _pos: dict, target: dict
) -> tuple[bool, dict]:
    """节气_月内位置: birth falls within N days after a named solar term.

    target keys:
      节气 — Chinese name of the solar term, e.g. "小寒"
      天数 — window in days (float), e.g. 10 ; defaults to 10
    Uses day-level precision from getJieQiTable(); the 0.5-day remainder is
    handled by accepting delta ≤ floor(天数) inclusive.
    """
    if ctx.lunar_birthday is None:
        return False, {}
    jie_qi_name: str = target.get("节气", "")
    days: float = float(target.get("天数", 10))
    if not jie_qi_name:
        return False, {}
    solar_term = ctx.lunar_birthday.getJieQiTable().get(jie_qi_name)
    if solar_term is None:
        return False, {}
    birth_solar = ctx.lunar_birthday.getSolar()
    term_date = date(solar_term.getYear(), solar_term.getMonth(), solar_term.getDay())
    birth_date = date(birth_solar.getYear(), birth_solar.getMonth(), birth_solar.getDay())
    delta = (birth_date - term_date).days
    if 0 <= delta <= int(days):
        return True, {"节气": jie_qi_name, "距节气天数": delta, "窗口天数": days}
    return False, {}


def eval_lu_zhi_san_he(ctx: ChartContext, pos: dict, target: dict) -> tuple[bool, dict]:
    """禄支三合: DM's lu branch shares a 三合 group with another pillar's branch.

    Optional filters:
      target["值"]  — ten-god list; omit to match any ten-god
      pos["柱"]     — pillar scope; omit to check all pillars
    """
    day_stem = ctx.pillars.get("日柱", {}).get("天干", {}).get("天干")
    lu_branch = _LU_WEI_MAP.get(day_stem)
    if not lu_branch:
        return False, {}

    san_he_partners: frozenset = frozenset()
    for group in _SAN_HE_GROUPS:
        if lu_branch in group:
            san_he_partners = group - {lu_branch}
            break

    wanted = set(target.get("值", []))
    pillars_to_check = _resolve_pillars(pos.get("柱", "全局"))
    matches = []
    for p in pillars_to_check:
        pillar = ctx.pillars.get(p, {})
        branch = pillar.get("地支", {}).get("地支")
        if branch not in san_he_partners:
            continue
        stem_tg = pillar.get("天干", {}).get("十神")
        if wanted and stem_tg not in wanted:
            continue
        matches.append({"宫位": p, "合支": branch, "天干十神": stem_tg})

    if matches:
        return True, {"禄支": lu_branch, "日干": day_stem, "三合": matches}
    return False, {}


def eval_lu_zhi_liu_he(ctx: ChartContext, pos: dict, target: dict) -> tuple[bool, dict]:
    """禄支六合: DM's lu branch's 六合 partner appears in another pillar's branch.

    Optional filters:
      target["值"]  — ten-god list; omit to match any ten-god
      pos["柱"]     — pillar scope; omit to check all pillars
    """
    day_stem = ctx.pillars.get("日柱", {}).get("天干", {}).get("天干")
    lu_branch = _LU_WEI_MAP.get(day_stem)
    if not lu_branch:
        return False, {}

    liu_he_partner = _LIU_HE_MAP.get(lu_branch)
    if not liu_he_partner:
        return False, {}

    wanted = set(target.get("值", []))
    pillars_to_check = _resolve_pillars(pos.get("柱", "全局"))
    matches = []
    for p in pillars_to_check:
        pillar = ctx.pillars.get(p, {})
        branch = pillar.get("地支", {}).get("地支")
        if branch != liu_he_partner:
            continue
        stem_tg = pillar.get("天干", {}).get("十神")
        if wanted and stem_tg not in wanted:
            continue
        matches.append({"宫位": p, "合支": branch, "天干十神": stem_tg})

    if matches:
        return True, {"禄支": lu_branch, "日干": day_stem, "六合": matches}
    return False, {}


def eval_gan_zhi_he_ma(ctx: ChartContext, _pos: dict, _target: dict) -> tuple[bool, dict]:
    """干支合马: A pillar carrying 驿马 has a different pillar that simultaneously
    六合s its branch AND 五合s its stem.
    Cannot be expressed with AND mode — both conditions must be on the same partner pillar.
    """
    for horse_p in _ALL_PILLARS:
        if not any(s.get("名称") == "驿马" for s in ctx.shen_sha.get(horse_p, [])):
            continue
        p_data = ctx.pillars.get(horse_p, {})
        horse_stem   = p_data.get("天干", {}).get("天干")
        horse_branch = p_data.get("地支", {}).get("地支")
        if not horse_stem or not horse_branch:
            continue
        liu_he_partner = _LIU_HE_MAP.get(horse_branch)
        wu_he_partner  = _WU_HE_STEM_MAP.get(horse_stem)
        if not liu_he_partner or not wu_he_partner:
            continue
        for other_p in _ALL_PILLARS:
            if other_p == horse_p:
                continue
            od = ctx.pillars.get(other_p, {})
            if (od.get("天干", {}).get("天干") == wu_he_partner
                    and od.get("地支", {}).get("地支") == liu_he_partner):
                return True, {
                    "马柱": horse_p, "合柱": other_p,
                    "合干": wu_he_partner, "合支": liu_he_partner,
                }
    return False, {}


def eval_yi_ma_duo_shi(ctx: ChartContext, _pos: dict, _target: dict) -> tuple[bool, dict]:
    """驿马驮尸: 驿马 falls in the year pillar's 空亡, AND the year-stem-specific
    forbidden branch appears in any other non-year pillar.

    Classical text (SMTH) gives three explicit stem → 忌支 examples:
      乙→忌寅 (乙未人), 己→忌申 (己亥人), 癸→忌寅 (癸卯人), then "余旬准此".
    Only these three yin stems are used; yang counterparts are not extrapolated
    as the text does not provide explicit examples for them.
    """
    # Only the three stems explicitly named in the classical text.
    _STEM_TABOO: dict[str, str] = {
        "乙": "寅",   # 乙未人得巳马，忌寅月日时
        "己": "申",   # 己亥人得巳马，忌申月日时
        "癸": "寅",   # 癸卯人得巳马，亦忌寅月日时
    }

    year_stem = ctx.pillars.get("年柱", {}).get("天干", {}).get("天干", "")
    taboo_branch = _STEM_TABOO.get(year_stem)
    if not taboo_branch:
        return False, {}

    year_kong = ctx.pillars.get("年柱", {}).get("空亡", {}).get("本柱旬空", "")
    non_year = ["月柱", "日柱", "时柱"]

    for horse_p in non_year:
        if not any(s.get("名称") == "驿马" for s in ctx.shen_sha.get(horse_p, [])):
            continue
        horse_branch = ctx.pillars.get(horse_p, {}).get("地支", {}).get("地支", "")
        if not horse_branch or horse_branch not in year_kong:
            continue
        for other_p in non_year:
            if other_p == horse_p:
                continue
            branch = ctx.pillars.get(other_p, {}).get("地支", {}).get("地支", "")
            if branch == taboo_branch:
                return True, {
                    "马柱": horse_p, "马支": horse_branch,
                    "触发柱": other_p, "触发支": branch,
                }
    return False, {}


def eval_jiu_di_ma(ctx: ChartContext, _pos: dict, _target: dict) -> tuple[bool, dict]:
    """九地马: horse branch moved two steps backward (−2 mod 12) appears anywhere in the four pillars."""
    _JIU_DI_MAP: dict[str, str] = {"寅": "子", "申": "午", "亥": "酉", "巳": "卯"}
    for pillar in _ALL_PILLARS:
        if not any(s.get("名称") == "驿马" for s in ctx.shen_sha.get(pillar, [])):
            continue
        horse_branch = ctx.pillars.get(pillar, {}).get("地支", {}).get("地支", "")
        jiu_di_branch = _JIU_DI_MAP.get(horse_branch)
        if not jiu_di_branch:
            continue
        for p in _ALL_PILLARS:
            if ctx.pillars.get(p, {}).get("地支", {}).get("地支") == jiu_di_branch:
                return True, {"马支": horse_branch, "九地支": jiu_di_branch, "宫位": p}
    return False, {}


def eval_ma_san_he_quan(ctx: ChartContext, _pos: dict, _target: dict) -> tuple[bool, dict]:
    """马三合全: all three san he bureau members of the 驿马's bureau appear in the four pillars.
    Horse→bureau map derived from _SAN_HE_GROUPS: 寅→{申子辰}, 申→{寅午戌}, 亥→{巳酉丑}, 巳→{亥卯未}.
    """
    _MA_BUREAU: dict[str, frozenset] = {
        "寅": frozenset({"申", "子", "辰"}),
        "申": frozenset({"寅", "午", "戌"}),
        "亥": frozenset({"巳", "酉", "丑"}),
        "巳": frozenset({"亥", "卯", "未"}),
    }
    all_branches = {
        ctx.pillars.get(p, {}).get("地支", {}).get("地支", "") for p in _ALL_PILLARS
    }
    for pillar in _ALL_PILLARS:
        if not any(s.get("名称") == "驿马" for s in ctx.shen_sha.get(pillar, [])):
            continue
        horse_branch = ctx.pillars.get(pillar, {}).get("地支", {}).get("地支", "")
        bureau = _MA_BUREAU.get(horse_branch)
        if not bureau:
            continue
        if bureau <= all_branches:
            return True, {"马支": horse_branch, "三合局": sorted(bureau)}
    return False, {}


def eval_na_yin_ke_zhu_jian(ctx: ChartContext, pos: dict, _target: dict) -> tuple[bool, dict]:
    """纳音克_柱间: nayin element of pos["柱A"] controls nayin element of pos["柱B"].
    Element extracted from the last character of the nayin phrase (e.g. "海中金"[-1] → "金").
    """
    pillar_a = pos.get("柱A", "年柱")
    pillar_b = pos.get("柱B", "月柱")
    na_yin_a = ctx.pillars.get(pillar_a, {}).get("纳音", "")
    na_yin_b = ctx.pillars.get(pillar_b, {}).get("纳音", "")
    if not na_yin_a or not na_yin_b:
        return False, {}
    elem_a = na_yin_a[-1]
    elem_b = na_yin_b[-1]
    if _WU_XING_KE.get(elem_a) == elem_b:
        return True, {
            "克方柱": pillar_a, "被克方柱": pillar_b,
            "克方纳音": na_yin_a, "被克方纳音": na_yin_b,
        }
    return False, {}


def eval_na_yin_ke_guanxi(
    ctx: ChartContext, _pos: dict, target: dict
) -> tuple[bool, dict]:
    """纳音克关系: nayin element of the pillar holding 施克支 controls nayin of the pillar holding 受克支.

    target keys:
        施克支: branch that provides the controlling nayin
        受克支: branch that provides the controlled nayin

    Iterates all pillar pairs — branches can land anywhere in the four pillars.
    """
    agent_branch = target.get("施克支")
    patient_branch = target.get("受克支")
    if not agent_branch or not patient_branch:
        return False, {}

    def _na_yin_elem(branch: str) -> list[tuple[str, str, str]]:
        return [
            (p, ctx.pillars[p]["纳音"], ctx.pillars[p]["纳音"][-1])
            for p in _ALL_PILLARS
            if ctx.pillars.get(p, {}).get("地支", {}).get("地支") == branch
            and ctx.pillars.get(p, {}).get("纳音", "")
        ]

    for agent_pillar, agent_na_yin, agent_elem in _na_yin_elem(agent_branch):
        for patient_pillar, patient_na_yin, patient_elem in _na_yin_elem(patient_branch):
            if _WU_XING_KE.get(agent_elem) == patient_elem:
                return True, {
                    "施克柱": agent_pillar, "施克支": agent_branch, "施克纳音": agent_na_yin,
                    "受克柱": patient_pillar, "受克支": patient_branch, "受克纳音": patient_na_yin,
                }
    return False, {}


def eval_na_yin_wu_xing(ctx: ChartContext, pos: dict, target: dict) -> tuple[bool, dict]:
    """纳音五行: the resolved pillar's nayin element matches any of target["值"].
    pos keys: 柱 (default 年柱). target keys: 值 (list of elements, e.g. ["金", "木"]).
    """
    pillar = pos.get("柱", "年柱")
    wanted = set(target.get("值", []))
    na_yin_str = ctx.pillars.get(pillar, {}).get("纳音", "")
    if not na_yin_str:
        return False, {}
    na_yin_elem = na_yin_str[-1]
    if na_yin_elem in wanted:
        return True, {"柱": pillar, "纳音": na_yin_str, "纳音五行": na_yin_elem}
    return False, {}


def eval_na_yin_wu_xing_count(ctx: ChartContext, _pos: dict, target: dict) -> tuple[bool, dict]:
    """计数_纳音五行: count pillars whose nayin element is in target["值"], check against 阈值."""
    wanted = set(target.get("值", []))
    if not wanted:
        return False, {}
    threshold: int = target.get("阈值", 2)
    comparator: str = target.get("比较", ">=")
    matched = [
        p for p in _ALL_PILLARS
        if ctx.pillars.get(p, {}).get("纳音", "")[-1:] in wanted
    ]
    ok = _compare_threshold(len(matched), threshold, comparator)
    return (ok, {"纳音五行": sorted(wanted), "计数": len(matched), "匹配柱": matched}) if ok else (False, {})


def eval_jiao_hu_zi_shu_xing(ctx: ChartContext, _pos: dict, target: dict) -> tuple[bool, dict]:
    """交互子属性: checks a named property on matching interactions from ctx.interactions.

    target keys:
        交互:  interaction 类型 to filter (e.g. "六冲")
        属性:  property key on the interaction dict (e.g. "纳音关系", "同类")
        值:    list of acceptable values (e.g. ["相生"], [True])
        强度:  optional list of acceptable 强度 values — if omitted, all strengths match
    """
    ix_type = target.get("交互")
    attr = target.get("属性")
    wanted = set(map(str, target.get("值", [])))  # normalise to str for comparison
    wanted_strength: set | None = set(target["强度"]) if "强度" in target else None
    for ix in ctx.interactions:
        if ix.get("类型") == ix_type:
            if wanted_strength and ix.get("强度") not in wanted_strength:
                continue
            val = ix.get(attr)
            if str(val) in wanted:
                return True, {attr: val, "组合": ix.get("组合", "")}
    return False, {}


def eval_ku_wei_chong_kai(ctx: ChartContext, _pos: dict, _target: dict) -> tuple[bool, dict]:
    """库位冲开: fires when any vault branch has been opened via clash (冲开 mechanism).

    Uses ctx.vault_states (sourced from 作用.库位状态).
    A vault is opened when 是否开库 is True and "冲开" is in 开库机制.
    """
    for vs in ctx.vault_states:
        if vs.get("是否开库") and "冲开" in vs.get("开库机制", []):
            return True, {"库支": vs.get("库支"), "释放": vs.get("释放"), "释放十神": vs.get("释放十神")}
    return False, {}


def eval_ku_wei_chong_kai_shi_shen(ctx: ChartContext, _pos: dict, target: dict) -> tuple[bool, dict]:
    """库位冲开_释放十神: vault opened by clash AND the released ten-god matches the wanted list.

    Target fields:
        值 (list[str]): ten-gods to match against 释放十神 (e.g. ["正财", "偏财", "正官", "偏官"])
    """
    wanted = set(target.get("值", []))
    for vs in ctx.vault_states:
        if vs.get("是否开库") and "冲开" in vs.get("开库机制", []):
            released_tg = vs.get("释放十神")
            if released_tg in wanted:
                return True, {"库支": vs.get("库支"), "释放": vs.get("释放"), "释放十神": released_tg}
    return False, {}


def eval_chong_chu_cang_gan_shi_shen(
    ctx: ChartContext, pos: dict, target: dict
) -> tuple[bool, dict]:
    """冲出藏干十神: the branch of 来源柱 clashes its 六冲 partner, and that partner's
    hidden stems contain the wanted ten-gods (relative to the day master).

    Used for 飞财格: the repeated branch (日支=时支) clashes out the opposite palace
    and the opposite branch's 藏干 must contain 正财 or 偏财.

    Target fields:
        来源柱 (str): pillar whose branch is the clash weapon (default "日柱")
        值 (list[str]): ten-gods to find in the clashed branch's 藏干
                        e.g. ["正财", "偏财"]
    """
    wanted_tgs = set(target.get("值", []))
    if not wanted_tgs:
        return False, {}

    lai_yuan = target.get("来源柱") or pos.get("柱") or "日柱"
    if isinstance(lai_yuan, list):
        lai_yuan = lai_yuan[0]

    branch = ctx.pillars.get(lai_yuan, {}).get("地支", {}).get("地支")
    if not branch:
        return False, {}

    clash_partner = _LIU_CHONG_ZHI.get(branch)
    if not clash_partner:
        return False, {}

    dm_element = ctx.day_master.get("五行")
    if not dm_element:
        return False, {}

    tg_map = TEN_GOD_ELEMENT.get(dm_element, {})
    # Build reverse: element → set of ten-gods that map to it
    wanted_elements = {tg_map[tg] for tg in wanted_tgs if tg in tg_map}

    for elem in _ZHI_CANG_GAN_ELEMENTS.get(clash_partner, []):
        if elem in wanted_elements:
            matched_tg = next(tg for tg in wanted_tgs if tg_map.get(tg) == elem)
            return True, {
                "来源柱": lai_yuan,
                "来源支": branch,
                "冲出支": clash_partner,
                "藏干五行": elem,
                "十神": matched_tg,
            }
    return False, {}


def eval_tai_yuan_di_zhi(ctx: ChartContext, _pos: dict, target: dict) -> tuple[bool, dict]:
    """胎元地支: checks if the 胎元 (conception palace) earthly branch matches any value in target["值"]."""
    wanted = set(target.get("值", []))
    branch = ctx.tai_yuan_branch
    if branch and branch in wanted:
        return True, {"胎元地支": branch}
    return False, {}


def eval_po_yin(ctx: ChartContext, _pos: dict, _target: dict) -> tuple[bool, dict]:
    """破印: an 印-star pillar (stem element generates DM) has its branch clashed by another
    pillar whose 纳音 element 克s the day master element.

    Classical example: 木人带癸未(印)，见乙丑金(纳音金克木)冲未，为破印。
    Last char of 纳音 phrase is the 五行 element (e.g. '海中金'[-1] == '金').
    """
    _STEM_ELEM: dict[str, str] = {
        "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
        "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
    }
    _SHENG: dict[str, str] = {"木": "水", "火": "木", "土": "火", "金": "土", "水": "金"}
    _KE_BY: dict[str, str] = {"木": "金", "火": "水", "土": "木", "金": "火", "水": "土"}
    _CLASH: dict[str, str] = {
        "子": "午", "午": "子", "丑": "未", "未": "丑",
        "寅": "申", "申": "寅", "卯": "酉", "酉": "卯",
        "辰": "戌", "戌": "辰", "巳": "亥", "亥": "巳",
    }
    _PILLAR_NAMES = ("年柱", "月柱", "日柱", "时柱")

    day_stem = ctx.pillars.get("日柱", {}).get("天干", {}).get("天干", "")
    dm_elem = _STEM_ELEM.get(day_stem, "")
    if not dm_elem:
        return False, {}

    yin_elem = _SHENG[dm_elem]
    ke_dm = _KE_BY[dm_elem]

    pdata = {
        p: {
            "stem_elem": _STEM_ELEM.get(ctx.pillars.get(p, {}).get("天干", {}).get("天干", ""), ""),
            "branch": ctx.pillars.get(p, {}).get("地支", {}).get("地支", ""),
            "nayin": ctx.pillars.get(p, {}).get("纳音", ""),
        }
        for p in _PILLAR_NAMES
    }

    for yin_p, yd in pdata.items():
        if yd["stem_elem"] != yin_elem:
            continue
        clash_b = _CLASH.get(yd["branch"], "")
        if not clash_b:
            continue
        for att_p, ad in pdata.items():
            if att_p == yin_p or ad["branch"] != clash_b:
                continue
            nayin_elem = ad["nayin"][-1] if ad["nayin"] else ""
            if nayin_elem == ke_dm:
                return True, {
                    "破印柱": yin_p, "印支": yd["branch"],
                    "攻击柱": att_p, "冲支": clash_b, "纳音": ad["nayin"],
                }
    return False, {}


_PO_LU_MAP: dict[str, tuple[str, str]] = {
    "甲": ("寅", "申"), "乙": ("卯", "酉"),
    "丙": ("巳", "亥"), "丁": ("午", "子"),
    "戊": ("巳", "亥"), "己": ("午", "子"),
    "庚": ("申", "寅"), "辛": ("酉", "卯"),
    "壬": ("亥", "巳"), "癸": ("子", "午"),
}


def eval_po_lu(ctx: ChartContext, _pos: dict, _target: dict) -> tuple[bool, dict]:
    """破禄: day master's 禄 branch and its clash branch are both present in the chart."""
    day_stem = ctx.pillars.get("日柱", {}).get("天干", {}).get("天干", "")
    entry = _PO_LU_MAP.get(day_stem)
    if not entry:
        return False, {}
    lu_b, clash_b = entry
    all_b = {ctx.pillars.get(p, {}).get("地支", {}).get("地支", "") for p in ("年柱", "月柱", "日柱", "时柱")}
    if lu_b in all_b and clash_b in all_b:
        return True, {"禄支": lu_b, "冲禄支": clash_b}
    return False, {}


_PO_MA_MAP: dict[str, tuple[str, str]] = {
    "申": ("寅", "申"), "子": ("寅", "申"), "辰": ("寅", "申"),
    "寅": ("申", "寅"), "午": ("申", "寅"), "戌": ("申", "寅"),
    "巳": ("亥", "巳"), "酉": ("亥", "巳"), "丑": ("亥", "巳"),
    "亥": ("巳", "亥"), "卯": ("巳", "亥"), "未": ("巳", "亥"),
}


def eval_po_ma(ctx: ChartContext, _pos: dict, _target: dict) -> tuple[bool, dict]:
    """破马: 驿马 branch (from year branch 三合 group) and its clash branch are both present."""
    year_b = ctx.pillars.get("年柱", {}).get("地支", {}).get("地支", "")
    entry = _PO_MA_MAP.get(year_b)
    if not entry:
        return False, {}
    ma_b, clash_b = entry
    all_b = {ctx.pillars.get(p, {}).get("地支", {}).get("地支", "") for p in ("年柱", "月柱", "日柱", "时柱")}
    if ma_b in all_b and clash_b in all_b:
        return True, {"马支": ma_b, "冲马支": clash_b}
    return False, {}


_STEM_ELEM_CAI: dict[str, str] = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
}
_DM_CAI_CLASHES: dict[str, list[tuple[str, str]]] = {
    "木": [("辰", "戌"), ("丑", "未")],  # 财=土
    "火": [("申", "寅"), ("酉", "卯")],  # 财=金
    "土": [("亥", "巳"), ("子", "午")],  # 财=水
    "金": [("寅", "申"), ("卯", "酉")],  # 财=木
    "水": [("巳", "亥"), ("午", "子")],  # 财=火
}


def eval_po_cai(ctx: ChartContext, _pos: dict, _target: dict) -> tuple[bool, dict]:
    """破财: DM's 财 element branches and their clash branches are both present."""
    day_stem = ctx.pillars.get("日柱", {}).get("天干", {}).get("天干", "")
    dm_elem = _STEM_ELEM_CAI.get(day_stem, "")
    if not dm_elem:
        return False, {}
    all_b = {ctx.pillars.get(p, {}).get("地支", {}).get("地支", "") for p in ("年柱", "月柱", "日柱", "时柱")}
    for cai_b, clash_b in _DM_CAI_CLASHES.get(dm_elem, []):
        if cai_b in all_b and clash_b in all_b:
            return True, {"财支": cai_b, "冲财支": clash_b}
    return False, {}


def eval_po_he(ctx: ChartContext, _pos: dict, _target: dict) -> tuple[bool, dict]:
    """破合: a strong 天干合 exists and a strong 六冲 acts on at least one of its two pillars.

    Classical: 干合被支破 — the branch of a 合 pillar is clashed by an outside pillar.
    Both 天干合 and 六冲 store pillar labels as keys in 根基, making overlap detection direct.
    """
    STRONG = {"强势主流", "显著影响"}

    he_pillar_pairs: list[frozenset[str]] = [
        frozenset(ix.get("根基", {}).keys())
        for ix in ctx.interactions
        if ix.get("类型") == "天干合" and ix.get("强度") in STRONG
    ]
    if not he_pillar_pairs:
        return False, {}

    for ix in ctx.interactions:
        if ix.get("类型") != "六冲" or ix.get("强度") not in STRONG:
            continue
        chong_pillars = frozenset(ix.get("根基", {}).keys())
        for he_ps in he_pillar_pairs:
            shared = he_ps & chong_pillars
            if shared:
                return True, {
                    "合柱": sorted(he_ps),
                    "被冲合柱": sorted(shared),
                    "冲组合": ix.get("组合", ""),
                }
    return False, {}


def eval_jiao_hu_ban_shen_sha(ctx: ChartContext, pos: dict, target: dict) -> tuple[bool, dict]:
    """交互伴神煞: finds partner pillars interacting with the bound pillar via specified 交互类型,
    then checks whether any of those partner pillars carries a shen sha in 值.
    Used with 同柱: True so pos["柱"] = bound pillar.
    pos keys: 柱 (set via 同柱 binding).
    target keys: 值 (list of shen sha names), 交互类型 (list of interaction types, default ["六合", "三合"]).
    """
    bound_pillar = pos.get("柱")
    if not bound_pillar:
        return False, {}
    wanted_sha = set(target.get("值", []))
    jiao_hu_types = set(target.get("交互类型", ["六合", "三合"]))
    for item in ctx.interactions:
        if item.get("类型") not in jiao_hu_types:
            continue
        combo = item.get("组合明细", {})
        if bound_pillar not in combo:
            continue
        for partner_pillar in combo:
            if partner_pillar == bound_pillar:
                continue
            for star in ctx.shen_sha.get(partner_pillar, []):
                if star.get("名称") in wanted_sha:
                    return True, {
                        "交互类型": item.get("类型"),
                        "伴柱": partner_pillar,
                        "神煞": star.get("名称"),
                    }
    return False, {}


def eval_yang_ren_xiang_shi(ctx: ChartContext, pos: dict, target: dict) -> tuple[bool, dict]:
    """羊刃相蚀: both ganzhi of any valid erosion pair must appear anywhere in the four pillars."""
    chart_gz: dict[str, str] = {}
    for p in _ALL_PILLARS:
        pillar = ctx.pillars.get(p, {})
        stem = pillar.get("天干", {}).get("天干", "")
        branch = pillar.get("地支", {}).get("地支", "")
        if stem and branch:
            chart_gz[p] = stem + branch
    gz_set = set(chart_gz.values())
    for p1, p2 in _YANG_REN_XIANG_SHI_PAIRS:
        if p1 in gz_set and p2 in gz_set:
            pillar1 = next(k for k, v in chart_gz.items() if v == p1)
            pillar2 = next(k for k, v in chart_gz.items() if v == p2)
            return True, {"羊刃相蚀": f"{p1}+{p2}", "柱1": pillar1, "柱2": pillar2}
    return False, {}


def eval_gan_ke_zhi(ctx: ChartContext, pos: dict, _target: dict) -> tuple[bool, dict]:
    """干克支: the resolved pillar's stem element controls its own branch element."""
    pillar = pos.get("柱")
    if not pillar:
        return False, {}
    pillar_data = ctx.pillars.get(pillar, {})
    stem   = pillar_data.get("天干", {}).get("天干", "")
    branch = pillar_data.get("地支", {}).get("地支", "")
    if not stem or not branch:
        return False, {}
    elem_s = _GAN_ELEMENT.get(stem)
    elem_b = _ZHI_ELEMENT.get(branch)
    if elem_s and elem_b and _WU_XING_KE.get(elem_s) == elem_b:
        return True, {"柱": pillar, "天干": stem, "地支": branch, "干五行": elem_s, "支五行": elem_b}
    return False, {}


def eval_yu_ce_shuang_jian(ctx: ChartContext, pos: dict, _target: dict) -> tuple[bool, dict]:
    """御策_双见: 御 (horse−1) and 策 (horse+1) branches both appear anywhere in the four pillars."""
    horse_pillar = pos.get("柱")
    if not horse_pillar:
        return False, {}
    horse_branch = ctx.pillars.get(horse_pillar, {}).get("地支", {}).get("地支", "")
    if not horse_branch:
        return False, {}
    try:
        idx = _BRANCHES_SEQ.index(horse_branch)
    except ValueError:
        return False, {}
    # 御 = 马前一辰 (one step forward/ahead, higher index); 策 = 马后一辰 (one step back)
    # Classical example: horse=寅, 卯(寅+1)=御, 丑(寅-1)=策
    yu_branch = _BRANCHES_SEQ[(idx + 1) % 12]
    ce_branch = _BRANCHES_SEQ[(idx - 1) % 12]
    all_branches = {ctx.pillars.get(p, {}).get("地支", {}).get("地支", "") for p in _ALL_PILLARS}
    if yu_branch in all_branches and ce_branch in all_branches:
        return True, {"马支": horse_branch, "御支": yu_branch, "策支": ce_branch}
    return False, {}


def eval_gan_ke_mu_biao(ctx: ChartContext, pos: dict, _target: dict) -> tuple[bool, dict]:
    """天干五行克_目标柱: stem element of pos["柱"] (set via 同柱: True from prereq)
    controls stem element of pos["目标柱"] (default: 时柱)."""
    source_pillar = pos.get("柱")
    target_pillar = pos.get("目标柱", "时柱")
    if not source_pillar:
        return False, {}
    source_stem = ctx.pillars.get(source_pillar, {}).get("天干", {}).get("天干", "")
    target_stem = ctx.pillars.get(target_pillar, {}).get("天干", {}).get("天干", "")
    if not source_stem or not target_stem:
        return False, {}
    elem_s = _GAN_ELEMENT.get(source_stem)
    elem_t = _GAN_ELEMENT.get(target_stem)
    if elem_s and elem_t and _WU_XING_KE.get(elem_s) == elem_t:
        return True, {
            "克方柱": source_pillar, "被克方柱": target_pillar,
            "克方天干": source_stem, "被克方天干": target_stem,
            "克方五行": elem_s, "被克方五行": elem_t,
        }
    return False, {}


def eval_cheng_xuan_ma(ctx: ChartContext, _pos: dict, _target: dict) -> tuple[bool, dict]:
    """乘轩马: day pillar stem's Lu branch coincides with day pillar branch's Horse branch,
    and that shared branch appears in both 月柱 and 时柱.
    Classical example: 甲申人 (day=甲申) → day stem 甲禄在寅, day branch 申子辰马在寅; both equal 寅.
    月柱庚寅 and 时柱甲寅 both carry 寅.
    """
    day_stem   = ctx.pillars.get("日柱", {}).get("天干", {}).get("天干", "")
    day_branch = ctx.pillars.get("日柱", {}).get("地支", {}).get("地支", "")
    if not day_stem or not day_branch:
        return False, {}
    lu_branch    = _LU_WEI_MAP.get(day_stem)
    horse_branch = _YEAR_BRANCH_TO_MA.get(day_branch)
    if not lu_branch or not horse_branch or lu_branch != horse_branch:
        return False, {}
    shared_branch = lu_branch
    month_branch = ctx.pillars.get("月柱", {}).get("地支", {}).get("地支", "")
    hour_branch  = ctx.pillars.get("时柱", {}).get("地支", {}).get("地支", "")
    if month_branch == shared_branch and hour_branch == shared_branch:
        return True, {
            "日干": day_stem, "日支": day_branch,
            "共享支": shared_branch,
        }
    return False, {}


def eval_lu_ma_tong_xiang(ctx: ChartContext, _pos: dict, _target: dict) -> tuple[bool, dict]:
    """禄马同乡: day master's Lu branch equals year's horse branch,
    and that common branch appears anywhere in the four pillars."""
    day_stem    = ctx.pillars.get("日柱", {}).get("天干", {}).get("天干", "")
    year_branch = ctx.pillars.get("年柱", {}).get("地支", {}).get("地支", "")
    if not day_stem or not year_branch:
        return False, {}
    lu_branch    = _LU_WEI_MAP.get(day_stem)
    horse_branch = _YEAR_BRANCH_TO_MA.get(year_branch)
    if not lu_branch or not horse_branch or lu_branch != horse_branch:
        return False, {}
    for p in _ALL_PILLARS:
        branch = ctx.pillars.get(p, {}).get("地支", {}).get("地支", "")
        if branch == lu_branch:
            return True, {"日干": day_stem, "年支": year_branch, "共同支": lu_branch, "宫位": p}
    return False, {}


def eval_jia_lu_jia_ma(ctx: ChartContext, _pos: dict, _target: dict) -> tuple[bool, dict]:
    """夹禄夹马: day master's Lu branch and year's Horse branch are exactly 2 steps apart;
    the branch between them (adjacent to both) appears anywhere in the four pillars."""
    day_stem    = ctx.pillars.get("日柱", {}).get("天干", {}).get("天干", "")
    year_branch = ctx.pillars.get("年柱", {}).get("地支", {}).get("地支", "")
    if not day_stem or not year_branch:
        return False, {}
    lu_branch    = _LU_WEI_MAP.get(day_stem)
    horse_branch = _YEAR_BRANCH_TO_MA.get(year_branch)
    if not lu_branch or not horse_branch:
        return False, {}
    lu_idx    = _BRANCHES_SEQ.index(lu_branch)
    horse_idx = _BRANCHES_SEQ.index(horse_branch)
    if (horse_idx - lu_idx) % 12 == 2:
        middle_branch = _BRANCHES_SEQ[(lu_idx + 1) % 12]
    elif (lu_idx - horse_idx) % 12 == 2:
        middle_branch = _BRANCHES_SEQ[(horse_idx + 1) % 12]
    else:
        return False, {}
    for p in _ALL_PILLARS:
        branch = ctx.pillars.get(p, {}).get("地支", {}).get("地支", "")
        if branch == middle_branch:
            return True, {
                "日干": day_stem, "年支": year_branch,
                "禄支": lu_branch, "马支": horse_branch, "夹支": middle_branch, "宫位": p,
            }
    return False, {}


def eval_zhi_wuxing_ke_mu_biao(ctx: ChartContext, pos: dict, _target: dict) -> tuple[bool, dict]:
    """支五行克_目标柱: branch element of pos["柱"] (set via 同柱: True from prereq)
    controls branch element of pos["目标柱"] (default: 月柱)."""
    source_pillar = pos.get("柱")
    target_pillar = pos.get("目标柱", "月柱")
    if not source_pillar:
        return False, {}
    source_branch = ctx.pillars.get(source_pillar, {}).get("地支", {}).get("地支", "")
    target_branch = ctx.pillars.get(target_pillar, {}).get("地支", {}).get("地支", "")
    if not source_branch or not target_branch:
        return False, {}
    elem_s = _ZHI_ELEMENT.get(source_branch)
    elem_t = _ZHI_ELEMENT.get(target_branch)
    if elem_s and elem_t and _WU_XING_KE.get(elem_s) == elem_t:
        return True, {
            "克方柱": source_pillar, "被克方柱": target_pillar,
            "克方地支": source_branch, "被克方地支": target_branch,
            "克方五行": elem_s, "被克方五行": elem_t,
        }
    return False, {}


def eval_zhi_wuxing_ke_mu_present(ctx: ChartContext, pos: dict, _target: dict) -> tuple[bool, dict]:
    """支五行克元素墓出现: branch element of pos["柱"] controls some element X;
    checks that X's tomb branch appears anywhere in the four pillars."""
    source_pillar = pos.get("柱")
    if not source_pillar:
        return False, {}
    source_branch = ctx.pillars.get(source_pillar, {}).get("地支", {}).get("地支", "")
    if not source_branch:
        return False, {}
    source_elem = _ZHI_ELEMENT.get(source_branch)
    if not source_elem:
        return False, {}
    controlled_elem = _WU_XING_KE.get(source_elem)
    if not controlled_elem:
        return False, {}
    mu_branch = _WU_XING_MU_BRANCH.get(controlled_elem)
    if not mu_branch:
        return False, {}
    all_branches = {ctx.pillars.get(p, {}).get("地支", {}).get("地支", "") for p in _ALL_PILLARS}
    if mu_branch in all_branches:
        return True, {
            "柱": source_pillar, "地支": source_branch,
            "克方五行": source_elem, "被克五行": controlled_elem, "墓支": mu_branch,
        }
    return False, {}


def eval_na_yin_elem_chang_sheng(ctx: ChartContext, pos: dict, _target: dict) -> tuple[bool, dict]:
    """纳音元素长生: pos["柱"] branch must be the 长生 branch for the day pillar's Nayin element."""
    source_pillar = pos.get("柱")
    if not source_pillar:
        return False, {}
    horse_branch = ctx.pillars.get(source_pillar, {}).get("地支", {}).get("地支", "")
    na_yin_str = ctx.pillars.get("日柱", {}).get("纳音", "")
    if not horse_branch or not na_yin_str:
        return False, {}
    na_yin_elem = na_yin_str[-1]
    chang_sheng_branch = _NA_YIN_ELEM_CHANG_SHENG.get(na_yin_elem)
    if chang_sheng_branch and horse_branch == chang_sheng_branch:
        return True, {"柱": source_pillar, "马支": horse_branch, "日纳音": na_yin_str, "纳音五行": na_yin_elem}
    return False, {}


def eval_na_yin_elem_lin_guan(ctx: ChartContext, pos: dict, _target: dict) -> tuple[bool, dict]:
    """纳音元素临官: pos["柱"] branch must be the 临官 branch for the day pillar's Nayin element.
    Classical basis (SMTH 衔花马): 庚申/壬子/戊辰 nayin皆木, 遇寅(木临官), 马临官之地.
    """
    source_pillar = pos.get("柱")
    if not source_pillar:
        return False, {}
    horse_branch = ctx.pillars.get(source_pillar, {}).get("地支", {}).get("地支", "")
    na_yin_str = ctx.pillars.get("日柱", {}).get("纳音", "")
    if not horse_branch or not na_yin_str:
        return False, {}
    na_yin_elem = na_yin_str[-1]
    lin_guan_branch = _NA_YIN_ELEM_LIN_GUAN.get(na_yin_elem)
    if lin_guan_branch and horse_branch == lin_guan_branch:
        return True, {"柱": source_pillar, "马支": horse_branch, "日纳音": na_yin_str, "纳音五行": na_yin_elem}
    return False, {}


def eval_horse_stem_has_qi(ctx: ChartContext, pos: dict, _target: dict) -> tuple[bool, dict]:
    """马干有气: the stem of the horse pillar has 长生 or 临官 at the horse branch.

    Classical basis (SMTH 有驿有马): "干为马" — the stem's element is vigorous at the
    horse position. For each stem, 有气 means horse branch == 长生 branch OR 临官 branch.
    """
    source_pillar = pos.get("柱")
    if not source_pillar:
        return False, {}
    horse_branch = ctx.pillars.get(source_pillar, {}).get("地支", {}).get("地支", "")
    stem = ctx.pillars.get(source_pillar, {}).get("天干", {}).get("天干", "")
    if not horse_branch or not stem:
        return False, {}
    chang_sheng = _CHANG_SHENG_MAP.get(stem)
    lin_guan    = _LIN_GUAN_MAP.get(stem)
    if horse_branch == chang_sheng:
        return True, {"马柱": source_pillar, "马干": stem, "马支": horse_branch, "干气": "长生"}
    if horse_branch == lin_guan:
        return True, {"马柱": source_pillar, "马干": stem, "马支": horse_branch, "干气": "临官"}
    return False, {}


def eval_ganzhi_pair_present(ctx: ChartContext, _pos: dict, target: dict) -> tuple[bool, dict]:
    """干支对同现: both ganzhi in target["对"] must appear anywhere in the four pillars."""
    pair = target.get("对", [])
    if len(pair) != 2:
        return False, {}
    all_ganzhi: set[str] = set()
    for p in _ALL_PILLARS:
        pillar = ctx.pillars.get(p, {})
        stem = pillar.get("天干", {}).get("天干", "")
        branch = pillar.get("地支", {}).get("地支", "")
        if stem and branch:
            all_ganzhi.add(stem + branch)
    a, b = pair[0], pair[1]
    if a in all_ganzhi and b in all_ganzhi:
        return True, {"对": pair}
    return False, {}


def _xun_of(stem: str, branch: str) -> int:
    """0-based 旬 index (0=甲子旬…5=甲寅旬) for a ganzhi pair."""
    s = _STEMS_SEQ.index(stem)
    b = _BRANCHES_SEQ.index(branch)
    k = (5 * ((b - s) // 2)) % 6
    return (s + 10 * k) // 10


def eval_xun_zhong_lu(ctx: ChartContext, _pos: dict, target: dict) -> tuple[bool, dict]:
    """旬中禄: the pillar bearing 禄神 (from 日干 or 年干) is in the same 旬 as the base pillar.
    target["基准柱"]: which pillar to measure the xun from (default: "年柱").
    """
    base_key = target.get("基准柱", "年柱")
    base = ctx.pillars.get(base_key, {})
    base_stem   = base.get("天干", {}).get("天干", "")
    base_branch = base.get("地支", {}).get("地支", "")
    if not base_stem or not base_branch:
        return False, {}
    base_xun = _xun_of(base_stem, base_branch)

    day_stem  = ctx.pillars.get("日柱", {}).get("天干", {}).get("天干", "")
    year_stem = ctx.pillars.get("年柱", {}).get("天干", {}).get("天干", "")
    lu_map: dict[str, str] = {}  # lu_branch → source label
    for stem, label in [(day_stem, "日干"), (year_stem, "年干")]:
        lu = _LU_WEI_MAP.get(stem)
        if lu:
            lu_map[lu] = label

    matches = []
    for p in _ALL_PILLARS:
        if p == base_key:
            continue
        pillar   = ctx.pillars.get(p, {})
        p_stem   = pillar.get("天干", {}).get("天干", "")
        p_branch = pillar.get("地支", {}).get("地支", "")
        if not p_stem or not p_branch or p_branch not in lu_map:
            continue
        if _xun_of(p_stem, p_branch) == base_xun:
            matches.append({"宫位": p, "禄支": p_branch, "来源": lu_map[p_branch]})

    if matches:
        return True, {"基准柱": base_key, "旬": base_xun, "旬中禄": matches}
    return False, {}


def eval_lu_ru_lu_tang(ctx: ChartContext, _pos: dict, _target: dict) -> tuple[bool, dict]:
    """禄入禄堂: a chart pillar's ganzhi matches the year stem's 禄堂 position(s).
    禄堂 = ganzhi where the year stem reappears in the 五虎遁 month stem sequence.
    Stems at offsets 0–1 wrap around and yield two 禄堂 ganzhi (e.g. 辛→辛卯+辛丑, 壬→壬寅+壬子).
    """
    year_stem = ctx.pillars.get("年柱", {}).get("天干", {}).get("天干", "")
    if not year_stem:
        return False, {}
    wu_hu_start = _WU_HU_DUN_START.get(year_stem)
    if not wu_hu_start:
        return False, {}

    base_offset = (_STEMS_SEQ.index(year_stem) - _STEMS_SEQ.index(wu_hu_start) + 10) % 10
    lu_tang: set[str] = set()
    for offset in (base_offset, base_offset + 10):
        if offset < 12:
            lu_tang.add(year_stem + _MONTH_BRANCHES[offset])

    for p in _ALL_PILLARS:
        pillar = ctx.pillars.get(p, {})
        gz = pillar.get("天干", {}).get("天干", "") + pillar.get("地支", {}).get("地支", "")
        if gz in lu_tang:
            return True, {"年干": year_stem, "禄堂": sorted(lu_tang), "命中": gz, "宫位": p}

    return False, {}


def eval_chao_yuan_jia_he(ctx: ChartContext, _pos: dict, _target: dict) -> tuple[bool, dict]:
    """朝元夹合: three-pillar pattern.
    (1) Day branch = Lu of day stem's 五合 partner (he_stem).
    (2) Two other pillars share stem = he_stem with branches flanking the day branch on both sides.
    E.g. 癸巳 + 戊辰 + 戊午: 戊合癸, Lu(戊)=巳=day branch, 辰-巳-午.
    """
    day_stem   = ctx.pillars.get("日柱", {}).get("天干", {}).get("天干", "")
    day_branch = ctx.pillars.get("日柱", {}).get("地支", {}).get("地支", "")
    if not day_stem or not day_branch:
        return False, {}

    he_stem = _STEMS_SEQ[(_STEMS_SEQ.index(day_stem) + 5) % 10]
    if _LU_WEI_MAP.get(he_stem) != day_branch:
        return False, {}

    b_idx  = _BRANCHES_SEQ.index(day_branch)
    b_prev = _BRANCHES_SEQ[(b_idx - 1) % 12]
    b_next = _BRANCHES_SEQ[(b_idx + 1) % 12]

    has_prev = has_next = False
    for p in _ALL_PILLARS:
        if p == "日柱":
            continue
        pillar = ctx.pillars.get(p, {})
        if pillar.get("天干", {}).get("天干") != he_stem:
            continue
        branch = pillar.get("地支", {}).get("地支", "")
        if branch == b_prev:
            has_prev = True
        if branch == b_next:
            has_next = True

    if has_prev and has_next:
        return True, {"日干": day_stem, "日支": day_branch, "合干": he_stem, "夹支": [b_prev, b_next]}
    return False, {}


def eval_hu_huan_gui_lu(ctx: ChartContext, _pos: dict, _target: dict) -> tuple[bool, dict]:
    """互换贵禄: two pillars mutually exchange 禄 — each pillar's branch is the other's stem's 禄.
    E.g. 庚寅 + 甲申: branch(庚寅)=寅=Lu(甲), branch(甲申)=申=Lu(庚).
    """
    pillar_data = [
        (p,
         ctx.pillars.get(p, {}).get("天干", {}).get("天干", ""),
         ctx.pillars.get(p, {}).get("地支", {}).get("地支", ""))
        for p in _ALL_PILLARS
    ]
    pillar_data = [(p, s, b) for p, s, b in pillar_data if s and b]

    for i, (p1, s1, b1) in enumerate(pillar_data):
        for p2, s2, b2 in pillar_data[i + 1:]:
            if b1 == _LU_WEI_MAP.get(s2) and b2 == _LU_WEI_MAP.get(s1):
                return True, {
                    "柱A": p1, "干支A": s1 + b1,
                    "柱B": p2, "干支B": s2 + b2,
                }

    return False, {}


def eval_gan_zhi_he_lu(ctx: ChartContext, _pos: dict, _target: dict) -> tuple[bool, dict]:
    """干支合禄: pillar P1 holds the day master's 禄 branch; another pillar P2 has the 六合 of that
    branch; and P1's stem 五合s with P2's stem. All three conditions must hold on the same pair.
    """
    day_stem = ctx.pillars.get("日柱", {}).get("天干", {}).get("天干", "")
    lu_branch = _LU_WEI_MAP.get(day_stem)
    if not lu_branch:
        return False, {}
    liu_he_branch = _LIU_HE_MAP.get(lu_branch)
    if not liu_he_branch:
        return False, {}

    p1_list, p2_list = [], []
    for p in _ALL_PILLARS:
        pillar = ctx.pillars.get(p, {})
        branch = pillar.get("地支", {}).get("地支", "")
        stem   = pillar.get("天干", {}).get("天干", "")
        if not stem:
            continue
        if branch == lu_branch:
            p1_list.append((p, stem))
        if branch == liu_he_branch:
            p2_list.append((p, stem))

    for p1, s1 in p1_list:
        for p2, s2 in p2_list:
            if p1 != p2 and abs(_STEMS_SEQ.index(s1) - _STEMS_SEQ.index(s2)) == 5:
                return True, {
                    "禄柱": p1, "禄干支": s1 + lu_branch,
                    "合柱": p2, "合干支": s2 + liu_he_branch,
                }

    return False, {}


def eval_tian_lu_gui_shen(ctx: ChartContext, _pos: dict, _target: dict) -> tuple[bool, dict]:
    """天禄贵神: 3-step classical pattern using 五虎遁 + 天乙贵人.

    (1) Derive 'True Lu stem' for the year stem via 五虎遁.
    (2) Find a chart pillar whose branch is 天乙贵人 of the True Lu stem.
    (3) Verify that pillar's stem's 天乙贵人 includes the original year-stem Lu branch.
    """
    year_stem = ctx.pillars.get("年柱", {}).get("天干", {}).get("天干", "")
    if not year_stem:
        return False, {}

    year_lu_branch = _LU_WEI_MAP.get(year_stem)
    wu_hu_start    = _WU_HU_DUN_START.get(year_stem)
    if not year_lu_branch or not wu_hu_start:
        return False, {}

    month_offset  = _MONTH_BRANCHES.index(year_lu_branch)
    true_lu_stem  = _STEMS_SEQ[(_STEMS_SEQ.index(wu_hu_start) + month_offset) % 10]
    noble_branches = _TIAN_YI_BRANCHES.get(true_lu_stem, frozenset())

    for p in _ALL_PILLARS:
        pillar = ctx.pillars.get(p, {})
        branch = pillar.get("地支", {}).get("地支", "")
        stem   = pillar.get("天干", {}).get("天干", "")
        if branch not in noble_branches or not stem:
            continue
        if year_lu_branch in _TIAN_YI_BRANCHES.get(stem, frozenset()):
            return True, {
                "年干": year_stem, "禄支": year_lu_branch,
                "真禄茎": true_lu_stem, "贵人支": branch, "贵人宫位": p,
            }

    return False, {}


def eval_tian_ma_gui_shen(ctx: ChartContext, _pos: dict, _target: dict) -> tuple[bool, dict]:
    """天马贵神: 3-step classical pattern using 五虎遁 + 天乙贵人, based on 驿马 instead of 禄神.

    (1) Derive year branch → horse branch via San He bureau, then 'True Horse stem' via 五虎遁.
    (2) Find a chart pillar whose branch is 天乙贵人 of the True Horse stem.
    (3) Verify that pillar's stem's 天乙贵人 includes the original horse branch.
    """
    year_stem   = ctx.pillars.get("年柱", {}).get("天干", {}).get("天干", "")
    year_branch = ctx.pillars.get("年柱", {}).get("地支", {}).get("地支", "")
    if not year_stem or not year_branch:
        return False, {}
    horse_branch = _YEAR_BRANCH_TO_MA.get(year_branch)
    wu_hu_start  = _WU_HU_DUN_START.get(year_stem)
    if not horse_branch or not wu_hu_start:
        return False, {}
    month_offset    = _MONTH_BRANCHES.index(horse_branch)
    true_horse_stem = _STEMS_SEQ[(_STEMS_SEQ.index(wu_hu_start) + month_offset) % 10]
    noble_branches  = _TIAN_YI_BRANCHES.get(true_horse_stem, frozenset())
    for p in _ALL_PILLARS:
        pillar = ctx.pillars.get(p, {})
        branch = pillar.get("地支", {}).get("地支", "")
        stem   = pillar.get("天干", {}).get("天干", "")
        if branch not in noble_branches or not stem:
            continue
        if horse_branch in _TIAN_YI_BRANCHES.get(stem, frozenset()):
            return True, {
                "年支": year_branch, "马支": horse_branch,
                "真马干": true_horse_stem, "贵人支": branch, "贵人宫位": p,
            }
    return False, {}


def eval_ma_zhou_tian_ting(ctx: ChartContext, _pos: dict, _target: dict) -> tuple[bool, dict]:
    """马骤天庭: horse leaps to the heavenly court — highest-rank formation.

    Two classical sub-conditions from SMTH (either triggers):
    (A) Nayin-木 person, year-branch horse = 亥, horse pillar ganzhi = 辛亥.
        ("木人得亥而见辛亥")
    (B) True Horse stem (五虎遁: year-stem → stem at horse-branch month) has 禄 at 巳
        (巳 = 天庭 / Southern Heavenly Court), AND 巳 and 酉 both appear in the chart.
        ("马上干逢得禄...戊之禄在巳，巳系天庭，复见巳，得酉合之")
    """
    year_stem   = ctx.pillars.get("年柱", {}).get("天干", {}).get("天干", "")
    year_branch = ctx.pillars.get("年柱", {}).get("地支", {}).get("地支", "")
    if not year_stem or not year_branch:
        return False, {}
    horse_branch = _YEAR_BRANCH_TO_MA.get(year_branch)
    if not horse_branch:
        return False, {}
    all_branches = {ctx.pillars.get(p, {}).get("地支", {}).get("地支", "") for p in _ALL_PILLARS}

    # Sub-condition A: nayin-木, horse=亥, horse ganzhi=辛亥
    if horse_branch == "亥":
        day_nayin = ctx.pillars.get("日柱", {}).get("纳音", "")
        if day_nayin and day_nayin[-1] == "木":
            for p in _ALL_PILLARS:
                if not any(s.get("名称") == "驿马" for s in ctx.shen_sha.get(p, [])):
                    continue
                pillar = ctx.pillars.get(p, {})
                if (pillar.get("天干", {}).get("天干") == "辛"
                        and pillar.get("地支", {}).get("地支") == "亥"):
                    return True, {"条件": "甲", "马支": "亥", "马干支": "辛亥", "日纳音": day_nayin}

    # Sub-condition B: true horse stem (五虎遁) has 禄=巳; 巳 and 酉 both in chart
    wu_hu_start = _WU_HU_DUN_START.get(year_stem)
    if wu_hu_start:
        month_offset    = _MONTH_BRANCHES.index(horse_branch)
        true_horse_stem = _STEMS_SEQ[(_STEMS_SEQ.index(wu_hu_start) + month_offset) % 10]
        if _LU_WEI_MAP.get(true_horse_stem) == "巳" and "巳" in all_branches and "酉" in all_branches:
            return True, {
                "条件": "乙", "年支": year_branch, "马支": horse_branch,
                "真马干": true_horse_stem, "天庭": "巳", "合支": "酉",
            }
    return False, {}


def eval_lu_zai_jue_xiang(ctx: ChartContext, _pos: dict, _target: dict) -> tuple[bool, dict]:
    """禄在绝乡: any pillar carrying 禄神 (日干之禄) has 十二长生=绝 for the day master.
    Classical basis (SMTH 无辔): "禄在绝乡者是" — the pillar bearing 禄神 is at the day
    master's 绝 stage, indicating the salary star is in its death-fall position.
    """
    day_stem = ctx.pillars.get("日柱", {}).get("天干", {}).get("天干", "")
    if not day_stem:
        return False, {}
    lu_branch = _LU_WEI_MAP.get(day_stem)
    if not lu_branch:
        return False, {}
    for p in _ALL_PILLARS:
        pillar = ctx.pillars.get(p, {})
        if pillar.get("地支", {}).get("地支") != lu_branch:
            continue
        shens = ctx.shen_sha.get(p, [])
        if not any(s.get("名称") == "禄神" for s in shens):
            continue
        stage = pillar.get("十二长生", {}).get("日干", "")
        if stage == "绝":
            return True, {"禄神柱": p, "禄支": lu_branch, "十二长生": stage}
    return False, {}


def eval_huo_lu(ctx: ChartContext, _pos: dict, _target: dict) -> tuple[bool, dict]:
    """活禄: the 戌-month stem (via 五虎遁 from year stem) equals the day master's stem,
    and that ganzhi (戌-month stem + 戌) appears anywhere in the four pillars."""
    year_stem = ctx.pillars.get("年柱", {}).get("天干", {}).get("天干", "")
    day_stem  = ctx.pillars.get("日柱", {}).get("天干", {}).get("天干", "")
    wu_hu_start = _WU_HU_DUN_START.get(year_stem)
    if not year_stem or not day_stem or not wu_hu_start:
        return False, {}
    xu_month_stem = _STEMS_SEQ[(_STEMS_SEQ.index(wu_hu_start) + 8) % 10]  # 戌 = index 8
    if xu_month_stem != day_stem:
        return False, {}
    huo_lu_gz = xu_month_stem + "戌"
    for p in _ALL_PILLARS:
        pillar = ctx.pillars.get(p, {})
        stem   = pillar.get("天干", {}).get("天干", "")
        branch = pillar.get("地支", {}).get("地支", "")
        if stem + branch == huo_lu_gz:
            return True, {"年干": year_stem, "日干": day_stem, "活禄": huo_lu_gz, "宫位": p}
    return False, {}


def eval_huo_ma(ctx: ChartContext, _pos: dict, _target: dict) -> tuple[bool, dict]:
    """活马: the 'true horse' pillar (stem derived via 五虎遁 + horse branch) appears anywhere in chart.
    Year branch → horse branch via San He bureau; year stem → 五虎遁 → stem on that horse month."""
    year_stem   = ctx.pillars.get("年柱", {}).get("天干", {}).get("天干", "")
    year_branch = ctx.pillars.get("年柱", {}).get("地支", {}).get("地支", "")
    wu_hu_start = _WU_HU_DUN_START.get(year_stem)
    if not year_stem or not year_branch or not wu_hu_start:
        return False, {}
    horse_branch = _YEAR_BRANCH_TO_MA.get(year_branch)
    if not horse_branch:
        return False, {}
    offset = _MONTH_BRANCHES.index(horse_branch)
    huo_ma_stem = _STEMS_SEQ[(_STEMS_SEQ.index(wu_hu_start) + offset) % 10]
    huo_ma_gz = huo_ma_stem + horse_branch
    for p in _ALL_PILLARS:
        pillar = ctx.pillars.get(p, {})
        stem   = pillar.get("天干", {}).get("天干", "")
        branch = pillar.get("地支", {}).get("地支", "")
        if stem + branch == huo_ma_gz:
            return True, {"年干": year_stem, "年支": year_branch, "活马": huo_ma_gz, "宫位": p}
    return False, {}


def eval_tian_gan_wu_he(ctx: ChartContext, _pos: dict, target: dict) -> tuple[bool, dict]:
    """天干五合: both stems in target["参与天干"] appear anywhere in the chart and form a 五合 pair."""
    wanted = target.get("参与天干", [])
    if len(wanted) != 2:
        return False, {}
    s1, s2 = wanted[0], wanted[1]
    try:
        if abs(_STEMS_SEQ.index(s1) - _STEMS_SEQ.index(s2)) != 5:
            return False, {}
    except ValueError:
        return False, {}
    chart_stems = {ctx.pillars.get(p, {}).get("天干", {}).get("天干", "") for p in _ALL_PILLARS}
    if s1 in chart_stems and s2 in chart_stems:
        return True, {"天干A": s1, "天干B": s2}
    return False, {}


def eval_tian_gan_tong(ctx: ChartContext, pos: dict, target: dict) -> tuple[bool, dict]:
    """天干同: the resolved pillar's stem equals the stem of target["源"] pillar."""
    source_pillar = target.get("源")
    if not source_pillar:
        return False, {}
    ref_stem = ctx.pillars.get(source_pillar, {}).get("天干", {}).get("天干")
    if not ref_stem:
        return False, {}
    for p in _resolve_pillars(pos.get("柱")):
        stem = ctx.pillars.get(p, {}).get("天干", {}).get("天干")
        if stem == ref_stem:
            return True, {"宫位": p, "天干": stem, "源": source_pillar}
    return False, {}


def eval_di_zhi_gong(ctx: ChartContext, _pos: dict, _target: dict) -> tuple[bool, dict]:
    """地支拱: two branches in the chart flank the day master's 禄 branch (one before, one after in the 12-branch cycle)."""
    day_stem = ctx.pillars.get("日柱", {}).get("天干", {}).get("天干", "")
    lu_branch = _LU_WEI_MAP.get(day_stem)
    if not lu_branch:
        return False, {}
    b_idx = _BRANCHES_SEQ.index(lu_branch)
    b_prev = _BRANCHES_SEQ[(b_idx - 1) % 12]
    b_next = _BRANCHES_SEQ[(b_idx + 1) % 12]
    chart_branches = {ctx.pillars.get(p, {}).get("地支", {}).get("地支", "") for p in _ALL_PILLARS}
    if b_prev in chart_branches and b_next in chart_branches:
        return True, {"禄支": lu_branch, "夹支": [b_prev, b_next]}
    return False, {}


def eval_lu_shen_direction(ctx: ChartContext, _pos: dict, target: dict) -> tuple[bool, dict]:
    """禄神_方向: chart contains the branch immediately before (向) or after (近) the day master's 禄 branch."""
    direction = target.get("方向")
    if direction not in ("向", "近"):
        return False, {}
    day_stem = ctx.pillars.get("日柱", {}).get("天干", {}).get("天干", "")
    lu_branch = _LU_WEI_MAP.get(day_stem)
    if not lu_branch:
        return False, {}
    b_idx = _BRANCHES_SEQ.index(lu_branch)
    target_branch = _BRANCHES_SEQ[(b_idx - 1) % 12] if direction == "向" else _BRANCHES_SEQ[(b_idx + 1) % 12]
    chart_branches = {ctx.pillars.get(p, {}).get("地支", {}).get("地支", "") for p in _ALL_PILLARS}
    if target_branch in chart_branches:
        return True, {"方向": direction, "禄支": lu_branch, "方向支": target_branch}
    return False, {}



_NOBLE_SHA_NAMES: frozenset[str] = frozenset({"昼天乙贵人", "夜天乙贵人"})


def eval_gui_shen_liu_he(ctx: ChartContext, _pos: dict, target: dict) -> tuple[bool, dict]:
    """贵神六合: counts how many noble-bearing branches have their 六合 partner present in chart."""
    threshold: int = target.get("阈值", 1)
    comparator: str = target.get("比较", "≥")
    noble_branches: set[str] = set()
    for p in _ALL_PILLARS:
        branch = ctx.pillars.get(p, {}).get("地支", {}).get("地支", "")
        if branch and any(s.get("名称") in _NOBLE_SHA_NAMES for s in ctx.shen_sha.get(p, [])):
            noble_branches.add(branch)
    chart_branches = {ctx.pillars.get(p, {}).get("地支", {}).get("地支", "") for p in _ALL_PILLARS}
    matches = [(b, _LIU_HE_MAP[b]) for b in noble_branches if _LIU_HE_MAP.get(b) in chart_branches]
    count = len(matches)
    ok = _compare_threshold(count, threshold, comparator)
    return (True, {"六合对数": count, "匹配": [f"{a}→{b}" for a, b in matches]}) if ok else (False, {})


def eval_gui_ren_jia_yong_tai_sui(ctx: ChartContext, _pos: dict, _target: dict) -> tuple[bool, dict]:
    """贵人夹拱太岁: two pillars whose branches flank the year branch (prev/next in cycle) both carry 天乙贵人."""
    year_branch = ctx.pillars.get("年柱", {}).get("地支", {}).get("地支", "")
    if not year_branch or year_branch not in _BRANCHES_SEQ:
        return False, {}
    b_idx = _BRANCHES_SEQ.index(year_branch)
    b_prev = _BRANCHES_SEQ[(b_idx - 1) % 12]
    b_next = _BRANCHES_SEQ[(b_idx + 1) % 12]
    noble_branches: set[str] = set()
    for p in _ALL_PILLARS:
        branch = ctx.pillars.get(p, {}).get("地支", {}).get("地支", "")
        if branch and any(s.get("名称") in _NOBLE_SHA_NAMES for s in ctx.shen_sha.get(p, [])):
            noble_branches.add(branch)
    if b_prev in noble_branches and b_next in noble_branches:
        return True, {"太岁支": year_branch, "左夹贵": b_prev, "右夹贵": b_next}
    return False, {}


CONDITION_EVALUATORS: dict[str, Callable] = {
    "十神": eval_ten_god,
    "十神_集合": eval_ten_god_set,
    "十神_无": eval_ten_god_absent,
    "十二长生": eval_di_shi,
    "十二长生_无": eval_di_shi_absent,
    "神煞": eval_shen_sha,
    "神煞_无": eval_shen_sha_absent,
    "神煞_地支相生": eval_shen_sha_dizhi_sheng,
    "空亡": eval_kong_wang,
    "互换空亡": eval_huhuan_kong_wang,
    "空亡支_五行":  eval_kong_wang_zhi_wuxing,
    "空亡支_地支值": eval_kong_wang_zhi_value,
    "日主克空亡支": eval_rizhu_ke_kongwang,
    "空亡支_长生":  eval_kong_wang_zhi_changsheng,
    "空亡支_同类冲": eval_kong_wang_tongwei_chong,
    "交互": eval_interaction,
    "交互_无": eval_interaction_absent,
    "计数": eval_counter,
    "计数_状态": eval_ten_god_count_by_state,
    "计数_差": eval_ten_god_count_diff,
    "计数_神煞": eval_shen_sha_count,
    "计数_神煞_差": eval_shen_sha_count_diff,
    "计数_天干合": eval_stem_harmony_count,
    "五行生克": eval_wu_xing_relation,
    "十神_五行状态": eval_ten_god_wu_xing_state,
    "十神_克": eval_ten_god_ke,
    "十神_生": eval_ten_god_sheng,
    "神煞支_五行关系": eval_sha_zhi_wu_xing_relation,
    "神煞支_五行关系_无": eval_sha_zhi_wu_xing_relation_absent,
    "十神_同柱": eval_ten_god_same_pillar,
    "日主强弱": eval_ri_zhu_strength,
    "无根": eval_wu_gen,
    "月令强弱": eval_yue_ling_strength,
    "地支值": eval_branch_value,
    "地支三合": eval_branch_triple,
    "天干值": eval_stem_value,
    "天干阴阳": eval_stem_yinyang,
    "空亡计数": eval_kong_wang_count,
    "五行有": eval_wu_xing_present,
    "纳音_五行有": eval_na_yin_wu_xing_present,
    "五行全": eval_wu_xing_complete,
    "天干全部相同": eval_stems_all_same,
    "地支全部相同": eval_branches_all_same,
    "天干相同_跨柱": eval_tian_gan_same_cross_pillar,
    "地支相同_跨柱": eval_di_zhi_same_cross_pillar,
    "特定组合": eval_specific_stem_branch_combo,
    "先后序": eval_xian_hou_xu,
    "干禄在支": eval_gan_lu_zai_zhi,

    "五行交战": eval_wu_xing_battle,
    "同柱_神煞": eval_shen_sha_same_pillar,
    "同柱_五行克": eval_wu_xing_ke_same_pillar,
    "计数_地支": eval_di_zhi_count,
    "计数_五行": eval_wu_xing_count,
    "五行计数差": eval_wu_xing_count_diff,
    "五行_位置关系": eval_wu_xing_position_relation,
    "重元星": eval_zhong_yuan_xing,
    "月令正气": eval_yue_ling_zheng_qi,
    "三合特定": eval_san_he_branches,
    "三合官局": eval_san_he_guan_ju,
    "官星坐禄": eval_guan_xing_zuo_lu,
    "五行克_柱间": eval_wu_xing_ke_cross_pillar,
    "干克关系": eval_gan_ke_guanxi,
    "地支偏移": eval_di_zhi_offset,
    "天干五合_柱间": eval_tian_gan_wu_he_cross_pillar,
    "十神五合": eval_ten_god_wu_he,
    "十神有合": eval_ten_god_you_he,
    "十神_阶段在支": eval_ten_god_jie_duan_zai_zhi,
    "十神_长生阶段": eval_ten_god_stage_at_pillar_branch,
    "天干合化气克纳音": eval_tian_gan_he_hua_qi_ke_na_yin,
    "十神_五行": eval_ten_god_element_attribute,
    "节气_月内位置": eval_jie_qi_yue_nei_position,
    "禄支三合": eval_lu_zhi_san_he,
    "禄支六合": eval_lu_zhi_liu_he,
    "干支合马": eval_gan_zhi_he_ma,
    "驿马驮尸": eval_yi_ma_duo_shi,
    "九地马": eval_jiu_di_ma,
    "马三合全": eval_ma_san_he_quan,
    "纳音克_柱间": eval_na_yin_ke_zhu_jian,
    "纳音克关系": eval_na_yin_ke_guanxi,
    "干克支": eval_gan_ke_zhi,
    "御策_双见": eval_yu_ce_shuang_jian,
    "天干五行克_目标柱": eval_gan_ke_mu_biao,
    "支五行克_目标柱": eval_zhi_wuxing_ke_mu_biao,
    "支五行克元素墓出现": eval_zhi_wuxing_ke_mu_present,
    "纳音元素长生": eval_na_yin_elem_chang_sheng,
    "纳音元素临官": eval_na_yin_elem_lin_guan,
    "马干有气": eval_horse_stem_has_qi,
    "乘轩马": eval_cheng_xuan_ma,
    "禄马同乡": eval_lu_ma_tong_xiang,
    "夹禄夹马": eval_jia_lu_jia_ma,
    "干支对同现": eval_ganzhi_pair_present,
    "旬中禄": eval_xun_zhong_lu,
    "天禄贵神": eval_tian_lu_gui_shen,
    "天马贵神": eval_tian_ma_gui_shen,
    "马骤天庭": eval_ma_zhou_tian_ting,
    "禄在绝乡": eval_lu_zai_jue_xiang,
    "活禄": eval_huo_lu,
    "活马": eval_huo_ma,
    "干支合禄": eval_gan_zhi_he_lu,
    "互换贵禄": eval_hu_huan_gui_lu,
    "朝元夹合": eval_chao_yuan_jia_he,
    "禄入禄堂": eval_lu_ru_lu_tang,
    "天干五合": eval_tian_gan_wu_he,
    "天干同": eval_tian_gan_tong,
    "地支拱": eval_di_zhi_gong,
    "禄神_方向": eval_lu_shen_direction,
    "贵神六合": eval_gui_shen_liu_he,
    "贵人夹拱太岁": eval_gui_ren_jia_yong_tai_sui,
    "纳音五行": eval_na_yin_wu_xing,
    "计数_纳音五行": eval_na_yin_wu_xing_count,
    "交互子属性": eval_jiao_hu_zi_shu_xing,
    "库位冲开": eval_ku_wei_chong_kai,
    "库位冲开_释放十神": eval_ku_wei_chong_kai_shi_shen,
    "冲出藏干十神": eval_chong_chu_cang_gan_shi_shen,
    "胎元地支": eval_tai_yuan_di_zhi,
    "破禄": eval_po_lu,
    "破马": eval_po_ma,
    "破财": eval_po_cai,
    "破印": eval_po_yin,
    "破合": eval_po_he,
    "交互伴神煞": eval_jiao_hu_ban_shen_sha,
    "羊刃相蚀": eval_yang_ren_xiang_shi,
}


# ── Rule engine ───────────────────────────────────────────────────────────────


def _merge_evidence(evidence_list: list[dict]) -> dict | list[dict]:
    if not evidence_list:
        return {}
    if len(evidence_list) == 1:
        return evidence_list[0]
    seen: set[str] = set()
    for e in evidence_list:
        if set(e.keys()) & seen:
            return evidence_list  # intentional: preserve per-condition grouping when keys collide
        seen |= set(e.keys())
    merged: dict = {}
    for e in evidence_list:
        merged.update(e)
    return merged


def evaluate_rule(rule: dict, context: ChartContext, _depth: int = 0, _prereq_pillar: str | None = None) -> tuple[bool, dict | list[dict]]:
    if _depth > 10:
        return False, {}
    if rule.get("requires_dynamic") and not getattr(context, "is_dynamic", False):
        return False, {}
    gender_filter = rule.get("适用性别", "通用")
    if gender_filter != "通用" and gender_filter != context.gender:
        return False, {}

    prereq_pillar: str | None = _prereq_pillar  # inherit from parent nested call
    prereq = rule.get("前提条件")
    prereq_evidence: dict = {}
    if prereq:
        pos = prereq.get("位置", {})
        target = prereq.get("判定目标", {})
        evaluator = CONDITION_EVALUATORS.get(target.get("类型"))
        if evaluator is None:
            return False, {}
        ok, prereq_evidence = evaluator(context, pos, target)
        if not ok:
            return False, {}
        prereq_pillar = prereq_evidence.get("宫位")

    mode = rule.get("判定模式", "AND")
    conditions = rule.get("判定逻辑", [])
    if not conditions:
        # Prerequisite met with no further conditions → rule fires on prerequisite alone
        if prereq:
            return True, prereq_evidence
        return False, {}

    results: list[bool] = []
    evidence_list: list[dict] = []

    for cond in conditions:
        # Nested sub-rule block (e.g. AND inside an OR)
        if "判定模式" in cond and "判定逻辑" in cond:
            ok, evidence = evaluate_rule(cond, context, _depth + 1, _prereq_pillar=prereq_pillar)
            results.append(ok)
            if ok and evidence:
                if isinstance(evidence, list):
                    evidence_list.extend(evidence)
                else:
                    evidence_list.append(evidence)
            continue

        pos = cond.get("位置", {})
        if pos.get("同柱") and prereq_pillar:
            pos = {**pos, "柱": prereq_pillar}
        target = cond.get("判定目标", {})

        # Conditions referencing an external chart (spouse's BaZi) are deferred
        pillar_spec = pos.get("柱", "")
        if isinstance(pillar_spec, str) and pillar_spec.startswith("外部_"):
            results.append(False)
            continue

        evaluator = CONDITION_EVALUATORS.get(target.get("类型"))
        if evaluator is None:
            results.append(False)
            continue

        ok, evidence = evaluator(context, pos, target)
        results.append(ok)
        if ok and evidence:
            prefix = cond.get("证据前缀", "")
            if prefix:
                evidence = {f"{prefix}_{k}": v for k, v in evidence.items()}
            evidence_list.append(evidence)

    if mode == "AND":
        matched = all(results)
    elif mode == "OR":
        matched = any(results)
    elif mode == "NOT":
        matched = not any(results)
    else:  # "阈值" — single 计数 condition
        matched = bool(results) and results[0]

    return (matched, _merge_evidence(evidence_list)) if matched else (False, {})


# ── Domain analyzers ──────────────────────────────────────────────────────────


def _format_rule_match(rule: dict, evidence: dict | list[dict]) -> dict:
    entry: dict = {
        "逻辑名称": rule["逻辑名称"],
        "结论": rule["断语"],
        "证据": evidence,
    }
    if "现代解读" in rule:
        entry["现代解读"] = rule["现代解读"]
    return entry


def analyse_family_prediction(context: ChartContext) -> dict:
    matched = []
    for rule in family_prediction_论六亲:
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"六亲": matched}


def analyse_female_prediction(context: ChartContext) -> dict:
    matched = []
    for rule in female_prediction_论女命:
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论女命": matched}


def analyse_children_prediction(context: ChartContext) -> dict:
    matched = []
    for rule in children_predictions_论小儿:
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论小儿": matched}


def analyse_juan_liu_patterns(context: ChartContext) -> dict:
    matched = []
    for rule in special_patterns_卷六:
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"特殊格局": matched}


def analyse_volume4_stems_prediction(context: ChartContext) -> dict:
    matched = []
    for rule in volume_4_stems_prediction:
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论日干格局": matched}


def analyse_volume4_month_day_stem(context: ChartContext) -> dict:
    matched = []
    for rule in volume_4_month_day_stem_prediction:
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论月支日干吉凶": matched}


def analyse_volume4_elements_combo(context: ChartContext) -> dict:
    matched = []
    for rule in volume_4_elements_combo_prediction:
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论五行组合": matched}


def analyse_volume2_tian_gan(context: ChartContext) -> dict:
    matched = []
    for rule in volume_2_tian_gan_predictions:
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论天干": matched}


def analyse_volume2_di_zhi(context: ChartContext) -> dict:
    matched = []
    for rule in volume_2_di_zhi_prediction:
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论地支": matched}


def analyse_volume2_di_zhi_geography(context: ChartContext) -> dict:
    matched = []
    for rule in volume_2_di_zhi_geography_predictions:
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论地支地理": matched}


def analyse_volume2_nian_yue_ri_shi(context: ChartContext) -> dict:
    matched = []
    for rule in volume_2_nian_yue_ri_shi_predictions:
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论年月日时": matched}


def analyse_volume2_shi_gan_he(context: ChartContext) -> dict:
    matched = []
    for rule in volume_2_shi_gan_he_predictions:
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论十干合": matched}


def analyse_volume2_jin_jiao_tui_fu(context: ChartContext) -> dict:
    matched = []
    for rule in volume_2_jin_jiao_tui_fu_predictions:
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论进交退伏": matched}


def analyse_volume2_hua_qi(context: ChartContext) -> dict:
    """
    Evaluates 论十干化气 prediction rules from 三命通会·卷二.

    Groups A/C/D encode their 化气格 prerequisite directly in their
    判定逻辑 via the 交互+形态 condition — no function-level gate needed.
    Groups B/E/F/H always evaluate regardless of 化气格 status.
    """
    matched = []
    for rule in volume_2_hua_qi_predictions:
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论化气格局": matched}


def analyse_volume2_zhi_yuan_liu_he(context: ChartContext) -> dict:
    matched = []
    for rule in volume_2_zhi_yuan_liu_he_predictions:
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论支元六合": matched}


def analyse_volume2_san_he(context: ChartContext) -> dict:
    matched = []
    for rule in volume_2_san_he_predictions:
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论支元三合": matched}


def analyse_volume2_jiang_xing_hua_gai(context: ChartContext) -> dict:
    matched = []
    for rule in volume_2_jiang_xing_hua_gai_predictions:
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论将星华盖": matched}


def analyse_volume2_xian_chi(context: ChartContext) -> dict:
    matched = []
    for rule in volume_2_xian_chi_predictions:
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论咸池": matched}


def analyse_volume2_liu_hai(context: ChartContext) -> dict:
    matched = []
    for rule in volume_2_liu_hai_predictions:
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论六害": matched}


def analyse_volume2_san_xing(context: ChartContext) -> dict:
    matched = []
    for rule in volume_2_san_xing_predictions:
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论三刑": matched}


def analyse_volume2_chong_ji(context: ChartContext) -> dict:
    matched = []
    for rule in volume_2_chong_ji_predictions:
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论冲击": matched}


def analyse_volume2_liu_shi_jiazi(context: ChartContext) -> dict:
    matched = []
    for rule in volume_1_liu_shi_jiazi_predictions:
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"释六十甲子": matched}


def analyse_volume1_nayin_ge_ju(context: ChartContext) -> dict:
    matched = []
    for rule in volume_1_nayin_ge_ju_predictions:
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"纳音格局": matched}


def analyse_volume3_lu_shen(context: ChartContext) -> dict:
    matched = []
    for rule in volume_3_lu_shen_prediction:
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论禄神": matched}


def analyse_volume5_guan_sha(context: ChartContext) -> dict:
    matched = []
    for rule in volume_5_rules:
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论官煞格局": matched}


def analyse_key_rules(context: ChartContext) -> dict:
    matched = []
    for rule in key_rules_predictions:
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"关键规则": matched}


def analyse_volume3_horse_fortune(context: ChartContext) -> dict:
    matched = []
    for rule in volume_3_horse_fortune_predictions:
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论禄马": matched}


def analyse_volume3_tian_yi_gui_ren(context: ChartContext) -> dict:
    matched = []
    for rule in volume_3_noble_star_predictions:
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论天乙贵人": matched}


def analyse_volume3_san_qi(context: ChartContext) -> dict:
    matched = []
    for rule in volume_3_3_wonders_predictions:
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论三奇": matched}


def analyse_volume3_tian_yue_de(context: ChartContext) -> dict:
    matched = []
    for rule in volume_3_heavenly_monthly_virtues_predictions:
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论天月德": matched}


def analyse_volume3_tai_ji_noble(context: ChartContext) -> dict:
    matched = []
    for rule in volume_3_tai_ji_noble_predictions:
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论太极贵人": matched}


def analyse_volume3_academy(context: ChartContext) -> dict:
    matched = []
    for rule in volume_3_academy_predictions:
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论学堂词馆": matched}


def analyse_volume3_direct_resource(context: ChartContext) -> dict:
    matched = []
    for rule in volume_3_direct_resource_predictions:
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论正印": matched}


def analyse_volume3_noble_virtue_and_elegance(context: ChartContext) -> dict:
    matched = []
    for rule in volume_3_noble_virtue_and_elegance_predictions:
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论德秀贵人": matched}


def analyse_volume3_empty_void(context: ChartContext) -> dict:
    matched = []
    for rule in volume_3_empty_void_predictions:
        if rule.get("requires_dynamic"):
            continue
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论空亡": matched}


def analyse_volume3_horse_star(context: ChartContext) -> dict:
    matched = []
    for rule in volume_3_horse_star_predictions:
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论驿马": matched}


def analyse_volume3_plundering_star(context: ChartContext) -> dict:
    matched = []
    for rule in volume_3_plundering_star_predictions:
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论劫煞亡神": matched}


def analyse_volume3_sheep_blade(context: ChartContext) -> dict:
    matched = []
    for rule in volume_3_sheep_blade_predictions:
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论羊刃": matched}


def analyse_volume3_seperation_and_discord_star(context: ChartContext) -> dict:
    matched = []
    for rule in volume_3_seperation_and_discord_star_predictions:
        if rule.get("requires_dynamic"):
            continue
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论元辰": matched}


def analyse_volume3_hidden_gold(context: ChartContext) -> dict:
    matched = []
    for rule in volume_3_hidden_gold_predictions:
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论暗金的煞": matched}


def analyse_volume3_calamity_star(context: ChartContext) -> dict:
    matched = []
    for rule in volume_3_calamity_star_predictions:
        if rule.get("requires_dynamic"):
            continue
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论灾煞": matched}


def analyse_volume3_six_adversities(context: ChartContext) -> dict:
    matched = []
    for rule in volume_3_six_adversities_predictions:
        if rule.get("requires_dynamic"):
            continue
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论六厄": matched}


def analyse_volume3_hook_twist(context: ChartContext) -> dict:
    matched = []
    for rule in volume_3_hook_twist_predictions:
        if rule.get("requires_dynamic"):
            continue
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论勾绞": matched}


def analyse_volume3_ten_great_failures(context: ChartContext) -> dict:
    matched = []
    for rule in volume_3_ten_great_failures_predictions:
        if rule.get("requires_dynamic"):
            continue
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论十恶大败": matched}


def analyse_volume3_heavenly_earthly_net(context: ChartContext) -> dict:
    matched = []
    for rule in volume_3_heavenly_earthly_net_predictions:
        if rule.get("requires_dynamic"):
            continue
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论天罗地网": matched}


def analyse_volume3_lonely_widow_star(context: ChartContext) -> dict:
    matched = []
    for rule in volume_3_lonely_widow_star_predictions:
        if rule.get("requires_dynamic"):
            continue
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论孤辰寡宿": matched}


def analyse_volume3_zi_yi_sha(context: ChartContext) -> dict:
    matched = []
    for rule in volume_3_zi_yi_sha_predictions:
        if rule.get("requires_dynamic"):
            continue
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论自缢煞": matched}


def analyse_volume3_gua_jian_sha(context: ChartContext) -> dict:
    matched = []
    for rule in volume_3_gua_jian_sha_predictions:
        if rule.get("requires_dynamic"):
            continue
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论挂剑煞": matched}


def analyse_volume3_tian_huo_sha(context: ChartContext) -> dict:
    matched = []
    for rule in volume_3_tian_huo_sha_predictions:
        if rule.get("requires_dynamic"):
            continue
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论天火煞": matched}


def analyse_volume3_po_sha(context: ChartContext) -> dict:
    matched = []
    for rule in volume_3_po_sha_predictions:
        if rule.get("requires_dynamic"):
            continue
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论破煞": matched}


def analyse_volume3_shui_ni_sha(context: ChartContext) -> dict:
    matched = []
    for rule in volume_3_shui_ni_sha_predictions:
        if rule.get("requires_dynamic"):
            continue
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论水溺煞": matched}


def analyse_volume3_yin_yang_sha(context: ChartContext) -> dict:
    matched = []
    for rule in volume_3_yin_yang_sha_predictions:
        if rule.get("requires_dynamic"):
            continue
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论阴阳煞": matched}


def analyse_volume3_yin_yang_cha_cuo(context: ChartContext) -> dict:
    matched = []
    for rule in volume_3_yin_yang_cha_cuo_predictions:
        if rule.get("requires_dynamic"):
            continue
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论阴阳差错": matched}


def analyse_volume3_ba_zhuan_jiu_chou(context: ChartContext) -> dict:
    matched = []
    for rule in volume_3_ba_zhuan_jiu_chou_predictions:
        if rule.get("requires_dynamic"):
            continue
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论八专九丑": matched}


def analyse_volume3_gu_luan(context: ChartContext) -> dict:
    matched = []
    for rule in volume_3_gu_luan_predictions:
        if rule.get("requires_dynamic"):
            continue
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论孤鸾寡鹊": matched}


def analyse_volume3_bing_fu(context: ChartContext) -> dict:
    matched = []
    for rule in volume_3_bing_fu_predictions:
        if rule.get("requires_dynamic"):
            continue
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论病符": matched}


def analyse_volume3_sang_men_diao_ke(context: ChartContext) -> dict:
    matched = []
    for rule in volume_3_sang_men_diao_ke_predictions:
        if rule.get("requires_dynamic"):
            continue
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论丧门吊客": matched}


def analyse_volume3_tao_hua(context: ChartContext) -> dict:
    matched = []
    for rule in volume_3_tao_hua_predictions:
        if rule.get("requires_dynamic"):
            continue
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论桃花": matched}


def analyse_volume3_hong_yan(context: ChartContext) -> dict:
    matched = []
    for rule in volume_3_hong_yan_predictions:
        if rule.get("requires_dynamic"):
            continue
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论红艳": matched}


def analyse_volume3_tian_tu_sha(context: ChartContext) -> dict:
    matched = []
    for rule in volume_3_tian_tu_sha_predictions:
        if rule.get("requires_dynamic"):
            continue
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论天屠煞": matched}


def analyse_volume3_jian_feng_sha(context: ChartContext) -> dict:
    matched = []
    for rule in volume_3_jian_feng_sha_predictions:
        if rule.get("requires_dynamic"):
            continue
        ok, evidence = evaluate_rule(rule, context)
        if ok:
            matched.append(_format_rule_match(rule, evidence))
    return {"论剑锋煞": matched}


# def analyse_volume3_guan_fu_sha(context: ChartContext) -> dict:
#     matched = []
#     for rule in volume_3_guan_fu_sha_predictions:
#         if rule.get("requires_dynamic"):
#             continue
#         ok, evidence = evaluate_rule(rule, context)
#         if ok:
#             matched.append(_format_rule_match(rule, evidence))
#     return {"论官符煞": matched}


# def analyse_volume3_si_fu_sha(context: ChartContext) -> dict:
#     matched = []
#     for rule in volume_3_si_fu_sha_predictions:
#         if rule.get("requires_dynamic"):
#             continue
#         ok, evidence = evaluate_rule(rule, context)
#         if ok:
#             matched.append(_format_rule_match(rule, evidence))
#     return {"论死符煞": matched}


# def analyse_volume3_zhai_mu_sha(context: ChartContext) -> dict:
#     matched = []
#     for rule in volume_3_zhai_mu_sha_predictions:
#         if rule.get("requires_dynamic"):
#             continue
#         ok, evidence = evaluate_rule(rule, context)
#         if ok:
#             matched.append(_format_rule_match(rule, evidence))
#     return {"论宅墓煞": matched}


# def analyse_volume3_lei_ting_sha(context: ChartContext) -> dict:
#     matched = []
#     for rule in volume_3_lei_ting_sha_predictions:
#         if rule.get("requires_dynamic"):
#             continue
#         ok, evidence = evaluate_rule(rule, context)
#         if ok:
#             matched.append(_format_rule_match(rule, evidence))
#     return {"论雷霆煞": matched}


# def analyse_volume3_ri_xing_sha(context: ChartContext) -> dict:
#     matched = []
#     for rule in volume_3_ri_xing_sha_predictions:
#         if rule.get("requires_dynamic"):
#             continue
#         ok, evidence = evaluate_rule(rule, context)
#         if ok:
#             matched.append(_format_rule_match(rule, evidence))
#     return {"论日刑煞": matched}


# def analyse_volume3_liu_xue_sha(context: ChartContext) -> dict:
#     matched = []
#     for rule in volume_3_liu_xue_sha_predictions:
#         if rule.get("requires_dynamic"):
#             continue
#         ok, evidence = evaluate_rule(rule, context)
#         if ok:
#             matched.append(_format_rule_match(rule, evidence))
#     return {"论流血煞": matched}


# def analyse_volume3_ji_feng_sha(context: ChartContext) -> dict:
#     matched = []
#     for rule in volume_3_ji_feng_sha_predictions:
#         if rule.get("requires_dynamic"):
#             continue
#         ok, evidence = evaluate_rule(rule, context)
#         if ok:
#             matched.append(_format_rule_match(rule, evidence))
#     return {"论戟锋煞": matched}


# def analyse_volume3_fu_chen_sha(context: ChartContext) -> dict:
#     matched = []
#     for rule in volume_3_fu_chen_sha_predictions:
#         if rule.get("requires_dynamic"):
#             continue
#         ok, evidence = evaluate_rule(rule, context)
#         if ok:
#             matched.append(_format_rule_match(rule, evidence))
#     return {"论浮沉煞": matched}


# def analyse_volume3_tun_xian_sha(context: ChartContext) -> dict:
#     matched = []
#     for rule in volume_3_tun_xian_sha_predictions:
#         if rule.get("requires_dynamic"):
#             continue
#         ok, evidence = evaluate_rule(rule, context)
#         if ok:
#             matched.append(_format_rule_match(rule, evidence))
#     return {"论吞陷煞": matched}


ANALYZERS: list[Callable[[ChartContext], dict]] = [
    analyse_volume3_lu_shen,
    analyse_volume3_horse_star,
    analyse_volume3_horse_fortune,
    analyse_volume3_tian_yi_gui_ren,
    analyse_volume3_san_qi,
    analyse_volume3_tian_yue_de,
    analyse_volume3_tai_ji_noble,
    analyse_volume3_academy,
    analyse_volume3_direct_resource,
    analyse_volume3_noble_virtue_and_elegance,
    analyse_volume3_plundering_star,
    analyse_volume3_sheep_blade,
    analyse_volume3_empty_void,
    analyse_volume3_seperation_and_discord_star,
    analyse_volume3_hidden_gold,
    analyse_volume3_calamity_star,
    analyse_volume3_six_adversities,
    analyse_volume3_hook_twist,
    analyse_volume3_ten_great_failures,
    analyse_volume3_heavenly_earthly_net,
    analyse_volume3_lonely_widow_star,
    analyse_volume3_zi_yi_sha,
    analyse_volume3_gua_jian_sha,
    analyse_volume3_tian_huo_sha,
    analyse_volume3_po_sha,
    analyse_volume3_shui_ni_sha,
    analyse_volume3_yin_yang_sha,
    analyse_volume3_yin_yang_cha_cuo,
    analyse_volume3_ba_zhuan_jiu_chou,
    analyse_volume3_gu_luan,
    analyse_volume3_bing_fu,
    analyse_volume3_sang_men_diao_ke,
    analyse_volume3_tao_hua,
    analyse_volume3_hong_yan,
    analyse_volume3_tian_tu_sha,
    analyse_volume3_jian_feng_sha,
    # analyse_volume3_guan_fu_sha,
    # analyse_volume3_si_fu_sha,
    # analyse_volume3_zhai_mu_sha,
    # analyse_volume3_lei_ting_sha,
    # analyse_volume3_ri_xing_sha,
    # analyse_volume3_liu_xue_sha,
    # analyse_volume3_ji_feng_sha,
    # analyse_volume3_fu_chen_sha,
    # analyse_volume3_tun_xian_sha,
    analyse_family_prediction,
    analyse_female_prediction,
    analyse_children_prediction,
    analyse_juan_liu_patterns,
    analyse_volume4_stems_prediction,
    analyse_volume4_month_day_stem,
    analyse_volume4_elements_combo,
    analyse_volume5_guan_sha,
    analyse_volume2_tian_gan,
    analyse_volume2_di_zhi,
    analyse_volume2_di_zhi_geography,
    analyse_volume2_nian_yue_ri_shi,
    analyse_volume2_shi_gan_he,
    analyse_volume2_jin_jiao_tui_fu,
    analyse_volume2_hua_qi,
    analyse_volume2_zhi_yuan_liu_he,
    analyse_volume2_san_he,
    analyse_volume2_jiang_xing_hua_gai,
    analyse_volume2_xian_chi,
    analyse_volume2_liu_hai,
    analyse_volume2_san_xing,
    analyse_volume2_chong_ji,
    analyse_volume2_liu_shi_jiazi,
    analyse_volume1_nayin_ge_ju,
    analyse_key_rules,
]


# ── Public gateway ────────────────────────────────────────────────────────────


def get_natal_interpretations(natal_chart: dict) -> dict:
    """
    Apply classical BaZi texts to the assembled natal chart.

    Args:
        natal_chart: Assembled chart dict containing 四柱实体, 作用, 五行, 日主, 神煞, 性别.

    Returns:
        {"古籍解读": {"六亲": {"触发规则": [...]}}}
    """
    context = build_chart_context(natal_chart)
    result: dict = {}
    for analyzer in ANALYZERS:
        result.update(analyzer(context))
    return {"古籍解读": result}
