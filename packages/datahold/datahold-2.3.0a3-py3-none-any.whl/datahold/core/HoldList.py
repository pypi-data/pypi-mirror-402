from typing import *

import setdoc

from .BaseHoldList import BaseHoldList
from .DataList import DataList
from .HoldObject import HoldObject

__all__ = ["HoldList"]

Item = TypeVar("Item")


class HoldList(HoldObject, DataList[Item, ...], BaseHoldList[Item, ...]):
    data: tuple[Item, ...]
    __slots__ = ()

    @property
    @setdoc.basic
    def data(self: Self) -> tuple[Item, ...]:
        return self._data

    @data.setter
    def data(self: Self, value: Any) -> None:
        self._data = tuple[Item, ...](value)
