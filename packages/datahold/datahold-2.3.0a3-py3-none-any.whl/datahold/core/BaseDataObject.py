from abc import ABCMeta, abstractmethod
from typing import *

__all__ = ["BaseDataObject"]


class BaseDataObject(metaclass=ABCMeta):

    data: Any
    __slots__ = ()

    @property
    @abstractmethod
    def data(self: Self) -> Any: ...
