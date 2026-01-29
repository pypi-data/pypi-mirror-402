from os import PathLike
import filetype

from BasicLibrary.data.mediaTypes import MediaTypes


class MediaHelper:
    @staticmethod
    def get_media_type(file_full_path: str | PathLike):
        """
        获取文件的媒体类型
        :param file_full_path: 文件路径
        :return: MediaTypes 媒体类型
        """
        # 1. 因为fileType库不能判断文本类型，所以需要单独判断文本类型
        txt_file_types = ('.txt', '.text', '.ini', '.conf', '.config', '.cfg', '.inf', '.dat', '.log', '.csv', '.xml',
                          '.json', '.yaml', '.yml', '.properties', '.env', '.env.dist', '.env.example', '.env.test',
                          '.env.dev', '.env.prod', '.md', '.sql')
        if file_full_path.endswith(txt_file_types):
            return MediaTypes.TEXT

        # 2. 调用fileType库获取媒体类型
        kind = filetype.guess(file_full_path)
        if kind is None:
            return MediaTypes.OTHER

        mime_type = kind.mime.split('/')[0]

        for media_type in MediaTypes:
            if media_type.value == mime_type:
                return media_type
            pass
        pass

        # 3. If the mime type is not in the MediaTypes enum, return OTHER
        return MediaTypes.OTHER

    pass

    @staticmethod
    def get_media_type_name(file_full_path: str | PathLike):
        """
        获取文件的媒体类型名称
        :param file_full_path:
        :return: str 媒体类型名称
        """
        return MediaHelper.get_media_type(file_full_path).value

    pass

    @staticmethod
    def determine_is_image(file_full_path: str | PathLike):
        """
        判断文件是否为图片类型
        :param file_full_path: 文件路径
        :return: bool 是否为图片
        """
        return MediaHelper.get_media_type(file_full_path) == MediaTypes.IMAGE

    @staticmethod
    def determine_is_video(file_full_path: str | PathLike):
        """
        判断文件是否为视频类型
        :param file_full_path: 文件路径
        :return: bool 是否为视频
        """
        return MediaHelper.get_media_type(file_full_path) == MediaTypes.VIDEO

    @staticmethod
    def determine_is_audio(file_full_path: str | PathLike):
        """
        判断文件是否为音频类型
        :param file_full_path: 文件路径
        :return: bool 是否为音频
        """
        return MediaHelper.get_media_type(file_full_path) == MediaTypes.AUDIO

    @staticmethod
    def determine_is_text(file_full_path: str | PathLike):
        """
        判断文件是否为文本类型
        :param file_full_path: 文件路径
        :return: bool 是否为文本
        """
        return MediaHelper.get_media_type(file_full_path) == MediaTypes.TEXT

    @staticmethod
    def determine_is_application(file_full_path: str | PathLike):
        """
        判断文件是否为应用程序类型
        :param file_full_path: 文件路径
        :return: bool 是否为应用程序
        """
        return MediaHelper.get_media_type(file_full_path) == MediaTypes.APPLICATION


pass
