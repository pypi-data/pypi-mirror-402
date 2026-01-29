import inspect as ins
from functools import partial
from types import FunctionType
from typing import *

__all__ = ["wraps"]


def getAnnotationsDict(sig: ins.Signature) -> dict:
    ans: dict[str, ins.Parameter]
    p: ins.Parameter
    ans = dict()
    for p in sig.parameters.values():
        ans[p.name] = p.annotation
    ans["return"] = sig.return_annotation
    return ans


def getNonEmpty(value: Any, backup: Any = Any) -> Any:
    if value is ins.Parameter.empty:
        return backup
    else:
        return value


def update(cls: type, member: FunctionType | classmethod) -> FunctionType | classmethod:
    if type(member) is classmethod:
        update_classmethod(cls, member)
    else:
        update_func(cls, member)
    return member


def update_classmethod(cls: type, clsmthd: classmethod) -> None:
    params: list
    a: Any
    func: FunctionType
    p: ins.Parameter
    q: ins.Parameter
    oldsig: ins.Signature
    old: Callable
    func = clsmthd.__func__
    old = getattr(cls, func.__name__)
    func.__doc__ = clsmthd.__doc__
    try:
        oldsig = ins.signature(old)
    except ValueError:
        return
    p = ins.Parameter(
        name="cls",
        kind=ins.Parameter.POSITIONAL_ONLY,
        annotation=type[Self],
    )
    params = [p]
    for p in oldsig.parameters.values():
        a = getNonEmpty(p.annotation)
        q = p.replace(annotation=a)
        params.append(q)
    func.__signature__ = ins.Signature(params, return_annotation=Self)
    func.__annotations__ = getAnnotationsDict(func.__signature__)


def update_func(cls: type, func: FunctionType) -> None:
    params: list
    a: Any
    n: int
    p: ins.Parameter
    q: ins.Parameter
    oldsig: ins.Signature
    old: Callable
    old = getattr(cls, func.__name__)
    func.__doc__ = old.__doc__
    try:
        oldsig = ins.signature(old)
    except ValueError:
        return
    params = list()
    for n, p in enumerate(oldsig.parameters.values()):
        a = getNonEmpty(p.annotation) if n else Self
        q = p.replace(annotation=a)
        params.append(q)
    if func.__name__ == "__init__":
        a = None
    else:
        a = getNonEmpty(oldsig.return_annotation)
    func.__signature__ = ins.Signature(params, return_annotation=a)
    func.__annotations__ = getAnnotationsDict(func.__signature__)


def wraps(cls: type) -> partial:
    return partial(update, cls)
