from typing import *

from frozendict import frozendict

from .BaseDataDict import BaseDataDict
from .FrozenDataObject import FrozenDataObject

__all__ = ["FrozenDataDict"]

Key = TypeVar("Key")
Value = TypeVar("Value")


class FrozenDataDict(FrozenDataObject, BaseDataDict[Key, Value]):
    data: frozendict[Key, Value]
    __slots__ = ()
