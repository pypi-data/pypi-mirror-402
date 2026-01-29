from typing import *

from .BaseDataSet import BaseDataSet
from .BaseHoldObject import BaseHoldObject

__all__ = ["BaseHoldSet"]

Item = TypeVar("Item")


class BaseHoldSet(BaseHoldObject, BaseDataSet[Item]):
    data: frozenset[Item]
    __slots__ = ()
