import os
import fnmatch
import shutil
import re

class Directory:
    @staticmethod
    def exists(directory_path):
        """检查目录是否存在"""
        return os.path.isdir(directory_path)

    @staticmethod
    def create(directory_path):
        """创建目录"""
        os.makedirs(directory_path, exist_ok=True)

    @staticmethod
    def delete(directory_path):
        """删除目录及其内容"""
        if Directory.exists(directory_path):
            os.rmdir(directory_path)  # 仅删除空目录
            # 使用 shutil.rmtree(directory_path) 删除非空目录

    @staticmethod
    def get_files(directory_path, pattern=None, regex_pattern=None):
        """获取目录中的所有文件，并根据模式过滤"""
        files = []
        for f in os.listdir(directory_path):
            file_path = os.path.join(directory_path, f)
            if os.path.isfile(file_path):
                # 根据通配符过滤
                if pattern and not fnmatch.fnmatch(f, pattern):
                    continue
                # 根据正则表达式过滤
                if regex_pattern and not re.match(regex_pattern, f):
                    continue
                files.append(file_path)
        return files

    @staticmethod
    def get_directories(directory_path, pattern=None, regex_pattern=None):
        """获取目录中的所有子目录，并根据模式过滤"""
        dirs = []
        for d in os.listdir(directory_path):
            dir_path = os.path.join(directory_path, d)
            if os.path.isdir(dir_path):
                # 根据通配符过滤
                if pattern and not fnmatch.fnmatch(d, pattern):
                    continue
                # 根据正则表达式过滤
                if regex_pattern and not re.match(regex_pattern, d):
                    continue
                dirs.append(dir_path)
        return dirs

    @staticmethod
    def get_all_subdirectories(directory_path, pattern=None, regex_pattern=None):
        """获取所有子目录（递归），并根据模式过滤"""
        subdirs = []
        for root, dirs, _ in os.walk(directory_path):
            for d in dirs:
                dir_path = os.path.join(root, d)
                # 根据通配符过滤
                if pattern and not fnmatch.fnmatch(d, pattern):
                    continue
                # 根据正则表达式过滤
                if regex_pattern and not re.match(regex_pattern, d):
                    continue
                subdirs.append(dir_path)
        return subdirs
    
    @staticmethod
    def get_all_subfiles(directory_path, pattern=None, regex_pattern=None):
        """获取所有子文件（递归），并根据模式过滤"""
        subfiles = []
        for root, _, files in os.walk(directory_path):
            for f in files:
                file_path = os.path.join(root, f)
                
                # 根据通配符过滤
                if pattern and not fnmatch.fnmatch(f, pattern):
                    continue
                
                # 根据正则表达式过滤
                if regex_pattern and not re.match(regex_pattern, f):
                    continue
                
                subfiles.append(file_path)
        return subfiles
    
    @staticmethod
    def move(source_directory_path, dest_directory_path):
        """移动目录"""
        os.rename(source_directory_path, dest_directory_path)

    @staticmethod
    def copy(source_directory_path, dest_directory_path):
        """复制目录及其内容"""
        shutil.copytree(source_directory_path, dest_directory_path)

    @staticmethod
    def get_directory_size(directory_path):
        """获取目录的大小（字节）"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(directory_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        return total_size