"""
Section registry — the single source of truth for the multi-section BaZi insight report.

Each section drives one LLM call. The full natal chart is passed to every call; the
``emphasis`` text is a soft focus cue (rendered into the user prompt as "pay special
attention to…"), NOT a data filter. ``古籍解读`` is intentionally never sliced — its
relevance to a life domain depends on stem/branch combinations, so the model sees all of it
and decides what applies.

Pillar -> life-area convention used across the emphasis hints:
    年柱 = ancestry / early life        月柱 = parents / career / youth
    日柱 = self & spouse (日支 = 配偶宫)  时柱 = children / later life
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Category:
    """One labelled group inside a structured section (e.g. career's "challenges")."""

    key: str  # JSON key the model must return, e.g. "path_to_success"
    label: str  # Human-readable group heading shown in the prompt


@dataclass(frozen=True)
class Section:
    key: str  # JSON wrapper key the model must return, e.g. "personality"
    title: str  # Human-readable section title shown in the prompt
    guidance: str  # What the narrative should cover (story, not field list)
    emphasis: str  # Chart areas to foreground for this domain (soft cue)
    # When set, the model returns a structured object keyed by these categories
    # (each a list of {point, explanation}) instead of a single prose string.
    categories: tuple[Category, ...] | None = None


SECTION_REGISTRY: list[Section] = [
    Section(
        key="personality",
        title="Core Personality & Character",
        categories=(
            Category(key="core", label="Core Nature"),
            Category(key="mind", label="How You Think & Feel"),
            Category(key="drives", label="What Drives You"),
            Category(key="strengths", label="Natural Strengths"),
            Category(key="weakness", label="Things to Look Out For"),
        ),
        guidance=(
            "Paint this person's character across five groups — core (what they fundamentally "
            "are: the base temperament set by their day-master element, polarity and strength, "
            "the overall five-element balance, and the dominant influence shaping the chart), "
            "mind (how they think and feel — their cognitive and emotional style: reflection and "
            "learning, self-expression, discipline, intellect), drives (what propels them: their "
            "deeper motivations and inner orientation — what they reach for, and why), strengths "
            "(their natural gifts and the traits that come easily), and weakness (the blind "
            "spots, imbalances and inner tensions worth watching). "
            "Each item is a 'point' — one crisp claim — plus an 'explanation' that must do three "
            "things: (a) ground the claim in the SPECIFIC evidence in this chart — name the actual "
            "stem(s), branch(es), ten-god(s), star(s), element balance or interaction(s) it rests "
            "on, weighed together where several bear on the same point, not a generic trait; (b) "
            "when a classical pattern applies, give the reading in plain English and cite the term "
            "once in parentheses, e.g. 'a reflective, knowledge-loving streak (正印)' or 'a "
            "solitary, artistic bent (华盖)'; (c) when a trait sits on a time-bound pillar and "
            "sharpens in a particular life phase, say so — though temperament is largely lifelong. "
            "Write two to four sentences per explanation — enough to teach the 'why', never a bare "
            "label. This is a CHARACTER reading: where a signal also touches money, career or "
            "relationships, speak only to what it reveals about the person's temperament, "
            "instincts and inner makeup — not financial outcomes, job paths or marriage events, "
            "which the wealth, career and romance sections cover."
        ),
        emphasis=(
            "The day master's element, polarity and overall strength (whether it is supported "
            "by its season, its roots, and the surrounding chart), and its life-stage. "
            "The balance of the five elements — which are strong, which are weak or missing — "
            "as the basis of temperament. The ten-gods on the visible and hidden stems, "
            "especially the dominant influence of the month branch, plus each pillar's na yin. "
            "The classical na-yin temperament readings for each pillar (古籍文献.三命通会_纳音性质) and "
            "the day/hour-pillar verses (古籍文献.三命通会_日时断: 日柱解读 and 时柱解读). Character-type "
            "classical rules (特殊格局 such as 日德 / 八专禄旺 / 财官双美, 论日干格局, 论五行组合, "
            "论正印, the noble-star readings 论太极贵人 / 论天乙贵人 / 论天月德, 释六十甲子). "
            "The FULL spiritual-star block (神煞) across every pillar — read each star's 解读, "
            "both the auspicious and the malefic; skip neither. On the gifted and benevolent "
            "side: 文昌 / 学堂 / 词馆 / 文星贵 / 文誉贵 (intellect, scholarship, eloquence), 太极贵人 "
            "(a philosophical, metaphysical bent), 六秀 / 十灵 / 三奇 (rare, multi-talented "
            "brilliance), 天医 (healing or psychological insight), 天乙贵人 / 天德 / 月德 / 德秀贵人 "
            "/ 龙德 (kindness, integrity, charisma and being readily helped), 国印 / 天官 / 天印贵 "
            "/ 将星 (reliability, principled bearing, natural authority), 福星 / 金舆 / 天厨贵人 "
            "(a contented, gracious, comfort-loving disposition), 进神 (steady, determined drive), "
            "驿马 (restlessness, a craving for change), 华盖 (a solitary, artistic streak). On the "
            "shadow side, equally telling: 亡神 (a guarded, scheming depth), 月厌 (feeling "
            "misunderstood or set apart), 绞煞 / 剑锋煞 / 天屠煞 / 破煞 (a sharp, combative or "
            "self-undermining edge), 元辰 / 吊客 (a brooding, melancholic undertow). Map the gifts "
            "to mind, strengths and drives, and the shadows to weakness. "
            "The branch and stem interactions (作用.关系总览 and 作用.柱位动态) — combinations and "
            "pulls (六合 / 三合 / 拱合 / 拱会), breaks (六破), clashes (六冲), harms, and distant "
            "stem combinations (天干遥合): these shape core temperament and inner tension more than "
            "any single star, so weigh them for core, strengths and weakness. "
            "All three palaces in 胎命身 (each given only as a 干支 + 纳音): read each through its "
            "element and its ten-god relation to the day master — NOT through the branch's zodiac "
            "animal, which is decorative, not diagnostic. 命宫 is conscious inner orientation; 身宫 "
            "(the body palace) is innate instinct and what the person subconsciously reaches for "
            "(drives); 胎元 (the conception palace) is the pre-natal constitutional baseline — the "
            "raw temperament one is formed with (core), and is NOT ancestry or lineage, which the "
            "year pillar covers."
        ),
    ),
    Section(
        key="family",
        title="Family & Upbringing",
        categories=(
            Category(key="roots", label="Roots & Ancestry"),
            Category(key="parents", label="Your Parents"),
            Category(key="siblings", label="Siblings & Friends Growing Up"),
        ),
        guidance=(
            "Tell this person's family-of-origin story across three groups — roots (where they "
            "come from: the standing and influence of their grandparents and ancestral line, and "
            "the early home that shaped them), parents (their bond with mother and father — "
            "closeness or distance, what each gave them, and any friction), and siblings (their "
            "brothers and sisters AND the friends and companions they grew up alongside — bonds, "
            "rivalry, support or distance). "
            "Read every relative-star as a TENDENCY, not a head-count: BaZi cannot confirm how "
            "many siblings or kin a person has. When a relative's star is weak, void or absent, "
            "say so plainly — few or no siblings (quite possibly an only child), a distant or "
            "absent parent — rather than inventing a relationship that may not exist. Each group "
            "owns its relative's whole story, warmth and friction alike; fold any clash, voidness "
            "or isolation affecting a relative into that relative's group. "
            "Before stating a point, reconcile ALL signals bearing on that relative — the relevant "
            "interaction or vault state, the spiritual stars on the pillar, and the six-relatives "
            "reading — into one verdict; never let a single interaction label stand as a "
            "conclusion on its own, and where signals point different ways, weigh which is better "
            "supported and say so. "
            "Each item is a 'point' — one crisp claim — plus an 'explanation' that must do three "
            "things: (a) ground the claim in the SPECIFIC evidence in this chart — name the actual "
            "pillar, ten-god (the seal star for mother, the wealth star for father, the "
            "companion/rob-wealth stars for siblings and same-generation peers), star, "
            "six-relatives reading or interaction it rests on, weighed together where several "
            "bear on the same point; (b) when a classical pattern applies, give the reading in "
            "plain English and cite the term once in parentheses, e.g. 'a nurturing, supportive "
            "mother (正印得地)' or 'rivalry over shared resources (劫财)'; (c) anchor a relative to "
            "their pillar's life phase where relevant (year = grandparents and early childhood, "
            "month = parents and youth). Write two to four sentences per explanation — enough to "
            "teach the 'why', never a bare label."
        ),
        emphasis=(
            "The year pillar (grandparents, ancestry and the early home) and the month pillar "
            "(parents and siblings): their stems and branches, ten-gods, na yin temperament, "
            "and the spiritual stars sitting on each. The relative-stars among the ten gods — "
            "the seal star for the mother and nurture, the wealth star for the father, and the "
            "companion/rob-wealth stars (比肩 / 劫财) for siblings AND the same-generation friends "
            "and peers one grows up with. For each relative-star, read its computed root strength "
            "(四柱实体.{柱}.天干.根基强度 and 通根于): a star marked 无根 / 无根浮干 / 浮根 is rootless "
            "or floating — that relative lacks personal power and a steady presence in the home "
            "(e.g. a rootless 正印 = a gentle mother who cannot anchor or shield), whereas a "
            "well-rooted (通根 / 得地) star is a strong, grounded, present relative. "
            "The six-relatives block (六亲) and the classical six-relatives readings "
            "(古籍解读.六亲: 祖先 / 父母 / 兄弟 / 公父), including the modern interpretations. "
            "Interactions between the year and month pillars (clashes, harms, breaks = friction "
            "with elders or parents) and any voidness on those pillars (distant or absent kin). "
            "Where a year/month branch is an earth vault (辰戌丑未), take its state from "
            "作用.库位状态 and its 备注 verdict, not from the bare 六破 / 六冲 in 柱位动态. Do not turn "
            "a 破而不开 or 藏而未开 vault into 'ancestral wealth lost' or 'a family secret surfacing': "
            "an unopened vault is disturbed, not spilled — 库位状态 says explicitly when one opens. "
            "Stars of isolation or mourning (华盖 / 孤辰 / 寡宿, 吊客 / 披麻). "
            "Sibling fate is NOT confined to the month branch or a 比劫 head-count: scan every "
            "神煞 解读 across all pillars for explicit sibling verdicts — wherever a star's reading "
            "names 兄弟 / 兄弟姐妹 / 父母兄弟 (e.g. 驿马 → '兄弟姐妹聚少离多', 国印 → '兄弟中有人为贵', "
            "自缢煞 → '父母兄弟有灾'), that named verdict carries the sibling story directly and "
            "overrides any generic 比劫 inference, even when the month branch itself is weak or void. "
            "The na-yin readings for the year and month pillars "
            "(古籍文献.三命通会_纳音性质: 年柱 / 月柱). In the family domain, render the na-yin not "
            "only as inherited temperament but as the FELT ATMOSPHERE of the childhood home — "
            "translate the sanctioned reading's own imagery into what the early home felt like "
            "(e.g. 乙丑 海中金 read as 顽矿, raw unrefined ore that needs fire to prove itself ⇒ a "
            "home that prized endurance and forging character over comfort). Stay anchored to the "
            "三命通会 reading's imagery; do not free-associate on the poetic na-yin name alone."
        ),
    ),
    Section(
        key="romance",
        title="Love, Marriage & Children",
        categories=(
            Category(key="partner", label="How You Love & Who Suits You"),
            Category(key="spouse", label="Your Spouse"),
            Category(key="journey", label="The Journey & Its Timing"),
            Category(key="children", label="Children & Your Own Home"),
        ),
        guidance=(
            "Tell this person's love-and-family-building story across four groups — partner (how "
            "they love and the kind of partner who suits them: their relationship style, what "
            "they seek and what they offer), spouse (the temperament, standing and likely "
            "background of their husband or wife, read from the marriage palace), journey (the "
            "shape and TIMING of significant relationships — early or late, smooth or delayed, "
            "one deep bond or several — spoken in life phases, never as fixed dates), and "
            "children (their bond with and outlook toward children, and the later-life household "
            "they build). Note tendencies, never fixed fate. "
            "IMPORTANT — read gender first: the spouse star is the wealth star (正财 = wife, 偏财) "
            "in a man's chart but the authority star (正官 = husband; 七杀, which this engine "
            "relabels 偏官 once it is tamed — same indirect-authority husband star) in a woman's "
            "chart; the children star is the output star (食伤) in a woman's chart but the "
            "authority star (官杀 — i.e. 正官 together with 七杀/偏官) in a man's chart. A 七杀 shown "
            "as 偏官 (marked 七杀化偏官) is a tamed one: read it as a strong but more controlled and "
            "dependable partner or child-bond, not a raw, volatile one. "
            "Each item is a 'point' — one crisp claim — plus an 'explanation' that must do three "
            "things: (a) ground the claim in the SPECIFIC evidence — the marriage palace (日支 / "
            "配偶宫), the spouse or children star and its strength/root/placement, the relevant "
            "star, classical reading or interaction — weighed together where several bear on the "
            "same point; (b) when a classical pattern applies, give the reading in plain English "
            "and cite the term once in parentheses, e.g. 'a steady, harmonious union (日支六合)' or "
            "'a partner who arrives late (配偶星入墓)'; (c) for the journey group, anchor timing to "
            "the life phase a signal sits on (spouse star on the year/month pillar ⇒ love early; "
            "on the day/hour ⇒ later) and to void / clash / peach-blossom conditions — never "
            "invent a specific age. Write two to four sentences per explanation — enough to teach "
            "the 'why', never a bare label."
        ),
        emphasis=(
            "IMPORTANT — read the gender first: the spouse star is the wealth star (正财 = wife, "
            "偏财) in a male chart, but the authority star (正官 = husband; 七杀, which this engine "
            "relabels 偏官 once tamed — marked 七杀化偏官 — so treat 偏官 as the same husband star, "
            "signalling a strong but more controlled, dependable partner) in a female "
            "chart. Foreground that star's strength, root and placement. "
            "The day pillar is the marriage palace: the day branch (配偶宫), its hidden stems "
            "(the concealed spouse star), and its self-seated life-stage. Read the day pillar's "
            "stars even-handedly — the auspicious and the malefic together, not only the "
            "flattering ones. Favourable: 天官贵人 (a spouse of good standing), 桃花 / 红艳 (charm "
            "and attraction). Cautionary, and just as telling: 绞煞 (a hot-tempered spouse, even "
            "physical conflict), 破煞 (婚姻易破 — a real risk of rupture, not a mere quirk), 自缢煞 / "
            "剑锋煞 (severe friction or clashes in the union), 童子煞 (a rocky early love-path and a "
            "late or reluctant route to settling — read alongside its remedy: a later, well-tended "
            "union can steady), 孤辰 / 寡宿 (loneliness within the bond). Where capable-"
            "spouse stars and these afflictions share the palace, render the TENSION — a strong but "
            "volatile marriage that needs active tending — not a one-sided rosy verdict. "
            "The classical spouse readings (古籍解读.六亲: 妻 / 夫, 妻语惬心) with "
            "modern interpretations, and the day-pillar verse (古籍文献.三命通会_日时断.日柱解读). "
            "Interactions touching the day branch — harmony (六合) for a steady marriage, clash "
            "(六冲) for instability, harm/break, and any combination pulling the spouse star "
            "away — plus voidness on the day branch or spouse star (delay or fragility). "
            "The day master's strength versus the spouse star's strength (the balance of the "
            "partnership), and the day-pillar na-yin temperament (古籍文献.三命通会_纳音性质.日柱). "
            "For TIMING (the journey): which pillar the spouse star sits on (year/month = an "
            "early partner, day/hour = a later one), whether it is revealed on a stem (an early, "
            "obvious partner) or hidden in 藏干 (a late-surfacing or concealed one), void or clash "
            "on the 配偶宫 (delay, instability, or more than one significant bond), the placement "
            "of the romance stars (桃花 / 红鸾 / 天喜 — which pillar they sit on shows when love "
            "runs hot), and loneliness/mismatch markers (孤辰 / 寡宿 / 孤鸾 / 阴阳差错 = a delayed "
            "or harder path to settling). "
            "For CHILDREN: the children star — the output star (食伤) in a female chart, the "
            "authority star (官杀 — 正官 and 七杀/偏官) in a male chart — with its strength and root; "
            "the hour pillar "
            "as the children palace (子女宫), its hidden stems, spiritual stars, na yin and verse "
            "(古籍文献.三命通会_日时断.时柱解读); and any classical six-relatives reading on children "
            "(古籍解读.六亲), framed as the bond and the later-life household, not as outcomes."
        ),
    ),
    Section(
        key="career",
        title="Career & Talents",
        categories=(
            Category(key="path_to_success", label="Path to Success"),
            Category(key="highlights", label="Career Highlights"),
            Category(key="challenges", label="Career Challenges"),
            Category(key="advice", label="Career Advice"),
        ),
        guidance=(
            "Tell this person's career story across four groups — path_to_success (the fields, "
            "roles and working environments their chart actually points to), highlights (their "
            "professional strengths and peak potentials), challenges (the frictions, "
            "instabilities and ceilings they must navigate), and advice (concrete, actionable "
            "guidance that follows directly from the three groups above). "
            "Each item is a 'point' — one crisp claim — plus an 'explanation' that must do three "
            "things: (a) ground the claim in the SPECIFIC evidence in this chart — name the actual "
            "stem(s), branch(es), ten-god(s), star(s) or interaction(s) it rests on, weighed "
            "together where several bear on the same point, not a generic trait; (b) when "
            "a classical pattern applies, give the reading in plain English and cite the term once "
            "in parentheses, e.g. 'wealth and status reinforce each other (财官双美)' or 'the income "
            "star sits in a weak position (背禄)'; (c) when the evidence sits on a time-bound pillar, "
            "say which life phase it bears on. Write two to four sentences per explanation — enough "
            "to teach the 'why', never a bare label. Timing is domain-neutral: wherever a signal "
            "sits on a time-bound pillar, name the life phase it bears on, across every group "
            "(early-career instability, a midlife peak, recognition arriving later)."
        ),
        emphasis=(
            "The month pillar as the career palace and the seasonal command (月令) — the chart's "
            "core driver — especially the primary ten-god of the month branch. The ten gods "
            "across the chart: authority stars (官杀 — 正官 and 七杀, the latter relabeled 偏官 when "
            "tamed) for management and discipline, "
            "output/expression stars (食伤) for creativity and talent, seal stars (印) for "
            "learning, credentials and mentors, and wealth stars (财) for enterprise and "
            "resources — note their strength so talents are actually usable. "
            "Classical career rules (古籍解读): 论官煞格局 (including 五行官性, which points to a "
            "suitable field — e.g. a wood authority star suits education and culture), "
            "论日干格局, 论禄神 for income stability, and 论驿马 / 论禄马 for mobility, travel and "
            "relocation work. The day/hour-pillar verses (古籍文献.三命通会_日时断) that judge rank, "
            "officialdom and achievement (e.g. 玉带荣身, 主贵). "
            "Spiritual stars: 文昌 / 学堂词馆 (academic and writing gifts), 国印 / 天官 "
            "(officialdom), 华盖 (arts, research, spiritual work), 驿马 (travel-based work). "
            "Vault states (作用.库位状态 — an open vault = access to resources and assets) and "
            "clashes on the month pillar (career volatility); the body palace (身宫) for "
            "achievement orientation; and the month-pillar na-yin temperament "
            "(古籍文献.三命通会_纳音性质.月柱)."
        ),
    ),
    Section(
        key="wealth",
        title="Wealth",
        categories=(
            Category(key="sources", label="How Wealth Comes to You"),
            Category(key="capacity", label="Capacity to Build & Keep"),
            Category(key="risks", label="Wealth Risks & Leaks"),
            Category(key="timing", label="Timing of Prosperity"),
            Category(key="strategy", label="Wealth Strategy"),
        ),
        guidance=(
            "Tell this person's wealth story across five groups — sources (how money actually "
            "comes to them: steady salary versus windfall, business and investment, and which "
            "channels their chart favours), capacity (their power to both build AND keep wealth — "
            "the balance between their own strength and the wealth they face, and whether they "
            "can store assets), risks (where money is competed for, leaks away, or fails to "
            "arrive), timing (the trajectory of wealth across life and its turning points — when "
            "fortunes shift gear between lean, building and accumulation phases — told as an arc, "
            "not a per-phase re-listing of signals already covered in the other groups), and "
            "strategy (concrete, actionable guidance that follows directly from the four groups "
            "above). "
            "Each item is a 'point' — one crisp claim — plus an 'explanation' that must do three "
            "things: (a) ground the claim in the SPECIFIC evidence in this chart — name the actual "
            "stem(s), branch(es), ten-god(s), star(s), vault state or interaction(s) it rests on, "
            "weighed together where several bear on the same point, not a generic trait; (b) when "
            "a classical pattern applies, give the reading in plain English and cite the term once "
            "in parentheses, e.g. 'steady income reliably supports you (正财)' or 'rivals compete "
            "for your money (劫财)'; (c) when the evidence sits on a time-bound pillar, say which "
            "life phase it bears on. Write two to four sentences per explanation — enough to teach "
            "the 'why', never a bare label. The timing group narrates the overall arc and its "
            "turning points — when wealth changes gear — rather than restating which star does "
            "what in each phase; elsewhere timing is domain-neutral: name the relevant phase "
            "wherever any signal is time-bound."
        ),
        emphasis=(
            "The wealth stars — their placement, strength and root: the direct wealth star "
            "(正财 = steady income and salary) versus the indirect wealth star (偏财 = windfall, "
            "business and investment) — and the strength state of the wealth element itself. "
            "The day master's strength relative to wealth, the core wealth-handling principle: "
            "a strong day master can hold and grow wealth, while a weak day master facing strong "
            "wealth tends to let it slip away. Vault states (作用.库位状态): the wealth vault — "
            "whether it is open or sealed, and the clash/punishment/revealing conditions that "
            "release it. Classical rules (古籍解读): 论禄神 (the salary/income star), 财官双美, "
            "the direct-wealth patterns (正财系列), 背禄, and output-feeding-wealth patterns "
            "(食伤生财). The output stars (食伤) as the source feeding wealth; the rob-wealth "
            "star (劫财 = competition for or loss of wealth) and clashes on the wealth star. "
            "Spiritual stars: 天厨贵人 (provision), 福星, 金舆; and the hour pillar for later-life "
            "wealth and accumulated assets. The day/hour-pillar verses (古籍文献.三命通会_日时断) on "
            "prosperity and livelihood (e.g. 活计生涯, 昌荣 versus 只许平), the hour-pillar na yin "
            "(古籍文献.三命通会_纳音性质.时柱) and the day-pillar na-yin fortune commentary (e.g. 富贵寿考)."
        ),
    ),
    Section(
        key="health",
        title="Health",
        categories=(
            Category(key="constitution", label="Constitution & Vitality"),
            Category(key="attention", label="Where Your Health Needs Attention"),
            Category(key="care", label="Staying Well"),
        ),
        guidance=(
            "Map this person's health story across three groups — constitution (their baseline "
            "vitality and resilience: FIRST whether the body runs warm or cold — the 调候 / "
            "climatic need — since that sets the direction of every remedy, then the strength and "
            "seasonal support of the day master and the five-element balance as energy reserves), "
            "attention (where the body needs watching — LEAD with the chronic, constitutional "
            "vulnerabilities: which organ systems run weak or over-stressed, read from the "
            "five-element balance and the overcoming (克) imbalance between a strong and a weak "
            "element as the disease mechanism, not a static count; THEN the acute flashpoints — "
            "injury, accident or acute-illness signals from clashes, punishments and the sharp "
            "神煞 — each tied to the life phase it falls in), and care (how to stay well: the weak "
            "link to strengthen, and the seasonal, dietary and lifestyle habits that support it). "
            "Each item is a 'point' — one crisp claim — plus an 'explanation' that must do three "
            "things: (a) ground the claim in the SPECIFIC evidence in this chart — name the "
            "actual element balance and strength state, the day-master condition, the "
            "branch/organ, star or interaction it rests on, weighed together where several bear "
            "on the same point; (b) when a classical pattern applies, give the reading in plain "
            "English and cite the term once in parentheses, e.g. 'a strained liver system from "
            "over-strong wood (木旺)' or 'a risk of cuts or surgery (血刃)'; (c) anchor a concern "
            "to the life phase its pillar sits on where relevant (year = childhood, month = "
            "youth, day = midlife, hour = old age). Write two to four sentences per explanation — "
            "enough to teach the 'why', never a bare label. "
            "This is WELLBEING guidance, not a medical diagnosis or a prediction of illness: "
            "speak of tendencies, systems to support and habits that help — never name a specific "
            "disease, date or fatal outcome, and frame every risk as an area to care for, not a fate. "
            "For injury and danger stars (自缢煞, 血刃, 剑锋煞, 天屠煞 …), render the star's own 解读 "
            "as written and stay within what it states — do NOT extrapolate beyond the reading into "
            "a tendency toward self-harm, suicide, despair or a mental-health crisis, even when a "
            "star's NAME (e.g. 自缢 = self-hanging) seems to invite it. The reading is the source, "
            "not the name."
        ),
        emphasis=(
            "Read each element's computed strength from 五行.{元素}.状态 (旺/相/休/囚/死), and the "
            "day master's own state from 日主.得令.状态 and 日主.强弱, DIRECTLY — never derive these "
            "seasonal states yourself; the engine applies root and 土旺用事 adjustments you cannot "
            "reproduce by hand. "
            "Begin with the thermal frame (调候): from the birth season (生时节气) and "
            "古籍解读.论五行组合 (e.g. '十月之土，惟喜火以温之', '遇水孤寒', '逢金则滞'), judge whether "
            "the constitution runs cold or warm — this sets the DIRECTION of every remedy "
            "(a cold-rooted weakness needs warming, a hot-rooted one needs cooling). "
            "Map the five elements to organ systems — wood: liver / gallbladder; fire: heart / "
            "small intestine; earth: spleen / stomach; metal: lungs / large intestine; water: "
            "kidneys / bladder — but read the DYNAMIC, not a static count: the mechanism is the "
            "overcoming (克) or flooding between a strong and a weak element (strong metal cutting "
            "wood = 金克木 straining the liver; excess water washing out earth = 水多土流, 寒湿困脾), "
            "taken from 古籍解读.论五行组合 where present rather than invented. "
            "Constitution: a weak or out-of-season day master means lower baseline vitality; the "
            "day master's life-stage low points (illness/death/tomb/extinction) mark vitality dips. "
            "In 古籍解读, use the HEALTH-relevant readings populated for this chart and silently "
            "skip the many empty ones: the constitutional pattern (论五行组合); the "
            "injury/illness/accident stars (论羊刃, 论挂剑煞, 论剑锋煞, 论天屠煞, 论天火煞, 论破煞, "
            "论水溺煞, 论灾煞, 论自缢煞, 论病符); and harm-by-interaction (论三刑 → chronic ailments, "
            "论六害, 论冲击 → sudden events, 论空亡 → weakness in a palace). Honour each reading's "
            "化解 entry: a star 逢天德 / 月德 has its 凶灾减轻 — state the risk as REAL but reduced, "
            "not absent. Take only the health dimension of a domain-mixed reading (破煞's 折伤之灾 = "
            "injury, not its 财破 wealth side) and treat indirect ones (论勾绞's 口舌 / 刑狱, "
            "论丧门吊客's grief) as stress / wellbeing factors, not organ diagnoses. Use each "
            "reading's own 结论 / 现代解读, never generic knowledge. "
            "Also read the 神煞 block's per-pillar injury stars (血刃, 剑锋煞, 羊刃 / 飞刃, 自缢煞, "
            "天屠煞, 病符) and 作用 interactions: 六冲 (map the clashed branch to its organ, the "
            "pillar to its life stage), 刑 (chronic ailments), harms, breaks; voidness on a palace. "
            "Pillar-to-life-stage timing for when concerns surface (year = childhood, month = "
            "youth, day = midlife, hour = old age). "
            "For the care group: the element that most needs strengthening (the weak or most "
            "stressed link) and the chart's heat-cold balance translate into concrete, ordinary "
            "wellbeing habits — rest rhythm, the warmth or coolness of diet, the season to take "
            "extra care, the organ system to protect — never medical prescriptions or named drugs."
        ),
    ),
]
