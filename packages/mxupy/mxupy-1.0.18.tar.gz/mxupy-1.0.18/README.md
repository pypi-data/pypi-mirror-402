# mxupy 编程参考

---

mxupy many/more extension/utils for python，是 python 语言下的多工具集合。

安装 pip install mxupy

安装依赖 pip install -r requirements.txt

## docGen.py

---

### extract_comments_from_file

获取模块文件的注释
Args:
    file_path (str): 模块文件路径

Returns:
    str: 注释文本（markdown格式）
### generate_markdown_docstring

生成 docstring markdown 文档。
Args:
    title (str): 标题
    dir_path (str): 包目录
    output_file (str): md 文件路径
## hardware.py

---

### getDiskInfo

获取磁盘信息。

返回:
    str: 包含磁盘信息的字符串。
### getCPUInfo

获取 CPU 信息。

返回:
    str: 包含 CPU 信息的字符串。
### getGPUInfo

获取 GPU 信息。

参数:
    idx (int, 可选): GPU 索引，默认为 0。

返回:
    str: 包含 GPU 信息的字符串。
### getSystemInfo

获取系统信息。

返回:
    str: 包含系统信息的字符串。
### getMemoryInfo

获取内存信息。

返回:
    str: 包含内存信息的字符串。
## misc.py

---

### istuple

检查对象是否为元组。

Args:
    t (object): 待检查对象。

Returns:
    bool: 若为元组则返回 True，否则返回 False。
### islist

检查对象是否为列表。

Args:
    lst (object): 待检查对象。

Returns:
    bool: 若为列表则返回 True，否则返回 False。
### isndarray

检查对象是否为 NumPy 数组（ndarray）。

Args:
    lst (object): 待检查对象。

Returns:
    bool: 若为 NumPy 数组则返回 True，否则返回 False。
### isdict

检查对象是否为字典。

Args:
    dt (object): 待检查对象。

Returns:
    bool: 若为字典则返回 True，否则返回 False。
### isfunc

检查对象是否为函数（可调用）。

Args:
    func (object): 待检查对象。

Returns:
    bool: 若为函数（可调用）则返回 True，否则返回 False。
### isvalue

检查对象是否为字符串、整数或浮点数。

Args:
    obj (object): 待检查对象。

Returns:
    bool: 若为字符串、整数或浮点数则返回 True，否则返回 False。
### isbool

检查对象是否为布尔类型。

Args:
    val (object): 待检查对象。

Returns:
    bool: 若为布尔类型则返回 True，否则返回 False。
### reverseTuple

反转元组。

Args:
    t (tuple): 待反转的元组。

Returns:
    tuple: 反转后的元组。
### rndStr

生成 1000 到 2000 之间的随机整数作为字符串。

Returns:
    str: 生成的随机整数字符串。
### toBool

将输入值转换为布尔类型。

Args:
    value (any): 待转换的值。

Returns:
    bool: 转换后的布尔值。
### toValue

将值转换为指定类型。

Args:
    value (any): 待转换的值。
    type (str): 目标类型，可选值包括 'str', 'int', 'float', 'bool', 'datetime', 'date' 或 'time'。
    format (str, optional): 日期时间格式（仅对日期时间类型有效）。

Returns:
    any: 转换后的值。
### toStr

将值转换为字符串格式。

Args:
    value (any): 待转换的值。
    type (str): 原始值的类型，可选值包括 'str', 'int', 'float' 或 'bool'。
    format (str, optional): 日期时间格式（仅对日期时间类型有效）。

Returns:
    str: 转换后的字符串。
### dict2Object

递归将字典转换为对象。

Args:
    dt (dict): 待转换的字典。

Returns:
    object: 转换后的对象。
### getProperties

获取字典或对象的成员属性列表。

Args:
    obj (dict|object): 待获取属性的字典或对象。

Returns:
    list: 属性列表。
### hasProperty

检查对象是否具有指定属性。

Args:
    obj (dict|object): 待检查对象。
    property (str): 待检查的属性名称。

Returns:
    bool: 若对象具有指定属性则返回 True，否则返回 False。
### getValue

获取字典或对象中指定键的值。

Args:
    obj (dict|object): 待获取值的字典或对象。
    key (str): 键名。

Returns:
    any: 键对应的值。
### setValue

设置字典或对象中指定键的值。

Args:
    obj (dict|object): 待设置值的字典或对象。
    key (str): 键名。
    value (any): 待设置的值。
### uniqueEx

对列表进行去重操作。

Args:
    lst (List[object]): 待去重列表。
    axis (int, optional): 操作维度。

Returns:
    list: 去重后的结果列表。
### removeItems

按索引删除元素，注意要从大到小删除

Args:
    lst (List(object)): 元素集
    idxs (List(int)): 索引集
### getItems

从list中获取idxs指定的索引的多个元素

Args:
    lst (list): list
    idxs (list): 索引集

Returns:
    list: 按索引取出的多个元素
### rlst

range to list

Args:
    arg (Sequence[int]): 参数

Returns:
    list: 返回结果
### npSort

对ndarray按某列（可多列）排序

Args:
    arr (ndarray): M*N，只支持二维
    idx (int|list[int]): 列索引，可多个

Returns:
    ndarray: 排序后
### cls

清除控制台显示内容。
### appPath

获取当前应用程序的路径。

Returns:
    str: 应用程序路径。
### myPath

获取当前脚本的路径。

Returns:
    str: 脚本路径。
### tik

记录时间戳。

Args:
    name (str, optional): 时间戳名称，默认为 '__tik__'。
### ptik

计算时间间隔并输出。

Args:
    name (str, optional): 时间戳名称，默认为 '__tik__'。
### points

将列表或元组转换为 NumPy 数组。

Args:
    pts (list|tuple): 点集。
    dims (int, optional): 返回数组的维度。默认为 2。
    type (dtype, optional): 返回数组的数据类型。

Returns:
    ndarray: 转换后的数组。
### tuples2Points

元组集转点集。
如：[(1,2),(3,4)] -> [[[1,2], [3,4]]]

Args:
    tuples (list): 元组集

Returns:
    points: 点集
### points2Tuples

点集转元组集。
如：[[[1,2], [3,4]]] -> [(1,2),(3,4)]
Args:
    points (points): 点集

Returns:
    tuples: 元组集
### each

遍历每个元素，支持 list/tuple/ndarray

Args:
    lst (any): Iterable 和 Iterator
    callback (function): 回调函数
### traverse

广度优先遍历

Args:
    obj (any): 对象，每个对象需要有 children 属性表示孩子
    callback (function): 回调，原型 callback(item, parent, depth)
    depth (int,optional): 深度，从0开始
### traverseList

广度优先遍历列表对象。

Args:
    items (list): 列表对象。
    callback (function): 回调函数。
    parent (any, optional): 父级对象。
    depth (int, optional): 遍历深度，默认为 0。
### enumName

通过枚举值找到枚举名

Args:
    enum1 (Enum): 枚举
    value (int): 值

Returns:
    string: 枚举名
### defkv

返回对象中指定键的值，如果键不存在，则返回默认值。如果对象是字典或强制使用字典，则使用get方法获取值；否则，使用getattr方法获取值。

Args:
    obj (object): 要查询的对象（可以是字典、实例对象等）。
    key (object): 要检索的键。
    defval (object): 默认值，如果键不存在时返回该值。
    forceDict (bool, optional): 如果为True，则强制将obj视为字典。默认为False。

Returns:
    object: 对象中指定键的值或默认值。
### defv

如果值为空（None、空字符串、空列表、空元组、空ndarray等），则返回默认值；否则，返回该值本身。

Args:
    val (object): 要检查的值。
    defval (object): 默认值。

Returns:
    object: 如果值为空，则返回默认值；否则，返回该值本身。
### argv

取函数参数值，有值取值，没值取默认值

Args:
    args (tuple|dict): *args 或 **kwargs
    i (int|str): args序号或kwargs参数名
    val (any): 默认值

Returns:
    any: 值
### isN

检查给定对象是否为空（None、空字符串、空列表、空元组、空ndarray等）。

Args:
    obj (object): 要检查的对象。

Returns:
    bool: 如果对象为空，则返回True；否则，返回False。
### isNN

检查给定对象是否不为空（不是None、不是空字符串、不是空列表、不是空元组、不是空ndarray等）。

Args:
    obj (object): 要检查的对象。

Returns:
    bool: 如果对象不为空，则返回True；否则，返回False。
### isT

检查值是否为True。

Args:
    val (object): 要检查的值。

Returns:
    bool: 如果值为True，则返回True；否则，返回False。
### isF

检查值是否为False。

Args:
    val (object): 要检查的值。

Returns:
    bool: 如果值为False，则返回True；否则，返回False。
### hex2rgb

将十六进制颜色代码转换为RGB颜色元组。

Args:
    hex_color (str): 十六进制颜色代码（可以包含#）。

Returns:
    tuple: RGB颜色元组。
### sprt

将print的输出捕获到StringIO对象中。

Args:
    lst1 (list): 存储StringIO对象的列表。
### eprt

将捕获的输出转换为字符串。

Args:
    lst1 (list): 存储StringIO对象的列表。
### formatBytes

将字节转换为合适的单位格式（例如：1253656 => '1.20MB', 1253656678 => '1.17GB'）。

Args:
    bytes (int): 要转换的字节数。
    suffix (str, optional): 单位后缀。默认为“B”。

Returns:
    str: 转换后的字符串表示。
### formatMilliseconds

将毫秒数转换为合适的时间格式（例如：1250 => '1250ms', 125000 => '1.25s', 125000000 => '2.08m'等）。

Args:
    milliseconds (int): 要转换的毫秒数。

Returns:
    str: 转换后的时间格式字符串。
## misc.py

---

### getHTMLFromClipboard

从剪贴板获取 HTML 数据。

返回:
    str: 如果可用，返回剪贴板中的 HTML 数据。
### getImageFromClipboard

从剪贴板获取图像。

返回:
    list: 如果可用，返回剪贴板中的图像列表。
## dir.py

---

### getFiles

'' 
获取一个目录下的所有文件 
## file.py

---

### fileParts

拆分文件路径，获取文件路径、文件名和扩展名。

参数:
    filename (str): 要处理的文件路径字符串。

返回:
    tuple: 文件路径、文件名和小写的扩展名组成的元组。
### readAllText

读取文本文件全部内容，注意文件编码必须是 utf-8

Args:
    filename (string): 文件路径

Returns:
    string: 文件内容
### writeAllText

将文本内容写入文件。

参数:
    filename (str): 要写入的文件路径。
    content (str): 要写入的文本内容。
    mode (str, 可选): 文件打开模式，默认为 'w'（写入模式）。

返回:
    str: 写入文件的字符数。
### writeStream

将二进制内容写入文件。

参数:
    filename (str): 要写入的文件路径。
    content (bytes): 要写入的二进制内容。
    mode (str, 可选): 文件打开模式，默认为 'wb'（二进制写入模式）。

返回:
    str: 写入文件的字符数。
### clearAllText

清空文件内容。

参数:
    filename (str): 要清空内容的文件路径。
### fileType

获取文件类型

Args:
    filename (str): 文件名、路径、扩展名(如 .txt)

Returns:
    str: 类型 image/office/...
## zip.py

---

### zipFolder

压缩文件夹并排除指定的目录。

:param folder_path: 要压缩的文件夹的路径。
:param output_path: 压缩文件的输出路径。
:param exclude_dirs: 要排除的目录列表。
### addFolderToZip

添加文件夹到zip文件
## audio.py

---

### segAudio

指定秒数，分割音频为多份文件
### cutAudio

截取音频
## image.py

---

### makeThumbnail

生成缩略图
### colorOverlay

给图像添加颜色叠加层。

参数:
    img (PIL.Image.Image): 原始图像。
    rgba (tuple): 包含颜色信息的元组，形如 (R, G, B, A)。

返回:
    PIL.Image.Image: 添加颜色叠加层后的图像。
### setAlpha

设置图像的透明度。

参数:
    img (PIL.Image.Image): 要设置透明度的图像。
    alpha (float): 透明度值，取值范围在 0 到 1 之间。

返回:
    None: 该函数直接修改传入的图像对象，不返回新的图像。
## video.py

---

### removeGreenBG

移除绿幕。
### overlayVideo

将mainvideo移除绿幕，与overlays进行叠加在一起。
视频和叠加物都是一个对象，包含 Url/Width/Height/X/Y/Z，Z越大越在前。
最终fps与mainvideo一致。
### segVideo

指定秒数，分割视频为多份文件
### cutVideo

裁剪视频
start：开始秒数
end：结束秒数
### captureVideoFrame

截取视频文件某一帧的画面
frame_number 可以是具体的帧数（注意从0开始到总帧数-1），也可以是：
-1 最后一帧
0 第一帧
0.5 中间帧，在(0.0,1.0)中间都表示为百分比
### getVideoSize

获取视频文件宽高
### extactAudio

从视频中取出音频部分
