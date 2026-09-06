/**
 * TypeScript interfaces for BaZi cycles data (大运 / 流年).
 *
 * Mirrors the Python schema returned by FastAPI POST /v1/chart/cycles. All
 * calculation output is under the 'data' key with Chinese-keyed structures —
 * keys are preserved verbatim (project rule: no camelCase transform).
 *
 * Caching note: cycles depend on the exact birth instant (起运 timing), which
 * chart_key deliberately excludes — never cache cycle data under chartKey.
 * Cache (if at all) per profileId + daYunIndex.
 */

/** Cycle pillar heavenly stem — mirrors natal, plus raw ten-god label. */
export interface CycleHeavenlyStem {
  天干: string;
  阴阳: string;
  五行: string;
  /** RAW ten god — cycle pillars never relabel 七杀→偏官 / 食神→伤官. */
  十神: string;
  /** 5-branch rooting: 4 natal branches + the cycle branch itself. */
  根基强度: string;
  通根于: string;
}

export interface CycleEarthlyBranch {
  地支: string;
  阴阳: string;
  五行: string;
}

export interface CycleHiddenStemTier {
  天干: string;
  阴阳: string;
  五行: string;
  十神: string;
}

/** Void block (see backend cycle_pillars docstring). */
export interface CycleVoid {
  /** The cycle pillar's own 旬空 pair (e.g. "午未"). */
  本柱旬空: string;
  /** 岁运临空亡 — 填实 annotation when the cycle branch sits in the natal 日柱 void pair, else "无". */
  落入命局空亡: string;
  /** Natal branches inside the cycle's own 旬空 — data only, or "无". */
  命局逢运空: string[] | string;
  /**
   * 流年 ONLY (absent on a 大运): the two transiting pillars each carry their own 旬, so
   * each can fall into the other's void — 「运逢流年空亡」. Data only, never a downgrade
   * driver: only the natal 日柱-anchored void has force. Always present on a 流年, "无"
   * when there is no overlap.
   */
  岁运互空?: string[] | string;
}

export interface CycleSeasonalState {
  天干: string;
  地支本气: string;
}

/** The 运柱 block — mirrors the natal 四柱实体 per-pillar shape. */
export interface CyclePillar {
  天干: CycleHeavenlyStem;
  地支: CycleEarthlyBranch;
  藏干: {
    本气?: CycleHiddenStemTier;
    中气?: CycleHiddenStemTier;
    余气?: CycleHiddenStemTier;
  };
  十二长生: {
    日干: string | null;
    自坐: string | null;
  };
  纳音: string;
  空亡: CycleVoid;
  季节状态: CycleSeasonalState;
  /**
   * 制化 annotation for an incoming 七杀 (食神制杀 / 印化杀) or 食神 (枭夺) — present only
   * when applicable. On a 流年 this also sees the enclosing 大运's stem: a 大运 食神 tames
   * a 流年 七杀 exactly as a natal one would, and the text names its source ("命局…" vs
   * "大运…"). A tamed 七杀 is an authority asset; an unrestrained one is danger — so the
   * distinction is load-bearing, not cosmetic.
   */
  制化?: string;
}

/** One cycle-vs-natal interaction item — same schema family as natal 柱位动态. */
export interface CycleInteraction {
  类型: string;
  /** Cycle side keyed by "大运"/"流年", natal side by pillar name. */
  组合明细: Record<string, string>;
  强度: string;
  /** Constant "紧贴" — a transiting pillar acts directly on every natal pillar. */
  距离: string;
  形态?: string;
  元素?: string;
  方位?: string;
  子类型?: string;
  备注?: string;
  主动方?: string;
  根基?: Record<string, string>;
  缺失支?: string;
  开库详情?: {
    库: string;
    柱: string;
    透出藏干: string;
    十神: string;
  };
  藏干详情?: {
    藏干: string;
    藏干层: string;
    藏干十神: string;
    合化五行: string;
  };
  引动藏干?: string;
  旬空涉及?: string[];
  日柱特殊?: boolean;
  涉及月柱?: boolean;
}

export interface CycleInteractions {
  关系总览: string[];
  柱位动态: CycleInteraction[];
}

export interface CycleShenShaEntry {
  名称: string;
  来源: string;
  解读: string;
  细节?: string;
  组合明细?: string[];
}

export interface CycleShenSha {
  年系: CycleShenShaEntry[];
  月系: CycleShenShaEntry[];
  日系: CycleShenShaEntry[];
  杂项: CycleShenShaEntry[];
}

export interface CycleWuXingDmAxis {
  关系: string;
  方向: string;
}

/** One element's period verdict: combined state, anchors, graded movement, domain, and 用神 tag. */
export interface CycleFiveElementState {
  /** Combined-period state (月令-capped classical): 旺 | 相 | 休 | 囚 | 死. */
  状态: string;
  /** Natal (birth-chart) state — a stable anchor (same vocabulary). */
  本命: string;
  /** 流年 only: the enclosing 大运's state, giving the natal → decade → year progression. */
  运基?: string;
  /** Graded movement on the pre-cap 力量 (not the capped 状态): 大升 | 升 | 持平 | 降 | 大降. */
  变化: string;
  /** The element's ten-god category for the day master (life-domain): 财星|官杀|印星|食伤|比劫. */
  十神: string;
  /** Chart-fixed 用神 verdict (调候 + 扶抑): 喜 | 忌 | 平. */
  喜忌: string;
  /**
   * Chart-fixed 五神 role — mirrors 用神.五行[el].角色. Distinguishes a 仇神 (idle but feeding
   * a 忌) from a true 闲神, which 喜忌 alone cannot: both read 平.
   */
  角色: YongShenRole;
  /** One-line reading fusing 用神 × movement × domain (LLM-facing guidance). */
  解读: string;
}

/** The 五神 role an element plays. See YongShen.仇 for the 仇神 rule. */
export type YongShenRole = "喜用神" | "忌神" | "仇神" | "闲神";

/** Per-element 用神 breakdown (see YongShen). */
export interface YongShenElement {
  十神: string;
  /** 扶抑 stance from day-master strength: 喜 | 忌 | 平. */
  扶抑: string;
  /** Whether this element is a 调候用神 (climate need). */
  调候: boolean;
  /** Combined verdict: 喜 | 忌 | 平. */
  综合: string;
  /**
   * The 五神 ROLE — a separate axis from 综合, not a restatement of it. 仇神 and 闲神 are
   * BOTH 综合 === "平", so a 仇神 never moves 运势.评级; only 综合 does.
   */
  角色: YongShenRole;
  备注: string;
}

/**
 * 格局 — the chart's STRUCTURE, which decides where 喜忌 come from at all.
 *
 * 正格 → 调候 + 扶抑 (the ordinary path). 从格/专旺格/化气格 → the structure dictates 喜忌
 * and 调候 is NOT applied: a surrendered day master follows its dominant force, so 印比
 * (which 扶抑 would call 喜 for a weak DM) are in fact 忌 — they 破格. Same 强弱, inverted
 * verdict. Note 强弱 ≠ 格局: 极弱 does NOT imply 从格.
 */
export interface GeJuDetail {
  格局: "正格" | "从财格" | "从杀格" | "从儿格" | "从势格" | "专旺格" | "化气格";
  /** Display name — 专旺格 resolves to 曲直/炎上/稼穑/从革/润下格; 化气格 to 化X格. */
  名称: string;
  /** null for 正格. 假从 keeps the 从格 direction but is fragile (破格-prone). */
  真假: "真从" | "假从" | "真化" | null;
  /** Ten-god category the chart follows (null for 正格/化气格). */
  主导: string | null;
  /** 化气格 only — the transformed element. */
  化神: string | null;
  /**
   * 化气格 only — what the day master USED to be. Load-bearing: 日主复根 (regaining a root
   * in this element) is one of the two ways a 化气格 shatters, and the cycle layer keys its
   * 破格 override on it.
   */
  原五行?: string;
  /**
   * Ten-god CATEGORIES (财星/食伤/官杀/印星/比劫) the structure favours — 从/专旺 only;
   * empty for 正格 and 化气格.
   *
   * NOT the answer to "what does this chart want" — that is `YongShen.喜用`, which holds
   * ELEMENTS (木火土金水). These are named 喜用十神/忌十神 precisely so the two cannot be
   * confused: they are different types in different domains.
   */
  喜用十神: string[];
  忌十神: string[];
  /** 化气格 only — element-keyed (serve the 化神) rather than category-keyed. */
  喜用五行?: string[];
  忌五行?: string[];
  依据: string[];
  /**
   * What would shatter the structure — POSITION matters.
   *
   * 化气格's 日主复根 is 地支-specific: for 辛化水 / 壬化木 the original element is ALSO the
   * 生化神者 (金生水, 水生木), so a floating 天干 genuinely FEEDS the 化神 and rates 喜 — while
   * a BRANCH carrying it re-roots the day master and breaks the 化. Same element, opposite
   * effect, decided purely by 位置. An element-level 忌 cannot express that; this can.
   */
  破格: Array<{
    条件: string;
    五行: string;
    /** "天干或地支" | "地支" — 地支 means only a ROOT triggers it. */
    位置: string;
    说明: string;
  }>;
  /** Advisory, e.g. the 假化 / 假从 instability note. */
  提示: string | null;
}

/**
 * The classical Five Gods, as a view over YongShen's sets (see YongShen.五神).
 * 用神 ∪ 喜神 partitions 喜用; 用神 is "" only when 喜用 is empty (a 中和 chart with no
 * curated 调候 row). 忌神/仇神/闲神 equal YongShen.忌/仇/闲.
 */
export interface WuShen {
  /** The single primary remedy — one element of 喜用, or "" when 喜用 is empty. */
  用神: string;
  /** The rest of 喜用 (supporters of 用神), NOT elements that 生 the 用神. */
  喜神: string[];
  忌神: string[];
  仇神: string[];
  闲神: string[];
}

/** Chart-fixed 用神 (调候用神 + 扶抑用神, or the structure). Same shape on /natal and /cycles. */
export interface YongShen {
  /** Day-master STRENGTH verdict. Previously (mis)named 格局 — they are different things. */
  强弱: "极旺" | "旺" | "中和" | "弱" | "极弱";
  /** The chart's STRUCTURE — decides whether 喜忌 are 扶抑-derived or structure-derived. */
  格局: GeJuDetail["格局"];
  格局详情: GeJuDetail;
  /**
   * The classical 五神 (Five Gods) as an ADDITIVE presentation split of the sets below —
   * NOT a re-derivation. 用神 names which single element of 喜用 leads; 喜神 is the rest of
   * the SAME 喜用 set (its supporters), never "生用神". 忌神/仇神/闲神 mirror 忌/仇/闲 exactly.
   * Read 综合/角色 (in 五行) for the authoritative engine axes; 五神 is human/LLM-facing.
   */
  五神: WuShen;
  /**
   * Is the 调候 (climate) layer IN FORCE? False for 从格/专旺格/化气格, which follow 顺其势 —
   * 调候 is a 正格 concept. The 调候* fields below stay populated as CONTEXT (indexed on the
   * effective day stem, so a 化气格 quotes the 化神's row), but 用神.喜用/忌 ignore them.
   *
   * Load-bearing: a 化火格 legitimately reports 调候忌五行 = ["火"] while 格局 makes 火 the
   * 化神 and 喜用. Do not enforce the 调候 block when this is false.
   */
  调候适用: boolean;
  /** 调候用神 stems (穷通宝鉴/tiaohou), priority order. */
  调候用神: string[];
  调候忌神: string[];
  调候忌五行: string[];
  调候喜五行: string[];
  /** Combined favorable elements (调候 ∪ 扶抑喜). */
  喜用: string[];
  /** Unfavorable elements (扶抑忌). */
  忌: string[];
  /**
   * 仇神 — 生忌神者: an element that is neither 喜用 nor 忌 itself, but GENERATES one the
   * chart fears (金生水 when 水 is 忌 → 金 is 仇). 喜/忌 always win the label, so this is a
   * split of the 平 leftovers, never a fourth verdict.
   *
   * Empty on 弱/旺 正格 charts BY CONSTRUCTION — 扶抑 tags all five elements 喜 or 忌 and
   * nothing is left idle. It fires on 中和 charts (where only 调候 speaks) and 非正格 charts.
   * An empty list is the right answer, not missing data.
   */
  仇: string[];
  /** 闲神 — the genuine idlers: 平, and feeding nothing the chart fears. */
  闲: string[];
  /**
   * Curated favorable 大运/流年 branches (金不换 方位表) — the source of each pillar's
   * 运势 verdict. Empty when the chart is uncurated, in which case 运势 falls back to 五行.
   */
  大运喜: string[];
  /** Curated unfavorable 大运/流年 branches (金不换 方位表). */
  大运忌: string[];
  五行: Record<"木" | "火" | "土" | "金" | "水", YongShenElement>;
  经典: { 原则?: string; 最佳?: string; 次佳?: string; 风险?: string } | null;
}

/**
 * 运势 — the holistic verdict for one 大运/流年, complementary to the per-element
 * 五行动态 breakdown: it answers "is this decade good?" in one call.
 */
export interface YunShi {
  /** 喜运 | 平运 | 忌运. */
  评级: "喜运" | "平运" | "忌运";
  /**
   * Why this rating — names the branch, the rule that fired, and (when the stem moved the
   * verdict) the 盖头/截脚 relationship that let it.
   *
   * A 大运 is a 干支 pair and both act (运以支为重，天干为辅). The branch sets the direction;
   * the stem moves it at most ONE step — but only if it has the power to. A stem the branch
   * 克s (截脚) is cut off at the root and cannot act at all, friendly or hostile; a stem that
   * 克s its own branch (盖头) smothers it.
   */
  依据: string;
  /**
   * "金不换"     — the curated 方位表 (正格 charts only).
   * "用神五行"   — fallback for a 正格 chart the table doesn't cover.
   * "从格用神"   — 从格/专旺格/化气格: the table is 正格-authored and would read backwards,
   *                so the verdict comes off the structure's 用神 instead.
   * "化气破格"   — 化气格 ONLY: the cycle branch re-roots the ORIGINAL day master (日主复根),
   *                so the 化 shatters. Overrides the element verdict — for 辛化水 a 酉/申
   *                decade rates 喜 on elements (金生水) yet is 忌运 in truth.
   */
  来源: "金不换" | "用神五行" | "从格用神" | "化气破格";
  /**
   * 流年 only, and only when a severe 岁运 configuration fires (岁运并临 / 岁运反吟 /
   * 运犯岁君). Deliberately NOT folded into 评级: 评级 measures elemental favourability
   * (what the period gives you), 警示 measures intensity and delivery (how violently it
   * arrives). Orthogonal axes — collapsing them into one score destroys both.
   */
  警示?: string[];
}

/** A named classical 岁运 pattern. */
export interface SuiYunSpecial {
  /** 岁运并临 | 岁运反吟 | 岁运双合 | 岁运相冲 | 运犯岁君 | 岁君伏运 | 天比地比 */
  名称: string;
  /** 重 = a genuine event trigger (surfaces in 运势.警示); 中; 轻. */
  级别: "重" | "中" | "轻";
  说明: string;
}

/**
 * One of the decade's actions on the natal chart, suppressed for THIS year because the
 * 流年 binds the 大运 (合绊 / 贪合忘冲 / 入局).
 *
 * Self-contained by design: 类型 + 组合明细 + both strengths + the causing 岁运 item are all
 * carried here, so a reader never has to join back to the decade entry's 柱位动态. Only items
 * whose 强度 actually moved appear — read 大运态 for the verdict when this list is empty.
 */
export interface DaYunConstraint {
  类型: string;
  组合明细: Record<string, string>;
  原强度: string;
  本年强度: string;
  /** The 岁运 relation that did the binding. */
  起因: { 类型: string; 组合明细: Record<string, string> };
  说明: string;
}

/**
 * 岁运 — the 流年's direct relationship with its enclosing 大运, and what that does to the
 * decade. Present on every 流年 EXCEPT those before 起运 (未行大运 — there is no decade yet).
 *
 * The 合/冲 asymmetry is the rule to hold onto when reading this: 合 binds (the decade is
 * 绊住 and its actions are downgraded — see 大运制约), whereas 冲 merely agitates (受冲: the
 * decade still acts on the 命局, and 大运制约 is empty).
 */
export interface SuiYun {
  /** The 流年-vs-大运 items, restated from 作用.柱位动态 (those with a 大运 key in 组合明细). */
  关系总览: string[];
  特殊组合: SuiYunSpecial[];
  /**
   * 交战  — 岁运并临/反吟: the two transiting pillars are wholly at odds; every decade action is muted.
   * 入局  — the 大运 branch is drawn into a 三合/三会 with the year and forgets its business elsewhere.
   * 被合绊 — 合 binds the decade; it cannot deliver its 冲/克 to the 命局 this year.
   * 受冲  — the year clashes the decade. Agitates, does NOT bind: 大运制约 is empty by design.
   * 常态  — no 岁运 constraint; the decade acts on the 命局 as the decade-level analysis says.
   */
  大运态: "交战" | "入局" | "被合绊" | "受冲" | "常态";
  /** Always present — an empty 大运制约 means "the decade acts normally", never "not computed". */
  大运态说明: string;
  大运制约: DaYunConstraint[];
  /** The 级别 === "重" configurations, flattened. Mirrored onto 运势.警示. */
  警示: string[];
}

export interface CycleWuXing {
  /**
   * Per-element 旺衰 verdict for the period, from re-running the natal classifier
   * with the transiting pillar added as a 5th pillar (season stays natal 月令).
   */
  五行: Record<"木" | "火" | "土" | "金" | "水", CycleFiveElementState>;
  对日主: {
    天干: CycleWuXingDmAxis;
    地支本气: CycleWuXingDmAxis;
    结合日主强弱: string;
  };
  /** Elemental events the cycle sets off, each tagged with the triggered element's period 状态. */
  引动: Array<{
    类型: string;
    元素: string;
    状态: string;
    说明: string;
  }>;
}

export interface TaiSui {
  /** "无" or joined relations e.g. "冲太岁、刑太岁". */
  关系: string;
  说明: string;
}

/**
 * One 流年 (annual pillar) entry.
 *
 * 流年 boundaries are UNIVERSAL — 立春, the same instant for everyone alive — whereas a
 * 大运's are individual (its 起运 anniversary). The two axes never align, so a year near
 * a 交运 is lived partly under each decade and appears in BOTH decades' 流年 lists with
 * 交运年 === true, analysed once against each. See DaYunEntry.
 */
export interface LiuNianEntry {
  年份: number;
  /**
   * 立春 of 年份 — when this 干支 year actually begins. NOT January 1st: picking the
   * "current" 流年 by calendar year is wrong from Jan 1 until ~Feb 4 every year.
   *
   * Same (TST-shifted) frame as every other instant in this response — convert before
   * comparing against a wall-clock `now`.
   */
  起始: string;
  /** 立春 of 年份 + 1, exclusive. */
  结束: string;
  /**
   * This year's 立春 window is not wholly inside the enclosing 大运 — it straddles a
   * 交运, so the year is shared with the neighbouring decade. On the pre-起运 stub the
   * two partial years are cut by the birth instant and by 起运 instead.
   */
  交运年: boolean;
  /** 虚岁 at 起始 — 立春-anchored (1 throughout the 立春-year of birth, +1 each 立春). */
  虚岁: number;
  /** 周岁 at 起始 — completed years lived, birthday-accurate, NOT 年份 − 出生年. */
  周岁: number;
  干支: string;
  生肖: string;
  运柱: CyclePillar;
  /**
   * The year scanned against the four natal pillars AND its enclosing 大运 (a 1×5 scan).
   * 岁运 items are the ones whose 组合明细 carries a "大运" key — including frames the two
   * transiting pillars complete together with a natal branch (大运申 + 流年子 + 日柱辰 →
   * 三合水局). See 岁运 below for the classical reading of them.
   */
  作用: CycleInteractions;
  神煞: CycleShenSha;
  /** Headline 喜运/平运/忌运 for the year — read alongside the 五行动态 detail. */
  运势: YunShi;
  五行动态: CycleWuXing;
  太岁: TaiSui;
  /** Absent only on the pre-起运 years (未行大运 — no decade to relate to yet). */
  岁运?: SuiYun;
  /** Reserved seam — always present, empty until the monthly layer ships. */
  流月: unknown[];
}

/**
 * One 大运 (decade) entry. Index 0 is the pre-运 stub (干支 === "").
 *
 * A decade's boundaries are INDIVIDUAL: it begins at the 起运 instant and every 10 years
 * on that anniversary (交运), with no relation to 立春 or to the calendar. Decades are
 * exactly contiguous — 结束 === the next entry's 起始, and 结束虚岁 === its 开始虚岁.
 *
 * There is deliberately no 开始年份/结束年份: a decade running Nov 1991 → Nov 2001 has no
 * honest year-pair label. Use 起始/结束 for boundaries and 周期 for a display label.
 */
export interface DaYunEntry {
  序号: number;
  干支: string;
  /** 交运 instant — 起运 + (序号 − 1) × 10 years. On the stub, the birth instant. */
  起始: string;
  /** The next 交运, exclusive. On the stub, 起运. */
  结束: string;
  /** 虚岁 at 起始 (立春-anchored). */
  开始虚岁: number;
  /** 虚岁 at 结束 — equals the next decade's 开始虚岁. */
  结束虚岁: number;
  /** 周岁 at 起始 — completed years lived, birthday-accurate. */
  开始周岁: number;
  /** 周岁 at 结束 — equals the next decade's 开始周岁. */
  结束周岁: number;
  /** Display label, 虚岁 endpoint-to-endpoint, e.g. "7-17岁". */
  周期: string;
  /** Present only on the index-0 pre-运 stub ("未行大运"). */
  阶段?: string;
  运柱?: CyclePillar;
  作用?: CycleInteractions;
  神煞?: CycleShenSha;
  /** Headline 喜运/平运/忌运 for the decade. Absent on the index-0 pre-运 stub. */
  运势?: YunShi;
  五行动态?: CycleWuXing;
  /**
   * Populated only for the decade requested via da_yun_index.
   *
   * Normally ELEVEN entries, not ten: 交运 falls mid-立春-year at both ends, so the first
   * and last are partial (交运年 === true) and are also carried by the neighbouring
   * decade. Only a 起运 landing exactly on 立春 yields a clean ten.
   */
  流年: LiuNianEntry[];
}

export interface QiYun {
  顺逆: string;
  起运阳历: string;
  起运计岁: string;
  性别: string;
}

/** The `data` object of POST /v1/chart/cycles. */
export interface CyclesData {
  起运: QiYun;
  /** Chart-fixed 用神 anchor that each pillar's 五行动态.喜忌 references. */
  用神: YongShen;
  大运: DaYunEntry[];
}
