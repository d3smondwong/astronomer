# This module defines the bone weights for the Yuan Tian Gang system based on the lunar birthday.

import logging
from src.utils.logging import get_logger

# Mapping of Earthly Branches (地支) to Western hour names
# The 12 earthly branches (地支) are: 子, 丑, 寅, 卯, 辰, 巳, 午, 未, 申, 酉, 戌, 亥
# These map to: Zi, Chou, Yin, Mao, Chen, Si, Wu, Wei, Shen, You, Xu, Hai
ZHI_TO_HOUR_NAME = {
    "子": "Zi",
    "丑": "Chou",
    "寅": "Yin",
    "卯": "Mao",
    "辰": "Chen",
    "巳": "Si",
    "午": "Wu",
    "未": "Wei",
    "申": "Shen",
    "酉": "You",
    "戌": "Xu",
    "亥": "Hai",
}

# Bone weights for years, months, days, and hours based on the Yuan Tian Gang system
YUAN_TIAN_GANG_BONE_WEIGHTS = {
    "years": {
        0: 1.2,
        1: 0.9,
        2: 0.6,
        3: 0.7,
        4: 1.2,
        5: 0.4,
        6: 0.9,
        7: 0.8,
        8: 0.7,
        9: 0.8,
        10: 1.5,
        11: 0.9,
        12: 1.6,
        13: 0.8,
        14: 0.8,
        15: 1.9,
        16: 1.2,
        17: 0.6,
        18: 0.8,
        19: 0.7,
        20: 0.5,
        21: 1.5,
        22: 0.6,
        23: 1.6,
        24: 0.7,
        25: 0.8,
        26: 0.9,
        27: 0.7,
        28: 1.0,
        29: 0.7,
        30: 1.5,
        31: 0.6,
        32: 0.5,
        33: 1.4,
        34: 1.4,
        35: 0.9,
        36: 0.7,
        37: 0.7,
        38: 0.9,
        39: 1.2,
        40: 0.8,
        41: 0.7,
        42: 1.3,
        43: 0.5,
        44: 1.4,
        45: 0.5,
        46: 1.9,
        47: 1.7,
        48: 0.5,
        49: 0.7,
        50: 1.2,
        51: 0.8,
        52: 0.8,
        53: 0.6,
        54: 1.9,
        55: 0.6,
        56: 0.8,
        57: 0.5,
        58: 1.0,
        59: 0.7,
    },
    "months": {
        1: 0.6,
        2: 0.7,
        3: 1.8,
        4: 0.9,
        5: 0.5,
        6: 1.6,
        7: 0.9,
        8: 1.5,
        9: 1.5,
        10: 0.8,
        11: 0.9,
        12: 0.5,
    },
    "days": {
        1: 0.5,
        2: 1.0,
        3: 0.8,
        4: 1.5,
        5: 1.6,
        6: 1.5,
        7: 0.8,
        8: 1.6,
        9: 0.8,
        10: 1.6,
        11: 0.9,
        12: 1.7,
        13: 0.8,
        14: 1.7,
        15: 1.0,
        16: 0.8,
        17: 0.9,
        18: 1.8,
        19: 0.5,
        20: 1.5,
        21: 1.0,
        22: 0.9,
        23: 0.8,
        24: 0.9,
        25: 1.5,
        26: 1.8,
        27: 0.7,
        28: 0.8,
        29: 1.6,
        30: 0.6,
    },
    "hours": {
        "Zi": 1.6,
        "Chou": 0.6,
        "Yin": 0.7,
        "Mao": 1.0,
        "Chen": 0.9,
        "Si": 1.6,
        "Wu": 1.0,
        "Wei": 0.8,
        "Shen": 0.8,
        "You": 0.9,
        "Xu": 0.6,
        "Hai": 0.6,
    },
}

BONE_WEIGHT_POEMS_WITH_ENGLISH = {
    2.1: {
        "poem": "短命非业谓大空，平生灾难事重重；凶祸频临陷苦境，终世困苦事不成。",
        "meaning": "Short-lived and empty; life is filled with repeated disasters and constant hardship.",
    },
    2.2: {
        "poem": "身寒骨冷苦伶仃，此命推来行乞人；劳劳碌碌无度日，终年打拱过平生。",
        "meaning": "Lonely and cold; a life of a beggar. Toiling daily just to survive.",
    },
    2.3: {
        "poem": "鸿雁失群难依靠，家业难继承世间；孤苦伶仃无所依，此命将来终堪怜。",
        "meaning": "Like a lost goose; no family inheritance and no one to rely on. A pitiful fate.",
    },
    2.4: {
        "poem": "别姓移居为上策，离祖成家立业成；终身辛苦勤劳力，老来衣食才盈余。",
        "meaning": "Moving away is best. Leaving your hometown to start a family leads to late-life stability after much toil.",
    },
    2.5: {
        "poem": "此命推来祖业微，门庭冷落家道衰；平生只合出门去，独立成家在外归。",
        "meaning": "Little ancestral inheritance; family home is desolate. Better to leave home and build your own life elsewhere.",
    },
    2.6: {
        "poem": "平生衣禄苦寻求，才得过时又担忧；忙忙碌碌苦中求，何日云开见日头。",
        "meaning": "Struggling for basic needs; as soon as one problem is solved, another arises. Waiting for the sun to break through the clouds.",
    },
    2.7: {
        "poem": "一生作事少商量，难靠祖宗作主张；独马单枪空做去，早年晚岁总凄凉。",
        "meaning": "Doing things without consultation; cannot rely on ancestors. A 'lone wolf' approach leads to a lonely life.",
    },
    2.8: {
        "poem": "一生行事似飘蓬，祖业难传到晚年；若得晚年能守旧，衣食无亏过此生。",
        "meaning": "Life drifts like a weed. Ancestral property is hard to keep, but if you are frugal in old age, you will have enough to eat.",
    },
    2.9: {
        "poem": "初年运限未曾亨，纵有功名在后成；须过四旬方可上，移居改姓始为良。",
        "meaning": "Early life is not prosperous. Success comes after age 40, especially if you move or change your environment.",
    },
    3.0: {
        "poem": "劳劳碌碌苦中求，东奔西走日未休；若得中年人称意，老来又是忧闷多。",
        "meaning": "Toiling and rushing without rest. Even if middle age brings some satisfaction, old age may bring renewed worries.",
    },
    3.1: {
        "poem": "忙忙碌碌苦中求，何日云开见日头；难得祖基家可立，中年衣食渐盈丰。",
        "meaning": "Struggling to find the light. Ancestral support is weak, but middle age brings gradual abundance in food and clothing.",
    },
    3.2: {
        "poem": "初年运限事难成，纵有财源在后程；须过中年方可上，移居改姓始为良。",
        "meaning": "Early efforts fail to bear fruit. Wealth comes later in life, particularly after middle age and through relocation.",
    },
    3.3: {
        "poem": "早年做事事难成，百计徒劳枉费心；半世自如流水去，后来运到得黄金。",
        "meaning": "Early plans are in vain. Half of life flows away like water, but eventually, your luck turns to gold.",
    },
    3.4: {
        "poem": "此命福气果如何，僧道门中衣禄多；离祖出家方为妙，终生清净不奔波。",
        "meaning": "What is this fortune? It points toward a religious or spiritual life. Leaving the secular world brings peace.",
    },
    3.5: {
        "poem": "生平福量不周全，祖业难根立地难；离祖成家为上策，骨肉亲朋不得力。",
        "meaning": "Fortune is incomplete; family roots are shallow. Leaving home is the best strategy as relatives aren't helpful.",
    },
    3.6: {
        "poem": "不须劳碌过平生，独自成家福不轻；早有财星常照临，任君左右到天明。",
        "meaning": "No need for extreme toil; you are capable of building a wealthy home. Wealth stars shine on you early on.",
    },
    3.7: {
        "poem": "此命般般事不成，弟兄少力自孤行；虽然祖业须微有，晚景凄凉到老穷。",
        "meaning": "Many things fail to manifest; siblings offer little help. Even with minor inheritance, old age may be difficult.",
    },
    3.8: {
        "poem": "一身骨肉最清高，早入簧门姓氏标；待到年将三十六，蓝衫脱去换红袍。",
        "meaning": "Noble character. You may achieve academic or professional fame early, and by 36, your status rises significantly (red robe).",
    },
    3.9: {
        "poem": "不须劳碌过平生，忙忙碌碌也无成；若遇财源盈满日，如同枯木再逢春。",
        "meaning": "Striving hard yields little, but when the moment of luck arrives, it’s like a dead tree blossoming in spring.",
    },
    4.0: {
        "poem": "平生衣禄是绵长，件件心中自主张；前面风霜多受过，后来必定享安康。",
        "meaning": "A long-lasting steady fortune. You are independent. After weathering early storms, peace and health are guaranteed.",
    },
    4.1: {
        "poem": "此命推来事不同，为人能干异凡庸；中年还有逍遥福，不比前时运未通。",
        "meaning": "A unique and capable person. Middle age brings a life of leisure and freedom, far better than the early years.",
    },
    4.2: {
        "poem": "得宽怀处且宽怀，何必双眉皱不开；若使中年命运济，那时名利一齐来。",
        "meaning": "Be patient and open-minded. When middle-age luck arrives, fame and fortune will come together.",
    },
    4.3: {
        "poem": "为人心性最聪明，做事轩昂近贵人；衣禄一生天数定，不须劳碌过平生。",
        "meaning": "Very intelligent and carry yourself with dignity. You attract influential people. Your comfortable life is predestined.",
    },
    4.4: {
        "poem": "万事由天莫苦求，须知福禄命里收；少壮功夫终有望，晚年荣华更无忧。",
        "meaning": "Everything is up to Heaven; don't force it. Youthful efforts pay off, leading to a glorious and worry-free old age.",
    },
    4.5: {
        "poem": "福禄丰盈万事全，一身荣耀显双亲；名扬威振人钦敬，处世扬名富贵全。",
        "meaning": "Abundant fortune and honor. You bring glory to your parents. Highly respected and famous for your wealth and character.",
    },
    4.6: {
        "poem": "东西南北尽皆通，出姓移居更觉隆；衣禄无亏天数定，中年晚景一般同。",
        "meaning": "Success in all directions. Moving home brings even more prosperity. Fortune is steady from middle to old age.",
    },
    4.7: {
        "poem": "此命推来旺末年，妻荣子贵自怡然；平生原有滔滔福，可有财源若水泉。",
        "meaning": "Fortune peaks in the later years. Wife and children bring honor. Wealth flows like a spring throughout life.",
    },
    4.8: {
        "poem": "幼年运道未曾亨，苦过初年福禄盈；勤俭持家宜守己，晚年衣食更丰盈。",
        "meaning": "Early years are rough, but luck fills up later. Frugality and diligence lead to an abundant old age.",
    },
    4.9: {
        "poem": "此命推来福不轻，自成自立显门庭；从来办事亲朋冷，到后衣食更有余。",
        "meaning": "A weighty fortune. You are self-made. Though relatives were cold at first, you will end up with more than enough.",
    },
    5.0: {
        "poem": "为利为名终日劳，中年福禄也多遭；老来福德更昌盛，不须劳碌过平生。",
        "meaning": "Working for fame and gain. Middle age has ups and downs, but old age is prosperous and peaceful.",
    },
    5.1: {
        "poem": "一世荣华事事通，不须劳碌自亨通；弟兄叔侄皆如意，家业成时福禄宏。",
        "meaning": "Lifelong glory. Everything goes smoothly without excessive effort. Family relations are harmonious.",
    },
    5.2: {
        "poem": "一世亨通事事能，不须劳碌自然能；家族荣华有余庆，安享晚年到老终。",
        "meaning": "Versatile and naturally successful. The family enjoys surplus happiness, and you enjoy a peaceful end.",
    },
    5.3: {
        "poem": "此格推来气象真，兴家立业在其中；一生衣食安排定，福禄双全天福人。",
        "meaning": "A truly grand fate. You are destined to build a great estate and family. Truly blessed by Heaven.",
    },
    5.4: {
        "poem": "此格推来气象真，兴家立业在其中；一生衣食安排定，福禄双全天福人。",
        "meaning": "A solid fate of building a house and career. Destiny has already arranged your abundance.",
    },
    5.5: {
        "poem": "走马扬鞭争利名，少年做事费筹论；一朝云开见日出，中年衣食更显能。",
        "meaning": "Chasing fame and gain on horseback. Youth is spent planning and striving, but once the clouds clear, middle age is brilliant.",
    },
    5.6: {
        "poem": "此格推来礼义通，一身福禄显门庭；中年财旺家业盛，晚景荣华富贵真。",
        "meaning": "Well-versed in manners and justice. Middle age sees peak wealth, and old age is truly rich and honorable.",
    },
    5.7: {
        "poem": "福禄盈盈万事全，一身荣耀显双亲；名扬威振人钦敬，处世扬名富贵全。",
        "meaning": "Overflowing luck. You bring great honor to your lineage. Famous, respected, and wealthy.",
    },
    5.8: {
        "poem": "平生衣禄苦寻求，才得过时又担忧；若使中年命运济，那时名利一齐来。",
        "meaning": "You search hard for fortune early on. Once luck turns in middle age, both fame and profit arrive at once.",
    },
    5.9: {
        "poem": "细推此格妙且清，必定才高满学问；甲第榜头有名声，一生衣禄自安稳。",
        "meaning": "A refined and clear fate. High intelligence and academic achievement. Your name appears on the honor rolls; life is stable.",
    },
    6.0: {
        "poem": "一世荣华事事通，不须劳碌自亨通；弟兄叔侄皆如意，家业成时福禄宏。",
        "meaning": "Universal success and glory. No hard labor required. Wealth and family thrive together.",
    },
    6.1: {
        "poem": "不作朝中金榜客，定为世上大财翁；聪明天赋经书熟，名显高门自不同。",
        "meaning": "If not a high-ranking official, then a massive tycoon. Naturally gifted and scholarly; a standout in society.",
    },
    6.2: {
        "poem": "此命生来福不穷，读书必定显亲宗；紫衣金带为卿相，富贵荣华皆自丰。",
        "meaning": "Endless fortune. Education brings honor to ancestors. High-ranking status (purple robes) and natural wealth.",
    },
    6.3: {
        "poem": "命主为官福禄长，得来富贵定非常；名题金塔传后世，定显门庭耀祖光。",
        "meaning": "Destined for high office with lasting luck. Extraordinary wealth. Your name will be remembered for generations.",
    },
    6.4: {
        "poem": "此格威权不可当，紫袍金带坐高堂；荣华富贵谁能及，万古留名姓氏扬。",
        "meaning": "Irresistible authority. Sitting in high halls with gold belts. Unmatched wealth and eternal fame.",
    },
    6.5: {
        "poem": "细推此命福非轻，富贵荣华孰与争；定国安邦成大业，高官厚禄显神明。",
        "meaning": "A massive fortune. None can compete with your prosperity. You serve the nation and achieve greatness.",
    },
    6.6: {
        "poem": "此格人间少有同，极其富贵显高风；太和太岁常照临，福禄双全在命中。",
        "meaning": "Rare among mortals. Extreme wealth and high moral character. Constantly blessed by the stars.",
    },
    6.7: {
        "poem": "此命生来福自宏，田园家业最高隆；平生衣禄盈盈满，一世荣华万事通。",
        "meaning": "Born with grand fortune. Your estates and family business reach the highest peaks. Abundant and successful in all things.",
    },
    6.8: {
        "poem": "富贵由天莫苦求，万家粮米库中收；如今不吃空劳力，老来荣华苦自休。",
        "meaning": "Wealth is heaven-sent. Granaries are full. No need for pointless struggle; glory is assured in your later years.",
    },
    6.9: {
        "poem": "此格推来气象真，兴家立业在其中；一生衣食安排定，福禄双全天福人。",
        "meaning": "A truly auspicious pattern. You are a 'Heaven-Blessed Person' with every detail of life's needs already settled.",
    },
    7.0: {
        "poem": "此命推来福不轻，不须愁虑苦劳心；一生天定衣与禄，富贵荣华过一生。",
        "meaning": "An immense fortune. Do not worry or stress. Your status and wealth are divinely ordained for your whole life.",
    },
    7.1: {
        "poem": "此命生成大不同，公侯卿相在其中；一生自有宵遥福，富贵荣华极品隆。",
        "meaning": "Born fundamentally different. Destiny of dukes and ministers. Enjoy a life of supreme freedom and ultimate honor.",
    },
    7.2: {
        "poem": "此格世界罕有同，十全十美大神通；一生福禄天注定，富贵荣华主圣聪。",
        "meaning": "Rarely seen in the world. Near-perfect fate with great power. Divinely ordained supreme wealth and sagely wisdom.",
    },
}

# 称骨歌 (Prophetic Poem)
BONE_WEIGHT_POEMS = {
    2.1: "短命非业谓大空，平生灾难事重重；凶祸频临陷苦境，终世困苦事不成。",
    2.2: "身寒骨冷苦伶仃，此命推来行乞人；劳劳碌碌无度日，终年打拱过平生。",
    2.3: "鸿雁失群难依靠，家业难继承世间；孤苦伶仃无所依，此命将来终堪怜。",
    2.4: "别姓移居为上策，离祖成家立业成；终身辛苦勤劳力，老来衣食才盈余。",
    2.5: "此命推来祖业微，门庭冷落家道衰；平生只合出门去，独立成家在外归。",
    2.6: "平生衣禄苦寻求，才得过时又担忧；忙忙碌碌苦中求，何日云开见日头。",
    2.7: "一生作事少商量，难靠祖宗作主张；独马单枪空做去，早年晚岁总凄凉。",
    2.8: "一生行事似飘蓬，祖业难传到晚年；若得晚年能守旧，衣食无亏过此生。",
    2.9: "初年运限未曾亨，纵有功名在后成；须过四旬方可上，移居改姓始为良。",
    3.0: "劳劳碌碌苦中求，东奔西走日未休；若得中年人称意，老来又是忧闷多。",
    3.1: "忙忙碌碌苦中求，何日云开见日头；难得祖基家可立，中年衣食渐盈丰。",
    3.2: "初年运限事难成，纵有财源在后程；须过中年方可上，移居改姓始为良。",
    3.3: "早年做事事难成，百计徒劳枉费心；半世自如流水去，后来运到得黄金。",
    3.4: "此命福气果如何，僧道门中衣禄多；离祖出家方为妙，终生清净不奔波。",
    3.5: "生平福量不周全，祖业难根立地难；离祖成家为上策，骨肉亲朋不得力。",
    3.6: "不须劳碌过平生，独自成家福不轻；早有财星常照临，任君左右到天明。",
    3.7: "此命般般事不成，弟兄少力自孤行；虽然祖业须微有，晚景凄凉到老穷。",
    3.8: "一身骨肉最清高，早入簧门姓氏标；待到年将三十六，蓝衫脱去换红袍。",
    3.9: "不须劳碌过平生，忙忙碌碌也无成；若遇财源盈满日，如同枯木再逢春。",
    4.0: "平生衣禄是绵长，件件心中自主张；前面风霜多受过，后来必定享安康。",
    4.1: "此命推来事不同，为人能干异凡庸；中年还有逍遥福，不比前时运未通。",
    4.2: "得宽怀处且宽怀，何必双眉皱不开；若使中年命运济，那时名利一齐来。",
    4.3: "为人心性最聪明，做事轩昂近贵人；衣禄一生天数定，不须劳碌过平生。",
    4.4: "万事由天莫苦求，须知福禄命里收；少壮功夫终有望，晚年荣华更无忧。",
    4.5: "福禄丰盈万事全，一身荣耀显双亲；名扬威振人钦敬，处世扬名富贵全。",
    4.6: "东西南北尽皆通，出姓移居更觉隆；衣禄无亏天数定，中年晚景一般同。",
    4.7: "此命推来旺末年，妻荣子贵自怡然；平生原有滔滔福，可有财源若水泉。",
    4.8: "幼年运道未曾亨，苦过初年福禄盈；勤俭持家宜守己，晚年衣食更丰盈。",
    4.9: "此命推来福不轻，自成自立显门庭；从来办事亲朋冷，到后衣食更有余。",
    5.0: "为利为名终日劳，中年福禄也多遭；老来福德更昌盛，不须劳碌过平生。",
    5.1: "一世荣华事事通，不须劳碌自亨通；弟兄叔侄皆如意，家业成时福禄宏。",
    5.2: "一世亨通事事能，不须劳碌自然能；家族荣华有余庆，安享晚年到老终。",
    5.3: "此格推来气象真，兴家立业在其中；一生衣食安排定，福禄双全天福人。",
    5.4: "此格推来气象真，兴家立业在其中；一生衣食安排定，福禄双全天福人。",
    5.5: "走马扬鞭争利名，少年做事费筹论；一朝云开见日出，中年衣食更显能。",
    5.6: "此格推来礼义通，一身福禄显门庭；中年财旺家业盛，晚景荣华富贵真。",
    5.7: "福禄盈盈万事全，一身荣耀显双亲；名扬威振人钦敬，处世扬名富贵全。",
    5.8: "平生衣禄苦寻求，才得过时又担忧；若使中年命运济，那时名利一齐来。",
    5.9: "细推此格妙且清，必定才高满学问；甲第榜头有名声，一生衣禄自安稳。",
    6.0: "一世荣华事事通，不须劳碌自亨通；弟兄叔侄皆如意，家业成时福禄宏。",
    6.1: "不作朝中金榜客，定为世上大财翁；聪明天赋经书熟，名显高门自不同。",
    6.2: "此命生来福不穷，读书必定显亲宗；紫衣金带为卿相，富贵荣华皆自丰。",
    6.3: "命主为官福禄长，得来富贵定非常；名题金塔传后世，定显门庭耀祖光。",
    6.4: "此格威权不可当，紫袍金带坐高堂；荣华富贵谁能及，万古留名姓氏扬。",
    6.5: "细推此命福非轻，富贵荣华孰与争；定国安邦成大业，高官厚禄显神明。",
    6.6: "此格人间少有同，极其富贵显高风；太和太岁常照临，福禄双全在命中。",
    6.7: "此命生来福自宏，田园家业最高隆；平生衣禄盈盈满，一世荣华万事通。",
    6.8: "富贵由天莫苦求，万家粮米库中收；如今不吃空劳力，老来荣华苦自休。",
    6.9: "此格推来气象真，兴家立业在其中；一生衣食安排定，福禄双全天福人。",
    7.0: "此命推来福不轻，不须愁虑苦劳心；一生天定衣与禄，富贵荣华过一生。",
    7.1: "此命生成大不同，公侯卿相在其中；一生自有宵遥福，富贵荣华极品隆。",
    7.2: "此格世界罕有同，十全十美大神通；一生福禄天注定，富贵荣华主圣聪。",
}


def calculate_yuan_tian_gang_bone_weight(lunar_birthday):
    """
    Calculate the Yuan Tian Gang bone weight based on lunar birthday.

    Args:
        lunar_birthday: A Lunar object with lunar date information
        bone_weights: Dictionary with 'years', 'months', 'days', 'hours' keys containing weight mappings

    Returns:
        A dictionary with breakdown and total bone weight
    """
    logger = get_logger(__name__)

    # 1. Extract Year and map to 0-59 range (60-year sexagenary cycle)
    # Starting reference: 1924 = Index 0 (Jiazi 甲子)
    year = lunar_birthday.getYear()
    year_index = (year - 1924) % 60
    if year_index not in YUAN_TIAN_GANG_BONE_WEIGHTS["years"]:
        raise ValueError(
            f"Year index {year_index} (year {year}) not found in YUAN_TIAN_GANG_BONE_WEIGHTS['years']"
        )
    year_weight = YUAN_TIAN_GANG_BONE_WEIGHTS["years"][year_index]

    # 2. Extract Month (1-12)
    month = lunar_birthday.getMonth()
    if month not in YUAN_TIAN_GANG_BONE_WEIGHTS["months"]:
        raise ValueError(f"Month {month} not found in bone_weights['months']")
    month_weight = YUAN_TIAN_GANG_BONE_WEIGHTS["months"][month]

    # 3. Extract Day (1-30)
    day = lunar_birthday.getDay()
    if day not in YUAN_TIAN_GANG_BONE_WEIGHTS["days"]:
        raise ValueError(f"Day {day} not found in YUAN_TIAN_GANG_BONE_WEIGHTS['days']")
    day_weight = YUAN_TIAN_GANG_BONE_WEIGHTS["days"][day]

    # 4. Extract Hour and convert to Western name
    # Get the earthly branch (Zhi) of the hour from the BaZi eight character
    hour_zhi = lunar_birthday.getEightChar().getTimeZhi()
    if hour_zhi not in ZHI_TO_HOUR_NAME:
        raise ValueError(f"Hour earthly branch '{hour_zhi}' not recognized")
    hour_name = ZHI_TO_HOUR_NAME[hour_zhi]
    if hour_name not in YUAN_TIAN_GANG_BONE_WEIGHTS["hours"]:
        raise ValueError(f"Hour '{hour_name}' not found in bone_weights['hours']")
    hour_weight = YUAN_TIAN_GANG_BONE_WEIGHTS["hours"][hour_name]

    # 5. Calculate total bone weight
    total_weight = year_weight + month_weight + day_weight + hour_weight
    total_weight_rounded = round(total_weight, 1)

    # Look up the corresponding poem
    if total_weight_rounded not in BONE_WEIGHT_POEMS:
        logger.error(
            f"Bone weight {total_weight_rounded} is not within defined poem entries. "
            f"Valid range: 2.1 - 7.2 liang. Lunar birthday: {lunar_birthday.getYear()}-{lunar_birthday.getMonth()}-{lunar_birthday.getDay()}"
        )
    poem = BONE_WEIGHT_POEMS.get(total_weight_rounded, "未找到对应的称骨歌")

    result = {
        "骨重分解": {
            "年": {"农历年": year, "年序": year_index, "骨重": year_weight},
            "月": {"农历月": month, "骨重": month_weight},
            "日": {"农历日": day, "骨重": day_weight},
            "时": {"时辰": hour_zhi + "时", "骨重": hour_weight},
        },
        "总骨重": total_weight_rounded,
        "计算过程": f"{year_weight} + {month_weight} + {day_weight} + {hour_weight} = {total_weight_rounded}",
        "称骨歌": poem,
    }

    return {"袁天罡称骨歌": result}


# --- EXECUTION ---

if __name__ == "__main__":
    import json
    from datetime import datetime
    from lunar_python import Solar
    from src.astronomer_calculations.solar_lunar_time import get_true_solar_time

    # python -m src.astronomer_calculations.yuan_tian_gang_bone_weight

    # Desmond's birthday example
    solar_birthday = Solar.fromYmdHms(1985, 11, 25, 17, 7, 0)
    datetime_birthday = datetime(1985, 11, 25, 17, 7, 0)
    tst_birthday, _ = get_true_solar_time(datetime_birthday, 1.3253, 103.808053)

    print("=" * 60)
    print("阳历生日: " + solar_birthday.toYmdHms())
    print("真太阳时生日: " + tst_birthday.toYmdHms())
    print("=" * 60)

    lunar_birthday = tst_birthday.getLunar()
    result = calculate_yuan_tian_gang_bone_weight(lunar_birthday)

    # Print JSON output
    print("\n```json")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("```\n")
