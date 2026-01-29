import json
from typing import Any, List

def to_int(obj, default=0, base=10):
    """ 
        转为 int 型

    Args:
        obj (any): 需要转的对象
        default (int): 默认值
        base (int): 2、8、10、16 四种进制

    Returns:
        int: int 值
    """
    def check_number_type(src):
        # 移除字符串中的空白字符
        src = src.strip()
        
        # 检查是否为整数
        if src.lstrip('-').isdigit():
            return int
        
        # 检查是否为浮点数
        if src.replace('.', '', 1).lstrip('-').isdigit():
            return float
        
        # 如果不是整数或浮点数，则为其他类型
        return str
    
    try:
        if not obj:
            return default
        
        # int型
        if isinstance(obj, int):
            return obj
        
        # 浮点型不支持进制转换
        if isinstance(obj, float):
            return int(obj)
        
        if isinstance(obj, str):
            tpe = check_number_type(obj)
            if tpe == int:
                return int(obj)
            if tpe == float:
                return int(float(obj))
            if tpe == str:
                return int(obj, base)
        
        return int(obj, base)
    except:
        return default

def convert_to_list(x: Any) -> List[Any]:
    """
        转换为列表

    Args:
        x (Any): 任意类型

    Returns:
        List[Any]: 列表
    """
    if isinstance(x, list):
        return x
    
    if isinstance(x, set):
        return list(x)
    
    if isinstance(x, tuple):
        return list(x)
    
    if not x:
        return []
    try:
        # 替换单引号为双引号，并确保外层是方括号
        x = x.replace("'", '"')
        return json.loads(x)
    except json.JSONDecodeError:
        return [item.strip() for item in str(x).split(',')]  
    
    
    
if __name__ == '__main__':
    import array
    
    print('整型')
    print(to_int(1))
    print(to_int(0))
    print(to_int(-1))
    print(to_int('-1'))
    
    print('浮点型')
    print(to_int(-1.1))
    print(to_int(1.8))
    print(to_int(9.8))
    print(to_int(-9.8))
    print(to_int('9.8'))
    print(to_int('-9.8'))
    
    print('无 base 参数')
    print(to_int(10))                   # 输出: 10
    print(to_int("10"))                 # 输出: 10

    print('有 base 参数')
    print(to_int("10", base=10))        # 输出: 10
    print(to_int("0b1010", base=2))     # 输出: 10
    print(to_int("0x1a", base=16))      # 输出: 26
    print(to_int("15", base=8))         # 输出: 13
    
    print('全部返回默认值')
    print(to_int(None, -1))
    print(to_int("", -1))
    print(to_int("   ", -1))
    print(to_int([], -1))
    print(to_int(set(), -1))
    print(to_int((), -1))
    print(to_int([1, 2, 3], -1))
    print(to_int(array.array('i', [1, 2, 3]), -1))
    print(to_int({'a': 1}, -1))