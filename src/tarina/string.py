import os
import sys

__all__ = ("split", "split_once", "split_once_without_escape", "split_once_index_only", "String")


NO_EXTENSIONS = bool(os.environ.get("TARINA_NO_EXTENSIONS"))  # type: bool
if sys.implementation.name != "cpython":
    NO_EXTENSIONS = True


if not NO_EXTENSIONS:  # pragma: no branch
    try:
        from ._string_c import String as String  # type: ignore[misc]
        from ._string_c import split as split  # type: ignore[misc]
        from ._string_c import split_once as split_once  # type: ignore[misc]
        from ._string_c import (  # type: ignore[misc]
            split_once_index_only as split_once_index_only,
        )
        from ._string_c import (  # type: ignore[misc]
            split_once_without_escape as split_once_without_escape,
        )
        from ._string_c import QUOTATION as QUOTATION  # type: ignore[misc]
    except ImportError:  # pragma: no cover
        from ._string_py import String as String
        from ._string_py import split as split
        from ._string_py import split_once as split_once
        from ._string_py import (
            split_once_index_only as split_once_index_only,
        )
        from ._string_py import (
            split_once_without_escape as split_once_without_escape,
        )
        from ._string_py import QUOTATION as QUOTATION
else:
    from ._string_py import String as String
    from ._string_py import split as split
    from ._string_py import split_once as split_once
    from ._string_py import (
        split_once_index_only as split_once_index_only,
    )
    from ._string_py import (
        split_once_without_escape as split_once_without_escape,
    )
    from ._string_py import QUOTATION as QUOTATION
