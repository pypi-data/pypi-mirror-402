import threading
import asyncio
from functools import wraps
from typing import Any, Callable, Dict


class UserLock:
    """
    用户级别锁管理类
    为不同用户创建独立的锁，确保同一用户的方法调用是串行的，但不同用户之间可以并行执行
    """
    
    def __init__(self):
        # 用于存储每个用户的锁
        self._user_locks: Dict[Any, threading.Lock] = {}
        self._user_async_locks: Dict[Any, asyncio.Lock] = {}
        self._global_lock = threading.Lock()
        self._global_async_lock = asyncio.Lock()
    
    def get_user_lock(self, user_id: Any) -> threading.Lock:
        """
        获取指定用户的锁（同步环境）
        
        Args:
            user_id: 用户ID
            
        Returns:
            threading.Lock: 用户的锁对象
        """
        # 双重检查锁定模式获取用户锁
        if user_id not in self._user_locks:
            with self._global_lock:
                if user_id not in self._user_locks:
                    self._user_locks[user_id] = threading.Lock()
        return self._user_locks[user_id]
    
    def get_user_async_lock(self, user_id: Any) -> asyncio.Lock:
        """
        获取指定用户的锁（异步环境）
        
        Args:
            user_id: 用户ID
            
        Returns:
            asyncio.Lock: 用户的锁对象
        """
        # 双重检查锁定模式获取用户锁
        if user_id not in self._user_async_locks:
            # 注意：在实际使用中，这段代码需要在async环境中运行
            if user_id not in self._user_async_locks:
                self._user_async_locks[user_id] = asyncio.Lock()
        return self._user_async_locks[user_id]


# 全局用户锁管理器实例
_user_lock_manager = UserLock()


def user_lock(user_id_getter: Callable[..., Any]):
    """
    为不同用户创建独立锁的装饰器。
    确保同一用户的方法调用是串行的，但不同用户之间可以并行执行。

    Args:
        user_id_getter: 一个可调用对象，用于从函数参数中获取用户ID

    用法示例:
        @user_lock(lambda self, user_id, *args, **kwargs: user_id)
        def my_method(self, user_id, data):
            # 同一个user_id的调用会串行执行
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 获取用户ID
            user_id = user_id_getter(*args, **kwargs)
            
            # 获取并使用用户锁
            user_lock = _user_lock_manager.get_user_lock(user_id)
            with user_lock:
                return func(*args, **kwargs)
        return wrapper
    return decorator


def async_user_lock(user_id_getter: Callable[..., Any]):
    """
    异步版本的用户级别锁装饰器。
    确保同一用户的方法调用是串行的，但不同用户之间可以并行执行。

    Args:
        user_id_getter: 一个可调用对象，用于从函数参数中获取用户ID

    用法示例:
        @async_user_lock(lambda self, user_id, *args, **kwargs: user_id)
        async def my_method(self, user_id, data):
            # 同一个user_id的调用会串行执行
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取用户ID
            user_id = user_id_getter(*args, **kwargs)
            
            # 获取并使用用户锁
            user_lock = _user_lock_manager.get_user_async_lock(user_id)
            async with user_lock:
                return await func(*args, **kwargs)
        return wrapper
    return decorator


# 默认的用户ID获取函数
def first_param_user_id(*args, **kwargs):
    """
    默认的用户ID获取函数，假设第一个参数是用户ID
    """
    if args:
        return args[0]
    return None


