# cython: language_level=3, boundscheck=False, cdivision=True, wraparound=False, initializedcheck=False, infer_types=True, binding=True


from cpython.dict cimport PyDict_Contains, PyDict_GetItem
from cpython.int cimport PyInt_AS_LONG
from cpython.list cimport PyList_Append, PyList_GET_ITEM, PyList_GET_SIZE, PyList_Insert
from cpython.unicode cimport (
    PyUnicode_Concat,
    PyUnicode_GET_LENGTH,
    PyUnicode_Join,
    PyUnicode_Split,
    PyUnicode_Substring,
)


cdef extern from "Python.h":
    Py_UCS4 PyUnicode_READ_CHAR(object s, Py_ssize_t i)
    cdef Py_ssize_t PY_SSIZE_T_MAX


cdef extern from "_op.h":
    bint str_contains(object str_obj, Py_UCS4 ch)
    unicode str_strip(object str_obj, int striptype, object chars_obj)
    cdef int LEFTSTRIP
    cdef int RIGHTSTRIP
    cdef int BOTHSTRIP

cdef dict QUOTATION = {'"': '"', "'": "'"}
cdef unicode CRLF = "\n\r"

def split(str text, str separator, bint crlf=True):
    if crlf:
        separator = PyUnicode_Concat(separator, CRLF)
    text = str_strip(text, BOTHSTRIP, separator)
    cdef:
        bint escape = 0
        list result = []
        Py_UCS4 quotation = 0
        Py_UCS4 ch = 0
        Py_ssize_t index = 0
        Py_ssize_t length = PyUnicode_GET_LENGTH(text)
        list quoted_sep_index = []
        Py_ssize_t last_sep_index = 0
        Py_ssize_t last_sep_pos = 0
        Py_ssize_t last_quote_index = 0
        Py_ssize_t _len = 0
        Py_ssize_t i = 0
        Py_ssize_t reslen = 0

    while index < length:
        ch = PyUnicode_READ_CHAR(text, index)
        index += 1
        if PyDict_Contains(QUOTATION, ch):
            if index == 1 + escape + max(last_sep_index, last_quote_index) and quotation == 0:
                quotation = PyUnicode_READ_CHAR(<str>PyDict_GetItem(QUOTATION, ch), 0)
            elif (
                PyList_GET_SIZE(result) == 0
                or index == length
                or PyDict_Contains(QUOTATION, PyUnicode_READ_CHAR(text, index))
                or str_contains(separator, PyUnicode_READ_CHAR(text, index))
            ) and ch == quotation:
                quotation = 0
                last_quote_index = index
            else:
                PyList_Append(result, ch)
            if escape:
                result[PyList_GET_SIZE(result)-1] = ch
        elif str_contains(separator, ch):
            reslen = PyList_GET_SIZE(result)
            if quotation:
                PyList_Append(quoted_sep_index, reslen + 1)
                PyList_Append(result, ch)
            else:
                last_sep_index = index
                last_sep_pos = reslen + 1
                if result and (<object>PyList_GET_ITEM(result, reslen-1)) != '\1':
                    PyList_Append(result, '\1')
                quoted_sep_index = []
        else:
            PyList_Append(result, ch)
        escape = ch == 92
    if PyList_GET_SIZE(result) == 0:
        return []
    _len = PyList_GET_SIZE(quoted_sep_index)
    if quotation and _len:
        PyList_Insert(result, last_sep_pos, PyUnicode_READ_CHAR(text,  last_sep_index or last_quote_index))
        # result[first_quoted_sep_index] = '\1'
        while i < _len:
            result[PyInt_AS_LONG(<object>PyList_GET_ITEM(quoted_sep_index, i))] = '\1'
            i += 1
    return PyUnicode_Split(PyUnicode_Join('', result), '\1', -1)


def split_once(str text, str separator, bint crlf=True):
    if crlf:
        separator = PyUnicode_Concat(separator, CRLF)
    text = str_strip(text, LEFTSTRIP, separator)
    cdef:
        Py_ssize_t index = 0
        list out_text = []
        Py_UCS4 quotation = 0
        Py_UCS4 ch = 0
        bint escape = 0
        bint sep = 0
        Py_ssize_t length = PyUnicode_GET_LENGTH(text)
        Py_ssize_t first_quoted_sep_index = -1
        Py_ssize_t last_quote_index = 0
    while index < length:
        ch = PyUnicode_READ_CHAR(text, index)
        index += 1
        if str_contains(separator, ch):
            if quotation == 0:
                sep = 1
                continue
            if first_quoted_sep_index == -1:
                first_quoted_sep_index = index
        if sep == 1:
            index -= 1
            break
        if PyDict_Contains(QUOTATION, ch):  # 遇到引号括起来的部分跳过分隔
            if index == 1 + escape + last_quote_index and quotation == 0:
                quotation = PyUnicode_READ_CHAR(<str>PyDict_GetItem(QUOTATION, ch), 0)
            elif (index == length or str_contains(separator, PyUnicode_READ_CHAR(text, index-2)) == 0) and ch == quotation:
                last_quote_index = index
                first_quoted_sep_index = -1
                quotation = 0
            else:
                PyList_Append(out_text, ch)
            if escape:
                out_text[PyList_GET_SIZE(out_text)-1] = ch
            escape = 0
        else:
            PyList_Append(out_text, ch)
        escape = ch == 92
    if index == length:
        if first_quoted_sep_index == -1:
            return PyUnicode_Join('', out_text) if last_quote_index else str_strip(text, RIGHTSTRIP, separator), ''
        return PyUnicode_Substring(text, 0, first_quoted_sep_index-1), PyUnicode_Substring(text, first_quoted_sep_index, PY_SSIZE_T_MAX)
    return PyUnicode_Join('', out_text), PyUnicode_Substring(text, index, PY_SSIZE_T_MAX)


def split_once_without_escape(str text, str separator, bint crlf=True):
    if crlf:
        separator = PyUnicode_Concat(separator, CRLF)
    text = str_strip(text, LEFTSTRIP, separator)
    cdef:
        Py_ssize_t index = 0
        Py_UCS4 quotation = 0
        Py_UCS4 ch = 0
        Py_ssize_t length = PyUnicode_GET_LENGTH(text)
        Py_ssize_t first_quoted_sep_index = -1
        Py_ssize_t last_quote_index = 0
    while index < length:
        ch = PyUnicode_READ_CHAR(text, index)
        index += 1
        if str_contains(separator, ch):
            if quotation == 0:
                break
            if first_quoted_sep_index == -1:
                first_quoted_sep_index = index
        if PyDict_Contains(QUOTATION, ch):  # 遇到引号括起来的部分跳过分隔
            if index == 1 + last_quote_index and quotation == 0:
                quotation = PyUnicode_READ_CHAR(<str>PyDict_GetItem(QUOTATION, ch), 0)
            elif (index == length or str_contains(separator, PyUnicode_READ_CHAR(text, index-2)) == 0) and ch == quotation:
                last_quote_index = index
                first_quoted_sep_index = -1
                quotation = 0
    if index == length:
        if first_quoted_sep_index == -1:
            return PyUnicode_Substring(text, 0, last_quote_index) if last_quote_index else str_strip(text, RIGHTSTRIP, separator), ''
        return PyUnicode_Substring(text, 0, first_quoted_sep_index-1), PyUnicode_Substring(text, first_quoted_sep_index, PY_SSIZE_T_MAX)
    return PyUnicode_Substring(text, 0, index-1), PyUnicode_Substring(text, index, PY_SSIZE_T_MAX)


cpdef inline tuple split_once_index_only(str text, str separator, Py_ssize_t offset, bint crlf=True):
    if crlf:
        separator = PyUnicode_Concat(separator, CRLF)
    cdef:
        Py_ssize_t index = offset
        Py_UCS4 quotation = 0
        Py_UCS4 ch = 0
        Py_ssize_t sep = 0
        Py_ssize_t length = PyUnicode_GET_LENGTH(text)
        Py_ssize_t quoted_sep_index = -1
        Py_ssize_t quoted_sep = 0
        Py_ssize_t last_quote_index = 0
    while index < length:
        ch = PyUnicode_READ_CHAR(text, index)
        index += 1
        if str_contains(separator, ch):
            if quotation == 0:
                sep += 1
                continue
            quoted_sep_index = index
            quoted_sep += 1
        if sep:
            index -= 1
            break
        if PyDict_Contains(QUOTATION, ch):  # 遇到引号括起来的部分跳过分隔
            if index == 1 + (last_quote_index or offset) and quotation == 0:
                quotation = PyUnicode_READ_CHAR(<str>PyDict_GetItem(QUOTATION, ch), 0)
            elif (index == length or str_contains(separator, PyUnicode_READ_CHAR(text, index-2)) == 0) and ch == quotation:
                last_quote_index = index
                quoted_sep_index = -1
                quoted_sep = 0
                quotation = 0
    if index == length and quoted_sep_index != -1:
        return quoted_sep_index, quoted_sep
    return index, sep


cdef class String:
    cdef public Py_ssize_t left_index
    cdef public Py_ssize_t next_index
    cdef public Py_ssize_t offset
    cdef public Py_ssize_t len
    cdef public str text

    def __init__(self, str text):
        self.text = text
        self.len = PyUnicode_GET_LENGTH(text)
        self.left_index = 0
        self.offset = 0
        self.next_index = 0

    def step(self, str separator, bint crlf=True):
        self.next_index, self.offset = split_once_index_only(self.text, separator, self.left_index, crlf)

    def val(self):
        return PyUnicode_Substring(self.text, self.left_index, self.next_index - self.offset)

    def apply(self, int left = -1):
        if left == -1:
            self.left_index = self.next_index
        else:
            self.next_index = self.left_index = left
        self.offset = 0

    def rest(self):
        return PyUnicode_Substring(self.text, self.left_index, self.len)

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
