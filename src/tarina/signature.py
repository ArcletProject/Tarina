from __future__ import annotations

import functools
import inspect
import sys
from collections.abc import Mapping
from typing import Any, Callable


@functools.lru_cache(4096)
def get_signature(target: Callable):
    return inspect.signature(target).parameters.values()


try:
    from inspect import get_annotations  # type: ignore
except ImportError:

    def get_annotations(
        obj: Callable,
        *,
        _globals: Mapping[str, Any] | None = None,
        _locals: Mapping[str, Any] | None = None,
        eval_str: bool = False,
    ) -> dict[str, Any]:  # sourcery skip: avoid-builtin-shadow
        if not callable(obj):
            raise TypeError(f"{obj!r} is not a module, class, or callable.")

        ann = getattr(obj, "__annotations__", None)
        obj_globals = getattr(obj, "__globals__", None)
        obj_locals = None
        unwrap = obj
        if ann is None:
            return {}

        if not isinstance(ann, dict):
            raise ValueError(f"{unwrap!r}.__annotations__ is neither a dict nor None")
        if not ann:
            return {}

        if not eval_str:
            return dict(ann)

        if unwrap is not None:
            while True:
                if hasattr(unwrap, "__wrapped__"):
                    unwrap = unwrap.__wrapped__  # type: ignore
                    continue
                if isinstance(unwrap, functools.partial):
                    unwrap = unwrap.func
                    continue
                break
            if hasattr(unwrap, "__globals__"):
                obj_globals = unwrap.__globals__

        if _globals is None:
            _globals = obj_globals
        if _locals is None:
            _locals = obj_locals

        return {
            key: eval(value, _globals, _locals) if isinstance(value, str) else value  # type: ignore
            for key, value in ann.items()
        }


@functools.lru_cache(4096)
def signatures(callable_target: Callable) -> list[tuple[str, Any, Any]]:
    callable_annotation = get_annotations(callable_target, eval_str=True)
    return [
        (
            param.name,
            (
                (callable_annotation.get(param.name) if isinstance(param.annotation, str) else param.annotation)
                if param.annotation is not inspect.Signature.empty
                else None
            ),
            param.default,
        )
        for param in get_signature(callable_target)
    ]


def parent_frame_namespace(*, parent_depth: int = 2, force: bool = False) -> dict[str, Any] | None:
    frame = sys._getframe(parent_depth)
    if force:
        return frame.f_locals

    # if either of the following conditions are true, the class is defined at the top module level
    # to better understand why we need both of these checks, see
    # https://github.com/pydantic/pydantic/pull/10113#discussion_r1714981531
    if frame.f_back is None or frame.f_code.co_name == "<module>":
        return None

    return frame.f_locals


def get_module_ns_of(obj: Any) -> dict[str, Any]:
    module_name = getattr(obj, "__module__", None)
    if module_name:
        try:
            return sys.modules[module_name].__dict__
        except KeyError:
            return {}
    return {}


def merge_cls_and_parent_ns(cls: type[Any], parent_namespace: dict[str, Any] | None = None) -> dict[str, Any]:
    ns = get_module_ns_of(cls).copy()
    if parent_namespace is not None:
        ns.update(parent_namespace)
    ns[cls.__name__] = cls
    return ns
