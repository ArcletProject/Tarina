from __future__ import annotations

import sys
import types
from collections.abc import Iterable, Mapping
from itertools import repeat
from types import GenericAlias
from typing import (
    Annotated,
    Any,
    ClassVar,
    Literal,
    TypedDict,
    TypeVar,
    Union,
    overload,
)

from typing_extensions import Literal as typing_ext_Literal
from typing_extensions import get_args
from typing_extensions import get_origin as typing_ext_get_origin

Unions = (Union, types.UnionType) if sys.version_info >= (3, 10) else (Union,)  # pragma: no cover
_TypedDictMeta = type(TypedDict.__mro_entries__(...)[0])  # type: ignore


def is_typed_dict(cls: Any) -> bool:
    return cls.__class__ is _TypedDictMeta


def origin_is_union(origin: type | None) -> bool:
    return any(origin is u for u in Unions)


def origin_is_literal(origin: type | None) -> bool:
    """判断是否是 Literal 类型"""
    return origin is Literal or origin is typing_ext_Literal


def get_origin(obj: Any) -> Any:
    return typing_ext_get_origin(obj) or obj


def is_classvar(origin):
    return get_origin(origin) is ClassVar


def isclass(cls: Any) -> bool:
    return isinstance(cls, type) and not isinstance(cls, GenericAlias)


def is_optional(scls, cls):
    scls_origin, scls_args = get_origin(scls) or scls, get_args(scls)
    if origin_is_union(scls_origin) and len(scls_args) == 2 and scls_args[1] is type(None):
        return generic_issubclass(scls_args[0], cls)
    return False


def generic_isinstance(obj: Any, par: Any) -> bool:
    """检查 obj 是否是 args 中的一个类型, 支持泛型, Any, Union
    Args:
        obj (Any): 要检查的对象
        par (Any): 要检查的对象的类型
    Returns:
        bool: 是否是类型
    """
    if par is Any:
        return True
    _origin = get_origin(par)
    try:
        if _origin is Annotated:
            return generic_isinstance(obj, get_args(par)[0])
        if _origin is Literal:
            return obj in get_args(par)
        if _origin in Unions:  # pragma: no cover
            for p in get_args(par):
                if generic_isinstance(obj, p):
                    return True
        if par.__class__ is tuple:
            for p in par:
                if generic_isinstance(obj, p):
                    return True
        if par.__class__ is _TypedDictMeta:
            if not isinstance(obj, Mapping):
                return False
            for k, v in par.__annotations__.items():
                if k in par.__required_keys__:
                    if k not in obj:
                        return False
                    if not generic_isinstance(obj[k], v):
                        return False
                elif k in par.__optional_keys__:
                    if k in obj and not generic_isinstance(obj[k], v):
                        return False
            return True
        if isclass(par):
            return isinstance(obj, par)
        if isinstance(par, TypeVar):  # pragma: no cover
            if par.__constraints__:
                return any(generic_isinstance(obj, p) for p in par.__constraints__)
            return generic_isinstance(obj, par.__bound__) if par.__bound__ else True
        if isinstance(obj, _origin):  # type: ignore
            if args := get_args(par):
                if _origin is tuple:
                    if len(args) == 2 and args[1] is Ellipsis:
                        return all(map(generic_isinstance, obj, repeat(args[0])))
                    return len(args) == len(obj) and all(map(generic_isinstance, obj, args))
                elif len(args) == 1 and isinstance(obj, Iterable):
                    return all(map(generic_isinstance, obj, repeat(args[0])))
                elif len(args) == 2 and isinstance(obj, Mapping):
                    return all(map(generic_isinstance, obj.keys(), repeat(args[0]))) and all(
                        map(generic_isinstance, obj.values(), repeat(args[1]))
                    )
            return True
    except TypeError:
        return False
    return False


@overload
def generic_issubclass(scls: Any, cls: Any) -> bool: ...


@overload
def generic_issubclass(scls: Any, cls: Any, list_: Literal[True]) -> list[Any] | bool: ...


def generic_issubclass(scls: Any, cls: Any, list_: bool = False) -> Any:
    """检查 scls 是否是 cls 中的一个子类, 支持泛型, Any, Union
    Args:
        scls (Any): 要检查的类
        cls (Any): 要检查的类的父类
        list_ (bool): 是否返回列表, 默认为 False
    Returns:
        bool: 是否是父类
    """
    if isinstance(cls, tuple):
        return any(generic_issubclass(scls, c, list_) for c in cls)  # type: ignore

    if cls is Any:
        return True

    if scls is Any:
        return [cls] if list_ else cls

    if isclass(scls) and isclass(cls):
        return issubclass(scls, cls)

    try:
        return issubclass(scls, cls)
    except TypeError:
        pass

    scls_origin, scls_args = get_origin(scls) or scls, get_args(scls)
    cls_origin, cls_args = get_origin(cls) or cls, get_args(cls)

    if scls_origin is tuple and cls_origin is tuple:
        if len(scls_args) == 2 and scls_args[1] is Ellipsis:
            return generic_issubclass(scls_args[0], cls_args, list_)  # type: ignore

        if len(cls_args) == 2 and cls_args[1] is Ellipsis:
            return _map_generic_issubclass(scls_args, repeat(cls_args[0]), failfast=True, list_=list_)

    if scls_origin is Annotated:
        return generic_issubclass(scls_args[0], cls, list_)  # type: ignore
    if cls_origin is Annotated:
        return generic_issubclass(scls, cls_args[0], list_)  # type: ignore

    if scls_origin.__class__ is _TypedDictMeta:
        if cls_origin.__class__ is _TypedDictMeta:
            return all(k in cls_origin.__annotations__ for k in scls_origin.__annotations__)
        return generic_issubclass(cls_origin, dict, list_)  # type: ignore
    if cls_origin.__class__ is _TypedDictMeta:
        return generic_issubclass(scls, dict, list_)  # type: ignore

    if origin_is_union(scls_origin):
        return _map_generic_issubclass(scls_args, repeat(cls), failfast=True, list_=list_)
    if origin_is_union(cls_origin):
        return generic_issubclass(scls, cls_args, list_)  # type: ignore

    if origin_is_literal(scls_origin) and origin_is_literal(cls_origin):
        return set(scls_args) <= set(cls_args)
    if isinstance(cls, TypeVar):
        if cls.__constraints__:
            return any(generic_issubclass(scls, p, list_) for p in cls.__constraints__)  # type: ignore
        return generic_issubclass(scls, cls.__bound__, list_) if cls.__bound__ else True  # type: ignore
    try:
        if not issubclass(scls_origin, cls_origin):
            return False
    except TypeError:
        return False

    if not cls_args:
        return True

    return _map_generic_issubclass(scls_args, cls_args, failfast=True, list_=list_)


def _map_generic_issubclass(
    scls: Iterable[Any], cls: Iterable[Any], *, failfast: bool = False, list_: bool = True
) -> bool | list[Any]:
    results = []
    for scls_arg, cls_arg in zip(scls, cls):
        if not (result := generic_issubclass(scls_arg, cls_arg, True)) and failfast:
            return False
        else:
            results.extend(result if isinstance(result, list) else [result])

    if list_:
        return results or False
    return all(results)
