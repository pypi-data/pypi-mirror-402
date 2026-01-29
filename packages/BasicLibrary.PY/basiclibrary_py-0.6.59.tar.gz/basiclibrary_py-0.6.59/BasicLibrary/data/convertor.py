"""
 * @file   : convertor.py
 * @time   : 10:40
 * @date   : 2025/3/22
 * @mail   : 9727005@qq.com
 * @creator: ShanDong Xiedali
 * @company: Less is more.Simple is best!
"""
from typing import Type


class Convertor:
    @staticmethod
    def change_type[InType, OutType](input_value: InType, output_type: Type[OutType]) -> OutType:
        """
        变量的数据类型转换
        :param input_value:
        :param output_type:
        :return:
        """
        return output_type(input_value)

    @staticmethod
    def convert_base(number_string: str, from_base: int, to_base: int):
        """
        进制转换
        :param number_string: 待转换的数字字符串
        :param from_base: 原进制（进制类型,目前支持 2: 二进制, 8: 八进制, 16: 十六进制）
        :param to_base: 目标进制（进制类型,目前支持 2: 二进制, 8: 八进制, 16: 十六进制）
        :return: 转换后的数字字符串
        """
        if from_base == to_base:
            return number_string

        # 1. 先将原字符串转换为整数
        int_value = Convertor.x_to_int(number_string, from_base)
        # 2. 再将整数转换为目标进制
        return Convertor.int_to_x(int_value, to_base)

    pass

    @staticmethod
    def int_to_x(int_value: int, number_base: int):
        """
        将整数转换为其他进制
        :param {int} int_value:  整数数值
        :param {int} number_base: 进制类型,目前支持 2: 二进制, 8: 八进制, 16: 十六进制
        :return {str}: 转换后的进制数值字符串
        """
        if number_base == 2:
            return bin(int_value)

        if number_base == 8:
            return oct(int_value)

        if number_base == 16:
            return hex(int_value)

        return int_value

    pass

    @staticmethod
    def x_to_int(x_value: str, number_base: int):
        """
        将其他进制的数值转换为整数
        :param x_value: 原进制数值字符串
        :param number_base: 原进制类型,目前支持 2: 二进制, 8: 八进制, 16: 十六进制
        :return:  转换后的整数数值
        """

        if number_base == 2:
            return int(x_value, 2)

        if number_base == 8:
            return int(x_value, 8)

        if number_base == 16:
            return int(x_value, 16)

        return int(x_value)

    pass


pass
