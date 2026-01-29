from typing import *

from .BaseDataObject import BaseDataObject

__all__ = ["HoldBase"]


class BaseHoldObject(BaseDataObject):
    data: Any
    __slots__ = ("_data",)
