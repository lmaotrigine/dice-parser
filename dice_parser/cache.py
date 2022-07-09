from __future__ import annotations
from collections import Counter

from collections.abc import Callable, Iterator, MutableMapping
from typing import Any, Literal, TypeVar, Hashable

K = TypeVar('K', bound=Hashable)
V = TypeVar('V')


class _DefaultSize:
    __slots__ = ()
    
    def __getitem__(self, _) -> Literal[1]:
        return 1
    
    def __setitem__(self, _, value: Any) -> None:
        assert value == 1
        
    def pop(self, _) -> Literal[1]:
        return 1


class _MissingSentinel:
    __slots__ = ()
    
    def __eq__(self, _) -> Literal[False]:
        return False
    
    def __hash__(self) -> Literal[0]:
        return 0
        
    def __bool__(self) -> Literal[False]:
        return False
    
    def __repr__(self) -> str:
        return '...'


MISSING: Any = _MissingSentinel()


class LFUCache(MutableMapping[K, V]):
    
    __size = _DefaultSize()
    
    def __init__(self, maxsize: int, getsizeof: Callable[[object], int] | None = None) -> None:
        if getsizeof:
            self.getsizeof = getsizeof
        if self.getsizeof is not LFUCache.getsizeof:
            self.__size = dict()
        self.__data: dict[K, V | None] = dict()
        self.__currsize = 0
        self.__maxsize = maxsize
        self.__counter = Counter()
            
    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({repr(self.__data)}, maxsize={self.__maxsize!r}, currsize={self.__currsize!r})'
    
    def __getitem__(self, key: K) -> V | None:
        try:
            value = self.__data[key]
        except KeyError:
            value = self.__missing__(key)
        if key in self:
            self.__counter[key] -= 1
        return value
    
    def __setitem__(self, key: K, value: V | None) -> None:
        maxsize = self.__maxsize
        size = self.getsizeof(value)
        if size > maxsize:
            raise ValueError('value too large')
        if key not in self.__data or self.__size[key] < size:
            while self.__currsize + size > maxsize:
                self.popitem()
        if key in self.__data:
            diffsize = size - self.__size[key]
        else:
            diffsize = size
        self.__data[key] = value
        self.__size[key] = size
        self.__currsize += diffsize
        self.__counter[key] -= 1
        
    def __delitem__(self, key: K) -> None:
        size = self.__size.pop(key)
        del self.__data[key]
        self.__currsize -= size
        del self.__counter[key]
        
    def __contains__(self, key: object) -> bool:
        return key in self.__data
    
    def __missing__(self, key: K) -> V:
        raise KeyError(key)
    
    def __iter__(self) -> Iterator[K]:
        return iter(self.__data)
    
    def __len__(self) -> int:
        return len(self.__data)
    
    def get(self, key: K, default: Any = MISSING) -> V | Any:
        if key in self:
            value = self[key]
            del self[key]
        elif default is MISSING:
            raise KeyError(key)
        else:
            value = default
        return value
    
    def setdefault(self, key: K, default: V | None = None) -> V | None:
        if key in self:
            value = self[key]
        else:
            self[key] = value = default
        return value
    
    def popitem(self) -> tuple[K, V | None]:
        try:
            ((key, _),) = self.__counter.most_common(1)
        except ValueError:
            raise KeyError(f'{type(self).__name__} is empty') from None
        else:
            return (key, self.pop(key))
    
    @property
    def maxsize(self) -> int:
        return self.__maxsize
    
    @property
    def currsize(self) -> int:
        return self.__currsize
    
    @staticmethod
    def getsizeof(value: object, /) -> int:
        return 1