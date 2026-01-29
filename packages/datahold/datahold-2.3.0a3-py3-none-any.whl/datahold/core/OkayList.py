from typing import *

import setdoc

from datahold.core.HoldList import HoldList
from datahold.core.OkayObject import OkayObject

__all__ = ["OkayList"]

Item = TypeVar("Item")


class OkayList(OkayObject, HoldList[Item]):
    data: tuple[Item, ...]
    __slots__ = ()

    @setdoc.basic
    def __add__(self: Self, other: Any, /) -> Self:
        return type(self)(self._data + list(other))

    @setdoc.basic
    def __mul__(self: Self, value: SupportsIndex, /) -> Self:
        return type(self)(self.data * value)

    @setdoc.basic
    def __rmul__(self: Self, value: SupportsIndex, /) -> Self:
        return self * value
