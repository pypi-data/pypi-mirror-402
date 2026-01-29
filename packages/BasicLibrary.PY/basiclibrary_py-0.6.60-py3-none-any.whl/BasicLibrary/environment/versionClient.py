"""
 * @file   : versionMate.py
 * @time   : 14:59
 * @date   : 2025/4/12
 * @mail   : 9727005@qq.com
 * @creator: ShanDong Xiedali
 * @company: Less is more.Simple is best!
"""
import os

from BasicLibrary.data.tomlMate import TomlMate
from BasicLibrary.environment.versionHelper import VersionHelper
from BasicLibrary.projectHelper import ProjectHelper


class VersionClient(object):
    """
    版本管理客户端（具体修改版本号的操作）
    """

    def __init__(self, pyproject_toml_file_full_path: str = "", version_node_path: str = ""):
        """
        初始化版本管理客户端
        :param pyproject_toml_file_full_path: pyproject.toml文件的全路径
        :param version_node_path: version节点的路径
        """
        if not pyproject_toml_file_full_path:
            pyproject_toml_file_full_path = os.path.join(ProjectHelper.get_root_physical_path(), "pyproject.toml")
        pass

        if not version_node_path:
            version_node_path = "project/version"
        pass

        self.pyproject_toml_file_full_path = pyproject_toml_file_full_path
        self.version_node_path = version_node_path
        self.tomlMate = TomlMate(self.pyproject_toml_file_full_path)

    pass

    def get(self):
        """
        获取pyproject.toml中的version节点的值
        :return:
        """
        return self.tomlMate.get(self.version_node_path)

    pass

    def set(self, new_version: str):
        """
        获取pyproject.toml中的version节点的值
        :return:
        """
        return self.tomlMate.set(self.version_node_path, new_version)

    pass

    def increase_patch(self):
        """
        将pyproject.toml中的version节点的patch版本号+1，并保存
        :return:
        """
        old_version = self.tomlMate.get(self.version_node_path)
        new_version = VersionHelper.increase_patch(old_version)
        self.tomlMate.set(self.version_node_path, new_version)

    pass


pass
