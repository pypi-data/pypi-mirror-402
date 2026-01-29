"""
 * @file   : LoopHelper.py
 * @time   : 16:34
 * @date   : 2025/4/1
 * @mail   : 9727005@qq.com
 * @creator: ShanDong Xiedali
 * @company: Less is more.Simple is best!
"""
import itertools


class LoopHelper(object):
    @staticmethod
    def zip(*args: list):
        """
        用于将多个列表按照相同的索引位置进行合并，返回一个新的列表
        :param args: 多个列表
        :return: 合并后的列表
        """
        return list(zip(*args))

    pass

    @staticmethod
    def product(*args: list):
        """
        用于生成笛卡尔积，返回一个新的list列表(列表中的元素是元组(tuple)，元组中的元素是多层循环中的每一个值)
        :param args:
        :return:
        """
        return list(itertools.product(*args))

    pass


pass
