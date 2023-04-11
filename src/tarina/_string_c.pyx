# cython: boundscheck=False
# cython: cdivision=True
# cython: initializedcheck=False

cdef inline int contains(Py_UCS4 ch, tuple chs):
    cdef Py_ssize_t i = 0
    cdef Py_ssize_t length = len(chs)
    while i < length:
        if ch == chs[i]:
            return 1
        i += 1
    return 0


def split(str text, tuple separates, char crlf=True):
    """尊重引号与转义的字符串切分

    Args:
        text (str): 要切割的字符串
        separates (tuple[str, ...]): 切割符. 默认为 " ".
        crlf (bool): 是否去除 \n 与 \r，默认为 True

    Returns:
        List[str]: 切割后的字符串, 可能含有空格
    """
    cdef char escape = 0
    cdef list result = []
    cdef Py_UCS4 quotation = 0
    cdef Py_UCS4 ch = 0
    cdef Py_ssize_t i = 0
    cdef Py_ssize_t length = len(text)

    while i < length:
        ch = text[i]
        i += 1
        if ch == 92:  # \\
            escape = 1
            result.append(ch)
        elif contains(ch, ('"', "'")):
            if quotation == 0:
                quotation = ch
                if escape:
                    result[-1] = ch
            elif ch == quotation:
                quotation = 0
                if escape:
                    result[-1] = ch
        elif (quotation == 0 and ch in separates) or (crlf and contains(ch, ('\r', '\n'))):
            if result and result[-1] != '\0':
                result.append('\0')
        else:
            result.append(ch)
            escape = 0
    return ''.join(result).split('\0') if result else []


def split_once(str text, tuple separates, char crlf=True):
    text = text.lstrip()
    cdef Py_ssize_t index = 0
    cdef list out_text = []
    cdef Py_UCS4 quotation = 0
    cdef Py_UCS4 ch = 0
    cdef char escape = 0
    cdef Py_ssize_t length = len(text)

    while index < length:
        ch = text[index]
        index += 1
        if ch == 92:  # \\
            escape = 1
            out_text.append(ch)
        elif contains(ch, ('"', "'")):  # 遇到引号括起来的部分跳过分隔
            if quotation == 0:
                quotation = ch
                if escape:
                    out_text[-1] = ch
            elif ch == quotation:
                quotation = 0
                if escape:
                    out_text[-1] = ch
        elif (ch in separates or (crlf and contains(ch, ('\n', '\r')))) and quotation == 0:
            break
        else:
            out_text.append(ch)
            escape = 0
    return ''.join(out_text), text[index + 1:]