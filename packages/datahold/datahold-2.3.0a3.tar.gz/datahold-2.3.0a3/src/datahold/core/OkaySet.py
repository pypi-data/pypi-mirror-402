from typing import *

import setdoc

from datahold.core.HoldSet import HoldSet
from datahold.core.OkayObject import OkayObject

__all__ = ["OkaySet"]

Item = TypeVar("Item")


class OkaySet(OkayObject, HoldSet[Item]):
    data: frozenset[Item]
    __slots__ = ()

    @setdoc.basic
    def __and__(self: Self, other: Any, /) -> Self:
        return type(self)(self._data & set(other))

    @setdoc.basic
    def __or__(self: Self, other: Any, /) -> Self:
        return type(self)(self._data | set(other))

    @setdoc.basic
    def __sub__(self: Self, other: Any, /) -> Self:
        return type(self)(self._data - set(other))

    @setdoc.basic
    def __xor__(self: Self, other: Any, /) -> Self:
        return type(self)(self._data ^ set(other))

    def difference(self: Self, /, *others: Any) -> Self:
        "This method returns a copy of self without the items also found in any of the others."
        return type(self)(self._data.difference(*others))

    def intersection(self: Self, /, *others: Any) -> set:
        "This method returns a copy of self without the items not found in all of the others."
        return type(self)(self._data.intersection(*others))

    def symmetric_difference(self: Self, other: Any, /) -> Self:
        "This method returns the symmetric difference between self and other."
        return type(self)(self._data.symmetric_difference(other))

    def union(self: Self, /, *others: Any) -> Self:
        "This method returns a copy of self with all the items in the others added."
        return type(self)(self._data.union(*others))
