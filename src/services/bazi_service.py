from datetime import datetime
from lunar_python import Lunar
from src.astronomer_calculations import (
    shen_sha,
    interactions_gan_zhi_zuo_yong,
    yuan_tian_gang_bone_weight,
    bazi_pillars,
    wu_xing,
    ten_gods_shi_shen,
    na_yin,
    basic_info,
    life_stage_di_shi,
    branch_energy,
    void_xun_kong,
    three_palace_san_yuan,
    embryonic_breath_tai_xi,
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
        self.na_yin = na_yin
        self.basic_info = basic_info
        self.di_shi = life_stage_di_shi
        self.branch_energy = branch_energy
        self.xun_kong = void_xun_kong
        self.san_yuan = three_palace_san_yuan
        self.tai_xi = embryonic_breath_tai_xi

    def analyze_bazi(
        self,
        lunar_birthday: Lunar,
        birth_datetime: datetime,
        latitude: float,
        longitude: float,
        gender: int,
    ) -> dict:
        """Single entry point for complete analysis"""
        result = {
            "basic_info": self.basic_info.get_basic_info(
                birth_datetime, latitude, longitude, gender
            ),
            "bazi": self.bazi_pillars.get_bazi_pillars(lunar_birthday),
            "wu_xing": self.wu_xin.get_wu_xing(lunar_birthday),
            "shen_sha": self.shen_sha.get_shen_sha(lunar_birthday),
            "xun_kong": self.xun_kong.get_xun_kong(lunar_birthday),
            "san_yuan": self.san_yuan.get_san_yuan(lunar_birthday),
            "tai_xi": self.tai_xi.get_tai_xi(lunar_birthday),
            "interactions": self.interactions.get_interactions(lunar_birthday),
            "bone_weight": self.bone_weight.calculate_yuan_tian_gang_bone_weight(
                lunar_birthday
            ),
            "shi_shen": self.shi_shen.get_shi_shen(lunar_birthday),
            "na_yin": self.na_yin.get_na_yin(lunar_birthday),
            "di_shi": self.di_shi.get_di_shi(lunar_birthday),
            "branch_energy": self.branch_energy.get_branch_energy(lunar_birthday),
        }

        return result
