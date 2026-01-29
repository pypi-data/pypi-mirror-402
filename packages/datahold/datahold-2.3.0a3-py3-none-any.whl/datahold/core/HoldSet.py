from typing import *

import setdoc

from .BaseHoldSet import BaseHoldSet
from .DataSet import DataSet
from .HoldObject import HoldObject

__all__ = ["HoldSet"]

Item = TypeVar("Item")


class HoldSet(HoldObject, DataSet[Item], BaseHoldSet[Item]):
    data: frozenset[Item]
    __slots__ = ()

    @property
    @setdoc.basic
    def data(self: Self) -> frozenset[Item]:
        return self._data

    @data.setter
    def data(self: Self, value: Any) -> None:
        self._data = frozenset[Item](value)
