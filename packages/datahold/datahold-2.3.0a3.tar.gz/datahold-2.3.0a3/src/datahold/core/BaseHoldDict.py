from typing import *

from frozendict import frozendict

from .BaseDataDict import BaseDataDict
from .BaseHoldObject import BaseHoldObject

__all__ = ["BaseHoldDict"]

Key = TypeVar("Key")
Value = TypeVar("Value")


class BaseHoldDict(BaseHoldObject, BaseDataDict[Key, Value]):
    data: frozendict[Key, Value]
    __slots__ = ()
