import collections
from typing import *

import setdoc

from datahold._utils.wrapping import wraps

from .BaseDataSet import BaseDataSet
from .DataObject import DataObject

__all__ = ["DataSet"]

Item = TypeVar("Item")


class DataSet(DataObject, BaseDataSet[Item], collections.abc.MutableSet[Item]):
    data: frozenset[Item]
    __slots__ = ()

    @wraps(set[Item])
    def __iand__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        ans: Any
        data: set[Item]
        data = set[Item](self.data)
        ans = data.__iand__(*args, **kwargs)
        self.data = frozenset[Item](data)
        return ans

    @setdoc.basic
    def __init__(self: Self, data: Iterable = (), /) -> None:
        self.data = frozenset[Item](data)

    @wraps(set[Item])
    def __ior__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        ans: Any
        data: set[Item]
        data = set[Item](self.data)
        ans = data.__ior__(*args, **kwargs)
        self.data = frozenset[Item](data)
        return ans

    @wraps(set[Item])
    def __isub__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        ans: Any
        data: set[Item]
        data = set[Item](self.data)
        ans = data.__isub__(*args, **kwargs)
        self.data = frozenset[Item](data)
        return ans

    @wraps(set[Item])
    def __ixor__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        ans: Any
        data: set[Item]
        data = set[Item](self.data)
        ans = data.__ixor__(*args, **kwargs)
        self.data = frozenset[Item](data)
        return ans

    @wraps(set[Item])
    def add(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        ans: Any
        data: set[Item]
        data = set[Item](self.data)
        ans = data.add(*args, **kwargs)
        self.data = frozenset[Item](data)
        return ans

    @wraps(set[Item])
    def clear(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        ans: Any
        data: set[Item]
        data = set[Item](self.data)
        ans = data.clear(*args, **kwargs)
        self.data = frozenset[Item](data)
        return ans

    @wraps(set[Item])
    def difference_update(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        ans: Any
        data: set[Item]
        data = set[Item](self.data)
        ans = data.difference_update(*args, **kwargs)
        self.data = frozenset[Item](data)
        return ans

    @wraps(set[Item])
    def discard(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        ans: Any
        data: set[Item]
        data = set[Item](self.data)
        ans = data.discard(*args, **kwargs)
        self.data = frozenset[Item](data)
        return ans

    @wraps(set[Item])
    def intersection_update(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        ans: Any
        data: set[Item]
        data = set[Item](self.data)
        ans = data.intersection_update(*args, **kwargs)
        self.data = frozenset[Item](data)
        return ans

    @wraps(set[Item])
    def pop(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        ans: Any
        data: set[Item]
        data = set[Item](self.data)
        ans = data.pop(*args, **kwargs)
        self.data = frozenset[Item](data)
        return ans

    @wraps(set[Item])
    def remove(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        ans: Any
        data: set[Item]
        data = set[Item](self.data)
        ans = data.remove(*args, **kwargs)
        self.data = frozenset[Item](data)
        return ans

    @wraps(set[Item])
    def symmetric_difference_update(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        ans: Any
        data: set[Item]
        data = set[Item](self.data)
        ans = data.symmetric_difference_update(*args, **kwargs)
        self.data = frozenset[Item](data)
        return ans

    @wraps(set[Item])
    def update(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        ans: Any
        data: set[Item]
        data = set[Item](self.data)
        ans = data.update(*args, **kwargs)
        self.data = frozenset[Item](data)
        return ans
