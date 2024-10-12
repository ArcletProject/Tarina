from __future__ import annotations

QUOTATION = {"'": "'", '"': '"'}
CRLF = {"\n", "\r"}


def split_once(text: str, separator: str, crlf: bool = True):
    """尊重引号与转义的字符串切分, 只切割一次

    Args:
        text (str): 要切割的字符串
        separator (str): 切割符.
        crlf (bool): 是否去除 \n 与 \r，默认为 True

    Returns:
        Tuple[str, str]: 切割后的字符串, 可能含有空格
    """
    index, out_text, quotation, escape, sep = 0, "", "", False, False
    text = text.lstrip()
    first_quoted_sep_index = -1
    last_quote_index = 0
    tlen = len(text)
    offset = 1
    for char in text:
        index += 1
        if char in separator or (crlf and char in CRLF):
            if not quotation:
                sep = True
                continue
            elif first_quoted_sep_index == -1:
                first_quoted_sep_index = index
        if sep:
            index -= 1
            break
        if char == "\\":
            escape = True
            offset += 1
            out_text += char
        elif char in QUOTATION:  # 遇到引号括起来的部分跳过分隔
            if index == offset + last_quote_index and not quotation:
                quotation = QUOTATION[char]
            elif text[index - 2] not in separator and char == quotation:
                last_quote_index = index
                quotation = ""
                first_quoted_sep_index = -1
            else:
                out_text += char
                continue
            if escape:
                out_text = out_text[:-1] + char
        else:
            out_text += char
            escape = False
    if index == tlen:
        if first_quoted_sep_index == -1:
            return text, ""
        return text[: first_quoted_sep_index - 1], text[first_quoted_sep_index:]
    return out_text, text[index:]


def split(text: str, separator: str, crlf: bool = True):
    """尊重引号与转义的字符串切分

    Args:
        text (str): 要切割的字符串
        separator (str): 切割符.
        crlf (bool): 是否去除 \n 与 \r，默认为 True

    Returns:
        List[str]: 切割后的字符串, 可能含有空格
    """
    result, quotation, escape = [], "", False
    quoted_sep_index = []
    last_sep_index = 0
    last_quote_index = 0
    index = 0
    offset = 1
    for char in text:
        index += 1
        if char == "\\":
            escape = True
            offset += 1
            result.append(char)
        elif char in QUOTATION:
            if index == offset + max(last_sep_index, last_quote_index) and not quotation:
                quotation = QUOTATION[char]
            elif result[-1] not in separator and char == quotation:
                quotation = ""
                last_quote_index = index
            else:
                result.append(char)
                continue
            if escape:
                result[-1] = char
        elif char in separator or (crlf and char in CRLF):
            if quotation:
                quoted_sep_index.append(len(result) + 1)
                result.append(char)
            else:
                last_sep_index = index
                if result and result[-1] != "\0":
                    result.append("\0")
        else:
            result.append(char)
            escape = False
    if not result:
        return []
    if quotation and quoted_sep_index:
        result.insert(last_sep_index, text[last_quote_index or last_sep_index])
        for i in quoted_sep_index:
            result[i] = "\0"
    return str.join("", result).split("\0")
