"""
 * @file   : numberHelper.py
 * @time   : 15:17
 * @date   : 2022/3/16
 * @mail   : 9727005@qq.com
 * @creator: ShanDong Xiedali
 * @company: HiLand & RainyTop
"""
import math

from BasicLibrary.data.convertor import Convertor
from BasicLibrary.data.listHelper import ListHelper


class NumberHelper(object):
    """

    """

    def __init__(self):
        pass

    @classmethod
    def get_division_result_before_dot(cls, whole, by):
        """
        获取商数结果中的整数部分
        :param whole:
        :param by:
        :return:
        """
        return cls.__get_division_result_by_math(whole, by)[1]

    pass

    @classmethod
    def get_division_result_after_dot(cls, whole, by):
        """
        获取商数结果中的小数部分
        :param whole:
        :param by:
        :return:
        """
        return cls.__get_division_result_by_math(whole, by)[0]

    pass

    @staticmethod
    def __get_division_result_by_math(whole, by):
        if by == 0:
            return False
        else:
            return math.modf(whole / by)
        pass

    pass

    @staticmethod
    def get_division_result(whole, by, precision_width=2):
        """
        获取带精度小数的商数
        :param whole:
        :param by:
        :param precision_width:精度的长度（默认 2位宽度）
        :return:
        """
        return round(whole / by, precision_width)

    pass

    @staticmethod
    def int_to_x(int_value: int, number_system_type: int):
        """
        将整数转换为其他进制
        :param {int} int_value:  整数数值
        :param {int} number_system_type: 进制类型,目前支持 2: 二进制, 8: 八进制, 16: 十六进制
        :return {str}: 转换后的进制数值字符串
        """
        return Convertor.int_to_x(int_value, number_system_type)

    pass

    @staticmethod
    def x_to_int(x_value: str, number_system_type: int):
        """
        将其他进制的数值转换为整数
        :param x_value: 原进制数值字符串
        :param number_system_type: 原进制类型,目前支持 2: 二进制, 8: 八进制, 16: 十六进制
        :return:  转换后的整数数值
        """
        return Convertor.x_to_int(x_value, number_system_type)

    pass

    @staticmethod
    def convert_base(number_string: str, from_base: int, to_base: int):
        """
        进制转换
        :param number_string: 待转换的数字字符串
        :param from_base: 原进制
        :param to_base: 目标进制
        :return: 转换后的数字字符串
        """
        return Convertor.convert_base(number_string, from_base, to_base)

    pass

    @staticmethod
    def get_moving_average[T:int | float](array_data: list[T], window_size) -> list[float]:
        """
        计算移动平均值
        :param array_data: 待计算的数组
        :param window_size: 窗口大小
        :return: 移动平均值数组
        """
        return ListHelper.get_moving_average(array_data, window_size)


pass
