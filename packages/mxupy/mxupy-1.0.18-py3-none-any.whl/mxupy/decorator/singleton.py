from functools import wraps
import threading
import asyncio

def singleton(cls):
    """
    单例模式装饰器(线程安全)。
    用法：
    @singleton
    class MyClass:
        def __init__(self):
            pass
            
    如果是有参的构造函数，则首次要传统的调用方式：
    MyClass(param1, param2)

    下次，则可以使用 MyClass.inst()

    如果是无参的，则 MyClass() 和 MyClass.inst() 作用一样
    """

    instances = {}
    lock = threading.Lock()

    @wraps(cls)
    def wrapper(*args, **kwargs):
        if cls not in instances:
            with lock:
                if cls not in instances:
                    instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    # # 保持类名等元信息
    # wrapper.__name__ = cls.__name__
    # wrapper.__module__ = cls.__module__
    # wrapper.__doc__ = cls.__doc__

    # 新增：类方法 inst
    wrapper.inst = classmethod(lambda _: instances.get(cls, wrapper()))
    return wrapper


def async_singleton(cls):
    """
    异步环境下的单例模式装饰器(支持FastAPI等异步框架)。
    用法：
    @async_singleton
    class MyClass:
        def __init__(self):
            pass
    """
    instances = {}
    lock = asyncio.Lock()

    @wraps(cls)
    async def wrapper(*args, **kwargs):
        if cls not in instances:
            async with lock:
                if cls not in instances:
                    instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    wrapper.inst = classmethod(lambda _: instances.get(cls, None))
    return wrapper


# def singleton(cls):
#     """
#     支持继承的单例装饰器，每个类有独立实例
#     """
#     instances = {}
#     lock = threading.Lock()

#     @wraps(cls)
#     def wrapper(*args, **kwargs):
#         # 关键：使用实际的类作为键，而不是装饰器包装的类
#         with lock:
#             if cls not in instances:
#                 instances[cls] = cls(*args, **kwargs)
#             return instances[cls]

#     wrapper.inst = classmethod(lambda cls_: instances.get(cls, wrapper()))
#     return wrapper

# def singleton(cls):
#     """
#     修正的单例装饰器
#     """
#     instances = {}
#     lock = threading.Lock()

#     # 移除 @wraps(cls)，它可能引起问题
#     def wrapper(*args, **kwargs):
#         with lock:
#             if cls not in instances:
#                 instances[cls] = cls(*args, **kwargs)
#             return instances[cls]

#     # 保持类名等元信息
#     wrapper.__name__ = cls.__name__
#     wrapper.__module__ = cls.__module__
#     wrapper.__doc__ = cls.__doc__
    
#     return wrapper