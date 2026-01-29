import mxupy as mu
def array_contains(lst, name, value):
    """
    检查列表中是否存在具有指定属性名且值等于给定值的项。

    Args:
        lst: 需要检查的列表
        name: 属性名
        value: 要匹配的值

    Returns:
        bool: 如果存在符合条件的项，返回True；否则返回False
    """
    if not lst:
        return False

    for item in lst:
        attr_value = mu.ObjectUtil.get_attr(item, name, None)
        if attr_value == value:
            return True

    return False

def array_find(lst, name, value):
    """
    从列表中找到第一个具有指定属性名且值等于给定值的项。

    Args:
        lst (list): 需要检查的列表。
        name (str): 属性名。
        value: 要匹配的值。

    Returns:
        object: 如果找到符合条件的项，返回该对象；否则返回 None。

    """
    if not lst:
        return None

    for item in lst:
        attr_value = mu.ObjectUtil.get_attr(item, name, None)
        if attr_value == value:
            return item

    return None

def array_find_all(lst, name, value):
    """
    从列表中找到所有具有指定属性名且值等于给定值的项。

    Args:
        lst (list): 需要检查的列表。
        name (str): 属性名。
        value: 要匹配的值。

    Returns:
        list: 包含所有符合条件的项的列表；如果没有匹配项，返回空列表。
    """
    result = []
    if not lst:
        return result

    for item in lst:
        attr_value = mu.ObjectUtil.get_attr(item, name, None)
        if attr_value == value:
            result.append(item)

    return result