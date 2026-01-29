from typing import *

from .BaseHoldObject import BaseHoldObject
from .FrozenDataObject import FrozenDataObject

__all__ = ["FrozenHoldObject"]


class FrozenHoldObject(FrozenDataObject, BaseHoldObject):
    data: Any
    __slots__ = ()

    @property
    def data(self: Self) -> Any:
        return self._data
