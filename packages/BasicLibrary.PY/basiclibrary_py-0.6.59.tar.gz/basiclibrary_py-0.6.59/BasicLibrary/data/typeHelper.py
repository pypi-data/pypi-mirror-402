"""
 * @file   : typeHelper.py
 * @time   : 19:17
 * @date   : 2023/6/13
 * @mail   : 9727005@qq.com
 * @creator: ShanDong Xiedali
 * @company: HiLand & RainyTop
"""
from typing import Type

from BasicLibrary.data.typeEnum import TypeEnum
from BasicLibrary.data.convertor import Convertor


# TODO:xiedali@20230613 添加其他的各种数据类型
class TypeHelper(object):
    @staticmethod
    def get_type(data):
        return type(data)

    pass

    @staticmethod
    def convert[InType, OutType](input_value: InType, output_type: Type[OutType]) -> OutType:
        return Convertor.change_type(input_value, output_type)

    pass


pass
