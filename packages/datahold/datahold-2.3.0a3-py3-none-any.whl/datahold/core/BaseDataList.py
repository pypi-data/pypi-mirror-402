import collections
from abc import abstractmethod
from typing import *

from datahold._utils.wrapping import wraps

from .BaseDataObject import BaseDataObject

__all__ = ["BaseDataList"]

Item = TypeVar("Item")


class BaseDataList(
    BaseDataObject,
    collections.abc.Sequence[Item],
):
    data: tuple[Item, ...]
    __slots__ = ()

    @wraps(list[Item])
    def __add__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        return list[Item](self.data).__add__(*args, **kwargs)

    @wraps(list[Item])
    def __contains__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        return list[Item](self.data).__contains__(*args, **kwargs)

    @wraps(list[Item])
    def __eq__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        return list[Item](self.data).__eq__(*args, **kwargs)

    @wraps(list[Item])
    def __format__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        return list[Item](self.data).__format__(*args, **kwargs)

    @wraps(list[Item])
    def __ge__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        return list[Item](self.data).__ge__(*args, **kwargs)

    @wraps(list[Item])
    def __getitem__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        return list[Item](self.data).__getitem__(*args, **kwargs)

    @wraps(list[Item])
    def __gt__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        return list[Item](self.data).__gt__(*args, **kwargs)

    @abstractmethod
    @wraps(list[Item])
    def __init__(self: Self, *args: Any, **kwargs: Any) -> None:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        ...

    @wraps(list[Item])
    def __iter__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        return list[Item](self.data).__iter__(*args, **kwargs)

    @wraps(list[Item])
    def __le__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        return list[Item](self.data).__le__(*args, **kwargs)

    @wraps(list[Item])
    def __len__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        return list[Item](self.data).__len__(*args, **kwargs)

    @wraps(list[Item])
    def __lt__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        return list[Item](self.data).__lt__(*args, **kwargs)

    @wraps(list[Item])
    def __mul__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        return list[Item](self.data).__mul__(*args, **kwargs)

    @wraps(list[Item])
    def __repr__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        return list[Item](self.data).__repr__(*args, **kwargs)

    @wraps(list[Item])
    def __reversed__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        return list[Item](self.data).__reversed__(*args, **kwargs)

    @wraps(list[Item])
    def __rmul__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        return list[Item](self.data).__rmul__(*args, **kwargs)

    @wraps(list[Item])
    def __str__(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        return list[Item](self.data).__str__(*args, **kwargs)

    @wraps(list[Item])
    def count(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        return list[Item](self.data).count(*args, **kwargs)

    @wraps(list[Item])
    def index(self: Self, *args: Any, **kwargs: Any) -> Any:
        "This doc string is overwritten together with the signature to match the original as closely as possible."
        return list[Item](self.data).index(*args, **kwargs)
