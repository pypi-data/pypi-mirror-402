import collections
from typing import *

import setdoc

from datahold._utils.wrapping import wraps

from .BaseDataList import BaseDataList
from .DataObject import DataObject

__all__ = ["DataList"]

Item = TypeVar("Item")


class DataList(DataObject, BaseDataList[Item], collections.abc.MutableSequence[Item]):
    data: tuple[Item, ...]
    __slots__ = ()

    @wraps(list[Item])
    def __delitem__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        ans: Any
        data: list[Item]
        data = list[Item](self.data)
        ans = data.__delitem__(*args, **kwargs)
        self.data = tuple[Item, ...](data)
        return ans

    @wraps(list[Item])
    def __iadd__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        ans: Any
        data: list[Item]
        data = list[Item](self.data)
        ans = data.__iadd__(*args, **kwargs)
        self.data = tuple[Item, ...](data)
        return ans

    @wraps(list[Item])
    def __imul__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        ans: Any
        data: list[Item]
        data = list[Item](self.data)
        ans = data.__imul__(*args, **kwargs)
        self.data = tuple[Item, ...](data)
        return ans

    @setdoc.basic
    def __init__(self: Self, data: Iterable = (), /) -> None:
        self.data = tuple[Item, ...](data)

    @wraps(list[Item])
    def __setitem__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        ans: Any
        data: list[Item]
        data = list[Item](self.data)
        ans = data.__setitem__(*args, **kwargs)
        self.data = tuple[Item, ...](data)
        return ans

    @wraps(list[Item])
    def append(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        ans: Any
        data: list[Item]
        data = list[Item](self.data)
        ans = data.append(*args, **kwargs)
        self.data = tuple[Item, ...](data)
        return ans

    @wraps(list[Item])
    def clear(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        ans: Any
        data: list[Item]
        data = list[Item](self.data)
        ans = data.clear(*args, **kwargs)
        self.data = tuple[Item, ...](data)
        return ans

    @wraps(list[Item])
    def extend(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        ans: Any
        data: list[Item]
        data = list[Item](self.data)
        ans = data.extend(*args, **kwargs)
        self.data = tuple[Item, ...](data)
        return ans

    @wraps(list[Item])
    def insert(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        ans: Any
        data: list[Item]
        data = list[Item](self.data)
        ans = data.insert(*args, **kwargs)
        self.data = tuple[Item, ...](data)
        return ans

    @wraps(list[Item])
    def pop(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        ans: Any
        data: list[Item]
        data = list[Item](self.data)
        ans = data.pop(*args, **kwargs)
        self.data = tuple[Item, ...](data)
        return ans

    @wraps(list[Item])
    def remove(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        ans: Any
        data: list[Item]
        data = list[Item](self.data)
        ans = data.remove(*args, **kwargs)
        self.data = tuple[Item, ...](data)
        return ans

    @wraps(list[Item])
    def reverse(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        ans: Any
        data: list[Item]
        data = list[Item](self.data)
        ans = data.reverse(*args, **kwargs)
        self.data = tuple[Item, ...](data)
        return ans

    @wraps(list[Item])
    def sort(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        ans: Any
        data: list[Item]
        data = list[Item](self.data)
        ans = data.sort(*args, **kwargs)
        self.data = tuple[Item, ...](data)
        return ans
