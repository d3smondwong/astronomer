from lunar_python import Lunar
from src.astronomer_calculations import (
    shen_sha,
    interactions_gan_zhi_zuo_yong,
    yuan_tian_gang_bone_weight,
    bazi_pillars,
    wu_xing,
    ten_gods_shi_shen,
)


class BaziService:
    """Orchestrates all BaZi calculations"""

    def __init__(self):

        self.shen_sha = shen_sha
        self.interactions = interactions_gan_zhi_zuo_yong
        self.bone_weight = yuan_tian_gang_bone_weight
        self.bazi_pillars = bazi_pillars
        self.wu_xin = wu_xing
        self.shi_shen = ten_gods_shi_shen

    def analyze_bazi(self, lunar_birthday: Lunar) -> dict:
        """Single entry point for complete analysis"""
        return {
            "bazi": self.bazi_pillars.get_bazi_pillars(lunar_birthday),
            "wu_xing": self.wu_xin.get_wu_xing(lunar_birthday),
            "shen_sha": self.shen_sha.get_shen_sha(lunar_birthday),
            "interactions": self.interactions.get_interactions(lunar_birthday),
            "bone_weight": self.bone_weight.calculate_yuan_tian_gang_bone_weight(
                lunar_birthday
            ),
            "shi_shen": self.shi_shen.get_shi_shen(lunar_birthday),
            # Add luck, pillars, etc.
        }
