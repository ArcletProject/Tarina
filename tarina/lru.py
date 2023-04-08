try:
    from lru import LRU
except ImportError:
    from collections import OrderedDict

    class LRU:

        __slots__ = ("__max", "__cache", "__size", "__callback")

        def __init__(self, size, callback=None) -> None:
            if size < 1:
                raise ValueError("Size should be a positive number")
            self.__max = size
            self.__cache = OrderedDict()
            self.__size = 0
            self.__callback = callback

        def clear(self) -> None:
            self.__cache.clear()

        def get(self, key, default):
            if key in self.__cache:
                self.__cache.move_to_end(key, last=False)
                return self.__cache[key]
            return default

        def get_size(self):
            return self.__max

        def has_key(self, key) -> bool:
            return key in self.__cache

        def keys(self):
            return list(self.__cache.keys())

        def values(self):
            return list(self.__cache.values())

        def items(self):
            return list(self.__cache.items())

        def peek_first_item(self):
            return self.__cache.items()[0]

        def peek_last_item(self):
            return self.__cache.items()[-1]

        def pop(self, key, default=None):
            return self.__cache.pop(key, default)

        def popitem(self, least_recent=True):
            return self.__cache.popitem(last=least_recent)

        def setdefault(self, key, value=None):
            if key in self.__cache:
                return self.__cache[key]
            self.__setitem__(key, value)
            return value
        
        def set_callback(self, callback):
            self.__callback = callback
        
        def set_size(self, size):
            self.__max = size
            if self.__max < self.__size:
                for _ in range(self.__size - self.__max):
                    k, v = self.__cache.popitem(last=True)
                    self.__size -= 1
                    if self.__callback:
                        self.__callback(k, v)

        def update(self, *args, **kwargs):
            self.__cache.update(*args, **kwargs)

        __contains__ = has_key

        def __delitem__(self, key):
            self.__cache.pop(key)

        def __getitem__(self, item):
            if item in self.__cache:
                self.__cache.move_to_end(item, last=False)
                return self.__cache[item]
            raise KeyError(item)

        def __len__(self) -> int:
            return len(self.__cache)

        def __repr__(self) -> str:
            return repr(self.__cache)

        def __setitem__(self, key, value):
            if key in self.__cache:
                self.__cache.move_to_end(key, last=False)
                self.__cache[key] = value
                return
            self.__cache[key] = value
            self.__size += 1
            if self.__max < self.__size:
                _k, _v = self.__cache.popitem(last=True)
                self.__size -= 1
                if self.__callback:
                    self.__callback(_k, _v)
