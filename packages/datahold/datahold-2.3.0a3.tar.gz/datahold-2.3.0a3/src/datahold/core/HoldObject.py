from typing import *

from .BaseHoldObject import BaseHoldObject
from .DataObject import DataObject

__all__ = ["HoldObject"]


class HoldObject(DataObject, BaseHoldObject):
    data: Any
    __slots__ = ()
