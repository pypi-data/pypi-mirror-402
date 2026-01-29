import inspect
import importlib

from functools import lru_cache
from peewee import ForeignKeyField, Model
from playhouse.shortcuts import model_to_dict
from playhouse.shortcuts import model_to_dict as original_model_to_dict
from peewee import ForeignKeyField

import mxupy as mu

# 提供一个所有类的可实例化的基类
class Obj(object):
    pass

def is_null(obj):
    """ 
        判断对象是否为空

    Args:
        obj (any): 需判断的对象

    Returns:
        bool: 为空否
    """
    import array
    import collections
    
    if obj is None:
        return True

    if isinstance(obj, str):
        return not obj.strip()

    if isinstance(obj, list) or isinstance(obj, tuple) or isinstance(obj, set):
        return len(obj) == 0

    if isinstance(obj, collections.abc.Iterable) and not isinstance(obj, (str, bytes, bytearray)):
        return not list(obj)

    if isinstance(obj, array.array):
        return len(obj) == 0

    if isinstance(obj, collections.abc.Collection):
        return not bool(obj)

    if hasattr(obj, '__iter__') and hasattr(obj, '__len__'):
        return len(obj) == 0

    # 对于自定义对象，假设它们有一个 isempty 属性或方法
    if hasattr(obj, 'isempty'):  
        return obj.isempty

    return False

def get_attr(obj, name, default=None):
    """ 
        支持多层获取属性

    Args:
        obj (cls|obj|dict): 类、对象、字典
        name (str): 名称 多层用".".隔开，如：Meta.instance_name
        default (any): 如果属性不存在，则返回此默认值

    Returns:
        any: 属性值
    """
    ns = name.split('.')
    attr = obj.get(ns[0], default) if isinstance(obj, dict) else getattr(obj, ns[0], default)
    if len(ns) == 1:
        return attr
    
    # 中途没有直接返回
    if not attr:
        return default
    
    return get_attr(attr, ''.join(ns[1:]), default)

def set_attr(obj, name, value):
    """
    支持多层设置属性或键值

    Args:
        obj (cls|obj|dict): 类、对象、字典
        name (str): 名称 多层用".".隔开，如：Meta.instance_name
        value (any): 要设置的值
    """
    ns = name.split('.')
    if len(ns) == 1:
        # 如果只有一层，直接设置
        if isinstance(obj, dict):
            obj[ns[0]] = value
        else:
            setattr(obj, ns[0], value)
    else:
        # 如果有多层，先递归获取到倒数第二层
        sub_name = '.'.join(ns[:-1])
        sub_obj = get_attr(obj, sub_name)
        if sub_obj is None:
            # 如果中间层不存在，根据类型动态创建
            if isinstance(obj, dict):
                for key in ns[:-1]:
                    if key not in obj:
                        obj[key] = {}
                    obj = obj[key]
            else:
                for key in ns[:-1]:
                    if not hasattr(obj, key):
                        setattr(obj, key, type(obj)())
                    obj = getattr(obj, key)
        # 最后一层直接设置
        if isinstance(obj, dict):
            obj[ns[-1]] = value
        else:
            setattr(obj, ns[-1], value)
    
def is_static_method(clazz, method_name = None):
    """ 通过类与函数名，判断一个函数是否为静态函数

    Args:
        clazz (class): 类
        method_name (string): 函数名
    
    Returns:
        bool: True 为静态函数，False 为成员函数
    """
    # 获取类中的方法，注意 clazz 一定要实例化后获取属性
    static_func = getattr(clazz, method_name)
    return not inspect.signature(static_func).parameters.get('self')

def get_method_fullname(method):
    """
    获取函数的完整路径，包括模块名和类名（如果是类方法）
    method.__module__ 模块名
    'bigOAINet.base.member.UserControl'
    method.__qualname__ 类名.函数名
    'UserControl.login'
    
    Args:
        method: 要获取路径的函数对象
        
    Returns:
        str: 函数的完整路径
    """
    if method is None:
        return ""

    try:
        # 实例方法
        if hasattr(method, "__self__"):
            cls = method.__self__.__class__
            return f"{cls.__module__}.{cls.__qualname__}.{method.__name__}"
        
        # 类方法
        if hasattr(method, "__qualname__") and "." in method.__qualname__:
            return f"{method.__module__}.{method.__qualname__}"
        
        # 静态方法
        return f"{method.__module__}.{method.__name__}"
    
    except Exception:
        return ""

@lru_cache(maxsize=1000)
def import_method(module_path):
    """
    根据点分隔的模块路径获取对应的方法
    
    Args:
        module_path: 点分隔的路径字符串，如"bigOAINet.base.safe.RuleControl.check_access"
        
    Returns:
        找到的方法对象
        
    Raises:
        适当的异常如果路径无效或无法找到方法
    """
    parts = module_path.split('.')
    if not parts:
        print(f"module_path: {module_path}，必须包含点号")
        return None
    
    # 从第一个部分开始，作为初始模块
    current = importlib.import_module(parts[0])
    
    # 遍历剩余部分
    for part in parts[1:]:

        if not hasattr(current, part):
            print(f"找不到属性: {part}")
            return None
        
        current = getattr(current, part)

        # # 如果是类，进行处理
        # if inspect.isclass(current):
        #     print(f"处理类: {current.__name__}")
        #     # 如果是EntityXControl子类，获取实例
        #     if issubclass(current, mu.EntityXControl):
        #         current = current.inst()
        #         print(f"使用{current.__class__.__name__}的实例")

        # 如果是方法或函数，直接返回
        if inspect.ismethod(current) or inspect.isfunction(current):
            return current

        # 如果当前是模块，尝试导入子模块
        elif inspect.ismodule(current):
            try:
                current = importlib.import_module(f"{current.__name__}.{part}")
                continue
            except ImportError:
                pass
        
    print(f"路径'{module_path}'最终指向的不是方法")
    return None

# 添加缓存清理方法
def clear_method_cache():
    """
    清理 get_method 函数的缓存
    """
    import_method.cache_clear()
    
def has_method(module_path):
    """
    判断模块路径是否存在方法

    Args:
        module_path (str): 模块路径

    Returns:
        bool: True 存在，False 不存在
    """
    m = import_method(module_path)
    return True if m else False


def dict_to_obj(dic):
    """ 字典转对象

    Args:
        dict (dict): 字典
    
    Returns:
        obj: 对象
    """
    if isinstance(dic, dict):
        obj = Obj()
        { setattr(obj, k, dict_to_obj(v)) for k, v in dic.items() }
        return obj
    elif isinstance(dic, (list, tuple, set)):
        container_type = type(dic)
        return container_type(dict_to_obj(item) for item in dic)
    else:
        return dic
    
def obj_to_dict(obj):
    """ 对象转字典

    Args:
        obj: 任意对象

    Returns:
        dict: 包含对象属性的字典
    """
    if isinstance(obj, dict):
        return {k: obj_to_dict(v) for k, v in obj.items()}
    elif hasattr(obj, '__dict__'):
        return {k: obj_to_dict(v) for k, v in obj.__dict__.items() if not k.startswith('__')}
    elif isinstance(obj, (list, tuple, set)):
        return [obj_to_dict(item) for item in obj]
    else:
        return obj


def dict_to_model(source, clazz):
    """ 字典转 model

    Args:
        source: 字典 或 字典集合
        clazz: model 类

    Returns:
        model: model 实例
    """
    if source is None or clazz is None:
        return None
    
    if isinstance(source, Obj):
        source = obj_to_dict(source)
    
    if isinstance(source, dict):
        return clazz(**source)
    
    elif isinstance(source, (list, tuple, set)):
        if len(source) == 0:
            return source
        
        container_type = type(source)
        return container_type(dict_to_model(item) for item in source)
        
    return source

def to_obj(source):
    """ 字典或model转对象

    Args:
        dict (dict): 字典
    
    Returns:
        obj: 对象
    """
    if source is None:
        return None
    
    if isinstance(source, dict):
        return dict_to_obj(source)
    
    if isinstance(source, Model):
        return dict_to_obj(model_to_dict_x(source))
    
    elif isinstance(source, (list, tuple, set)):
        if len(source) == 0:
            return source
        
        container_type = type(source)
        return container_type(to_obj(item) for item in source)
        
        # if isinstance(source[0], dict):
        #     return dict_to_obj(source)
        # elif isinstance(source[0], Model):
        #     return dict_to_obj([model_to_dict_x(item) for item in source])
        
    return source
def to_dict(source, recurse=True, backrefs=False, only=None, exclude=None, max_depth=1, extra_attrs=None, **kwargs):
    """ 对象转字典

    Args:
        source: obj 或 Model，或两者的集合
        recurse: 是否递归处理关联对象
        backrefs: 是否处理反向引用
        only: 只包含指定字段
        exclude: 排除指定字段
        max_depth: 递归最大深度
        extra_attrs: 包含额外属性
        **kwargs: 其他传递给原始 model_to_dict 的参数

    Returns:
        dict: 包含对象属性的字典
    """
    if source is None:
        return None
    
    if isinstance(source, Obj):
        return obj_to_dict(source)
    
    if isinstance(source, Model):
        # return model_to_dict_x(source, recurse=recurse, backrefs=backrefs, max_depth=max_depth, extra_attrs=extra_attrs, only=only, exclude=exclude, **kwargs)
        return model_to_dict_x(source, recurse, backrefs,  only, exclude, max_depth, extra_attrs, **kwargs)
    
    elif isinstance(source, (list, tuple, set)):
        if len(source) == 0:
            return source
        
        container_type = type(source)
        return container_type(to_dict(item, recurse, backrefs, max_depth, extra_attrs, only, exclude, **kwargs) for item in source)
        
    return source
def to_model(source, clazz):
    """ 字典或obj转 model

    Args:
        source: 字典或obj 或 集合
        clazz: model 类

    Returns:
        model: model 实例
    """
    if source is None or clazz is None:
        return None
    
    if isinstance(source, Obj):
        source = obj_to_dict(source)
    
    if isinstance(source, dict):
        return clazz(**source)
    
    elif isinstance(source, (list, tuple, set)):
        if len(source) == 0:
            return source
        
        container_type = type(source)
        return container_type(to_model(item) for item in source)
        
    return source

def param_to_obj(params):
    """ 将参数集中的每个字典转为对象
        params 本身还是 dict

    Args:
        params (list[any]): 参数集
    
    Returns:
        dict: 字典
    """
    if not params:
        return None
    
    params2 = {}
    for key, value in params.items():
        if isinstance(value, dict):
            params2[key] = dict_to_obj(value)
    return params2

def merge_obj(obj1, obj2):
    """
    合并两个对象，将 obj2 合并到 obj1 中
    
    Args:
        obj1: 目标对象
        obj2: 源对象
    
    Returns:
        dict: 合并后的对象
    """
    dict1 = obj_to_dict(obj1)
    dict2 = obj_to_dict(obj2)
    merged_dict = {**dict1, **dict2}
    return dict_to_obj(merged_dict)

def model_to_dict_x(model, recurse=True, backrefs=False, only=None, exclude=None, max_depth=1, extra_attrs=None, **kwargs):
    """
        处理所有外键情况的完整解决方案

    Args:
        model: Peewee 模型实例
        recurse: 是否递归处理关联对象
        backrefs: 是否处理反向引用
        only: 只包含指定字段
        exclude: 排除指定字段
        max_depth: 递归最大深度
        extra_attrs: 包含额外属性
        **kwargs: 其他传递给原始 model_to_dict 的参数

    return:
        dict: 转换后的字典 
    """
    data = original_model_to_dict(model, recurse, backrefs, only, exclude, max_depth = max_depth, extra_attrs=extra_attrs, **kwargs)
    
    def process_nested_fk(obj, obj_class):
        if not isinstance(obj, dict) or not obj_class:
            return obj
        
        result = obj.copy()
        
        # 处理外键字段
        for field_name in list(result.keys()):
            if hasattr(obj_class, field_name):
                field = getattr(obj_class, field_name)
                # 外键三种值：int、None、dict
                if isinstance(field, ForeignKeyField):
                    field_value = result[field_name]
                    # [1]：外键字段为None
                    # 如果数据库存储的是-1，获取的时候会出错，所以不如保持 None
                    if field_value is None:
                        # print('None', field_name)
                        result[field.column_name] = None
                    
                    # [2]：外键字段已经是ID值（整数）
                    elif isinstance(field_value, int):
                        # print('int', field_name)
                        result[field.column_name] = field_value
                        # 去掉实体等于整型的情况
                        del result[field_name]

                    # [3]：外键字段被展开为字典对象
                    elif isinstance(field_value, dict):
                        # print('dict', field_name)
                        # 获取外键对象的主键值
                        foreign_key_obj = field_value
                        primary_key_value = None
                        
                        # 尝试常见的主键字段名
                        for pk_field in [field.rel_model._meta.primary_key.name]:
                            if pk_field in foreign_key_obj:
                                primary_key_value = foreign_key_obj[pk_field]
                                break
                        
                        if primary_key_value is not None:
                            result[field.column_name] = primary_key_value

                        # 实体需要保留
                        # del result[field_name]
        
        # 递归处理嵌套对象
        for key, value in result.items():
            if isinstance(value, dict):
                # 查找对应的模型类
                nested_class = None
                if hasattr(obj_class, key):
                    nested_field = getattr(obj_class, key)
                    if hasattr(nested_field, 'rel_model'):
                        nested_class = nested_field.rel_model
                result[key] = process_nested_fk(value, nested_class)
            
            elif isinstance(value, list) and value:
                # 处理对象列表
                nested_class = None
                if hasattr(obj_class, key):
                    nested_field = getattr(obj_class, key)
                    if hasattr(nested_field, 'rel_model'):
                        nested_class = nested_field.rel_model
                result[key] = [process_nested_fk(item, nested_class) if isinstance(item, dict) else item 
                              for item in value]
        
        return result
    
    return process_nested_fk(data, type(model))

def model_to_dict_x2(model, recurse=True, backrefs=False, max_depth=1, extra_attrs=None, 
                    only=None, exclude=None, **kwargs
):
    """
    增强版 model_to_dict，自动处理外键字段转换，同时支持所有原始参数
    
    参数:
        model: Peewee 模型实例
        recurse: 是否递归处理关联对象
        backrefs: 是否处理反向引用
        max_depth: 递归最大深度
        extra_attrs: 包含额外属性
        only: 只包含指定字段
        exclude: 排除指定字段
        **kwargs: 其他传递给原始 model_to_dict 的参数
    
    返回:
        转换后的字典
    """
    if isinstance(model, dict):
        return model
    
    if exclude is None:
        exclude = []
    
    # 获取所有字段
    fields = model._meta.fields
    
    if not recurse:
        # 找出所有外键
        fk_fields = []
        for field_name, field in fields.items():
            if isinstance(field, ForeignKeyField):
                exclude.append(field)
                fk_fields.append(field_name)
        
        # 确保外键字段不被原始 model_to_dict 处理
        exclude = list(set(exclude) | set(fk_fields))
        
        # 调用原始 model_to_dict
        data = model_to_dict(
            model,
            recurse=recurse,
            backrefs=backrefs,
            only=only,
            exclude=exclude,
            max_depth=max_depth,
            extra_attrs=extra_attrs,
            **kwargs
        )
        
        # 处理外键字段
        for field_name in fk_fields:
            field = fields[field_name]
            data[field.column_name] = getattr(model, field.column_name)
            
    else:
        data = model_to_dict(
            model,
            recurse=recurse,
            backrefs=backrefs,
            only=only,
            exclude=exclude,
            max_depth=max_depth,
            extra_attrs=extra_attrs,
            **kwargs
        )
    
    return data


if __name__ == '__main__':
    import array
    import collections
    
    # 使用示例
    print(is_null(None))  # True
    print(is_null(""))  # True
    print(is_null("   "))  # True
    print(is_null([]))  # True
    print(is_null(set()))  # True
    print(is_null(()))  # True
    print(is_null([1, 2, 3]))  # False
    print(is_null(array.array('i', [1, 2, 3])))  # False
    print(is_null({'a': 1}))  # False