from typing import *

import setdoc
from cmp3 import CmpABC
from datarepr import datarepr
from scaevola import Scaevola

from .HoldObject import HoldObject

__all__ = ["OkayObject"]


class OkayObject(CmpABC, Scaevola, HoldObject):
    data: Any
    __slots__ = ()

    @setdoc.basic
    def __bool__(self: Self, /) -> bool:
        return bool(self._data)

    @setdoc.basic
    def __cmp__(self: Self, other: Any, /) -> Optional[float | int]:
        ref: Any
        if type(self) is type(other):
            ref = other
        else:
            try:
                ref = type(self._data)(other)
            except Exception:
                return
        try:
            if self._data <= ref._data <= self._data:
                return 0
            if (not self._data <= ref._data) and ref._data <= self._data:
                return 1
            if self._data <= ref._data and (not ref._data <= self._data):
                return -1
        except Exception:
            if self._data == ref._data:
                return 0
        return float("nan")

    @setdoc.basic
    def __format__(self: Self, format_spec: Any = "", /) -> str:
        return format(self._data, str(format_spec))

    @setdoc.basic
    def __repr__(self: Self, /) -> str:
        return datarepr(type(self).__name__, self._data)

    @setdoc.basic
    def __str__(self: Self, /) -> str:
        return repr(self)
