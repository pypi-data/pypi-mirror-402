import collections
from typing import *

import setdoc
from frozendict import frozendict

from datahold._utils.wrapping import wraps

from .BaseDataDict import BaseDataDict
from .DataObject import DataObject

__all__ = ["DataDict"]

Key = TypeVar("Key")
Value = TypeVar("Value")


class DataDict(
    DataObject, BaseDataDict[Key, Value], collections.abc.MutableMapping[Key, Value]
):
    data: frozendict[Key, Value]
    __slots__ = ()

    @wraps(dict[Key, Value])
    def __delitem__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        ans: Any
        data: dict[Key, Value]
        data = dict[Key, Value](self.data)
        ans = data.__delitem__(*args, **kwargs)
        self.data = frozendict[Key, Value](data)
        return ans

    @setdoc.basic
    def __init__(self: Self, data: Any = (), /, **kwargs: Any) -> None:
        self.data = frozendict[Key, Value](data, **kwargs)

    @wraps(dict[Key, Value])
    def __ior__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        ans: Any
        data: dict[Key, Value]
        data = dict[Key, Value](self.data)
        ans = data.__ior__(*args, **kwargs)
        self.data = frozendict[Key, Value](data)
        return ans

    @wraps(dict[Key, Value])
    def __setitem__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        ans: Any
        data: dict[Key, Value]
        data = dict[Key, Value](self.data)
        ans = data.__setitem__(*args, **kwargs)
        self.data = frozendict[Key, Value](data)
        return ans

    @wraps(dict[Key, Value])
    def clear(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        ans: Any
        data: dict[Key, Value]
        data = dict[Key, Value](self.data)
        ans = data.clear(*args, **kwargs)
        self.data = frozendict[Key, Value](data)
        return ans

    @wraps(dict[Key, Value])
    def pop(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        ans: Any
        data: dict[Key, Value]
        data = dict[Key, Value](self.data)
        ans = data.pop(*args, **kwargs)
        self.data = frozendict[Key, Value](data)
        return ans

    @wraps(dict[Key, Value])
    def popitem(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        ans: Any
        data: dict[Key, Value]
        data = dict[Key, Value](self.data)
        ans = data.popitem(*args, **kwargs)
        self.data = frozendict[Key, Value](data)
        return ans

    @wraps(dict[Key, Value])
    def setdefault(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        ans: Any
        data: dict[Key, Value]
        data = dict[Key, Value](self.data)
        ans = data.setdefault(*args, **kwargs)
        self.data = frozendict[Key, Value](data)
        return ans

    @wraps(dict[Key, Value])
    def update(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        ans: Any
        data: dict[Key, Value]
        data = dict[Key, Value](self.data)
        ans = data.update(*args, **kwargs)
        self.data = frozendict[Key, Value](data)
        return ans
