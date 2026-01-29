from typing import *

import setdoc

from .BaseHoldList import BaseHoldList
from .FrozenDataList import FrozenDataList
from .FrozenHoldObject import FrozenHoldObject

__all__ = ["FrozenHoldList"]

Item = TypeVar("Item")


class FrozenHoldList(FrozenHoldObject, FrozenDataList, BaseHoldList[Item]):
    data: tuple[Item, ...]
    __slots__ = ()

    @setdoc.basic
    def __init__(self: Self, data: Iterable, /) -> None:
        self._data = tuple[Item, ...](data)
