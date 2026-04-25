# BaZi Interaction Types – Detection Logic & Classical Meaning

## Branch Interactions (Earthly Branches)

| Interaction | Detection Logic | Classical Meaning |
|-------------|----------------|-------------------|
| **三会 (San Hui)** | Three branches forming a complete season: `寅卯辰` (Wood/East), `巳午未` (Fire/South), `申酉戌` (Metal/West), `亥子丑` (Water/North). All three present. | Strongest structural bond – seasonal directional energy. Overrides almost everything. |
| **三合 (San He)** | Three branches forming full elemental cycle: `申子辰` (Water), `亥卯未` (Wood), `寅午戌` (Fire), `巳酉丑` (Metal). All three present. | Powerful elemental transformation. Slightly weaker than 三会. |
| **半合 (Ban He)** | Two branches of a 三合 where the **cardinal (帝旺)** branch is present, one satellite missing. E.g., `申＋子` (missing 辰). Adjacent only. | Partial combination – still significant but lacks full transformation. |
| **拱合 (Gong He)** | Two **non-cardinal** branches of a 三合, cardinal absent from chart. E.g., `申＋辰` (missing 子). Adjacent only. | Virtual arch – no real occupation, only a faint attraction towards the missing cardinal. |
| **残会 (Can Hui)** | Two branches of a 三会 where the **cardinal** (middle of season) is present, one satellite missing. E.g., `寅＋卯` (missing 辰). Adjacent only. | Partial directional – weaker than full 三会 but still expressive. |
| **拱会 (Gong Hui)** | Two **flanking** branches of a 三会, cardinal absent from chart. E.g., `寅＋辰` (missing 卯). Adjacent only. | Virtual directional arch – echoes the season but has no substance. |
| **六冲 (Liu Chong)** | Opposite branches on the compass: `子午`, `丑未`, `寅申`, `卯酉`, `辰戌`, `巳亥`. Any distance. | Direct opposition – breaks harmony, can open or destroy structures. |
| **六合 (Liu He)** | Six harmonious pairs: `子丑`, `寅亥`, `卯戌`, `辰酉`, `巳申`, `午未`. Adjacent only. | Binding harmony – can transform into a new element. “贪合忘冲” principle. |
| **比和 (Bi He)** | Two branches of the same element: `寅卯` (Wood), `巳午` (Fire), `申酉` (Metal), `亥子` (Water), and any two of the four Earth branches (`辰丑未戌`). | Friendly coexistence – mild support, no transformation, not binding. |
| **伏吟 (Fu Yin)** | Identical stem **and** branch on two pillars (e.g., `甲子` on year and month). | Stagnation, repetition, internal blockage – like an echo that immobilises. |
| **无恩之刑 (Ungrateful Punishment)** | Branches `寅`, `巳`, `申` – all three present (full) or any two (half). | Scheming, betrayal, legal troubles. Severity depends on count. |
| **恃势之刑 (Bullying Punishment)** | Branches `丑`, `戌`, `未` – all three present (full) or any two (half). | Arrogance, oppression, internal family strife. |
| **无礼之刑 (Uncivilized Punishment)** | Pair `子－卯` only. | Improper relationships, lack of boundaries, emotional clumsiness. |
| **自刑 (Self-Punishment)** | Duplicate branch among pillars: `辰`, `午`, `酉`, `亥` (e.g., two 辰, two 午, etc.). | Self‑inflicted pressure, mental loops, indecision. |
| **六害 (Liu Hai)** | Six harmful pairs: `子未`, `丑午`, `寅巳`, `卯辰`, `申亥`, `酉戌`. Adjacent only. | Undermining, gradual erosion of luck, hidden obstacles. |
| **六破 (Liu Po)** | Six destructive pairs: `子酉`, `卯午`, `辰丑`, `未戌`, `寅亥`, `巳申`. Adjacent only. | Small cracks, broken cooperation, minor annoyances. |
| **暗合 (An He)** | Hidden stem combinations between branches: `寅－丑` (甲己合), `卯－申` (乙庚合), `午－亥` (丁壬合). Adjacent only. | Secret affairs, unspoken agreements, covert attraction. |

## Stem Interactions (Heavenly Stems)

| Interaction | Detection Logic | Classical Meaning |
|-------------|----------------|-------------------|
| **天干合 (Tian Gan He)** | Five combinations: `甲己`(土), `乙庚`(金), `丙辛`(水), `丁壬`(木), `戊癸`(火). Any distance. | Harmonisation – can transform if adjacent and supported. Locks stems, absorbs 克/冲. |
| **天干克 (Tian Gan Ke)** | Controlling relationships (e.g., `庚克甲`, `辛克乙`, `甲克戊`, etc.). Defined in `stem_controls` set. | Direct control – one stem dominates another. Weaker than 合 but stronger than 冲. |
| **天干冲 (Tian Gan Chong)** | Opposing stems: `甲庚`, `乙辛`, `丙壬`, `丁癸`. Detected only when no branch clash (otherwise becomes 天克地冲). | Stem‑level clash – destabilising but less severe than 六冲. |

## Pillar‑level Composite

| Interaction | Detection Logic | Classical Meaning |
|-------------|----------------|-------------------|
| **天克地冲 (Tian Ke Di Chong)** | Branch **and** stem clash simultaneously on same pillar pair (e.g., `甲子` vs `庚午`). | Complete opposition at both heavenly and earthly levels – very severe, especially on day pillar. |
| **干支透合 (Gan Zhi Tou He)** | Stem from one pillar covertly combines with a **hidden stem** of another pillar’s branch (e.g., 乙 combines with hidden 庚 in a申). | Covert bond – stem‑to‑hidden‑stem attraction. Very subtle, often nullified by stronger locks. |

## Summary Hierarchy (Strongest → Weakest)

1. 三会, 三合
2. 六冲, 天克地冲
3. 六合
4. 半合, 残会
5. 天干合
6. 拱合, 拱会
7. 比和, 伏吟
8. All punishments (刑)
9. 六害, 六破
10. 天干克, 天干冲
11. 暗合, 干支透合

Detection Phase (lines 2504-2507)
All pairwise interactions among branches [丑, 亥, 辰, 申] and stems [乙, 丁, 戊, 庚]:

Branch Pairwise (lines 2164-2283)
Pair	Distance	Check	Result
丑-亥	1	six_he_map(丑)=子 ✗, clash_map(丑)=未 ✗, peer? 丑=Earth,亥=Water ✗	NONE
丑-辰	2	six_he_map ✗, peer? 丑=Earth, 辰=Earth ✓	比和 registered
丑-申	3	distant, pairwise skipped	NONE
亥-辰	1	six_he_map(亥)=寅 ✗, clash? ✗, peer? different element ✗	NONE
亥-申	2	various checks...	NONE (neither六冲 nor others)
辰-申	1	various checks...	NONE
Result: Only 比和(丑-辰) registered from branch interactions.

Heavenly Stem Interactions (lines 2285-2340)
All stem pairs are checked for 天干合, 天干克, 天干冲:

Pair	Distance	Interaction	Check	Result
乙-丁	1	天干合?	stem_combines(乙)=庚, not 丁 ✗	NONE
乙-戊	2	天干克?	stem_controls(乙→戊)? Wood controls Earth ✓	天干克 (乙克戊)
乙-庚	3	天干合?	stem_combines(乙)=庚 ✓	天干合(乙+庚→金)
乙-庚	3	天干克?	stem_controls(庚→乙)? Metal cuts Wood ✓	天干克 (庚克乙)
丁-戊	1	天干冲?	stem_clashes(丁)≠戊, not clash ✗	NONE
丁-庚	2	天干克?	stem_controls(丁→庚)? Fire melts Metal ✓, OR (庚→丁)? Metal cuts Fire ✗	天干克 (丁克庚)
戊-庚	1	天干克?	stem_controls(戊→庚)? Earth blocks Water ✗, (庚→戊)? Metal cuts? ✗	NONE
Registered from stems:

天干克(乙→戊)
天干合(乙-庚)
天干克(庚→乙)
天干克(丁→庚)
干支透合 (lines 2285-2340+)
Checks if a stem from one pillar covertly bonds with hidden stems (藏干) in another pillar's branch:

For distance < 3 (exclude Year-Hour):

乙(年) + 丑(年)'s hidden stems? Same pillar, skip
乙(年) + 亥(月)'s hidden stems 甲, 壬 → 乙 combines with ? (no match)
乙(年) + 辰(日)'s hidden stems 戊, 乙, 癸 → 乙 combines with 庚 (not in this list, but 乙 itself is hidden) no match
丁(月) + 申(时)'s hidden stems 庚, 壬, 戊 → 丁 + 壬? (丁 combines with 壬 → 木) 干支透合 registered
戊(日) + 丑(年)'s hidden stems 己, 癸, 辛 → 戊 + 癸? (戊 combines with 癸 → 火) 干支透合 registered
庚(时) + 辰(日)'s hidden stems 戊, 乙, 癸 → 庚 + 乙? (庚 combines with 乙 → 金) 干支透合 registered
Registered干支透合:

干支透合(丁+申中气壬→木)
干支透合(戊+丑中气癸→火)
干支透合(庚+辰中气乙→金)
三会 & 三合 (lines 2040-2117)
Check for three-branch directional/elemental triads:

With branches [丑, 亥, 辰, 申]:

三会 Water = 亥-子-丑: Have 亥, 丑 but missing 子 → Can form 拱会(亥-丑) (virtual arch)
三合 Water = 申-子-辰: Have 申, 辰 but missing 子 → Can form 拱合(申-辰) (virtual arch)
Registered:

拱会(亥-丑) — virtual, distance from adjacent=1
拱合(申-辰) — virtual, distance from adjacent=1
Pass 1 — Structural Lock (lines 1192-1305)
Check each branch for competing 三会/三合:

丑: participates in 拱会 (virtual only, not 三会/三合 actual)
亥: participates in 拱会 (virtual)
辰: participates in 拱合 (virtual)
申: participates in 拱合 (virtual)
Result: No real 三会/三合, so no locking, no downgrades.

Pass 2 — Dual Lock (Greedy Six-Harmony) (lines 1351-1472)
Check for 六合 and 六冲 conflicts:

No 六合 detected → no greedy lock happens
No 六冲 detected → nothing to absorb
Result: No changes.

Pass 3 — Conflict Resolution (lines 1474-1507)
This is where the real suppression happens!

Key rule applied:


# From PRIORITY_RULE_TABLE
("STEM_天干合", "天干克"): cap to 消融吸收
("STEM_天干合", "天干冲"): cap to 消融吸收
天干合(乙-庚) locks both 乙 and 庚 as STEM_天干合.

Now any 天干克 involving 乙 or 庚 is suppressed:

天干克(乙→戊) — involves locked 乙

Remark: "天干合化锁定，克力被合化消融"
Strength → 消融吸收
天干克(庚→乙) — involves both locked stems

Same remark
Strength → 消融吸收
天干克(丁→庚) — involves locked 庚

Same remark
Strength → 消融吸收
Result: All three 天干克 downgraded to 消融吸收.

Pass 4 — Group/Environment (拱合/拱会 Echo) (lines 1583-1695)
Check virtual arches:

拱会(亥-丑) seeking 子

Element: Water (亥-子-丑 trio)
No clash turbidity (neither 亥 nor 丑 clashed)
Default strength (distance=1) = 强势主流
拱合(申-辰) seeking 子

Element: Water (申-子-辰 trio)
No clash turbidity
Default strength (distance=1) = 强势主流
Result: Both provisionally assigned 强势主流, but...

Pass 5 — Default Strength Assignment (lines 1697-1726)
Any item without 强度 yet gets default from DEFAULT_STRENGTH table:


("比和", 2): "显著影响"        # distance=2
("天干合", 3): "中等衰减"      # distance=3, year-hour
("天干克", 2): "中等衰减"      # distance=2
("干支透合", 1): "强势主流"    # distance=1
("干支透合", 2): "显著影响"    # distance=2
("拱会", 1): "强势主流"        # distance=1
("拱合", 1): "强势主流"        # distance=1
Assignments:

比和(丑-辰) distance=2 → 显著影响 ✓
天干合(乙-庚) distance=3 → 中等衰减 ✓ + remark "年时相距三柱，远距衰减加深"
干支透合(戊+丑中气癸) distance=2 → 显著影响 ✓
干支透合(丁+申中气壬) distance=2 → 显著影响 ✓
干支透合(庚+辰中气乙) distance=1 → 强势主流 (initially)
拱会(亥-丑) distance=1 → 强势主流 (initially)
拱合(申-辰) distance=1 → 强势主流 (initially)
Pass 6 — Xun Kong (旬空) Post-Filter (lines 1846-1943)
Check which branches/stems fall in void positions:

For your chart (assuming standard void calculation):

Day pillar (戊辰) is in a specific 旬 (decade cycle)
The void pair for that 旬 affects certain branches
From the output remarks: "月柱支落旬空" — 月柱 (亥) is in 旬空!

When a branch is in 旬空:

Interactions involving that branch are downgraded
拱会(亥-丑) involves 亥 in 旬空 → downgraded from 强势主流 to 中等衰减 ✓
Remark: "月柱支落旬空，合力虚浮，力场不实"
Also, 干支透合(庚+辰中气乙) (distance=1):

庚 is in 时柱 (hour), which is adjacent to 日柱(辰)
But the remark says: "源天干已与他干直合，贪合之下，藏干透合消融"
This means 庚 is locked in 天干合(乙-庚), so its 干支透合 is suppressed
Strength → 消融吸收 ✓
拱合(申-辰) — no void involvement, stays 显著影响 ✓

Pass S — Stem Rooting Modulation (lines 1738-1814)
Modulate 天干合/克/冲 based on root depth:

天干合(乙-庚):

乙: 中根 (not 无根)
庚: 深根 (not 无根)
Rule: "one stem 无根 → cap to 显著影响; both 无根 → cap to 中等衰减"
Neither is 无根 → no downgrade
Strength remains 中等衰减 (from Pass 5)
(The three suppressed 天干克 already at 消融吸收, no further modulation applies)

Summary Table
Interaction	Type	Distance	Initial Strength	Pass 3 (Conflict)	Pass 6 (Void)	Pass S (Rooting)	Final
比和(丑-辰)	Peer harmony	2	显著影响	—	—	—	显著影响
天干合(乙-庚)	Harmony	3	中等衰减	—	—	—	中等衰减
天干克(乙→戊)	Control	2	中等衰减	STEM_天干合 suppress	—	—	消融吸收
天干克(庚→乙)	Control	3	大幅衰减	STEM_天干合 suppress	—	—	消融吸收
天干克(丁→庚)	Control	2	中等衰减	STEM_天干合 suppress	—	—	消融吸收
干支透合(戊+癸)	Covert bond	2	显著影响	—	—	—	显著影响
干支透合(丁+壬)	Covert bond	2	显著影响	—	—	—	显著影响
干支透合(庚+乙)	Covert bond	1	强势主流	—	—	STEM_天干合 suppress	消融吸收
拱会(亥-丑)	Virtual arch	1	强势主流	—	亥 in 旬空 ↓	—	中等衰减
拱合(申-辰)	Virtual arch	1	强势主流	—	—	—	显著影响
Key Insights
No六合/六冲 — my biggest error. The chart has NO mutual attractions or direct branch clashes at the branch level.

天干合 is the kingpin — 乙-庚 harmony locks at distance 3, suppressing ALL related 天干克 to 消融吸收. This is 贪合忘克 ("harmony forgets control").

Void (旬空) weakens virtual arches — 拱会(亥-丑) drops from 强势主流 to 中等衰减 because 亥 is in void.

Covert stem bonds (干支透合) — 庚 combining with hidden 乙 in 辰 is also suppressed because 庚 is locked in the 乙-庚 harmony.

Distribution across tiers — most interactions end up in 第二梯队_气势层 or 第三梯队_琐碎层; nothing in 第一梯队_纲领层 because there are no structural 六合/六冲/三会/三合 to dominate.

This chart is harmoniously locked by the year-hour stem cooperation (乙-庚→金), which suppresses a lot of underlying control dynamics.