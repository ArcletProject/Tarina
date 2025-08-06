from __future__ import annotations

import inspect
from collections.abc import AsyncGenerator, Awaitable, Coroutine, Generator
from functools import lru_cache
from typing import Any, Callable

from typing_extensions import TypeIs

cache_size = 4096


@lru_cache(cache_size)
def is_coroutinefunction(call) -> TypeIs[Callable[..., Coroutine]]:
    """检查 call 是否是一个协程函数"""
    return inspect.iscoroutinefunction(call)


@lru_cache(cache_size)
def is_awaitable(o) -> TypeIs[Awaitable]:
    return inspect.isawaitable(o)


@lru_cache(cache_size)
def is_async(o: Any) -> TypeIs[Callable[..., Coroutine] | Awaitable]:
    return is_coroutinefunction(o) or is_awaitable(o)


@lru_cache(cache_size)
def is_gen_callable(call: Callable[..., Any]) -> TypeIs[Callable[..., Generator]]:
    """检查 call 是否是一个生成器函数"""
    if inspect.isgeneratorfunction(call):
        return True
    func_ = getattr(call, "__call__", None)
    return inspect.isgeneratorfunction(func_)


@lru_cache(cache_size)
def is_async_gen_callable(call: Callable[..., Any]) -> TypeIs[Callable[..., AsyncGenerator]]:
    """检查 call 是否是一个异步生成器函数"""
    if inspect.isasyncgenfunction(call):
        return True
    func_ = getattr(call, "__call__", None)
    return inspect.isasyncgenfunction(func_)
