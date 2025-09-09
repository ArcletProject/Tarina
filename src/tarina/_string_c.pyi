from typing import Iterable, Iterator, Self

CRLF: str
QUOTATION: dict[str, str]

def split(text: str, separator: str, crlf: bool = True) -> list[str]:
    """尊重引号与转义的字符串切分

    Args:
        text (str): 要切割的字符串
        separator (str): 切割符.
        crlf (bool): 是否去除 \n 与 \r，默认为 True

    Returns:
        List[str]: 切割后的字符串, 可能含有空格
    """
    ...

def split_once(text: str, separator: str, crlf: bool = True) -> tuple[str, str]:
    """尊重引号与转义的字符串切分, 只切割一次

    Args:
        text (str): 要切割的字符串
        separator (str): 切割符.
        crlf (bool): 是否去除 \n 与 \r，默认为 True
    Returns:
        Tuple[str, str]: 切割后的字符串, 可能含有空格
    """
    ...

def split_once_without_escape(text: str, separator: str, crlf: bool = True) -> tuple[str, str]:
    """尊重引号的字符串切分, 只切割一次

    Args:
        text (str): 要切割的字符串
        separator (str): 切割符.
        crlf (bool): 是否去除 \n 与 \r，默认为 True
    Returns:
        Tuple[str, str]: 切割后的字符串, 可能含有空格
    """
    ...

def split_once_index_only(text: str, separator: str, offset: int, crlf: bool = True):
    """尊重引号的字符串切分, 只切割一次

    Args:
        text (str): 要切割的字符串
        separator (str): 切割符.
        offset (int): 起始位置
        crlf (bool): 是否去除 \n 与 \r，默认为 True

    Returns:
        Tuple[str, str]: 切割后的字符串, 可能含有空格
    """
    ...

class String(Iterator[str]):
    left_index: int
    offset: int
    next_index: int
    len: int
    text: str

    def __init__(self, text: str): ...
    def step(self, separator: str, crlf: bool = True) -> None: ...
    def val(self) -> str: ...
    def apply(self, left: int = -1): ...
    def rest(self) -> str: ...
    def reset(self) -> None: ...
    @property
    def complete(self) -> bool: ...
    @property
    def will_complete(self) -> bool: ...
    def __iter__(self) -> Self: ...
    def __next__(self) -> str: ...
