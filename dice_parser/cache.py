# Copyright (c) 2022-present, Varun J., All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Iterator, MutableMapping
from typing import Any, Hashable, Literal, TypeVar


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
    """Least Frequently Used (LFU) cache implementation."""

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
