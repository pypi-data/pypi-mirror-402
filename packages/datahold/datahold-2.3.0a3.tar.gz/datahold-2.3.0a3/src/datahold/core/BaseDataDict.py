import collections
from abc import abstractmethod
from typing import *

from frozendict import frozendict

from datahold._utils.wrapping import wraps

from .BaseDataObject import BaseDataObject

__all__ = ["BaseDataDict"]

Key = TypeVar("Key")
Value = TypeVar("Value")


class BaseDataDict(
    BaseDataObject,
    collections.abc.Mapping[Key, Value],
):
    data: frozendict[Key, Value]
    __slots__ = ()

    @wraps(dict[Key, Value])
    def __contains__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        return dict[Key, Value](self.data).__contains__(*args, **kwargs)

    @wraps(dict[Key, Value])
    def __eq__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        return dict[Key, Value](self.data).__eq__(*args, **kwargs)

    @wraps(dict[Key, Value])
    def __format__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        return dict[Key, Value](self.data).__format__(*args, **kwargs)

    @wraps(dict[Key, Value])
    def __ge__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        return dict[Key, Value](self.data).__ge__(*args, **kwargs)

    @wraps(dict[Key, Value])
    def __getitem__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        return dict[Key, Value](self.data).__getitem__(*args, **kwargs)

    @wraps(dict[Key, Value])
    def __gt__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        return dict[Key, Value](self.data).__gt__(*args, **kwargs)

    @abstractmethod
    @wraps(dict[Key, Value])
    def __init__(self: Self, *args: Any, **kwargs: Any) -> None:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        ...

    @wraps(dict[Key, Value])
    def __iter__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        return dict[Key, Value](self.data).__iter__(*args, **kwargs)

    @wraps(dict[Key, Value])
    def __le__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        return dict[Key, Value](self.data).__le__(*args, **kwargs)

    @wraps(dict[Key, Value])
    def __len__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        return dict[Key, Value](self.data).__len__(*args, **kwargs)

    @wraps(dict[Key, Value])
    def __lt__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        return dict[Key, Value](self.data).__lt__(*args, **kwargs)

    @wraps(dict[Key, Value])
    def __or__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        return dict[Key, Value](self.data).__or__(*args, **kwargs)

    @wraps(dict[Key, Value])
    def __repr__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        return dict[Key, Value](self.data).__repr__(*args, **kwargs)

    @wraps(dict[Key, Value])
    def __reversed__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        return dict[Key, Value](self.data).__reversed__(*args, **kwargs)

    @wraps(dict[Key, Value])
    def __ror__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        return dict[Key, Value](self.data).__ror__(*args, **kwargs)

    @wraps(dict[Key, Value])
    def __str__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        return dict[Key, Value](self.data).__str__(*args, **kwargs)

    @classmethod
    @wraps(dict[Key, Value])
    def fromkeys(cls: type[Self], *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        return cls[Key, Value](dict[Key, Value].fromkeys(*args, **kwargs))

    @wraps(dict[Key, Value])
    def get(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        return dict[Key, Value](self.data).get(*args, **kwargs)

    @wraps(dict[Key, Value])
    def items(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        return dict[Key, Value](self.data).items(*args, **kwargs)

    @wraps(dict[Key, Value])
    def keys(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        return dict[Key, Value](self.data).keys(*args, **kwargs)

    @wraps(dict[Key, Value])
    def values(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        return dict[Key, Value](self.data).values(*args, **kwargs)
