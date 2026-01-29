# ------------------------------------------------------------------------------
#  Copyright (c) General. 2022-2026. All rights reserved.
#  @file     : itemListGenerator.py
#  @time     : 22:54:45
#  @date     : 2026/01/20
#  @mail     : 9727005@qq.com
#  @creator  : ShanDong Xiedali
#  @objective: Less is more. Simple is best!
# ------------------------------------------------------------------------------

import os

from BasicLibrary.data.dateTimeHelper import DateTimeHelper
from BasicLibrary.data.regexHelper import RegexHelper
from BasicLibrary.data.listHelper import ListHelper


class ItemListGenerator:

    @classmethod
    def __get_export_info(cls, file_name, file_content):
        """
        从 export default 块中提取 name 或 title 和 description 或 describe
        :param file_name:
        :param file_content:
        :return:
        """
        regex = r"#\s\|:TITLE:{7}\|\s*(.*)"
        match = RegexHelper.get_matched_items(file_content, regex)

        if match:
            name_or_title = match[0]

            # 匹配 description 或 describe
            description_regex = r"#\s\|:DESCRIPTION:\|\s*(.*)"
            description_match = RegexHelper.get_matched_items(file_content, description_regex)
            description_or_describe = description_match[0] if description_match else ""

            description_addon_regex = r"#\s\|\s{13}\|\s*(.*)"
            description_addon_match = RegexHelper.get_matched_items(file_content, description_addon_regex)
            if description_addon_match:
                for _item in description_addon_match:
                    description_or_describe += f"{_item}"
                pass
            pass

            if description_or_describe.strip() == "":
                description_or_describe = "暂无描述"
            pass

            # description_or_describe = description_or_describe.replace("\n", "")

            return {
                "filePath"             : file_name,
                "nameOrTitle"          : name_or_title,
                "descriptionOrDescribe": description_or_describe,
            }
        return None

    @classmethod
    def __process_directory(cls, dir_path: os.PathLike | str, file_extensions: str) -> list:
        """
        遍历目录并处理文件，生成 00.ItemList.md
        :param dir_path:
        :param file_extensions:
        :return:
        """
        if not file_extensions:
            file_extensions = ".py"
        pass

        items = []

        for item in os.listdir(dir_path):
            item_path = os.path.join(dir_path, item)
            if os.path.isdir(item_path):
                # 递归处理子目录
                sub_items = ItemListGenerator.__process_directory(item_path, file_extensions)
                items = ListHelper.merge(items, sub_items)
            elif os.path.isfile(item_path) and item.endswith(file_extensions):
                with open(item_path, 'r', encoding='utf8') as file:
                    content = file.read()
                    export_info = ItemListGenerator.__get_export_info(item_path, content)
                    if export_info:
                        items.append(export_info)
                    pass
                pass
            pass
        pass

        return items

    @classmethod
    def __generate_markdown(cls, dir_path: os.PathLike | str, items: list):
        """
        生成 Markdown 列表
        :param dir_path:
        :param items:
        :return:
        """
        if items is None or len(items) == 0:
            return
        pass

        # markdown_content = "\n".join(
        #     f"- [{item['nameOrTitle']}]({item['filePath']}) - {item['descriptionOrDescribe']}"
        #     for item in items
        # )
        markdown_content = ""
        for _item in items:
            relative_file_path = os.path.relpath(_item['filePath'], dir_path)
            markdown_content += f"- [{_item['nameOrTitle']}]({relative_file_path}) - {_item['descriptionOrDescribe']}\n"
        pass

        # 写入到 00.ITEMLIST.md
        out_file_path = os.path.join(dir_path, "00.ITEMLIST.md")
        markdown_content = f"# 目录\n\n{markdown_content}"
        with open(out_file_path, 'w', encoding='utf8') as out_file:
            out_file.write(markdown_content)
        print(f"已生成 {out_file_path}")

    # 主函数
    @classmethod
    def generate(cls, target_dir, file_extensions):
        try:
            # 确保目标目录存在
            if not os.path.exists(target_dir):
                print(f"❌目录 {target_dir} 不存在，请检查路径！")
                return

            print(f"》》》正在处理目录：{target_dir}")
            items = ItemListGenerator.__process_directory(target_dir, file_extensions)
            ItemListGenerator.__generate_markdown(target_dir, items)
            print("✅✅✅处理完成。")
        except Exception as error:
            print(f"处理过程中发生错误：{error}")


if __name__ == '__main__':
    # 启动主函数，传入目标目录
    _target_directory = "../../"
    _file_extensions = ".py"
    ItemListGenerator.generate(_target_directory, _file_extensions)
    print(f"处理完成时间：{DateTimeHelper.get_standard_string()}")
