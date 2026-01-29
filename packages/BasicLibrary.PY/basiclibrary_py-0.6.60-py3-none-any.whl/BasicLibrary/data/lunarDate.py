"""
 * @file   : lunarDate.py
 * @time   : 下午3:30
 * @date   : 2024/4/15
 * @mail   : 9727005@qq.com
 * @creator: ShanDong Xiedali
 * @company: HiLand & RainyTop
"""
from datetime import datetime

from zhdate import ZhDate

from BasicLibrary.data.chineseData import ChineseData
from BasicLibrary.data.regexHelper import RegexHelper


class LunarDate:
    def __init__(self, solar_year=None, solar_month=None, solar_day=None):
        if not solar_year:
            solar_year = datetime.year
        pass

        if not solar_month:
            solar_month = datetime.month
        pass

        if not solar_day:
            solar_day = datetime.day
        pass

        # lunar_date = sxtwl.fromSolar(solar_year, solar_month, solar_day)
        # lunar_year = lunar_date.getYearGZ()

        # self.isLunarLeap = lunar_date.isLunarLeap()
        # self.year = ChineseData.TianGan[lunar_year.tg] + ChineseData.DiZhi[lunar_year.dz]
        # self.month = ChineseData.YueMing[lunar_date.getLunarMonth() - 1]
        # self.day = ChineseData.RiMing[lunar_date.getLunarDay() - 1]

        target_solar_date = datetime(solar_year, solar_month, solar_day)
        lunar_date = ZhDate.from_datetime(target_solar_date)

        self.isLunarLeap = lunar_date.leap_month
        self.month = ChineseData.YueMing[lunar_date.lunar_month - 1]
        self.day = ChineseData.RiMing[lunar_date.lunar_day - 1]

        chinese_string = lunar_date.chinese()
        chinese_year = LunarDate.__calc_lunar_year(chinese_string)

        if chinese_year:
            self.year = chinese_year
        else:
            self.year = lunar_date.lunar_year

        self.SX = LunarDate.__parse_SX(chinese_string)

    pass

    @staticmethod
    def __parse_SX(lunar_chinese_string: str):
        regex = r'\((.*)年\)'
        result = RegexHelper.get_matched_items(lunar_chinese_string, regex)
        if not result:
            return ""
        pass

        return result[0]

    pass

    @staticmethod
    def __calc_lunar_year(lunar_chinese_string: str):
        if not lunar_chinese_string:
            return None
        pass

        year_string = lunar_chinese_string.split(' ')
        if not year_string or len(year_string) < 2:
            return None  # 格式错误
        pass

        year_string = year_string[1]
        year_string = year_string.replace('年', '')

        return year_string

    pass

    def __str__(self):
        return self.get_string()

    def get_string(self, formatter: str = "{yy}年{mm}月{dd}日"):
        """
        获取格式化的农历日期字符串
        :param formatter: 格式化字符串，支持的格式化参数有：yy(年), mm(月), dd(日)
        :return:
        """
        month = self.month
        if self.isLunarLeap:
            month = "闰" + self.month
        pass

        return formatter.format(yy=self.year, mm=month, dd=self.day)
