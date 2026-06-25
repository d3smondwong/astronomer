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
        guidance=(
            "Tell the story of who this person is at their core — their temperament, how they "
            "think and feel, what drives them, their natural gifts, and the growth edges they "
            "carry. Weave it into a connected portrait, not a list of traits."
        ),
        emphasis=(
            "The day master's element, polarity and overall strength (whether it is supported "
            "by its season, its roots, and the surrounding chart), and its life-stage. "
            "The balance of the five elements — which are strong, which are weak or missing — "
            "as the basis of temperament. The ten-gods on the visible and hidden stems, "
            "especially the dominant influence of the month branch, plus each pillar's na yin. "
            "The classical na-yin temperament readings for each pillar (三命通会_纳音性质) and "
            "the day/hour-pillar verses (三命通会_日时断: 日柱解读 and 时柱解读). Character-type "
            "classical rules (特殊格局 such as 日德 / 八专禄旺 / 财官双美, 论日干格局, 论五行组合, "
            "论正印, the noble-star readings 论太极贵人 / 论天乙贵人 / 论天月德, 释六十甲子). "
            "Personality-shaping spiritual stars across all pillars (文昌 for intellect, "
            "太极贵人 for a philosophical bent, 华盖 for a solitary or artistic streak). "
            "The life palace (命宫) for inner orientation."
        ),
    ),
    Section(
        key="family",
        title="Family (Grandparents, Parents & Siblings)",
        guidance=(
            "Describe this person's family story — the standing and influence of their "
            "grandparents and ancestry, their relationship with their parents, and the bonds "
            "(or distance) with siblings. Tell it as a narrative of where they come from and "
            "how family shapes them."
        ),
        emphasis=(
            "The year pillar (grandparents, ancestry and the early home) and the month pillar "
            "(parents and siblings): their stems and branches, ten-gods, na yin temperament, "
            "and the spiritual stars sitting on each. The relative-stars among the ten gods — "
            "the seal star for the mother and nurture, the wealth star for the father, and the "
            "companion/rob-wealth stars for siblings — with their strength and rooting. "
            "The six-relatives block (六亲) and the classical six-relatives readings "
            "(古籍解读.论六亲: 祖先 / 父母 / 兄弟 / 公父), including the modern interpretations. "
            "Interactions between the year and month pillars (clashes, harms, breaks = friction "
            "with elders or parents) and any voidness on those pillars (distant or absent kin). "
            "Stars of isolation or mourning (华盖 / 孤辰 / 寡宿, 吊客 / 披麻). "
            "The hour-pillar verse (三命通会_日时断.时柱解读) and na-yin reading for descendants "
            "and the later-life household, plus the na-yin temperament readings for the year, "
            "month and hour pillars."
        ),
    ),
    Section(
        key="romance",
        title="Romance",
        guidance=(
            "Tell the story of how this person loves and partners — their relationship style, "
            "the kind of partner who suits them, the temperament of their spouse, and the "
            "shape and timing of significant relationships. Note tendencies, never fixed fate."
        ),
        emphasis=(
            "IMPORTANT — read the gender first: the spouse star is the wealth star (正财 = wife, "
            "偏财) in a male chart, but the authority star (正官 = husband, 七杀) in a female "
            "chart. Foreground that star's strength, root and placement. "
            "The day pillar is the marriage palace: the day branch (配偶宫), its hidden stems "
            "(the concealed spouse star), and its self-seated life-stage. Spiritual stars on the "
            "day pillar (绞煞, 天官贵人 = a spouse of good standing, 桃花 / 红艳 if present, "
            "孤辰 / 寡宿). The classical spouse readings (古籍解读.论六亲: 妻 / 夫, 妻语惬心) with "
            "modern interpretations, and the day-pillar verse (三命通会_日时断.日柱解读). "
            "Interactions touching the day branch — harmony (六合) for a steady marriage, clash "
            "(六冲) for instability, harm/break, and any combination pulling the spouse star "
            "away — plus voidness on the day branch or spouse star (delay or fragility). "
            "The day master's strength versus the spouse star's strength (the balance of the "
            "partnership), relationship-timing stars (桃花 / 红鸾 / 天喜) if present, and the "
            "day-pillar na-yin temperament (三命通会_纳音性质.日柱)."
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
            "across the chart: authority stars (官杀) for management and discipline, "
            "output/expression stars (食伤) for creativity and talent, seal stars (印) for "
            "learning, credentials and mentors, and wealth stars (财) for enterprise and "
            "resources — note their strength so talents are actually usable. "
            "Classical career rules (古籍解读): 论官煞格局 (including 五行官性, which points to a "
            "suitable field — e.g. a wood authority star suits education and culture), "
            "论日干格局, 论禄神 for income stability, and 论驿马 / 论禄马 for mobility, travel and "
            "relocation work. The day/hour-pillar verses (三命通会_日时断) that judge rank, "
            "officialdom and achievement (e.g. 玉带荣身, 主贵). "
            "Spiritual stars: 文昌 / 学堂词馆 (academic and writing gifts), 国印 / 天官 "
            "(officialdom), 华盖 (arts, research, spiritual work), 驿马 (travel-based work). "
            "Vault states (作用.库位状态 — an open vault = access to resources and assets) and "
            "clashes on the month pillar (career volatility); the body palace (身宫) for "
            "achievement orientation; and the month-pillar na-yin temperament "
            "(三命通会_纳音性质.月柱)."
        ),
    ),
    Section(
        key="wealth",
        title="Wealth",
        guidance=(
            "Tell the story of this person's relationship with money and resources — how wealth "
            "tends to come to them, whether through steady income or windfall and enterprise, "
            "their capacity to hold and grow it, and the timing of financial gain. Note "
            "tendencies, not guarantees."
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
            "wealth and accumulated assets. The day/hour-pillar verses (三命通会_日时断) on "
            "prosperity and livelihood (e.g. 活计生涯, 昌荣 versus 只许平), the hour-pillar na yin "
            "(三命通会_纳音性质.时柱) and the day-pillar na-yin fortune commentary (e.g. 富贵寿考)."
        ),
    ),
    Section(
        key="health",
        title="Health",
        guidance=(
            "Describe this person's constitution and the areas of health they should care for — "
            "which body systems may be vulnerable, the rhythm of their vitality, and the life "
            "stages where health concerns tend to surface. Frame it as guidance for wellbeing, "
            "not prediction of illness."
        ),
        emphasis=(
            "Five-element imbalance is the core frame: which element is excessive, weak or "
            "missing (its strength state), pointing to the organ systems to care for — wood: "
            "liver and gallbladder; fire: heart and small intestine; earth: spleen and stomach; "
            "metal: lungs and large intestine; water: kidneys and bladder. "
            "Constitution: a weak or out-of-season day master means lower baseline vitality; the "
            "day master's life-stage hitting its low points (illness/death/tomb/extinction "
            "stages) marks vitality dips; the birth solar-term/season indicates heat-cold "
            "balance needs. Spiritual stars of injury and risk (血刃 for blood/injury/surgery, "
            "剑锋煞 for cuts and accidents, 羊刃 / 飞刃, 自缢煞, 童子煞, 天屠煞, 病符) where "
            "present. Interactions (作用): clashes (六冲 — map the clashed branch to its organ "
            "and the pillar to its life stage for sudden events), punishments (刑 for chronic "
            "ailments), harms and breaks; voidness on a palace (weakness there). "
            "Pillar-to-life-stage timing for when concerns surface (year = childhood, month = "
            "youth, day = midlife, hour = old age)."
        ),
    ),
]
