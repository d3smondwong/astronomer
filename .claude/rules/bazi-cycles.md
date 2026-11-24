---
paths:
  - "apps/backend/astronomer_logic/cycles/**"
  - "apps/backend/orchestrator/cycles_orchestrator.py"
  - "apps/backend/data/climate_data.py"
  - "apps/backend/data_models/cycles.py"
  - "apps/backend/tests/test_cycles.py"
  - "apps/backend/tests/test_cycle_interpretation.py"
  - "apps/backend/data/san_ming_tong_hui*.py"
  - "apps/web/types/cyclesChart.ts"
  - "apps/web/app/api/cycles/**"
---

# 大运 / 流年 / 岁运 rules

Natal-side rules (格局, 用神, 五神, 七杀→偏官) are in `bazi-natal.md`; the response shape is in
`api-contract.md`.

**Cycle-pillar ten gods are RAW:** 大运/流年 pillar ten gods (`apps/backend/astronomer_logic/cycles/cycle_pillars.py`) are pure `LunarUtil.SHI_SHEN` lookups — the natal 七杀→偏官 / 食神→伤官 relabeling is adjacency-based and adjacency is undefined for a transiting pillar. Rules matching cycle-pillar gods use `["正官", "七杀"]` WITHOUT `"偏官"`; natal-side matching still requires `"偏官"`. When taming gods are revealed in the natal chart, the cycle pillar carries a `制化` annotation instead of a relabel.

**Cycle interaction engine is separate but shares definitions:** `cycles/cycle_interactions.py` runs a 1×N scan (one transiting pillar vs its opponents) — `natal_interactions.py` is hard-wired to exactly 4 pillars and must not be extended. All relation maps, `PRIORITY_RULE_TABLE`, and strength tables are imported from `natal_interactions.py`; never redefine what counts as a 冲/合/刑. Every pairing uses the constant `距离: "紧贴"` (no distance decay).

**岁运 — a 大运 is scanned 1×4, a 流年 1×5:** a decade exists independently of any year inside it, so the 大运 meets only the 4 natal pillars. A 流年 meets the natal pillars **plus its enclosing 大运** (`CompanionPillar`, opponent index 4) — classically the year meets its decade FIRST, and only what survives reaches the 命局. 岁运 items are those whose `组合明细` carries a `"大运"` key. Opponent index 4 is NOT a natal pillar: the `日柱特殊`/`涉及月柱` salience flags, the 日主贪合 remark, and the 日柱-anchored void pass all stay gated on indices 0-3 (`_NATAL_COUNT`) — a transiting branch has no slot in the natal 旬 to be absent from. The 1×5 scan is what makes cross-frames visible (大运申 + 流年子 + 日柱辰 → 三合水局); no 1×1 side-scan could see them, which is why there is no second engine.

**The companion reaches every cycle layer — but 神煞 anchors are the hard boundary.** A 流年's `CompanionPillar` (defined in `cycles/cycle_pillars.py`) feeds four layers: the 1×5 interaction scan, the 制化 annotation, 岁运互空, and the set-completion 神煞. Two of these were *wrong answers* before, not merely missing ones:
- **制化** (`_zhi_hua_annotation`) read only natal revealed stems, so a 流年 七杀 arriving while the **大运 carries 食神** reported 「命局无明显制化，岁运七杀直临」 — an unrestrained killing. 食神制杀 works from the 大运 stem too (it is revealed and present for ten years). A tamed 七杀 is an authority asset; an unrestrained one is danger — the verdict inverts.
- **天火煞** (`cycle_shen_sha.py`) is voided by water, but the evaluator could not see the 大运, so a 流年 completing 寅午戌 inside a **癸亥** decade fired anyway. A false positive.

**神煞 splits into ANCHOR stars and SET stars, and only SET stars see the 大运.** Anchor stars (年支/月支/日支/日干/年干/纳音 → 驿马, 桃花, 天乙贵人, 羊刃, 元辰 …) derive from **birth facts**; the 大运 is itself a guest and must NEVER become an anchor, or we invent 神煞 no classical text recognises. Set stars (天罗, 地网, 自缢煞, 破煞, 挂剑煞, 天火煞, 德秀贵人's 秀 pair) ask whether a group is *present together*, and 岁运命 are all present at once — so they draw on natal + 大运 + guest, exactly like the interaction engine's cross-frames. **三奇 is excluded despite being a combination star**: it needs three stems in *consecutive* pillars, and a 大运/流年 pair has no sequence position (same documented parity gap as 共拱/拱会).

**通根 and 空亡 stay narrow, deliberately.** A 流年 stem does NOT root into the 大运's branch (原局 + 自坐 only) — 通根 describes the chart a stem *stands on*, and rooting into a transient neighbour would make the same year's stem strength swing decade to decade. 岁运互空 is reported but **never downgrades**, preserving the standing rule that only the natal 日柱-anchored void has force.

**合 binds, 冲 agitates — the 岁运 rule that is easiest to get backwards.** `cycles/sui_yun.py` re-resolves the decade's `柱位动态` under the year's 岁运 locks, because the 大运's actions are computed ONCE per decade but a 大运 bound by the 流年 does not deliver its 冲 to the 命局 *that year* (贪合忘冲). **合/三合/伏吟/反吟 downgrade the decade's actions; 六冲 downgrades NOTHING** — 岁冲运 destabilises the decade (`大运态: 受冲`) but does not tie it down, and reading 冲 as suppression would silence exactly the years the classics call the loudest. Each lock behaves exactly as the same lock behaves inside the engine's own passes (`PRIMARY_六合` → branch layer, `STEM_天干合` → stem layer, `STRUCTURAL_三合/三会` → branch+pillar, 交战 → everything). Output is a **compact delta** (`大运制约`) — only items whose 强度 moved, each self-contained so no join back to the decade entry is needed — plus an always-present `大运态` verdict, so an empty delta reads as "the decade acts normally", never "not computed". The re-resolved dynamics (not the raw ones) feed the year's 五行动态, or the two layers would disagree about whether the 大运 acted. Severity surfaces as `运势.警示`, never as a change to `评级`: 评级 is elemental favourability, 警示 is intensity/delivery — orthogonal axes.

**运势 (per-decade / per-year verdict):** the holistic 喜运/平运/忌运 headline the per-element `五行动态` breakdown cannot give (five elements each move their own way). Sourced from the hand-curated `大运喜`/`大运忌` branch table in `data/climate_data.py` (金不换), keyed `日干+月支` — 运支 ∈ 大运喜 → 喜运, ∈ 大运忌 → 忌运, else 平运. These branch lists are **curated, not derived**: mechanically expanding 喜用 五行 to branches would flag ~7 of 12 branches favorable and say nothing. For the handful of charts with no curated table, the verdict degrades to the branch's 本气 五行 read against the chart's 用神, and reports `来源: "用神五行"` so callers can tell the two apart. Invariant (locked by tests): every 大运喜/大运忌 list holds only pure branch chars, and no branch appears in both.

**The 方位表 is 正格-authored — 非正格 charts bypass it entirely.** It assumes the day master stands and must be balanced, so for a 从格/专旺格/化气格 its directions are not merely unhelpful but *backwards*. `get_cycle_yun_shi` therefore skips it whenever `格局 != 正格` and reads the structure-derived 用神 instead (`来源: "从格用神"`). This is the general form of a real bug: 癸午's source clause (`喜从火财 忌申(无根夭)`) is **从格-conditional, not a 方位 judgment**, and encoding its `忌申` rated 庚金 — the very element 癸午's 经典 calls 必须庚辛为生身之本 — as 忌运 for ordinary charts. Both `大运喜`/`大运忌` there are deliberately empty; do not "restore" them from the raw source string.

**大运 and 流年 are TWO INDEPENDENT TIME AXES — never align one to the other.** A 大运 boundary is **individual**: the 起运 instant, then every 10 years on that anniversary (交运). A 流年 boundary is **universal**: 立春, the same instant for everyone alive. Nothing synchronises them, so a year straddling a 交运 is lived partly under each decade and **appears in BOTH decades' `流年` lists** with `交运年: true` — analysed once per decade against that decade's companion, which is the classical "read the 交运 year against both decades" for free. A decade therefore normally carries **11 流年, not 10**; only a 起运 landing exactly on 立春 gives a clean ten.

This is why `DaYun.getLiuNian()` is **not** used: it groups years by calendar year counted off the decade's start year (1991-2000 for a decade actually running Nov 1991 → Nov 2001), silently snapping the individual axis onto the universal one. `cycles_orchestrator._overlapping_liu_nian_years` enumerates them instead. For the same reason a 大运 has no `开始年份`/`结束年份` — a Nov→Nov decade has no honest year-pair label; `起始`/`结束` carry the boundaries and `周期` is the display string.

**Ages are ENDPOINT ages, and 虚岁 is 立春-anchored.** `开始虚岁`/`结束虚岁` are read at the period's own two boundaries, so a decade's `结束虚岁` equals the next decade's `开始虚岁` exactly as their instants coincide (7→17, 17→27 — not lunar-python's 7-16, a calendar-year artifact). `虚岁` counts 1 throughout the **立春-year** of birth and +1 at every 立春; lunar-python's `year - 出生年 + 1` (`DaYun.getStartAge`, inherited by `LiuNian.getAge`) agrees for anyone born after 立春 but is off by one **for life** for a January-born subject, whose birth 立春-year is the previous solar year. `周岁` is completed years lived, birthday-accurate — at 立春 2021 a subject born 1985-11-25 is **35** (虚岁 37), not the 36 that `年份 - 出生年` reports. Both ages are read at `max(period start, birth)`, so the birth year reports 虚 1 / 周 0 rather than a negative age.

**All instants share the chart's (TST-shifted) frame** — the birth instant, `起运阳历`, every 节气 lunar-python reports, and every `起始`/`结束`. Callers comparing against a wall-clock `now` must convert first; never mix frames.

## 小运 — the personal annual pillar, pre-起运 only (for now)

《三命通会·论小运》: 「大运司十年之休咎，小运掌一岁之灾祥…补大运之不足」. **流年 is universal**
(the calendar's year pillar, the same for everyone); **小运 is personal** — the **hour pillar**
stepped one 干支 per 虚岁 (醉醒子's method, which the text endorses: 「尝试用之，屡验」), forward or
backward by the same 阳男阴女 rule as the 大运. 大运 steps the month pillar per decade, 小运 the hour
pillar per year.
- **Computed in `cycles_orchestrator._xiao_yun_gan_zhi`, NOT `DaYun.getXiaoYun()`**: lunar-python
  ages by `year - 出生年 + 1`, off by one for life for a January-born subject. 小运 steps on this
  module's 立春-anchored 虚岁, so it always matches the 流年 entry it sits in.
- **Scope: the pre-起运 stub's 流年 only** (「童限未交大运，专用此法」). The text runs 小运 for life,
  but lifelong 小运 waits for 卷二·论小运's rules that weigh it against the 大运 (「大运虽吉，其小运
  不通，未可便言吉利」) — without them a third annual verdict would contradict 运势.
- **1×4 against the natal chart only.** It never interacts with the 流年 or a 大运: the text weighs
  it against the 大运 as a verdict and runs it beside the 太岁, never 冲/合 between them.
- **卷一's 「限」 rules apply** (限 = 大运 + 小运, see *Encoding decisions*); 小运's own rules come
  from 论小运 and the 神煞 passages that name it (驿马, 天乙, 孤寡, 丧吊, 真鬼).

## Classical cycle rules (`cycles/interpretation_cycle_chart.py` → `古籍解读`)

The cycle counterpart of `interaction_natal_chart.py`. Rules live **next to their chapter's
natal rules**, in separate `*_cycle_predictions` lists (e.g. `san_ming_tong_hui_v1.py` ›
`volume_1_nayin_ge_ju_cycle_predictions`), and are encoded **chapter by chapter**. Same schema as
the natal rules, evaluated by the natal `evaluate_rule` — the engine adds no evaluators of its own.
- **Positions:** `运柱` = the pillar being analysed; `大运` = the enclosing decade (流年 rules
  only); `全局` / `年柱` / `月柱` … still mean the **natal** pillars — `全局` never matches a
  transiting pillar, so a rule must name `运柱` explicitly. The engine runs once per pillar
  (大运 / 流年 / 小运) and `适用周期` picks which runs a rule joins, so one `运柱` rule serves
  several periods. `运柱` is rule vocabulary only: emitted evidence names the period instead
  (`宫位: 小运`, not `宫位: 运柱`).
- **Fields:** `适用周期` and `来源` are required; `依据` (the sentence licensing the cycle reading,
  e.g. 「限运同论」), `标注` (severity) and `编码说明` (how the rule reads an ambiguous or departing
  passage — emitted with the match so the interpretive choice is visible) are optional.
- **What a rule can see.** Natal pillars come from `NatalContext.rule_si_zhu` — the natal pipeline's
  七杀→偏官 / 食神→伤官 relabels applied, so a natal 煞 condition picks its label by what the text
  describes (see `bazi-natal.md`: star → both, uncontrolled → `七杀`, controlled → `偏官`)
  (`natal_si_zhu` stays raw for 制化). The 运柱 carries 天干/地支 + 五行, **RAW** ten gods (天干 +
  藏干 tiers — no adjacency, so never relabelled), `十二长生 {日干, 自坐}` and 纳音; its computed
  神煞 and interactions are passed in (`组合明细` key renamed to `运柱`, natal strength floor
  applied). `CYCLE_POSITION_TYPES` / `NATAL_POSITION_TYPES` whitelist what each side may use —
  widening either is a deliberate engine change.
- **Guard tests** (`tests/test_cycle_interpretation.py`): every cycle list is wired into
  `CYCLE_ANALYZERS`; every rule names a cycle position; natal lists gain no cycle positions
  (`PENDING_MIGRATION` holds the 4 legacy rules in 卷五/卷六 and may only shrink); every rule can fire.

**Encoding decisions (confirmed by the user):**
- **限 / 限运 / 限数 → `适用周期: ["大运", "小运"]`** — in 三命通会 限 always names a **运** period:
  大限 (the 大运), 童限 (the 小运 years), 大小运限 (both, set apart from the 太岁: 「太岁凶煞并临大小
  运限」). 小限 never occurs, and the 太岁/流年 is never called a 限 — so 「限」 rules do NOT apply to
  流年. (Revised 2026-11-23; the first reading had been 大运 + 流年.) 运 alone (运规, 运入, 风运) →
  `["大运"]`.
- **运规东南 (己巳) = 巽 = 辰巳 only**; **沈潜之乡 (己未) = 亥子丑** (北方水).
- **A licensing clause reaches only as far as its grammar.** Read where the clause sits, not just
  that it exists: 金泊金's 「此金体薄，不能反源定夭，限运同论」 closes the **fire passage**, so only 平地
  and the fire judgements (有火主夭 / 太阳 / 山下山头清水 / 炉火) get cycle rules; the 水/金/土
  judgements after it stay natal-only. 山下火's 「限数喜忌，**俱**依此断」 is the section's last
  sentence and says 俱, so the whole section extends.
- **Within a licensed passage** the 运柱 supplies the partner 纳音/干支/branch; supporting
  conditions (有木, 有山, 生秋月) stay natal. Rules that are natal-positional (日时见, 月令) are not
  converted; a count can be met by natal + 运柱 together (风多, 无木多逢).
- **No clause, no cycle rule.** A natal verdict in a section with no licensing clause (覆灯火 日时辰巳,
  霹雳火 戊子逢丙寅, 山头火's 山木) is never encoded as a cycle rule.
- **山 is the text's own list** where the text names it (山下火: 癸丑, 乙丑). The natal rules use a
  broader 壬子/癸丑/庚子/辛丑; cycle rules do not inherit it.
- **Encoding departures are documented, not hidden:** a rule whose conditions deviate from the
  literal text carries `编码说明` (e.g. 山下火 「若无火无山」 encoded as 无**木**无山). `标注` stays
  reserved for severity.
- **Severe verdicts (夭, 死) stay verbatim** and carry `标注: "条件触发·非定论"` — never softened.

**卷二 decisions (confirmed 2026-11-23):**
- **Directions:** 东 寅卯辰, 南 巳午未, 西 申酉戌, 北 亥子丑; 东南 = 寅–未, 西北 = 申–丑 (己巳 「在巽」
  stays the 辰巳 special case).
- **A 运's ten god is its BRANCH 本气** (大运重地支). The branch sets the decade's ground and decides the
  verdict; the stem is a secondary modifier read *through* the branch, never a verdict of its own
  (「在干兼用地支之神，在支则弃天干之物」). So 壬午 judges 印 by 午 — 印欲运旺 can fire, but the stem's 财
  never adds the opposite 印不欲运衰. The stem's god stays visible in the entry's `运柱`. The decade is
  read as one unit — no 前五年/后五年 split.
- **论大运's unnamed wants** are encoded as classes, each with its `编码说明`: 煞欲运**制** = 食神 +
  伤官 (食神 primary); 煞不欲运**助** = 财; 财欲运**扶** = 食伤; 财不欲运**劫** = 比劫; 印欲运**旺** =
  官杀 + 印 (官杀 primary); 印不欲运**衰** = 财; 官欲运**生** = 财; 官不欲运**伤** = 伤官.
- **Tamed vs untamed 煞 matters where the text's concern does.** 煞欲运制 matches only an untamed natal
  `七杀` — a tamed `偏官` meeting more 制 is 制伏太过 (总论岁运, phase 2b). 煞不欲运助 matches both.
- **论地支 passages describe each branch as its month** (辰建季春, 午月, 酉建八月) → subject = 月支.
- **Not encoded / deferred:** 原有灾 (「灾」 undefined); the 运元 passages (疏通 / 归宿 / 晦息 unpinned;
  only 沉潜 = 亥子丑 is confirmed); 得气深浅 timing; 「太岁持之」; 日年相并 (verdict depends on social
  standing); 「太岁当头立…重丧」.
- **岁运并临:** 论太岁's ten-god split (「独羊刃、七煞为凶，财、官、印绶亦吉」) is the rule; 喜忌 is only
  its abstraction. `sui_yun.py` still gates 级别 on 喜忌 — reconciling it is part of phase 2b.
- **Natal-rule gaps found** (to fix separately, not via cycle rules): the 论地支 natal rules never
  check the branch they describe; the 巳 and 酉 rules require a 月支 that contradicts their own
  subject; the 未 rule uses 日支.

## Deferred, by design
- **Dropped on user decision:** 流月 / 流日 — none of the classical texts in the library (三命通会,
  渊海子平, 子平真诠, 滴天髓, 穷通宝鉴) reads cycles below the year; only modern practice does. Do
  not re-propose. Also 九星能量, 方位分析, 五黄煞 (feng-shui almanac, not chart analysis);
  共拱/拱会 virtual arches (need positional adjacency).
- **Cycle 神煞 解读:** natal interpretation texts are pillar-positional prose; the LLM layer
  interprets cycle stars instead.
- **Remaining chapters:** 卷一 and 卷二 phase 2a (论大运 + the 论地支 / 十干 大运 clauses) are
  encoded. Next: 卷二 2b (论太岁 + 总论岁运, with the 岁运并临 reconciliation), 2c (论小运), then
  the other volumes' 行运-clause natal rules and the 4 `PENDING_MIGRATION` rules in 卷五/卷六.
