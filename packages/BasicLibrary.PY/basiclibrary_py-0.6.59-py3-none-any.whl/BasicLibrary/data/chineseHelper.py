"""
 * @file   : chineseHelper.py
 * @time   : 17:32
 * @date   : 2025/3/12
 * @mail   : 9727005@qq.com
 * @creator: ShanDong Xiedali
 * @company: Less is more.Simple is best!
"""

import re


class ChineseHelper(object):
    @staticmethod
    def extract_chinese_characters(text: str):
        """
        从文本中提取出中文字符
        :param str text: 待提取的整体文本
        :return: 中文字符
        """
        chinese_only = re.sub(r'[^\u4e00-\u9fff]', '', text)
        return chinese_only

    # TODO:xiedali@2025/03/12 有bug，待修复
    @staticmethod
    def get_uppercase_currency(num):
        # 人民币大写单位映射
        num_to_char = ["零", "壹", "贰", "叁", "肆", "伍", "陆", "柒", "捌", "玖"]
        integer_units = ["", "拾", "佰", "仟"]
        section_units = ["", "万", "亿", "万亿"]
        decimal_units = ["角", "分"]

        # 参数校验
        try:
            num = float(num)
        except:
            return "输入不是有效数字"

        if num < 0:
            return "金额不能为负数"
        if num > 9999999999999999.99:
            return "超出转换范围"

        # 分离整数和小数部分（避免浮点误差）
        str_num = "{0:.2f}".format(num)
        integer_part, decimal_part = str_num.split(".") if "." in str_num else (str_num, "00")
        integer_part = integer_part.zfill(1)  # 至少保留一个零

        # 处理整数部分（每4位分段处理）
        rmb_integer = []
        zero_flag = False  # 零标记
        section_count = 0  # 节数（万/亿）

        # 从低位向高位处理（反转字符串）
        reversed_int = integer_part[::-1]
        for i in range(0, len(reversed_int), 4):
            section = reversed_int[i:i + 4][::-1]  # 当前4位
            section_str = ""

            for j, digit in enumerate(section):
                digit = int(digit)
                unit = integer_units[j] if digit != 0 else ""

                if digit == 0:
                    if not zero_flag and section_str:  # 避免连续零
                        section_str = num_to_char[0] + section_str
                        zero_flag = True
                else:
                    section_str = num_to_char[digit] + unit + section_str
                    zero_flag = False

            if section_str:  # 添加节单位（万/亿）
                section_str += section_units[section_count]
                if rmb_integer and rmb_integer[-1].startswith("零"):
                    rmb_integer[-1] = section_str  # 合并高位零
                else:
                    rmb_integer.insert(0, section_str)
                zero_flag = False
            section_count += 1

        # 合并整数部分
        rmb_integer = "".join(rmb_integer).rstrip("零").replace("零零", "零") or "零"
        if rmb_integer == "零" and integer_part != "0":
            rmb_integer = ""

        # 处理小数部分
        rmb_decimal = []
        for i in range(2):
            digit = int(decimal_part[i])
            if digit:
                rmb_decimal.append(num_to_char[digit] + decimal_units[i])

        # 组合结果
        result = []
        if rmb_integer:
            result.append(rmb_integer + "元")
        if rmb_decimal:
            result.append("".join(rmb_decimal))
        else:
            if rmb_integer:
                result.append("整")
            else:
                result.append("零元整")  # 处理0元的情况

        return "".join(result) if any(result) else "零元整"


if __name__ == '__main__':
    # 测试用例
    test_cases = [
        (0, "零元整"),
        (0.12, "壹角贰分"),
        (1024.56, "壹仟零贰拾肆元伍角陆分"),
        (1000000, "壹佰万元整"),
        (123456789012.05, "壹仟贰佰叁拾肆亿伍仟陆佰柒拾捌万玖仟零壹拾贰元零伍分"),
        (6007.14, "陆仟零柒元壹角肆分"),
        (8010.00, "捌仟零壹拾元整"),
        (1000000000000.99, "壹万亿元玖角玖分")
    ]

    for amount, expected in test_cases:
        output = ChineseHelper.get_uppercase_currency(amount)
        print(f"输入: {amount:<18} 预期: {expected:<30} 输出: {output}")
