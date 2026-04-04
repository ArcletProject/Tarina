from __future__ import annotations
from typing import Iterator

QUOTATION = {"'": "'", '"': '"'}
CRLF = "\n\r"


def split_once(text: str, separator: str, crlf: bool = True):
    """尊重引号与转义的字符串切分, 只切割一次

    Args:
        text (str): 要切割的字符串
        separator (str): 切割符.
        crlf (bool): 是否去除 \n 与 \r，默认为 True

    Returns:
        Tuple[str, str]: 切割后的字符串, 可能含有空格
    """
    if crlf:
        separator += CRLF
    index, out_text, quotation, escape, sep = 0, "", "", False, False
    text = text.lstrip()
    first_quoted_sep_index = -1
    last_quote_index = 0
    tlen = len(text)
    for char in text:
        index += 1
        if char in separator:
            if not quotation:
                sep = True
                continue
            if first_quoted_sep_index == -1:
                first_quoted_sep_index = index
        if sep:
            index -= 1
            break
        if char in QUOTATION:  # 遇到引号括起来的部分跳过分隔
            if index == 1 + escape + last_quote_index and not quotation:
                quotation = QUOTATION[char]
            elif (text[index - 2] not in separator or index == tlen) and char == quotation:
                last_quote_index = index
                quotation = ""
                first_quoted_sep_index = -1
            else:
                out_text += char
            if escape:
                out_text = out_text[:-1] + char
        else:
            out_text += char
        escape = char == "\\"
    if index == tlen:
        if first_quoted_sep_index == -1:
            return out_text if last_quote_index else text.rstrip(separator), ""
        return text[: first_quoted_sep_index - 1], text[first_quoted_sep_index:]
    return out_text, text[index:]


def split_once_without_escape(text: str, separator: str, crlf: bool = True):
    """尊重引号的字符串切分, 只切割一次

    Args:
        text (str): 要切割的字符串
        separator (str): 切割符.
        crlf (bool): 是否去除 \n 与 \r，默认为 True

    Returns:
        Tuple[str, str]: 切割后的字符串, 可能含有空格
    """
    if crlf:
        separator += CRLF
    index, quotation = 0, ""
    text = text.lstrip()
    first_quoted_sep_index = -1
    last_quote_index = 0
    tlen = len(text)
    for char in text:
        index += 1
        if char in separator:
            if not quotation:
                break
            if first_quoted_sep_index == -1:
                first_quoted_sep_index = index
        if char in QUOTATION:  # 遇到引号括起来的部分跳过分隔
            if index == 1 + last_quote_index and not quotation:
                quotation = QUOTATION[char]
            elif (text[index - 2] not in separator or index == tlen) and char == quotation:
                last_quote_index = index
                quotation = ""
                first_quoted_sep_index = -1
    if index == tlen:
        if first_quoted_sep_index == -1:
            return text[:last_quote_index] if last_quote_index else text.rstrip(separator), ""
        return text[: first_quoted_sep_index - 1], text[first_quoted_sep_index:]
    return text[: index - 1], text[index:]


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
    if crlf:
        separator += CRLF
    index = offset
    quotation = ""
    sep = 0
    quoted_sep_index = -1
    quoted_sep = 0
    last_quote_index = 0
    tlen = len(text)
    while index < tlen:
        char = text[index]
        index += 1
        if char in separator:
            if not quotation:
                sep += 1
                continue
            quoted_sep_index = index
            quoted_sep += 1
        if sep:
            index -= 1
            break
        if char in QUOTATION:  # 遇到引号括起来的部分跳过分隔
            if index == 1 + (last_quote_index or offset) and not quotation:
                quotation = QUOTATION[char]
            elif (text[index - 2] not in separator or index == tlen) and char == quotation:
                last_quote_index = index
                quotation = ""
                quoted_sep_index = -1
                quoted_sep = 0
    if index == tlen:
        if quoted_sep_index == -1:
            return index, sep
        return quoted_sep_index, quoted_sep
    return index, sep


def split(text: str, separator: str, crlf: bool = True):
    """尊重引号与转义的字符串切分

    Args:
        text (str): 要切割的字符串
        separator (str): 切割符.
        crlf (bool): 是否去除 \n 与 \r，默认为 True

    Returns:
        List[str]: 切割后的字符串, 可能含有空格
    """
    if crlf:
        separator += CRLF
    text = text.strip(separator)
    tlen = len(text)
    result, quotation, escape = [], "", False
    quoted_sep_index = []
    last_sep_index = 0
    last_sep_pos = 0
    last_quote_index = 0
    index = 0
    for char in text:
        index += 1
        if char in QUOTATION:
            if index == 1 + escape + max(last_sep_index, last_quote_index) and not quotation:
                quotation = QUOTATION[char]
            elif (not result or index == tlen or text[index] in QUOTATION or text[index] in separator) and char == quotation:
                quotation = ""
                last_quote_index = index
            else:
                result.append(char)
            if escape:
                result[-1] = char
        elif char in separator:
            if quotation:
                quoted_sep_index.append(len(result) + 1)
                result.append(char)
            else:
                last_sep_index = index
                last_sep_pos = len(result) + 1
                if result and result[-1] != "\0":
                    result.append("\0")
                quoted_sep_index = []
        else:
            result.append(char)
        escape = char == "\\"
    if not result:
        return []
    if quotation and quoted_sep_index:
        result.insert(last_sep_pos, text[last_sep_index or last_quote_index])
        for i in quoted_sep_index:
            result[i] = "\0"
    return str.join("", result).split("\0")


class String(Iterator[str]):
    left_index: int
    offset: int
    next_index: int
    len: int
    text: str

    def __init__(self, text: str):
        self.text = text
        self.len = len(text)
        self.left_index = 0
        self.offset = 0
        self.next_index = 0

    def step(self, separator: str, crlf: bool = True):
        self.next_index, self.offset = split_once_index_only(self.text, separator, self.left_index, crlf)

    def val(self):
        return self.text[self.left_index : self.next_index - self.offset]

    def apply(self, left: int = -1):
        if left == -1:
            self.left_index = self.next_index
        else:
            self.next_index = self.left_index = left
        self.offset = 0

    def rest(self):
        return self.text[self.left_index :]

    def reset(self):
        self.left_index = 0
        self.offset = 0
        self.next_index = 0

    @property
    def complete(self):
        return self.left_index == self.len

    @property
    def will_complete(self):
        return self.next_index == self.len

    def __repr__(self):
        return f"String({self.text!r}[{self.left_index}:{self.next_index - self.offset}])"

    def __str__(self):
        return self.val()

    def __iter__(self):
        self.reset()
        return self

    def __next__(self):
        if self.complete:
            raise StopIteration
        self.step(" ")
        val = self.val()
        self.apply()
        return val
