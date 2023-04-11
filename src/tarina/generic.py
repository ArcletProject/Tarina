from __future__ import annotations

import contextlib
import sys
import types
from typing import TYPE_CHECKING, Any, List, Literal, TypeVar, Union

from typing_extensions import Annotated, get_args
from typing_extensions import get_origin as typing_ext_get_origin

if TYPE_CHECKING:
    from types import GenericAlias  # noqa
else:
    GenericAlias: type = type(List[int])

AnnotatedType: type = type(Annotated[int, lambda x: x > 0])
Unions = (
    (Union, types.UnionType) if sys.version_info >= (3, 10) else (Union,)  # pragma: no cover
)


def get_origin(obj: Any) -> Any:
    return typing_ext_get_origin(obj) or obj


def generic_isinstance(obj: Any, par: type | Any | tuple[type, ...]) -> bool:
    """检查 obj 是否是 args 中的一个类型, 支持泛型, Any, Union
    Args:
        obj (Any): 要检查的对象
        par (Union[type, Any, Tuple[type, ...]]): 要检查的对象的类型
    Returns:
        bool: 是否是类型
    """
    if par is Any:
        return True
    with contextlib.suppress(TypeError):
        if isinstance(par, AnnotatedType):
            return generic_isinstance(obj, get_args(par)[0])
        if isinstance(par, type):
            return isinstance(obj, par)
        if get_origin(par) is Literal:
            return obj in get_args(par)
        if get_origin(par) in Unions:  # pragma: no cover
            return any(generic_isinstance(obj, p) for p in get_args(par))
        if isinstance(par, TypeVar):  # pragma: no cover
            if par.__constraints__:
                return any(generic_isinstance(obj, p) for p in par.__constraints__)
            return generic_isinstance(obj, par.__bound__) if par.__bound__ else True
        if isinstance(par, tuple):
            return any(generic_isinstance(obj, p) for p in par)
        if isinstance(obj, get_origin(par)):  # type: ignore
            return True
    return False


def generic_issubclass(cls: type, par: Union[type, Any, tuple[type, ...]]) -> bool:
    """检查 cls 是否是 args 中的一个子类, 支持泛型, Any, Union
    Args:
        cls (type): 要检查的类
        par (Union[type, Any, Tuple[type, ...]]): 要检查的类的父类
    Returns:
        bool: 是否是父类
    """
    if par is Any:
        return True
    with contextlib.suppress(TypeError):
        if isinstance(par, AnnotatedType):
            return generic_issubclass(cls, get_args(par)[0])
        if isinstance(par, type):
            return issubclass(cls, par)
        if get_origin(par) in Unions:
            return any(generic_issubclass(cls, p) for p in get_args(par))
        if isinstance(par, TypeVar):
            if par.__constraints__:
                return any(generic_issubclass(cls, p) for p in par.__constraints__)
            if par.__bound__:
                return generic_issubclass(cls, par.__bound__)
        if isinstance(par, tuple):
            return any(generic_issubclass(cls, p) for p in par)
        if issubclass(cls, get_origin(par)):  # type: ignore
            return True
    return False
