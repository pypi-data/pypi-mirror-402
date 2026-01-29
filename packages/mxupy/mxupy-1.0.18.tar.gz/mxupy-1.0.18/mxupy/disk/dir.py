import os.path
import mxupy as mu
from mxupy import ObjectUtil

def getSubDirs(directory):
    """获取指定目录下的所有子目录列表"""
    subdirs = []
    # os.listdir() 返回目录中的所有文件和目录列表
    for entry in os.listdir(directory):
        # os.path.join用于路径拼接
        full_path = os.path.join(directory, entry)
        # os.path.isdir() 判断是否为目录
        if os.path.isdir(full_path):
            subdirs.append(full_path)
    return subdirs


def getAllSubDirs(directory):
    """递归获取指定目录下的所有子目录"""
    all_subdirs = []
    for root, dirs, files in os.walk(directory):
        for dir in dirs:
            all_subdirs.append(os.path.join(root, dir))
    return all_subdirs


def getFiles(path, level=1):
    ''''' 
    获取一个目录下的所有文件 
    '''
    import win32file
    import win32con
    dirList = []
    fileList = []
    files = os.listdir(path)
    for f in files:
        ff = path + '/' + f
        file_flag = win32file.GetFileAttributesW(ff)
        is_hiden = file_flag & win32con.FILE_ATTRIBUTE_HIDDEN
        is_system = file_flag & win32con.FILE_ATTRIBUTE_SYSTEM
        if (os.path.isdir(ff)):
            if is_hiden or is_system:
                pass
            elif (f[0] == '.'):
                pass
            else:
                dirList.append(f)

        if (os.path.isfile(ff)):

            if is_hiden or is_system:
                pass
            elif (f[0] == '.'):
                pass
            else:
                fileList.append(ff)

    for dl in dirList:
        fileList.extend(getFiles(dl))

    return fileList



