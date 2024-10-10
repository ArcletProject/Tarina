# cython: boundscheck=False
# cython: cdivision=True
# cython: initializedcheck=False

from cpython.dict cimport PyDict_Contains, PyDict_GetItem
from cpython.list cimport PyList_Append, PyList_GET_SIZE, PyList_Insert
from cpython.unicode cimport (
    PyUnicode_Contains,
    PyUnicode_GET_LENGTH,
    PyUnicode_Join,
    PyUnicode_Split,
)


cdef extern from "Python.h":
    Py_UCS4 PyUnicode_READ_CHAR(object s, Py_ssize_t i)
    tuple PyUnicode_Partition(object str_obj, object sep_obj)

cdef extern from "_op.h":
    bint set_contains_key(object anyset, object key) except -1

cdef dict QUOTES = {'"': '"', "'": "'"}
cdef set CRLF = {'\r', '\n'}

cpdef inline list split(str text, str separator, char crlf=True):
    cdef:
        char escape = 0
        list result = []
        Py_UCS4 quotation = 0
        Py_UCS4 ch = 0
        Py_ssize_t index = 0
        Py_ssize_t length = PyUnicode_GET_LENGTH(text)
        Py_ssize_t first_quoted_sep_index = -1
        Py_ssize_t last_sep_index = 0
        Py_ssize_t last_quote_index = 0
        Py_ssize_t offset = 1

    while index < length:
        ch = PyUnicode_READ_CHAR(text, index)
        index += 1
        if ch == 92:  # \\
            escape = 1
            offset += 1
            PyList_Append(result, ch)
        elif PyDict_Contains(QUOTES, ch):
            if index == offset + max(last_sep_index, last_quote_index) and quotation == 0:
                quotation = PyUnicode_READ_CHAR(<str>PyDict_GetItem(QUOTES, ch), 0)
            elif PyUnicode_Contains(separator, result[-1]) == 0 and ch == quotation:
                quotation = 0
                last_quote_index = index
            else:
                PyList_Append(result, ch)
                continue
            if escape:
                result[-1] = ch
        elif PyUnicode_Contains(separator, ch) or (crlf and set_contains_key(CRLF, ch)):
            if quotation:
                if first_quoted_sep_index == -1:
                    first_quoted_sep_index = PyList_GET_SIZE(result) + 1
                PyList_Append(result, ch)
            else:
                last_sep_index = index
                if result and result[-1] != '\1':
                    PyList_Append(result, '\1')
        else:
            PyList_Append(result, ch)
            escape = 0
    if PyList_GET_SIZE(result) == 0:
        return []
    if quotation and first_quoted_sep_index != -1:
        PyList_Insert(result, last_sep_index, PyUnicode_READ_CHAR(text,  last_quote_index or last_sep_index))
        result[first_quoted_sep_index] = '\1'
    return PyUnicode_Split(PyUnicode_Join('', result), '\1', -1)


cpdef inline tuple split_once(str text, str separator, char crlf=True):
    text = text.lstrip()
    cdef:
        Py_ssize_t index = 0
        list out_text = []
        Py_UCS4 quotation = 0
        Py_UCS4 ch = 0
        char escape = 0
        char sep = 0
        Py_ssize_t length = PyUnicode_GET_LENGTH(text)
        Py_ssize_t first_quoted_sep_index = -1
        Py_ssize_t last_quote_index = 0
        Py_ssize_t offset = 1
    while index < length:
        ch = PyUnicode_READ_CHAR(text, index)
        index += 1
        if PyUnicode_Contains(separator, ch) or (crlf and set_contains_key(CRLF, ch)):
            if quotation == 0:
                sep = 1
                continue
            elif first_quoted_sep_index == -1:
                first_quoted_sep_index = index
        if sep == 1:
            index -= 1
            break
        if ch == 92:  # \\
            escape = 1
            offset += 1
            PyList_Append(out_text, ch)
        elif PyDict_Contains(QUOTES, ch):  # 遇到引号括起来的部分跳过分隔
            if index == offset + last_quote_index and quotation == 0:
                quotation = PyUnicode_READ_CHAR(<str>PyDict_GetItem(QUOTES, ch), 0)
            elif PyUnicode_Contains(separator, PyUnicode_READ_CHAR(text, index-2)) == 0 and ch == quotation:
                last_quote_index = index
                first_quoted_sep_index = -1
                quotation = 0
            else:
                PyList_Append(out_text, ch)
                continue
            if escape:
                out_text[-1] = ch
        else:
            PyList_Append(out_text, ch)
            escape = 0
    if index == length:
        if first_quoted_sep_index == -1:
            return text, ''
        return text[:first_quoted_sep_index - 1], text[first_quoted_sep_index:]
    return PyUnicode_Join('', out_text), text[index:]
