import os
import random
import string

class Path:
    invalid_file_name_chars = [
        "\x22",
        "\x3c",
        "\x3e",
        "\x7c",
        "\x00",
        "\x01",
        "\x02",
        "\x03",
        "\x04",
        "\x05",
        "\x06",
        "\x07",
        "\x08",
        "\x09",
        "\x0a",
        "\x0b",
        "\x0c",
        "\x0d",
        "\x0e",
        "\x0f",
        "\x10",
        "\x11",
        "\x12",
        "\x13",
        "\x14",
        "\x15",
        "\x16",
        "\x17",
        "\x18",
        "\x19",
        "\x1a",
        "\x1b",
        "\x1c",
        "\x1d",
        "\x1e",
        "\x1f",
        "\x3a",
        "\x2a",
        "\x3f",
        "\x5c",
        "\x2f",
    ]
    invalid_file_path_chars = [
        "\x7c",
        "\x00",
        "\x01",
        "\x02",
        "\x03",
        "\x04",
        "\x05",
        "\x06",
        "\x07",
        "\x08",
        "\x09",
        "\x0a",
        "\x0b",
        "\x0c",
        "\x0d",
        "\x0e",
        "\x0f",
        "\x10",
        "\x11",
        "\x12",
        "\x13",
        "\x14",
        "\x15",
        "\x16",
        "\x17",
        "\x18",
        "\x19",
        "\x1a",
        "\x1b",
        "\x1c",
        "\x1d",
        "\x1e",
        "\x1f",
    ]

    @staticmethod
    def combine(*paths):
        """组合多个路径"""
        return os.path.join(*paths)

    @staticmethod
    def get_file_name(file_path):
        """获取文件名（不包含路径）"""
        return os.path.basename(file_path)

    @staticmethod
    def get_file_name_without_extension(file_path):
        """获取文件名（不包含扩展名）"""
        return os.path.splitext(os.path.basename(file_path))[0]

    @staticmethod
    def get_extension(file_path):
        """获取文件扩展名"""
        return os.path.splitext(file_path)[1]

    @staticmethod
    def get_directory_name(file_path):
        """获取文件的目录名"""
        return os.path.dirname(file_path)

    @staticmethod
    def change_extension(file_path, new_extension):
        """更改文件扩展名"""
        return os.path.splitext(file_path)[0] + new_extension

    @staticmethod
    def is_path_rooted(path):
        """检查路径是否为根路径"""
        return os.path.isabs(path)

    @staticmethod
    def get_temp_path():
        """获取临时文件夹路径"""
        return os.path.join(
            os.path.expanduser("~"), "tmp"
        )  # 也可以使用 tempfile.gettempdir()

    @staticmethod
    def get_full_path(path):
        """获取绝对路径"""
        return os.path.abspath(path)

    @staticmethod
    def has_extension(file_path):
        """检查文件是否有扩展名"""
        return bool(os.path.splitext(file_path)[1])

    @staticmethod
    def get_relative_path(base_path, target_path):
        """获取相对路径"""
        return os.path.relpath(target_path, base_path)

    @staticmethod
    def clean_file_name(file_name, newchar="_"):
        """清理文件名中的无效字符"""
        for char in Path.invalid_file_name_chars:
            file_name = file_name.replace(char, newchar)
        return file_name

    @staticmethod
    def clean_file_path(file_path, newchar="_"):
        """清理文件路径中的无效字符"""
        for char in Path.invalid_file_path_chars:
            file_path = file_path.replace(char, newchar)
        return file_path

    @staticmethod
    def replace_InvalidFileNameChars(base_path, target_path):
        """获取相对路径"""
        return os.path.relpath(target_path, base_path)

    @staticmethod
    def new_rnd_filepath(base_path,length=6):
        """返回同级目录源文件+6位随机名"""
        real_path=os.path.abspath(base_path)
        fp,ext=os.path.splitext(real_path)
        rnd = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
        while os.path.exists(fp+"_"+rnd+ext):
            rnd=''.join(random.choices(string.ascii_letters + string.digits, k=length))
        return fp+"_"+rnd+ext
