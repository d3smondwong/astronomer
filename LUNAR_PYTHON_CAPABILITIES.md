# lunar-python Library Capabilities Analysis

## Quick Summary: What's Available vs What's Custom

| Feature | Available | Source | Status |
|---------|-----------|--------|--------|
| **Stem → Element (天干→五行)** | ✅ YES | `LunarUtil.WU_XING_GAN` | Ready to use |
| **Branch → Element (地支→五行)** | ✅ YES | `LunarUtil.WU_XING_ZHI` | Ready to use |
| **DI_SHI (地势/12生)** | ❌ NO | Custom in EightChar | Must stay custom |
| **Hidden Stems (藏干)** | ✅ YES | `EightChar.getXxxHideGan()` | Ready to use |
| **Xun/XunKong (旬/旬空)** | ✅ YES | `LunarUtil.getXun/Kong()` | Ready to use |
| **Seasonal States (旺/相/囚/休/死)** | ❌ NO | Custom in your code | Must stay custom |
| **Nayin (纳音)** | ✅ YES | `LunarUtil.NAYIN` | Ready to use |
| **ShiShen (十神)** | ✅ YES | `LunarUtil.SHI_SHEN` lookup | Ready to use |

---

## 1. STEM → ELEMENT MAPPING

### Available in LunarUtil
```python
LunarUtil.WU_XING_GAN = {
    "甲": "木", "乙": "木",
    "丙": "火", "丁": "火",
    "戊": "土", "己": "土",
    "庚": "金", "辛": "金",
    "壬": "水", "癸": "水"
}
```

**How to use:**
```python
element = LunarUtil.WU_XING_GAN.get(stem_char)  # Returns: "木", "火", "土", "金", or "水"
```

**Polarity (阳/阴):**
- Stems are stored in `LunarUtil.GAN` tuple: ("", "甲", "乙", ..., "癸")
- Even indices (甲丙戊庚壬) = Yang (阳)
- Odd indices (乙丁己辛癸) = Yin (阴)

---

## 2. BRANCH → ELEMENT MAPPING

### Available in LunarUtil
```python
LunarUtil.WU_XING_ZHI = {
    "寅": "木", "卯": "木",
    "巳": "火", "午": "火",
    "辰": "土", "丑": "土", "戌": "土", "未": "土",
    "申": "金", "酉": "金",
    "亥": "水", "子": "水"
}
```

**How to use:**
```python
element = LunarUtil.WU_XING_ZHI.get(branch_char)
```

**Polarity:**
- Branches in `LunarUtil.ZHI`: ("", "子", "丑", ..., "亥")
- Even indices = Yang
- Odd indices = Yin

---

## 3. HIDDEN STEMS (藏干)

### Available via EightChar methods

```python
eight_char = lunar.getEightChar()

# Each method returns a LIST of hidden stems (1-3 elements)
year_hidden = eight_char.getYearHideGan()     # e.g., ["甲", "丙", "戊"]
month_hidden = eight_char.getMonthHideGan()   # e.g., ["己", "癸", "辛"]
day_hidden = eight_char.getDayHideGan()       #
time_hidden = eight_char.getTimeHideGan()     #
```

### Also Available via LunarUtil Lookup

```python
LunarUtil.ZHI_HIDE_GAN = {
    "子": ["癸"],
    "丑": ["己", "癸", "辛"],
    "寅": ["甲", "丙", "戊"],
    "卯": ["乙"],
    # ... etc for all 12 branches
}

# Use it to unpack hidden stems:
hidden = LunarUtil.ZHI_HIDE_GAN.get("寅")  # Returns: ["甲", "丙", "戊"]
ben_qi = hidden[0] if hidden else None     # Primary: "甲"
zhong_qi = hidden[1] if len(hidden) > 1 else None  # Middle: "丙"
yu_qi = hidden[2] if len(hidden) > 2 else None     # Residual: "戊"
```

**Note:** Your `bazi_pillars.py` already uses this correctly with `_hidden_stems()` function.

---

## 4. DI_SHI (地势) / 12 LIFE STAGES — NOT IN LunarUtil ❌

### NOT Available in lunar-python Library
The library **does NOT** provide a direct mapping for 地势 (the 12 life stages: 长生, 沐浴, 冠带, etc.)

### How EightChar Computes It
```python
# Inside EightChar class
CHANG_SHENG = ("长生", "沐浴", "冠带", "临官", "帝旺", "衰", "病", "死", "墓", "绝", "胎", "养")
__CHANG_SHENG_OFFSET = {
    "甲": 1, "丙": 10, "戊": 10, "庚": 7, "壬": 4,
    "乙": 6, "丁": 9, "己": 9, "辛": 0, "癸": 3
}

def __getDiShi(self, zhi_index):
    """Computes 地势 based on day stem + branch polarity"""
    index = self.__CHANG_SHENG_OFFSET.get(self.getDayGan()) + \
            (zhi_index if self.getDayGanIndex() % 2 == 0 else -zhi_index)
    if index >= 12: index -= 12
    if index < 0: index += 12
    return EightChar.CHANG_SHENG[index]
```

**Methods available:**
```python
year_di_shi = eight_char.getYearDiShi()      # Returns: "长生", "沐浴", etc.
month_di_shi = eight_char.getMonthDiShi()
day_di_shi = eight_char.getDayDiShi()
time_di_shi = eight_char.getTimeDiShi()
```

**Your workspace:** You have custom `get_di_shi()` in `cycle_di_shi.py` — **keep it custom**, as it's more flexible.

---

## 5. XUN / XUN_KONG (旬 / 旬空 - Void Stems)

### Available in LunarUtil

```python
LunarUtil.XUN = ("甲子", "甲戌", "甲申", "甲午", "甲辰", "甲寅")
LunarUtil.XUN_KONG = ("戌亥", "申酉", "午未", "辰巳", "寅卯", "子丑")

# Utility functions
xun = LunarUtil.getXun("甲子")          # Returns: "甲子" (which xun group)
xun_kong = LunarUtil.getXunKong("甲子") # Returns: "戌亥" (void branches)
xun_index = LunarUtil.getXunIndex("甲子") # Returns: 0-5
```

**How lunar-python determines Xun:**
- Takes stem index and branch index
- Calculates difference: `(stem_index - branch_index) / 2`
- Maps to one of 6 xun groups

**Usage in your code:**
```python
xun = LunarUtil.getXun(bazi.getYear())
xun_kong = LunarUtil.getXunKong(bazi.getYear())
```

---

## 6. SEASONAL STRENGTH STATES (旺/相/囚/休/死) — NOT IN LunarUtil ❌

### NOT Available in lunar-python Library
The library provides **ZERO** information about seasonal strength states.

### What Your Code Does (Custom)
In `day_master.py` and `wu_xing.py`, you have:

```python
_SEASONAL_TABLE: dict = {
    "spring": {
        Element.WOOD: "旺",
        Element.FIRE: "相",
        Element.EARTH: "死",
        Element.METAL: "囚",
        Element.WATER: "休",
    },
    "summer": {
        Element.FIRE: "旺",
        # ... etc
    },
    # ... autumn, winter
}
```

This mapping **must stay custom** because:
1. lunar-python doesn't provide seasonal factors
2. Your implementation is sophisticated (includes climate, needs, state descriptions)
3. The 旺相休囚死 system is core to your BaZi engine

---

## 7. NAYIN (纳音) — 5-ELEMENT SOUNDS

### Available in LunarUtil

```python
LunarUtil.NAYIN = {
    "甲子": "海中金",
    "甲午": "沙中金",
    "丙寅": "炉中火",
    # ... 60 GanZhi pairs with their sounds
}

# Usage
nayin = LunarUtil.NAYIN.get("甲子")  # Returns: "海中金"
```

**Methods:**
```python
year_nayin = eight_char.getYearNaYin()
month_nayin = eight_char.getMonthNaYin()
day_nayin = eight_char.getDayNaYin()
time_nayin = eight_char.getTimeNaYin()
```

---

## 8. SHI SHEN (十神) — TEN GODS

### Available via LunarUtil

```python
LunarUtil.SHI_SHEN = {
    "甲甲": "比肩",
    "甲乙": "劫财",
    "甲丙": "食神",
    # ... all 100 stem pairs
}

# Lookup pattern: DayMaster_Gan + Target_Gan
shi_shen = LunarUtil.SHI_SHEN.get(day_gan + target_gan)
```

**EightChar Methods:**
```python
# For stems
year_shi_shen_gan = eight_char.getYearShiShenGan()      # Returns: "比肩", etc.
month_shi_shen_gan = eight_char.getMonthShiShenGan()
day_shi_shen_gan = eight_char.getDayShiShenGan()        # Always "日主"
time_shi_shen_gan = eight_char.getTimeShiShenGan()

# For hidden stems in branches (returns list)
year_shi_shen_zhi = eight_char.getYearShiShenZhi()      # e.g., ["偏印", "七杀", "正官"]
month_shi_shen_zhi = eight_char.getMonthShiShenZhi()
day_shi_shen_zhi = eight_char.getDayShiShenZhi()
time_shi_shen_zhi = eight_char.getTimeShiShenZhi()
```

---

## 9. OTHER AVAILABLE MAPPINGS

### Wu Xing Related
```python
LunarUtil.LU = {
    "甲": "寅", "乙": "卯", ...,  # stem → lu position (禄位)
}
```

### Nayin/Complex
```python
LunarUtil.SHENG_XIAO = ("鼠", "牛", ..., "猪")  # Zodiac animals
```

---

## 10. EightChar OBJECT METHODS SUMMARY

### Year Pillar
- `getYear()` → "乙亥"
- `getYearGan()`, `getYearZhi()`
- `getYearHideGan()` → ["甲", "丙", "戊"]
- `getYearWuXing()` → "木水"
- `getYearNaYin()` → "海中金"
- `getYearShiShenGan()`, `getYearShiShenZhi()`
- `getYearDiShi()` → "长生"

### Month Pillar (same pattern)
- `getMonth()`, `getMonthGan()`, `getMonthZhi()`
- `getMonthHideGan()`, `getMonthWuXing()`, `getMonthNaYin()`
- `getMonthShiShenGan()`, `getMonthShiShenZhi()`
- `getMonthDiShi()`

### Day Pillar (same pattern)
- `getDay()`, `getDayGan()`, `getDayZhi()`
- `getDayHideGan()`, `getDayWuXing()`, `getDayNaYin()`
- `getDayShiShenGan()`, `getDayShiShenZhi()`
- `getDayDiShi()`

### Time Pillar (same pattern)
- `getTime()`, `getTimeGan()`, `getTimeZhi()`
- `getTimeHideGan()`, `getTimeWuXing()`, `getTimeNaYin()`
- `getTimeShiShenGan()`, `getTimeShiShenZhi()`
- `getTimeDiShi()`

---

## WORKSPACE USAGE PATTERNS

### In `cycle_wu_xing.py`
```python
from lunar_python.util import LunarUtil

# Utility functions wrapping LunarUtil
def get_stem_wu_xing(stem: str) -> dict:
    element = LunarUtil.WU_XING_GAN.get(stem)
    index = LunarUtil.GAN.index(stem)
    polarity = "阳" if index % 2 == 0 else "阴"
    return {"五行": element, "阴阳": polarity}

def get_branch_wu_xing(branch: str) -> dict:
    element = LunarUtil.WU_XING_ZHI.get(branch)
    # ... similar polarity logic
```

### In `bazi_pillars.py`
```python
# Extracts pillars using EightChar methods
gans  = [bazi.getYearGan(),  bazi.getMonthGan(), ...]
zhis  = [bazi.getYearZhi(),  bazi.getMonthZhi(), ...]
hides = [bazi.getYearHideGan(), bazi.getMonthHideGan(), ...]

# Then unpacks hidden stems with custom logic
def _hidden_stems(hide_gan: list) -> tuple:
    stems = list(hide_gan) + ["无", "无", "无"]
    return (stems[0], stems[1], stems[2])
```

### In workspace code (wu_xing.py, day_master.py)
```python
# Uses custom seasonal tables & multipliers
SEASONAL_TABLE  # maps month_branch → element states
SHENG_WANG_TABLE  # maps stem,branch → 12生 stage
STATE_MULT  # 旺=1.0, 相=0.8, 休=0.6, 囚=0.4, 死=0.2
```

---

## WHAT MUST STAY CUSTOM

### ❌ DO NOT Replace (keep custom implementations):

1. **Seasonal strength states** (旺/相/囚/休/死)
   - Your `day_master.py` has sophisticated seasonal tables
   - lunar-python provides nothing for this
   - Your implementation is correct

2. **DI_SHI computation** (14th century Imperial method)
   - EightChar has basic formula, but
   - Your `cycle_di_shi.py` likely has enhancements
   - Keep custom for consistency

3. **Wu Xing dynamics engine** (Qi weighting, interaction scoring)
   - This is 100% your custom logic
   - Much more sophisticated than anything in lunar-python

4. **Ten God (十神) derivations from interactions**
   - lunar-python has basic lookup tables
   - Your interaction system is custom and advanced

---

## RECOMMENDED APPROACH

### ✅ DO Use from lunar-python:
1. Stem/Branch → Element mappings
2. Hidden stems (藏干) from `getXxxHideGan()`
3. Xun/XunKong lookups
4. Nayin lookups
5. Basic ShiShen table for reference

### ✅ AUGMENT with Custom Logic:
1. Seasonal factors (旺相休囚死) — needs domain intelligence
2. DI_SHI (12生) — your system is coherent
3. Interaction weighting system — Ming Dynasty methodology
4. Strength calculations — your professional algorithm

---

## REFERENCE: LunarUtil Static Constants Available

```python
LunarUtil.GAN                    # ("", "甲", "乙", ..., "癸")
LunarUtil.ZHI                    # ("", "子", "丑", ..., "亥")
LunarUtil.WU_XING_GAN            # {gan: element}
LunarUtil.WU_XING_ZHI            # {zhi: element}
LunarUtil.ZHI_HIDE_GAN           # {zhi: [hidden stems]}
LunarUtil.NAYIN                  # {gan_zhi: nayin_sound}
LunarUtil.SHI_SHEN              # {gan1+gan2: shi_shen}
LunarUtil.XUN                    # ("甲子", "甲戌", ...)
LunarUtil.XUN_KONG              # ("戌亥", "申酉", ...)
LunarUtil.JIA_ZI                 # All 60 gan-zhi pairs
LunarUtil.LU                     # {gan: lu_zhi}
LunarUtil.HE_GAN_5               # Heavenly stem combinations
LunarUtil.HE_ZHI_6               # Earthly branch combinations
```

---

## SUMMARY: What Must Stay Custom vs What Can Use lunar-python

**Keep Custom (Your Advantage):**
- Seasonal strength multipliers
- DI_SHI computation formula
- Wu Xing interaction weighting
- Ten God synthesis logic

**Can Safely Delegate to lunar-python:**
- Stem/Branch ↔ Element lookups
- Hidden stems extraction
- Xun/XunKong determination
- Nayin lookups
- Basic ShiShen reference

Your current architecture is sound. The custom implementations give you **domain-specific control** over complex BaZi logic that generic libraries can't provide.
