"""
 * @file   : imageMate.py
 * @time   : 11:46
 * @date   : 2023/10/29
 * @mail   : 9727005@qq.com
 * @creator: ShanDong Xiedali
 * @company: HiLand & RainyTop
"""
import base64
from os import PathLike
from pathlib import Path

from PIL import Image

from BasicLibrary.data.mediaHelper import MediaHelper


class ImageHelper:
    @staticmethod
    def get_base64(image_file_full_name: PathLike | str):
        """
        获取图片的base64编码
        :param image_file_full_name:
        :return:
        """
        with open(image_file_full_name, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        pass

        return image_data

    pass

    @classmethod
    def is_image_type(cls, file_full_name: str | Path):
        return MediaHelper.determine_is_image(file_full_name)

    pass

    @staticmethod
    def get_size(image_full_path: str | Path) -> tuple[int, int]:
        """
        获取图片的尺寸，返回一个元组:（width, height）
        :param image_full_path:
        :return:一个元组:（width, height）
        """
        image = Image.open(image_full_path)
        return image.size

    pass

    @staticmethod
    def get_dpi(image_full_path: str | Path) -> tuple[int, int]:
        """
        获取图片的dpi解析度（每英寸的点数），返回一个元组:（width解析度, height解析度）
        :param image_full_path:
        :return:一个元组:（width解析度, height解析度）
        """
        image = Image.open(image_full_path)

        # 获取图片的DPI信息
        dpi = image.info.get('dpi')

        if dpi:
            return dpi
        else:
            return 0, 0

    pass

    @classmethod
    def get_format(cls, image_full_path: str | Path) -> str | None:
        """
        获取图片的格式（如果是非图片格式，返回None）
        :param image_full_path:
        :return:
        """
        if cls.is_image_type(image_full_path):
            image = Image.open(image_full_path)
            return image.format.lower()
        pass

        return None

    pass

    @classmethod
    def get_image_type_name(cls, file_full_name: str | Path):
        """
        获取图片的类型名称（如果是非图片格式，返回None）（get_format的别名）
        :param file_full_name:
        :return:
        """
        return cls.get_format(file_full_name)

    pass

    @classmethod
    def what(cls, file_full_name: str | Path):
        """
        获取图片的类型名称（如果是非图片格式，返回None）（get_format的别名）
        :param file_full_name:
        :return:
        """
        return cls.get_format(file_full_name)

    pass

    @staticmethod
    def get_common_extension_names(return_type: str = "tuple"):
        """
        获取常见图片格式的扩展名
        :param return_type: 返回类型，默认为tuple，可选为list
        :return:
        """
        all_list = ['.webp', '.bmp', '.dib', '.png', '.jpg', '.jpeg', '.pbm', '.pgm', '.ppm', '.tif', '.tiff']

        if return_type == "tuple":
            return tuple(all_list)
        pass

        return all_list


pass
