from typing import *

from .BaseDataList import BaseDataList
from .BaseHoldObject import BaseHoldObject

__all__ = ["BaseHoldList"]

Item = TypeVar("Item")


class BaseHoldList(BaseHoldObject, BaseDataList[Item]):
    data: tuple[Item, ...]
    __slots__ = ()
