import requests
from mxupy import IM

def set_cookie(key, value):
    """ 
        设置 cookie

    Args:
        key (str): 键
        value (any): 值
    """
    try:
        ___session.cookies.set(key, value)
        return IM(True, 'cookie set success.')
    except Exception as e:
        print(e)
        return IM(False, 'cookie set fail.' + str(e))

def get_cookie(key):
    """ 
        读取 cookie

    Args:
        key (str): 键
        value (any): 值
    """
    try:
        return IM(True, 'cookie get success.', ___session.cookies.get(key))
    except Exception as e:
        print(e)
        return IM(False, 'cookie get fail.' + str(e))



global ___session
___session = requests.Session()