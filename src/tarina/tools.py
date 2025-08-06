from __future__ import annotations

import asyncio
import inspect
import re
from collections.abc import AsyncGenerator, Awaitable, Coroutine, Generator, Iterable
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Literal, Protocol, TypeVar, overload

from typing_extensions import Concatenate, ParamSpec

from .guard import is_async

T = TypeVar("T")
R = TypeVar("R")
P = ParamSpec("P")
C = TypeVar("C")
_T_co = TypeVar("_T_co", covariant=True)

TCallable = TypeVar("TCallable", bound=Callable)


def annotation(**types):
    def wrapper(func: TCallable) -> TCallable:
        func.__annotations__ = types
        return func

    return wrapper


class SupportsNext(Protocol[_T_co]):
    def __next__(self) -> _T_co: ...


def group_dict(iterable: Iterable, key_callable: Callable[[Any], Any]):
    temp = {}
    for i in iterable:
        k = key_callable(i)
        temp.setdefault(k, []).append(i)
    return temp


async def run_always_await(target: Callable[..., Any] | Callable[..., Awaitable[Any]], *args, **kwargs) -> Any:
    obj = target(*args, **kwargs)
    if is_async(target) or is_async(obj):
        obj = await obj  # type: ignore
    return obj


def run_sync(call: Callable[P, T]) -> Callable[P, Coroutine[None, None, T]]:
    """一个用于包装 sync function 为 async function 的装饰器

    参数:
        call: 被装饰的同步函数
    """

    @wraps(call)
    async def _wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        result = await asyncio.to_thread(call, *args, **kwargs)
        if inspect.isawaitable(result):
            return await result
        return result

    return _wrapper


def run_sync_generator(call: Callable[P, Generator[T]]) -> Callable[P, AsyncGenerator[T, None]]:
    """一个用于包装 sync generator function 为 async generator function 的装饰器"""

    def _next(it: SupportsNext[C]) -> C:
        try:
            return next(it)
        except StopIteration:
            raise StopAsyncIteration from None

    async_next = run_sync(_next)

    @wraps(call)
    async def _wrapper(*args: P.args, **kwargs: P.kwargs) -> AsyncGenerator[T, None]:
        gen = call(*args, **kwargs)
        try:
            while True:
                yield await async_next(gen)
        except StopAsyncIteration:
            return

    return _wrapper


def gen_subclass(cls: type[T]) -> Generator[type[T], None, None]:
    """生成某个类的所有子类 (包括其自身)
    Args:
        cls (Type[T]): 类
    Yields:
        Type[T]: 子类
    """
    yield cls
    for sub_cls in cls.__subclasses__():
        if TYPE_CHECKING:
            assert issubclass(sub_cls, cls)
        yield from gen_subclass(sub_cls)


@overload
def init_spec(fn: Callable[P, T]) -> Callable[[Callable[[T], R]], Callable[P, R]]: ...


@overload
def init_spec(
    fn: Callable[P, T], is_method: Literal[True]
) -> Callable[[Callable[[C, T], R]], Callable[Concatenate[C, P], R]]: ...


def init_spec(  # type: ignore
    fn: Callable[P, T], is_method: bool = False
) -> Callable[[Callable[[T], R] | Callable[[C, T], R]], Callable[P, R] | Callable[Concatenate[C, P], R]]:
    def wrapper(func: Callable[[T], R] | Callable[[C, T], R]) -> Callable[P, R] | Callable[Concatenate[C, P], R]:
        def inner(*args: P.args, **kwargs: P.kwargs):
            if is_method:
                return func(args[0], fn(*args[1:], **kwargs))  # type: ignore
            return func(fn(*args, **kwargs))  # type: ignore

        return inner

    return wrapper


def safe_eval(route: str, _locals: dict[str, Any]):
    parts = re.split(r"\.|(\[.+?\])|(\(.*?\))", route)
    if (key := parts[0]) not in _locals:
        raise NameError(key)
    res = _locals[key]
    for part in parts[1:]:
        if not part:
            continue
        if part.startswith("_"):
            raise ValueError(route)
        if part.startswith("[") and part.endswith("]"):
            item = part[1:-1]
            if item[0] in ("'", '"') and item[-1] in ("'", '"'):
                res = res[item[1:-1]]
            elif ":" in item:
                res = res[slice(*(int(x) if x else None for x in item.split(":")))]
            else:
                try:
                    res = res[int(item)]
                except ValueError:
                    res = res[item]
        elif part.startswith("(") and part.endswith(")"):
            item = part[1:-1]
            if not item:
                res = res()
            else:
                _parts = item.split(",")
                _args = []
                _kwargs = {}
                for _part in _parts:
                    _part = _part.strip()
                    if re.match(".+=.+", _part):
                        k, v = _part.split("=")
                        if v[0] in ("'", '"') and v[-1] in ("'", '"'):
                            v = v[1:-1]
                        _kwargs[k] = v
                    else:
                        if _part[0] in ("'", '"') and _part[-1] in ("'", '"'):
                            _part = _part[1:-1]
                        _args.append(_part)
                res = res(*_args, **_kwargs)
        else:
            res = getattr(res, part)
    return res


def uncapitalize(source: str) -> str:
    return source[0].lower() + source[1:]


def camel_case(source: str) -> str:
    return re.sub("[_-][a-z]", lambda mat: mat[0][1:].upper(), source)


def pascal_case(source: str) -> str:
    return re.sub("[_-][a-z]", lambda mat: mat[0][1:].upper(), source.capitalize())


def param_case(source: str) -> str:
    return re.sub(".[A-Z]+", lambda mat: mat[0][0] + "-" + mat[0][1:].lower(), uncapitalize(source).replace("_", "-"))


def snake_case(source: str) -> str:
    return re.sub(".[A-Z]", lambda mat: mat[0][0] + "_" + mat[0][1:].lower(), uncapitalize(source).replace("-", "_"))


def coroutine(func: Callable[P, T]) -> Callable[P, Coroutine[Any, Any, T]]:
    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        return func(*args, **kwargs)

    return wrapper


def nest_dict_update(old: dict, new: dict) -> dict:
    """递归更新字典"""
    for k, v in new.items():
        if k not in old:
            old[k] = v
        elif isinstance(v, dict):
            old[k] = nest_dict_update(old[k], v)
        elif isinstance(v, list):
            old[k] = nest_list_update(old[k], v)
        else:
            old[k] = v
    return old


def nest_list_update(old: list, new: list) -> list:
    """递归更新列表"""
    for i, v in enumerate(new):
        if i >= len(old):
            old.append(v)
        elif isinstance(v, dict):
            old[i] = nest_dict_update(old[i], v)
        elif isinstance(v, list):
            old[i] = nest_list_update(old[i], v)
        else:
            old[i] = v
    return old


def nest_obj_update(old, new, attrs: list[str]):
    """递归更新对象"""
    for attr in attrs:
        new_attr = getattr(new, attr)
        if not hasattr(old, attr):
            setattr(old, attr, new_attr)
            continue
        old_attr = getattr(old, attr)
        if not isinstance(new_attr, old_attr.__class__):
            setattr(old, attr, new_attr)
            continue
        if isinstance(new_attr, dict):
            nest_dict_update(old_attr, new_attr)
        elif isinstance(new_attr, list):
            nest_list_update(old_attr, new_attr)
        else:
            setattr(old, attr, new_attr)
    return old
