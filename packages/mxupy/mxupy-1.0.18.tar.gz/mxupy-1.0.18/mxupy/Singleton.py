import threading


class Singleton:
    """
    线程安全的单例基类
    继承此类的子类将自动具备单例特性
    """
    _insts = {}
    _init_locks = {}
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """
        线程安全的单例实现
        """
        if cls not in cls._insts:
            with cls._lock:
                # 双重检查锁定模式
                if cls not in cls._insts:
                    cls._insts[cls] = super().__new__(cls)
                    cls._init_locks[cls] = threading.Lock()
        return cls._insts[cls]

    def __init__(self, *args, **kwargs):
        # 使用每个类的特定锁来确保 __init__ 只执行一次
        with self._init_locks[self.__class__]:
            if getattr(self, '_inited', False):
                return
            self._inited = True
            # 实际的初始化代码应该在子类中实现 init 方法
            self.init(*args, **kwargs)

    def init(self, *args, **kwargs):
        # 子类应重写此方法而不是 __init__
        pass

    @classmethod
    def inst(cls):
        """
        获取类的单例实例

        Returns:
            Singleton: 单例实例
        """
        return cls()


if __name__ == "__main__":
    import concurrent.futures

    class Logger(Singleton):
        # 注意，重载init方法，而不是 __init__
        def init(self, name: str = "default"):
            self.name = name
            print(f"[{self.name}] Logger init running once")

    def test(n):
        return Logger(str(n))

    # 单次测试
    print(id(test("test")))

    # 20 线程并发获取
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
        instances = list(pool.map(test, range(20)))

    # 全部指向同一对象
    print({id(inst) for inst in instances})  # 仅一个 ID
