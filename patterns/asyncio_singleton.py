from typing_extensions import Self
import asyncio
from asyncio.locks import Lock
import inspect


def _async_init_with_lock(func):
    def instance_function(instance, lock: Lock):
        async def wrapper(*args, **kwargs):
            # Lock to avoid creating multiple instances
            await lock.acquire()
            function_result = await func(instance, *args, **kwargs)
            # Relesae lock
            lock.release()

            if function_result is not None:
                raise TypeError("__async_init__() should return None")
            return instance

        return wrapper

    instance_function.__name__ = func.__name__
    return instance_function


class SingletonMeta(type):
    """
    Do not use sync '__init__' if used this class as metaclass shoud be used in asynchronious context.
    Use 'async __init__' instead.

    Rewrites __async_init__ function, do not use this in method naming.
    """

    _instances = {}
    _lock = asyncio.Lock()

    def __new__(
        cls, clazz_name: str, clazz_base: tuple, clazz_dict: dict, *args, **kwargs
    ) -> Self:
        if "__init__" in clazz_dict and inspect.iscoroutinefunction(
            clazz_dict["__init__"]
        ):
            clazz_dict["__async_init__"] = _async_init_with_lock(
                clazz_dict.pop("__init__")
            )
        return super().__new__(cls, clazz_name, clazz_base, clazz_dict, *args, **kwargs)

    def __call__(cls, *args, **kw):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kw)
            if not isinstance(instance, cls) or not hasattr(cls, "__async_init__"):
                # Could cause shadowing instances when initializing first time.
                cls._instances[cls] = instance
            else:
                cls._instances[cls] = instance.__async_init__(cls._lock)(*args, **kw)
        return cls._instances[cls]
