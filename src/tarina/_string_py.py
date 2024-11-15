from __future__ import annotations

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
            elif text[index - 2] not in separator and char == quotation:
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
            elif text[index - 2] not in separator and char == quotation:
                last_quote_index = index
                quotation = ""
                first_quoted_sep_index = -1
    if index == tlen:
        if first_quoted_sep_index == -1:
            return text[:last_quote_index] if last_quote_index else text.rstrip(separator), ""
        return text[: first_quoted_sep_index - 1], text[first_quoted_sep_index:]
    return text[:index-1], text[index:]


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
    text = text[offset:]
    first_quoted_sep_index = -1
    last_quote_index = 0
    tlen = len(text)
    for char in text:
        index += 1
        if char in separator:
            if not quotation:
                sep += 1
                continue
            if first_quoted_sep_index == -1:
                first_quoted_sep_index = index
        if sep:
            index -= 1
            break
        if char in QUOTATION:  # 遇到引号括起来的部分跳过分隔
            if index == 1 + last_quote_index and not quotation:
                quotation = QUOTATION[char]
            elif text[index - offset- 2] not in separator and char == quotation:
                last_quote_index = index
                quotation = ""
                first_quoted_sep_index = -1
    if index == tlen:
        if first_quoted_sep_index == -1:
            return index, sep
        return first_quoted_sep_index, sep
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
    result, quotation, escape = [], "", False
    quoted_sep_index = []
    last_sep_index = 0
    last_quote_index = 0
    index = 0
    for char in text:
        index += 1
        if char in QUOTATION:
            if index == 1 + escape + max(last_sep_index, last_quote_index) and not quotation:
                quotation = QUOTATION[char]
            elif (not result or result[-1] not in separator) and char == quotation:
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
                if result and result[-1] != "\0":
                    result.append("\0")
        else:
            result.append(char)
        escape = char == "\\"
    if not result:
        return []
    if quotation and quoted_sep_index:
        result.insert(last_sep_index, text[last_quote_index or last_sep_index])
        for i in quoted_sep_index:
            result[i] = "\0"
    return str.join("", result).split("\0")


class String:
    left_index: int
    right_index: int
    next_index: int
    _len: int
    text: str

    def __init__(self, text: str):
        self.text = text
        self._len = len(text)
        self.left_index = 0
        self.right_index = 0
        self.next_index = 0

    def step(self, separator: str, crlf: bool = True):
        self.next_index, offset = split_once_index_only(self.text, separator, self.left_index, crlf)
        self.right_index = self.next_index - offset

    def val(self):
        return self.text[self.left_index:self.right_index]

    def apply(self):
        self.left_index = self.next_index
        self.right_index = self._len

    @property
    def complete(self):
        return self.left_index == self._len

    def __repr__(self):
        return f"String({self.text!r}[{self.left_index}:{self.right_index}])"

    def __str__(self):
        return self.val()
