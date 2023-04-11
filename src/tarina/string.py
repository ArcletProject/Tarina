import os
import sys

__all__ = ("split", "split_once")


NO_EXTENSIONS = bool(os.environ.get("TARINA_NO_EXTENSIONS"))  # type: bool
if sys.implementation.name != "cpython":
    NO_EXTENSIONS = True


if not NO_EXTENSIONS:  # pragma: no branch
    try:
        from ._string_c import split, split_once  # type: ignore[misc]
    except ImportError:  # pragma: no cover
        from ._string_py import split, split_once  # type: ignore[misc]
else:
    from ._string_py import split, split_once  # type: ignore[misc]
