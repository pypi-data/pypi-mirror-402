"""
 * @file   : rollingWindow.py
 * @time   : 14:42
 * @date   : 2025/3/10
 * @mail   : 9727005@qq.com
 * @creator: ShanDong Xiedali
 * @company: Less is more.Simple is best!
"""
from BasicLibrary.data.listHelper import ListHelper


class RollingWindow[T:int | float]:
    """
     * @class  : 滑动窗口类
     * @brief  : 对给定数组进行滚动窗口计算移动平均值
    """

    def __init__(self, arr_data: list[T] = []):
        self.data = arr_data

    pass

    def append_data(self, *args: T):
        self.data.extend(args)

    pass

    def get_moving_average(self, window_size: int) -> list[float]:
        return ListHelper.get_moving_average(self.data, window_size)

    pass


pass
