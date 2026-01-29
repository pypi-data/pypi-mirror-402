from io import StringIO
import json
import os
import sys
import numpy as np
import random
import time
# import inspect
import os.path
import pandas as pd
import datetime
import traceback
import string
import hashlib
from fastapi.responses import StreamingResponse, JSONResponse
import mxupy as mu

global glb
glb = {}

glb['debug'] = False


def ping():
    """ 测试网络响应

    Returns:
        str: 响应结果
    """
    return "pong"


def hello():
    """ 欢迎

    Returns:
        str: 欢迎结果
    """
    return "HI, I am mxupy!"


def istuple(t):
    """
    检查对象是否为元组。

    Args:
        t (object): 待检查对象。

    Returns:
        bool: 若为元组则返回 True，否则返回 False。
    """
    return isinstance(t, tuple)


def islist(lst):
    """
    检查对象是否为列表。

    Args:
        lst (object): 待检查对象。

    Returns:
        bool: 若为列表则返回 True，否则返回 False。
    """
    return isinstance(lst, list)


def isndarray(lst):
    """
    检查对象是否为 NumPy 数组（ndarray）。

    Args:
        lst (object): 待检查对象。

    Returns:
        bool: 若为 NumPy 数组则返回 True，否则返回 False。
    """
    return isinstance(lst, np.ndarray)


def isdict(dt):
    """
    检查对象是否为字典。

    Args:
        dt (object): 待检查对象。

    Returns:
        bool: 若为字典则返回 True，否则返回 False。
    """
    return isinstance(dt, dict)


def isfunc(func):
    """
    检查对象是否为函数（可调用）。

    Args:
        func (object): 待检查对象。

    Returns:
        bool: 若为函数（可调用）则返回 True，否则返回 False。
    """
    return callable(func)


def isvalue(obj):
    """
    检查对象是否为字符串、整数或浮点数。

    Args:
        obj (object): 待检查对象。

    Returns:
        bool: 若为字符串、整数或浮点数则返回 True，否则返回 False。
    """
    return isinstance(obj, str) or isinstance(obj, int) or isinstance(obj, float)


def isbool(val):
    """
    检查对象是否为布尔类型。

    Args:
        val (object): 待检查对象。

    Returns:
        bool: 若为布尔类型则返回 True，否则返回 False。
    """
    return isinstance(val, bool)


def reverseTuple(t):
    """
    反转元组。

    Args:
        t (tuple): 待反转的元组。

    Returns:
        tuple: 反转后的元组。
    """
    return tuple(reversed(t))


def rndStr():
    """
    生成 1000 到 2000 之间的随机整数作为字符串。

    Returns:
        str: 生成的随机整数字符串。
    """
    return str(random.randint(1000, 2000))


def toBool(value):
    """
    将输入值转换为布尔类型。

    Args:
        value (any): 待转换的值。

    Returns:
        bool: 转换后的布尔值。
    """
    if type(value) is str:
        return value == 'True' or value == 'true'
    else:
        return bool(value)


def toValue(value, type, format=None):
    """
    将值转换为指定类型。

    Args:
        value (any): 待转换的值。
        type (str): 目标类型，可选值包括 'str', 'int', 'float', 'bool', 'datetime', 'date' 或 'time'。
        format (str, optional): 日期时间格式（仅对日期时间类型有效）。

    Returns:
        any: 转换后的值。
    """
    if type == 'str':
        return str(value)
    elif type == 'int':
        return int(value)
    elif type == 'float':
        return float(value)
    elif type == 'bool':
        return toBool(value)
    elif type == 'datetime' or type == 'date' or type == 'time':
        return datetime.datetime.strptime(value, format)


def toStr(value, type, format=None):
    """
    将值转换为字符串格式。

    Args:
        value (any): 待转换的值。
        type (str): 原始值的类型，可选值包括 'str', 'int', 'float' 或 'bool'。
        format (str, optional): 日期时间格式（仅对日期时间类型有效）。

    Returns:
        str: 转换后的字符串。
    """
    if type == 'str' or type == 'int' or type == 'float':
        return str(value)
    elif type == 'bool':
        return 'True' if value == True else 'False'
    elif type == 'datetime' or type == 'date' or type == 'time':
        return datetime.datetime.strftime(value, format)


def toSerializable(item):
    """转换为json.dump的对象

    Args:
        item (any): 对象

    Returns:
        any: 可序列化对象
    """
    if isinstance(item, dict):
        return {key: toSerializable(value)
                for key, value in item.items()}
    elif hasattr(item, '__dict__'):
        return toSerializable(item.__dict__)
    elif isinstance(item, list) or isinstance(item, tuple):
        return [toSerializable(element) for element in item]
    else:
        return item


def dict2Object(dt):
    """
    递归将字典转换为对象。

    Args:
        dt (dict): 待转换的字典。

    Returns:
        object: 转换后的对象。
    """
    if isinstance(dt, dict):
        obj = type('dynamicClass', (object, ), {})()
        for key, value in dt.items():
            setattr(obj, key, dict2Object(value))
        return obj
    elif isinstance(dt, list):
        return [dict2Object(item) for item in dt]
    else:
        return dt


def getProperties(obj):
    """
    获取字典或对象的成员属性列表。

    Args:
        obj (dict|object): 待获取属性的字典或对象。

    Returns:
        list: 属性列表。
    """
    if isinstance(obj, dict):
        return list(set(obj))
    if isinstance(obj, object):
        ps = [attr for attr in dir(obj) if not attr.startswith("__")]
        return ps


def hasProperty(obj, property):
    """
    检查对象是否具有指定属性。

    Args:
        obj (dict|object): 待检查对象。
        property (str): 待检查的属性名称。

    Returns:
        bool: 若对象具有指定属性则返回 True，否则返回 False。
    """
    ps = getProperties(obj)
    return ps.count(property) == 1


def getValue(obj, key):
    """
    获取字典或对象中指定键的值。

    Args:
        obj (dict|object): 待获取值的字典或对象。
        key (str): 键名。

    Returns:
        any: 键对应的值。
    """
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        else:
            return None
    elif isinstance(obj, object):
        if hasattr(obj, key):
            return getattr(obj, key)
        else:
            return None


def setValue(obj, key, value):
    """
    设置字典或对象中指定键的值。

    Args:
        obj (dict|object): 待设置值的字典或对象。
        key (str): 键名。
        value (any): 待设置的值。
    """
    if isinstance(obj, dict):
        obj[key] = value
    elif isinstance(obj, object):
        setattr(obj, key, value)


def assign(src, dest):
    ps = getProperties(src)
    for p in ps:
        setValue(dest, p, getValue(src, p))


def uniqueEx(lst, axis=0):
    """
    对列表进行去重操作。

    Args:
        lst (List[object]): 待去重列表。
        axis (int, optional): 操作维度。

    Returns:
        list: 去重后的结果列表。
    """
    if islist(lst):
        return list(dict.fromkeys(lst))

    _, idx = np.unique(lst, return_index=True, axis=axis)
    return lst[np.sort(idx)]


def removeItems(lst, idxs):
    """ 按索引删除元素，注意要从大到小删除

    Args:
        lst (List(object)): 元素集
        idxs (List(int)): 索引集
    """
    idxs.sort()
    idxs.reverse()
    for idx in idxs:
        # 使用del关键字来根据索引删除元素
        # lst.remove(lst[idx])
        del lst[idx]


def getItems(lst, idxs):
    """从list中获取idxs指定的索引的多个元素

    Args:
        lst (list): list
        idxs (list): 索引集

    Returns:
        list: 按索引取出的多个元素
    """
    return [lst[i] for i in idxs]


def rlst(*args):
    """range to list

    Args:
        arg (Sequence[int]): 参数

    Returns:
        list: 返回结果
    """
    start, end, step = 0, 1, 1
    if len(args) == 1:
        end = args[0]
    elif len(args) == 2:
        start, end = args[0], args[1]
    elif len(args) == 3:
        start, end, step = args[0], args[1], args[2]

    return list(range(start, end, step))


def npSort(arr, idx, ascending=True):
    """对ndarray按某列（可多列）排序

    Args:
        arr (ndarray): M*N，只支持二维
        idx (int|list[int]): 列索引，可多个

    Returns:
        ndarray: 排序后
    """
    cols = arr.shape[1]
    colns = []
    for i in range(cols):
        colns.append('col' + str(i))

    df = pd.DataFrame(arr, columns=colns)
    if isF(islist(idx)):
        idx = [idx]

    colss = []
    for i in idx:
        colss.append('col' + str(i))

    df2 = df.sort_values(colss, ascending=ascending)
    return df2.values


def cls():
    """
    清除控制台显示内容。
    """
    os.system('cls')


def appPath():
    """
    获取当前应用程序的路径。

    Returns:
        str: 应用程序路径。
    """
    return os.getcwd()


def myPath():
    """
    获取当前脚本的路径。

    Returns:
        str: 脚本路径。
    """
    dirname, filename = os.path.split(os.path.abspath(sys.argv[0]))
    return dirname


__tik__ = {}


def tik(name='__tik__'):
    """
    记录时间戳。

    Args:
        name (str, optional): 时间戳名称，默认为 '__tik__'。
    """
    __tik__[name] = time.time()


def ptik(name='__tik__'):
    """
    计算时间间隔并输出。

    Args:
        name (str, optional): 时间戳名称，默认为 '__tik__'。
    """
    t = time.time()
    print('tick for', name, ':', t - __tik__[name])
    __tik__[name] = t


def perror(title='Error', e=None):

    info = ''
    tb = None
    if e:
        # 1. 打印基础错误信息
        print(info1 := f"{title}: {type(e).__name__}: {e}")
        info += info1

        # 2. 获取回溯对象（优先从__traceback__，失败则从sys.exc_info()）
        tb = getattr(e, "__traceback__", None)

    if tb is None:
        _, _, tb = sys.exc_info()  # 从当前异常上下文获取[2,3](@ref)

    # 3. 无回溯则直接退出
    if tb is None:
        return 'No traceback found.'

    # 4. 提取并过滤堆栈帧（排除site-packages）
    tb_list = traceback.extract_tb(tb)
    project_frames = [
        frame for frame in tb_list
        if all(word not in os.path.abspath(frame.filename) for word in ["site-packages", "lib"])
    ]

    # 5. 打印过滤后的堆栈
    if project_frames:
        print(info1 := "\nStack trace (project files only):")
        info += info1
        for frame in project_frames:
            print(
                info1 := f"  File: {frame.filename}, line {frame.lineno}, in {frame.name}")
            info += info1
            print(info1 := f"    {frame.line or ''}")
            info += info1
    else:
        print(
            info1 := "\nNo project-related stack frames found (all calls were from site-packages).")
        info += info1

    return info


def points(pts, dims=2, type=None):
    """
    将列表或元组转换为 NumPy 数组。

    Args:
        pts (list|tuple): 点集。
        dims (int, optional): 返回数组的维度。默认为 2。
        type (dtype, optional): 返回数组的数据类型。

    Returns:
        ndarray: 转换后的数组。
    """

    r = pts
    if istuple(pts):
        r = np.array(list(pts))

    if islist(pts):
        r = np.array(pts)

    if type is not None:
        r = r.astype(type)

    if dims == 1:
        return r.flatten()
    if dims == 2:
        return r.reshape(-1, 2)
    elif dims == 3:
        return r.reshape(-1, 1, 2)


def tuples2Points(tuples):
    """元组集转点集。
    如：[(1,2),(3,4)] -> [[[1,2], [3,4]]]

    Args:
        tuples (list): 元组集

    Returns:
        points: 点集
    """
    pts = np.array(tuples)
    return pts.reshape(-1, 1, 2)


def points2Tuples(pts):
    """点集转元组集。
    如：[[[1,2], [3,4]]] -> [(1,2),(3,4)]
    Args:
        points (points): 点集

    Returns:
        tuples: 元组集
    """
    pts = points(pts, 2)
    return list(map(tuple, pts))


def each(lst, callback):
    """遍历每个元素，支持 list/tuple/ndarray

    Args:
        lst (any): Iterable 和 Iterator
        callback (function): 回调函数
    """
    lst2 = points(lst)

    # TODO:还要支持 Iterator
    for i in range(len(lst2)):
        callback(lst2[i], i)


def traverse(obj, callback, depth=0):
    """广度优先遍历

    Args:
        obj (any): 对象，每个对象需要有 children 属性表示孩子
        callback (function): 回调，原型 callback(item, parent, depth)
        depth (int,optional): 深度，从0开始
    """
    if obj is None:
        return

    if hasProperty(obj, 'children') is False:
        return

    for child in getValue(obj, 'children'):
        b = callback(child, obj, depth)
        if b is False:
            return

        traverse(child, callback, depth + 1)


def traverseList(items, callback, parent=None, depth=0):
    """
    广度优先遍历列表对象。

    Args:
        items (list): 列表对象。
        callback (function): 回调函数。
        parent (any, optional): 父级对象。
        depth (int, optional): 遍历深度，默认为 0。
    """
    for item in items:
        b = callback(item, parent, depth)
        if b is False:
            return

        children = getValue(item, 'children')
        if children is not None:
            traverseList(children, callback, item, depth + 1)


def enumName(enum1, value):
    """通过枚举值找到枚举名

    Args:
        enum1 (Enum): 枚举
        value (int): 值

    Returns:
        string: 枚举名
    """
    n = ''
    for item in enum1:
        if item.value == value:
            n = item.name
            break
    return n


def defkv(obj, key, defval='', forceDict=False):
    """
    返回对象中指定键的值，如果键不存在，则返回默认值。如果对象是字典或强制使用字典，则使用get方法获取值；否则，使用getattr方法获取值。

    Args:
        obj (object): 要查询的对象（可以是字典、实例对象等）。
        key (object): 要检索的键。
        defval (object): 默认值，如果键不存在时返回该值。
        forceDict (bool, optional): 如果为True，则强制将obj视为字典。默认为False。

    Returns:
        object: 对象中指定键的值或默认值。
    """
    if isdict(obj) or forceDict:
        return obj.get(key, defval)
    return getattr(obj, key, defval)


def defv(val, defval=''):
    """
    如果值为空（None、空字符串、空列表、空元组、空ndarray等），则返回默认值；否则，返回该值本身。

    Args:
        val (object): 要检查的值。
        defval (object): 默认值。

    Returns:
        object: 如果值为空，则返回默认值；否则，返回该值本身。
    """
    if isN(val):
        return defval
    return val


def argv(args, i, val=''):
    """取函数参数值，有值取值，没值取默认值

    Args:
        args (tuple|dict): *args 或 **kwargs
        i (int|str): args序号或kwargs参数名
        val (any): 默认值

    Returns:
        any: 值
    """

    if isinstance(args, tuple):
        if len(args) > i:
            return args[i]
        else:
            return val

    elif isinstance(args, dict):
        if i in args.keys():
            return args[i]
        else:
            return val


def isN(obj):
    """
    检查给定对象是否为空（None、空字符串、空列表、空元组、空ndarray等）。

    Args:
        obj (object): 要检查的对象。

    Returns:
        bool: 如果对象为空，则返回True；否则，返回False。
    """

    if obj is None:
        return True

    if isinstance(obj, str):
        return len(obj.strip()) == 0

    if isndarray(obj) or istuple(obj) or islist(obj):
        return len(obj) == 0

    if isdict(obj):
        return len(obj.keys()) == 0


def isNN(obj):
    """
    检查给定对象是否不为空（不是None、不是空字符串、不是空列表、不是空元组、不是空ndarray等）。

    Args:
        obj (object): 要检查的对象。

    Returns:
        bool: 如果对象不为空，则返回True；否则，返回False。
    """
    return not isN(obj)


def isT(val):
    """
    检查值是否为True。

    Args:
        val (object): 要检查的值。

    Returns:
        bool: 如果值为True，则返回True；否则，返回False。
    """
    return val == True


def isF(val):
    """
    检查值是否为False。

    Args:
        val (object): 要检查的值。

    Returns:
        bool: 如果值为False，则返回True；否则，返回False。
    """
    return val == False


def hex2rgb(hex_color):
    """
    将十六进制颜色代码转换为RGB颜色元组。

    Args:
        hex_color (str): 十六进制颜色代码（可以包含#）。

    Returns:
        tuple: RGB颜色元组。
    """
    # 去除可能包含的 '#' 符号
    hex_color = hex_color.lstrip('#')

    # 使用 int 函数将十六进制字符串转换为整数
    value = int(hex_color, 16)

    # 通过位运算获取红色、绿色和蓝色分量
    red = (value >> 16) & 255
    green = (value >> 8) & 255
    blue = value & 255

    return (red, green, blue)


def sprt(lst1):
    """
    将print的输出捕获到StringIO对象中。

    Args:
        lst1 (list): 存储StringIO对象的列表。
    """
    # 创建一个StringIO对象，用于捕获print的输出
    lst1[0] = StringIO()
    # 重定向标准输出流（sys.stdout）到StringIO
    sys.stdout = lst1[0]


def eprt(lst1):
    """
    将捕获的输出转换为字符串。

    Args:
        lst1 (list): 存储StringIO对象的列表。
    """
    # 获取捕获的输出作为字符串
    lst1[1] = lst1[0].getvalue()

    # 恢复标准输出
    sys.stdout = sys.__stdout__


def formatBytes(bytes, suffix="B"):
    """
    将字节转换为合适的单位格式（例如：1253656 => '1.20MB', 1253656678 => '1.17GB'）。

    Args:
        bytes (int): 要转换的字节数。
        suffix (str, optional): 单位后缀。默认为“B”。

    Returns:
        str: 转换后的字符串表示。
    """
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor


def formatMilliseconds(milliseconds):
    """
    将毫秒数转换为合适的时间格式（例如：1250 => '1250ms', 125000 => '1.25s', 125000000 => '2.08m'等）。

    Args:
        milliseconds (int): 要转换的毫秒数。

    Returns:
        str: 转换后的时间格式字符串。
    """
    if milliseconds < 1000:
        return f"{milliseconds}ms"
    seconds = milliseconds / 1000
    if seconds < 60:
        return f"{seconds:.2f}s"
    minutes = seconds / 60
    if minutes < 60:
        return f"{minutes:.2f}m"
    hours = minutes / 60
    if hours < 24:
        return f"{hours:.2f}h"
    days = hours / 24
    if days < 30.44:  # 平均每月的天数
        return f"{days:.2f}d"
    months = days / 30.44
    if months < 12:
        return f"{months:.2f}mo"
    years = months / 12
    return f"{years:.2f}y"


def guid4():
    # 生成4位随机数，基于36进制（0-9和a-z）
    return ''.join(random.choices(string.digits + 'abcdefghijklmnopqrstuvwxyz', k=4))


def parseDateTime(date_string):
    # 尝试解析不同的日期格式，如果都错了，返回当前日期
    for format in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d'):
        try:
            return datetime.datetime.strptime(date_string, format)
        except ValueError:
            continue

    return datetime.datetime.now()


def md5(src):
    """Generate MD5 hash for the given string."""
    md5_obj = hashlib.md5()
    md5_obj.update(src.encode('utf-8'))
    return md5_obj.hexdigest()


def generate_eventstream_data(obj):
    '''
    生成EventStream数据格式的字符串
    '''
    if isinstance(obj, mu.IM):
        obj = obj.to_dict(obj)
    return 'data: '+json.dumps(obj)+'\n\n'

def error_stream_response_generator(msg):
    def error_stream():
        yield mu.generate_eventstream_data(mu.IM(False,msg))
    return StreamingResponse(error_stream(), media_type="text/event-stream")
def stream_response_generator(queue):
    async def stream_generator():
        try:
            while True:
                # 从状态队列中获取数据
                data = await queue.get()
                if data is None:  # 结束标记
                    break

                yield mu.generate_eventstream_data(data)

        except Exception as e:
            # 发生异常，发送错误消息
            yield mu.generate_eventstream_data(mu.IM(False, "stream_generator error: " + str(e)))

    return StreamingResponse(stream_generator(), media_type="text/event-stream")

def safe_dump(data):
    """
    传入任意 dict，返回一个“可 JSON 序列化”的干净副本。
    不可序列化的字段会被递归剔除。
    """
    def _is_bad(obj) -> bool:
        try:
            json.dumps(obj)
            return False
        except Exception as e:
            print(f'mxupy->safe_dump->_is_bad error:{e}')
            return True

    def _clean(obj):
        if isinstance(obj, dict):
            # 用副本避免修改原 dict
            cleaned = {}
            for k, v in obj.items():
                if isinstance(v, datetime.datetime):
                    cleaned[k] = v.isoformat()
                    continue
                if not isinstance(v,dict) and _is_bad(v):
                    continue
                cleaned[k] = _clean(v)
            return cleaned
        if isinstance(obj, list):
            return [_clean(item) for item in obj]
        return obj

    return _clean(data)