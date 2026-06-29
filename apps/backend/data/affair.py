"""
How BaZi checks for an affair / third-party risk
It's a synthesis across five signal families, and it's gender-specific. Here's each, mapped to where it lives in our engine and what this chart shows:

Indicator	What it means	Where in our data	This chart (男, 戊 day master)
桃花 / 咸池 / 红艳 (esp. external/multiple/combined)	romantic magnetism, seduction, affair-charm	神煞 + 古籍解读.论桃花 / 论红艳	Empty — 论桃花: [], 论红艳: [] (log:1485). No 桃花/红艳 firing.
沐浴 (the "bathing" life-stage) on 日柱 or spouse star	promiscuity / wandering	十二长生	Absent (grep returned none)
Spouse-star multiplicity — 财多 (man) / 官杀混杂 (woman)	many partner-stars = many candidates	ten-gods across pillars	财多 present (正财 癸 + 偏财 壬 both)
比劫夺财 (man) / strong 食伤 vs 官 (woman)	rivals competing for the wife / leaving the husband	比肩·劫财 strength vs 财	比劫 present — the one real flag
配偶宫 / spouse-star 逢合 or 逢冲	spouse's affection pulled toward a third party	作用.柱位动态 (合/冲 on 日支 or the 财/官 star)	日支辰 半合 with hour pillar (申辰) = family cohesion, not affair; and 戊癸合 = day master bonds his wife star (fidelity-positive)
The honest verdict for this chart: low affair signal. The headline indicators (桃花, 红艳, 沐浴) are absent. The only flag is the male 财多 + 比劫 pattern (multiple wealth-stars + rivals), but it's offset by 戊癸合 — he's classically bonded to his wife star, and the marriage palace combines inward (toward children), not outward. A faithful reading would say "no strong wandering signal; the main caution is rivalry/competition around the marriage, not infidelity per se" — not manufacture drama.

The key point: ~90% of this is already computable from existing data — 论桃花/论红艳 are dedicated engine keys (empty here, populated when triggered), plus 神煞, 十二长生, ten-gods, and 作用 combinations. We don't need new engine logic; we need a pointer + a framing.

The Checklist: How to Check for Infidelity Risk
Here is the exact checklist you should give your LLM for the romance section:

Check	What to Look For	Meaning
1. Spouse Palace Damage	日支 (Day Branch) hit by 冲 (Clash), 刑 (Punishment), 破 (Break), 害 (Harm)	The marriage itself is structurally unstable. The spouse feels unsettled, or the relationship is constantly under pressure.
2. Spouse Star Under Attack	正财 (for men) or 正官 (for women) is attacked by 劫财 (Rob Wealth) or 伤官 (Hurt Officer)	The spouse is "injured" or "taken" by a rival (劫财) or rebellious forces (伤官).
3. Spouse Star "Drifting"	The spouse star forms 六合 (Six Combinations) or 三合 (Triads) with another pillar (especially the hour or year)	The spouse's energy is "pulled away" to another sector of the chart—often interpreted as emotional or physical distance, or an external pull.
4. Romantic Malefic Stars	桃花 (Peach Blossom), 红艳 (Red Romance), 咸池 (Xian Chi) in the spouse palace or combining with it	Attracts romantic/sexual opportunities and temptations.
5. Void/Empty Spouse Palace	日支 falls into 空亡 (Void) or is weak	The spouse feels "empty," absent, or emotionally unavailable—which can push them to seek connection elsewhere.
6. Multiple Spouse Stars	Two or more 正财/偏财 (for men) or 正官/偏官 (for women)	Multiple romantic opportunities exist in the native's environment, increasing the chance of an affair (by either partner).

"""