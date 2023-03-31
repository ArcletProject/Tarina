from __future__ import annotations

from typing import Awaitable, Callable, Coroutine, Any
from typing_extensions import TypeGuard
import inspect
from functools import lru_cache

cache_size = 4096


@lru_cache(cache_size)
def is_coroutinefunction(o) -> TypeGuard[Callable[..., Coroutine]]:
    return inspect.iscoroutinefunction(o)


@lru_cache(cache_size)
def is_awaitable(o) -> TypeGuard[Awaitable]:
    return inspect.isawaitable(o)


@lru_cache(cache_size)
def is_async(o: Any) -> TypeGuard[Callable[..., Coroutine] | Awaitable]:
    return is_coroutinefunction(o) or is_awaitable(o)
