import os
import json
import stat
import requests
import mimetypes

import mxupy as mu

from mxupy import IM
from requests.exceptions import RequestException


def removeFileList(filePathList, prefix=""):
    for filePath in filePathList:
        removeFile(filePath, prefix)


def removeFile(filePath, prefix=""):
    rpath = prefix + filePath
    if os.path.exists(rpath):
        os.chmod(rpath, stat.S_IWRITE)
        os.remove(rpath)


def existsFile(filePath):
    if os.path.exists(filePath):
        return True
    return False


def existsFileList(filePathList, prefix=""):
    exists = []
    not_exists = []

    for filePath in filePathList:
        epath = prefix + filePath
        if os.path.exists(epath):
            exists.append(filePath)
        else:
            not_exists.append(filePath)
    return exists, not_exists


def fileParts(filename):
    """
    拆分文件路径，获取文件路径、文件名和扩展名。

    参数:
        filename (str): 要处理的文件路径字符串。

    返回:
        tuple: 文件路径、文件名和小写的扩展名组成的元组。
    """
    (filepath, tempfilename) = os.path.split(filename)
    (shotname, extension) = os.path.splitext(tempfilename)
    return filepath, shotname, extension.lower()


def readAllText(filename):
    """读取文本文件全部内容，注意文件编码必须是 utf-8

    Args:
        filename (string): 文件路径

    Returns:
        string: 文件内容
    """
    r = ''
    f = None
    try:
        f = open(filename, 'r', encoding='utf-8')
        r = f.read()
    except Exception as e:
        print(e)
    finally:
        if f:
            f.close()
    return r


def writeAllText(filename, content, mode='w'):
    """
    将文本内容写入文件。

    参数:
        filename (str): 要写入的文件路径。
        content (str): 要写入的文本内容。
        mode (str, 可选): 文件打开模式，默认为 'w'（写入模式）。
            'r'：只读模式。这是默认的模式。如果文件不存在，会抛出一个FileNotFoundError。
            'w'：写入模式。如果文件存在，会被覆盖。如果文件不存在，会创建一个新文件。
            'a'：追加模式。如果文件存在，写入的内容会被追加到文件末尾。如果文件不存在，会创建一个新文件。
            'b'：二进制模式。用于读写二进制文件。
            't'：文本模式。用于读写文本文件（这是默认的，通常可以省略）。
            '+'：更新模式。用于读写文件。如果与'r'、'w'或'a'结合使用，会打开文件用于更新（读写）。
        结合使用的例子：
            'r+'：读写模式。文件必须存在。
            'w+'：读写模式。如果文件存在，会被覆盖。如果文件不存在，会创建一个新文件。
            'a+'：读写模式。如果文件存在，写入的内容会被追加到文件末尾。如果文件不存在，会创建一个新文件。
            'x'：独占创建模式。用于写入。如果文件已存在，会抛出一个FileExistsError。
            'r+b'：读写二进制模式。文件必须存在。
            'w+b'：读写二进制模式。如果文件存在，会被覆盖。如果文件不存在，会创建一个新文件。
            'a+b'：读写二进制模式。如果文件存在，写入的内容会被追加到文件末尾。如果文件不存在，会创建一个新文件。

    返回:
        str: 写入文件的字符数。
    """
    r = ''
    f = None
    try:
        f = open(filename, mode, encoding='utf-8')
        r = f.write(content)
    except Exception as e:
        print(e)
    finally:
        if f:
            f.close()
    return r


def readJSON(filename):
    f = None
    try:
        f = open(filename, 'r', encoding='utf-8')
        return json.load(f)
    except Exception as e:
        print(e)
    finally:
        if f:
            f.close()


def writeJSON(filename, obj, mode='w'):
    f = None
    try:
        obj = mu.toSerializable(obj)

        f = open(filename, mode, encoding='utf-8')
        json.dump(obj, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(e)
    finally:
        if f:
            f.close()


def readStream(filename):
    """
    读取二进制文件内容。

    参数:
        filename (str): 要读取的文件路径。

    返回:
        bytes: 文件内容。
    """
    r = b''
    f = None
    try:
        f = open(filename, 'rb')
        r = f.read()
    except Exception as e:
        print(e)
    finally:
        if f:
            f.close()

    return r


def writeStream(filename, content):
    """
    将二进制内容写入文件。

    参数:
        filename (str): 要写入的文件路径。
        content (bytes): 要写入的二进制内容。

    返回:
        str: 写入文件的字符数。
    """
    r = 0
    f = None
    try:
        f = open(filename, 'wb')
        r = f.write(content)
    except Exception as e:
        print(e)
    finally:
        if f:
            f.close()
    return r


def clearAllText(filename):
    """
    清空文件内容。

    参数:
        filename (str): 要清空内容的文件路径。
    """
    open(filename, 'w').close()


def appendSuffix(file_path, suffix):
    # 分离文件名和扩展名
    file_dir, file_name_ext = os.path.split(file_path)
    file_name, file_ext = os.path.splitext(file_name_ext)

    # 添加后缀并重新构建文件路径
    new_file_path = os.path.join(file_dir, file_name + suffix + file_ext)

    return new_file_path


def ext_dict():
    """ 文件类型与扩展名的对应关系


    Returns:
        dict: 文件类型与扩展名字典
    """
    ext_dict = {
        'image': ['jpg', 'jpeg', 'png', 'gif', 'tiff', 'tif', 'bmp', 'tga', 'ico', 'webp', 'psd'],
        'document': ['doc', 'docx', 'pdf', 'md', 'markdown', 'txt', 'ppt', 'pptx', 'key', 'odp', 'xls', 'xlsx', 'csv', 'ods'],
        'video': ['mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm', 'm4v'],
        'audio': ['mp3', 'wav', 'ogg', 'flac', 'aac', 'wma', 'm4a'],
        'code': ['js', 'py', 'cs', 'cpp', 'c', 'h', 'hpp', 'java', 'php', 'rb', 'go', 'rs', 'swift', 'html', 'htm', 'shtml'],
        'archive': ['zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz'],
        'database': ['db', 'sqlite', 'sql', 'mdb'],
        'vector': ['ai', 'eps', 'svg'],
        '3dmodel': ['obj', 'fbx', 'stl', 'dae', 'ply'],
        'font': ['otf', 'ttf', 'woff', 'woff2'],
        'executable': ['exe', 'bat', 'sh', 'msi', 'app'],
        'config': ['ini', 'cfg', 'xml', 'yaml', 'yml', 'toml'],
        'virtualmachine': ['vdi', 'vmdk', 'vhd', 'ova', 'ovf'],
        'ebook': ['epub', 'mobi', 'azw', 'azw3', 'djvu']
    }
    return ext_dict


def file_exts_by_type(file_type):
    """ 通过文件类型获取对应的扩展名集

    Args:
        file_type (string): image、video、office 等

    Returns:
        list[string]: 扩展名集
    """
    return ext_dict().get(file_type, 'unknow')


def file_type(filename):
    """获取文件类型

    Args:
        filename (str): 文件名、路径、扩展名(如 .txt)

    Returns:
        str: 类型 image/office/...
    """
    _, _, ext = fileParts(filename)
    if ext == '':
        return 'unknow'
    ext = ext[1:]

    # 将字典的键和值互换
    type_dict = {ext: type for type, exts in ext_dict().items()
                 for ext in exts}
    return type_dict.get(ext, 'unknow')


def file_exists(filename):
    """ 文件是否存在

    Args:
        file_path (文件路径): 文件路径

    Returns:
        bool: 存在否
    """
    return os.path.exists(filename)


def media_type(ext):
    """ 获取媒体类型

    Args:
        ext (str): 扩展名

    Returns:
        str: 媒体类型
    """
    types_map = mimetypes.types_map
    types_map['.apk'] = 'application/vnd.android.package-archive'
    types_map['.ts'] = 'video/MP2T'
    return mimetypes.types_map.get(ext)


def upload_file_to_server(url, file_path, keep=True, override=False, *, user_id, access_token, sub_dir=''):
    """ 从本地上传文件到服务器

    Args:
        url (str): 服务器地址，如：http://www.excample888.com/file
        file_path (str): 文件路径 如：'F:/T/1/1732264770.mp3'
        keep (True): 是否保持原文件名
        override (bool, optional): 是否覆盖
        user_id (int): 用户id
        access_token (str): 访问令牌，在装饰器中进行校验
        sub_dir (str): 子目录
    """
    # path = mu.file_dir('user', user_id, sub_dir)
    # path += "\\" + file_path

    data = {
        'keep': keep,
        'override': override,
        'chunk_index': -1,
        'total_chunks': 1,
        'userId': -1,
        'access_token': access_token,
        'sub_dir': sub_dir
    }

    # 打开文件，准备上传
    with open(file_path, 'rb') as file:
        files = {'file': (file_path, file)}
        try:
            response = requests.post(url, files=files, data=data)
            if response.status_code == 200:
                return IM().from_dict(response.json())
            else:
                return IM(False, response.text, response.text, response.status_code)
        except Exception as e:
            return IM(False, '', e)


def download_file_from_server(url: str, save_path: str):
    """
    从服务器下载文件到本地，自动创建所需目录

    参数:
        url (str): 要下载的文件URL
        save_path (str): 本地保存路径（包含文件名）

    返回:
        IM对象: 包含操作结果（成功/失败）和相关信息
    """
    try:
        # 1. 自动创建目标目录
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        # 2. 发起HTTP GET请求，stream=True启用流式下载
        with requests.get(url, stream=True) as response:
            # 检查HTTP状态码，如果是4XX/5XX会抛出HTTPError异常
            response.raise_for_status()

            # 3. 以二进制写入模式打开文件
            with open(save_path, 'wb') as file:
                # 分块读取内容，chunk_size=8192表示每次读取8KB
                for chunk in response.iter_content(chunk_size=8192):
                    # 过滤掉空的chunk
                    if chunk:
                        file.write(chunk)

        # 返回成功结果
        return IM(True, 'Download completed.', save_path)

    # 异常处理部分
    except RequestException as e:
        # 处理网络相关错误（连接超时、DNS解析失败、HTTP错误等）
        return IM(False, f'Network error: {str(e)}')
    except IOError as e:
        # 处理文件IO错误（权限不足、磁盘空间不够等）
        return IM(False, f'File write error: {str(e)}')
    except Exception as e:
        # 处理其他未预料到的错误
        return IM(False, f'Unexpected error: {str(e)}')
