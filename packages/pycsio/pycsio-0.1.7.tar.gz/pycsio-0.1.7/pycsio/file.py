import os
import shutil
import hashlib
import imagehash
from PIL import Image

class File:
    @staticmethod
    def exists(file_path):
        """检查文件是否存在"""
        return os.path.isfile(file_path)

    @staticmethod
    def read_all_text(file_path):
        """读取文件的所有文本"""
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()

    @staticmethod
    def write_all_text(file_path, content):
        """写入文本到文件"""
        dirpath = os.path.dirname(os.path.abspath(os.path.normpath(file_path)))
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)

    @staticmethod
    def append_all_text(file_path, content):
        """追加文本到文件"""
        dirpath = os.path.dirname(os.path.abspath(os.path.normpath(file_path)))
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
        with open(file_path, 'a', encoding='utf-8') as file:
            file.write(content)

    @staticmethod
    def delete(file_path):
        """删除文件"""
        if File.exists(file_path):
            os.remove(file_path)

    @staticmethod
    def copy(source_file_path, dest_file_path):
        """复制文件"""
        shutil.copy2(source_file_path, dest_file_path)

    @staticmethod
    def move(source_file_path, dest_file_path):
        """移动文件"""
        shutil.move(source_file_path, dest_file_path)

    @staticmethod
    def read_lines(file_path):
        """按行读取文件内容"""
        with open(file_path, 'r', encoding='utf-8') as file:
            return [line.rstrip('\n') for line in file.readlines()]

    @staticmethod
    def write_lines(file_path, lines):
        """写入多个行到文件"""
        dirpath = os.path.dirname(os.path.abspath(os.path.normpath(file_path)))
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
        with open(file_path, 'w', encoding='utf-8') as file:
            for line in lines:
                file.write(line + '\n')

    @staticmethod
    def get_file_size(file_path):
        """获取文件大小（字节）"""
        return os.path.getsize(file_path) if File.exists(file_path) else 0
    
    @staticmethod
    def read_bytes(file_path):
        """读取字节"""
        with open(file_path,"rb") as file:
            return file.read()
    @staticmethod
    def write_bytes(file_path,data):
        """写入字节"""
        dirpath = os.path.dirname(os.path.abspath(os.path.normpath(file_path)))
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
        with open(file_path,"wb") as file:
            file.write(data)
    @staticmethod
    def md5_file(file_path):
        return hashlib.md5(File.read_bytes(file_path)).hexdigest()
    @staticmethod
    def sha1_file(file_path):
        return hashlib.sha1(File.read_bytes(file_path)).hexdigest()
    @staticmethod
    def sha256_file(file_path):
        return hashlib.sha256(File.read_bytes(file_path)).hexdigest()
    @staticmethod
    def sha512_file(file_path):
        return hashlib.sha512(File.read_bytes(file_path)).hexdigest()
    @staticmethod
    def sha3_256_file(file_path):
        return hashlib.sha3_256(File.read_bytes(file_path)).hexdigest()
    @staticmethod
    def phash_image_file(file_path):
        img = Image.open(file_path)
        phash = imagehash.phash(img)
        return str(phash)