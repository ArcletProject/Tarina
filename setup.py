import os
import sys

from setuptools import Extension, setup

NO_EXTENSIONS = bool(os.environ.get("TARINA_NO_EXTENSIONS"))  # type: bool

if sys.implementation.name != "cpython":
    NO_EXTENSIONS = True


extensions = [
    Extension("tarina._string_c", ["src/tarina/_string_c.c"]),
    Extension("tarina._lru_c", ["src/tarina/_lru_c.c"]),
]

args = {
    "include_package_data": True,
    "exclude_package_data": {"": ["*.c"]},
}

if not NO_EXTENSIONS:
    print("**********************")
    print("* Accelerated build *")
    print("**********************")
    setup(ext_modules=extensions, **args)
else:
    print("*********************")
    print("* Pure Python build *")
    print("*********************")
    setup(**args)
