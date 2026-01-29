from typing import *

from .BaseDataSet import BaseDataSet
from .FrozenDataObject import FrozenDataObject

__all__ = ["FrozenDataSet"]

Item = TypeVar("Item")


class FrozenDataSet(FrozenDataObject, BaseDataSet[Item]):
    data: frozenset[Item]
    __slots__ = ()
