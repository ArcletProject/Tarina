# cython: language_level=3, boundscheck=False, cdivision=True, wraparound=False, initializedcheck=False, infer_types=True, binding=True
"""Cython 加速的 Trie 完整实现(参照 _string_c.pyx 的加速模式).

与 ``tarina.trie`` 全量 API 对齐(merge/copy/deepcopy/pickle/traverse/
walk_towards/prefixes/strictly_equals/slice 读写等), 语义保持一致:

- ``Trie`` / ``CharTrie`` 使用 ``separator=""`` 的逐字符模式(等价于纯版
  基类 Trie 与 CharTrie 对 str 键的行为); ``StringTrie`` 按 separator 切分。
- 与纯版的已知差异: 键必须是 ``str``(纯版基类还接受任意可迭代键);
  ``__hash__`` 同样不可用; ``__eq__`` 回退行为一致。
"""

import copy as _copy
from collections.abc import Mapping
from types import GenericAlias

from cpython.dict cimport PyDict_GetItem, PyDict_Keys, PyDict_Values
from cpython.list cimport PyList_GET_SIZE
from cpython.ref cimport PyObject
from cpython.unicode cimport PyUnicode_Join, PyUnicode_Split

from tarina.trie import ShortKeyError  # noqa


class _MissingType:
    """值缺失哨兵; deepcopy/copy 恒等, 保证结构拷贝后语义不变."""

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self

    def __reduce__(self):
        return (_get_missing, ())


def _get_missing():
    return _MISSING


_MISSING = _MissingType()


def _slice_maybe(key_or_slice):
    """Checks whether argument is a slice or a plain key.

    Returns ``(key, is_slice)``.  Raises TypeError for slices with stop/step.
    """
    if isinstance(key_or_slice, slice):
        if key_or_slice.stop is not None or key_or_slice.step is not None:
            raise TypeError(key_or_slice)
        return key_or_slice.start, True
    return key_or_slice, False


cdef class _Children:
    """Children 存储基类, 三态: _NoChildren / _OneChild / _MultiChildren."""

    cpdef _Node get(self, str step):
        return None

    cpdef _Node require(self, _Node parent, str step):
        raise NotImplementedError

    cpdef _Node add(self, _Node parent, str step):
        raise NotImplementedError

    cdef void delete(self, _Node parent, str step) noexcept:
        pass

    cpdef object items(self):
        return ()

    cpdef object sorted_items(self):
        return ()

    cpdef tuple pick(self):
        raise NotImplementedError

    cpdef _Children merge(self, _Children other, list queue):
        raise NotImplementedError

    cpdef _Children copy(self, object make_copy, list queue):
        raise NotImplementedError

    cpdef tuple sequences(self, bint sorted_items):
        return [], []

    def __len__(self):
        return 0

    def __bool__(self):
        return False


cdef class _NoChildren(_Children):
    cpdef _Node get(self, str step):
        return None

    cpdef _Node add(self, _Node parent, str step):
        cdef _Node node = _Node()
        parent.children = _OneChild(step, node)
        return node

    cpdef _Node require(self, _Node parent, str step):
        return self.add(parent, step)

    cpdef object items(self):
        return ()

    cpdef object sorted_items(self):
        return ()

    cpdef _Children merge(self, _Children other, list queue):
        return other

    cpdef _Children copy(self, object make_copy, list queue):
        return self


cdef class _OneChild(_Children):
    cdef readonly str step
    cdef _Node node

    def __cinit__(self, str step, _Node node):
        self.step = step
        self.node = node

    cpdef _Node get(self, str step):
        if step == self.step:
            return self.node
        return None

    cpdef _Node add(self, _Node parent, str step):
        cdef _Node node = _Node()
        parent.children = _MultiChildren({self.step: self.node, step: node})
        return node

    cpdef _Node require(self, _Node parent, str step):
        if step == self.step:
            return self.node
        return self.add(parent, step)

    cdef void delete(self, _Node parent, str step) noexcept:
        if step == self.step:
            parent.children = _NO_CHILDREN

    cpdef object items(self):
        return ((self.step, self.node),)

    cpdef object sorted_items(self):
        return self.items()

    cpdef tuple pick(self):
        return self.step, self.node

    cpdef _Children merge(self, _Children other, list queue):
        """Moves children from other into this object."""
        cdef _MultiChildren m
        if isinstance(other, _OneChild) and (<_OneChild>other).step == self.step:
            queue.append((self.node, (<_OneChild>other).node))
            return self
        m = _MultiChildren({self.step: self.node})
        return m.merge(other, queue)

    cpdef _Children copy(self, object make_copy, list queue):
        cdef _OneChild cpy = _OneChild(make_copy(self.step), self.node.shallow_copy(make_copy))
        queue.append((cpy.node,))
        return cpy

    cpdef tuple sequences(self, bint sorted_items):
        return [self.step], [self.node]

    def __len__(self):
        return 1

    def __bool__(self):
        return True


cdef class _MultiChildren(_Children):
    cdef dict data

    def __cinit__(self, dict data):
        self.data = data

    cpdef _Node get(self, str step):
        cdef PyObject *ptr = PyDict_GetItem(self.data, step)
        if ptr == NULL:
            return None
        return <_Node>ptr

    cpdef _Node add(self, _Node parent, str step):
        cdef _Node node = _Node()
        self.data[step] = node
        return node

    cpdef _Node require(self, _Node parent, str step):
        cdef PyObject *ptr = PyDict_GetItem(self.data, step)
        cdef _Node node
        if ptr != NULL:
            return <_Node>ptr
        node = _Node()
        self.data[step] = node
        return node

    cdef void delete(self, _Node parent, str step) noexcept:
        cdef dict d = self.data
        cdef object k, v
        del d[step]
        if len(d) == 1:
            k, v = next(iter(d.items()))
            parent.children = _OneChild(k, v)

    cpdef object items(self):
        return self.data.items()

    cpdef object sorted_items(self):
        return sorted(self.data.items())

    cpdef tuple pick(self):
        return next(iter(self.data.items()))

    cpdef _Children merge(self, _Children other, list queue):
        """Moves children from other into this object."""
        cdef _Node node
        for step, other_node in other.items():
            node = self.data.setdefault(step, other_node)
            if node is not other_node:
                queue.append((node, other_node))
        return self

    cpdef _Children copy(self, object make_copy, list queue):
        cdef _MultiChildren cpy = _MultiChildren(
            {make_copy(step): node.shallow_copy(make_copy) for step, node in self.data.items()}
        )
        queue.append(tuple(cpy.data.values()))
        return cpy

    cpdef tuple sequences(self, bint sorted_items):
        if sorted_items:
            pairs = sorted(self.data.items())
            return [p[0] for p in pairs], [p[1] for p in pairs]
        return PyDict_Keys(self.data), PyDict_Values(self.data)

    def __len__(self):
        return len(self.data)

    def __bool__(self):
        return bool(self.data)


cdef _NoChildren _NO_CHILDREN = _NoChildren()


cdef class _Node:
    """A single node of a trie.  与 tarina.trie._Node 同构."""

    cdef public object value
    cdef public _Children children

    def __cinit__(self):
        self.value = _MISSING
        self.children = _NO_CHILDREN

    def merge(self, _Node other, bint overwrite):
        """Move children from other node into this one."""
        queue = [(self, other)]
        while queue:
            lhs, rhs = queue.pop()
            if lhs.value is _MISSING or (overwrite and rhs.value is not _MISSING):
                lhs.value = rhs.value
            if lhs.children is _NO_CHILDREN:
                lhs.children = rhs.children
            elif rhs.children is not _NO_CHILDREN:
                lhs.children = lhs.children.merge(rhs.children, queue)
            rhs.children = _NO_CHILDREN

    def iterate(self, list path, bint shallow, bint sorted_items):
        """与 tarina.trie._Node.iterate 同算法的游标版栈遍历."""
        cdef _Node node = self
        cdef list stack = []  # 元素: [steps, nodes, index]
        cdef list entry, steps, nodes
        cdef Py_ssize_t idx
        cdef str step
        while True:
            if node.value is not _MISSING:
                yield path, node.value

            if (not shallow or node.value is _MISSING) and node.children:
                steps, nodes = node.children.sequences(sorted_items)
                stack.append([steps, nodes, 0])
                path.append("")

            while True:
                if not stack:
                    return
                entry = stack[PyList_GET_SIZE(stack) - 1]
                steps = entry[0]
                nodes = entry[1]
                idx = entry[2]
                if idx == PyList_GET_SIZE(steps):
                    stack.pop()
                    path.pop()
                    continue
                entry[2] = idx + 1
                step = steps[idx]
                node = nodes[idx]
                path[PyList_GET_SIZE(path) - 1] = step
                break

    def traverse(self, node_factory, path_conv, list path, bint sorted_items):
        """Traverses the node and returns another type of node from factory."""
        cdef list seq_steps, seq_nodes
        seq_steps, seq_nodes = self.children.sequences(sorted_items)
        children = (
            node.traverse(node_factory, path_conv, path + [step], sorted_items)
            for step, node in zip(seq_steps, seq_nodes)
        )
        value_maybe = None
        if self.value is not _MISSING:
            value_maybe = self.value
        return node_factory(path_conv, tuple(path), children, value_maybe)

    def equals(self, other):
        """Returns whether this and other node are recursively equal."""
        if not isinstance(other, _Node):
            return False
        cdef _Node a = self
        cdef _Node b = <_Node>other
        stack = []
        while True:
            if a.value != b.value or len(a.children) != len(b.children):
                return False
            if len(a.children) == 1 and isinstance(a.children, _OneChild) and isinstance(b.children, _OneChild):
                if (<_OneChild>a.children).step != (<_OneChild>b.children).step:
                    return False
                a = (<_OneChild>a.children).node
                b = (<_OneChild>b.children).node
                continue
            if a.children:
                stack.append((iter(a.children.items()), b.children))

            while True:
                if not stack:
                    return True
                top = stack[PyList_GET_SIZE(stack) - 1]
                entry = next(top[0], _MISSING)
                if entry is _MISSING:
                    stack.pop()
                    continue
                key, a = entry
                b = top[1].get(key)
                if b is None:
                    return False
                break

    def shallow_copy(self, make_copy):
        """Returns a copy of the node which shares the children property."""
        cdef _Node cpy = _Node()
        cpy.children = self.children
        cpy.value = make_copy(self.value)
        return cpy

    def copy(self, make_copy):
        """Returns a copy of the node structure."""
        cdef _Node cpy = self.shallow_copy(make_copy)
        queue = [(cpy,)]
        while queue:
            for node in queue.pop():
                node.children = node.children.copy(make_copy, queue)
        return cpy

    def __getstate__(self):
        """Get state used for pickling (与 tarina.trie._Node.__getstate__ 同格式).

        状态是一个扁平命令列表: [n, step0..stepn-1, value] 前进 n 步并赋值,
        [-n] 回退 n 步.
        """
        state: list = [] if self.value is _MISSING else [0]
        last_cmd = 0
        node = self
        stack = []
        while True:
            if node.value is not _MISSING:
                last_cmd = 0
                state.append(node.value)
            stack.append(iter(node.children.items()))

            while True:
                step, node = next(stack[PyList_GET_SIZE(stack) - 1], (None, None))
                if node is not None:
                    break

                if last_cmd < 0:
                    state[PyList_GET_SIZE(state) - 1] -= 1
                else:
                    last_cmd = -1
                    state.append(-1)
                stack.pop()
                if not stack:
                    state.pop()  # Final -n command is not necessary
                    return state

            if last_cmd > 0:
                last_cmd += 1
                state[PyList_GET_SIZE(state) - last_cmd] += 1
            else:
                last_cmd = 1
                state.append(1)
            state.append(step)

    def __setstate__(self, state):
        """Unpickles node.  See :func:`_Node.__getstate__`."""
        self.value = _MISSING
        self.children = _NO_CHILDREN
        state = iter(state)
        stack = [self]
        for cmd in state:
            if cmd < 0:
                del stack[PyList_GET_SIZE(stack) + cmd:]
            else:
                while cmd > 0:
                    parent = stack[PyList_GET_SIZE(stack) - 1]
                    stack.append(parent.children.add(parent, next(state)))
                    cmd -= 1
                stack[PyList_GET_SIZE(stack) - 1].value = next(state)

    def __reduce__(self):
        return (_rebuild_node, (self.__getstate__(),))


def _rebuild_node(state):
    cdef _Node node = _Node()
    node.__setstate__(state)
    return node


cdef class _NoneStep:
    """Representation of a non-existent step towards non-existent node."""

    def __bool__(self):
        return False

    def get(self, default=None):
        return default

    def set(self, value):
        return

    def setdefault(self, value):
        return value

    @property
    def is_set(self):
        return False

    @property
    def has_subtrie(self):
        return False

    @property
    def key(self):
        return None

    @property
    def value(self):
        return None

    def __repr__(self):
        return "(None Step)"


cdef _NoneStep _NONE_STEP = _NoneStep()


cdef class _Step:
    """Representation of a single step on a path towards particular node."""

    cdef readonly object _trie
    cdef readonly list _path
    cdef readonly Py_ssize_t _pos
    cdef readonly _Node _node
    cdef object _key_cache

    def __cinit__(self, trie, list path, Py_ssize_t pos, _Node node):
        self._trie = trie
        self._path = path
        self._pos = pos
        self._node = node
        self._key_cache = None

    def __bool__(self):
        return True

    @property
    def is_set(self):
        """Returns whether the node has value assigned to it."""
        return self._node.value is not _MISSING

    @property
    def has_subtrie(self):
        """Returns whether the node has any children."""
        return bool(self._node.children)

    def get(self, default=None):
        """Returns node's value or the default if value is not assigned."""
        v = self._node.value
        return default if v is _MISSING else v

    def set(self, value):
        """Deprecated.  Use ``step.value = value`` instead."""
        self._node.value = value

    def setdefault(self, value):
        """Assigns value to the node if one is not set then returns it."""
        if self._node.value is _MISSING:
            self._node.value = value
        return self._node.value

    @property
    def key(self):
        """Returns key of the node."""
        if self._key_cache is None:
            self._key_cache = self._trie._key_from_path(self._path[: self._pos])
        return self._key_cache

    @property
    def value(self):
        """Returns node's value or raises ShortKeyError."""
        v = self._node.value
        if v is _MISSING:
            raise ShortKeyError(self.key)
        return v

    @value.setter
    def value(self, value):
        self._node.value = value

    def __repr__(self):
        return f"({self.key!r}, {self.value!r})"


cdef class Trie:
    """Trie 完整实现的 Cython 版(separator 语义与 tarina.trie 对齐)."""

    cdef readonly _Node _root
    cdef readonly str _separator
    cdef bint _sorted
    cdef bint _per_char

    HAS_VALUE = 1
    HAS_SUBTRIE = 2
    __hash__ = None
    __class_getitem__ = classmethod(GenericAlias)

    def __init__(self, other=None, str separator="", **kwargs):
        if not isinstance(separator, str):
            raise TypeError(separator)
        self._root = _Node()
        self._separator = separator
        self._sorted = 0
        self._per_char = separator == ""
        self.update(other, **kwargs)

    def enable_sorting(self, bint enable=True):
        """Enables sorting of child nodes when iterating and traversing."""
        self._sorted = enable

    def __reduce__(self):
        return (
            _rebuild_trie,
            (type(self), self._separator, bool(self._sorted), self._root.__getstate__()),
        )

    def clear(self):
        """Removes all the values from the trie."""
        self._root = _Node()

    def update(self, other=None, **kwargs):
        """Updates stored values.  Works like :meth:`dict.update`."""
        if other:
            if hasattr(other, "keys"):
                for key in other.keys():
                    self[key] = other[key]
            else:
                for key, value in other:
                    self[key] = value
        for key, value in kwargs.items():
            self[key] = value

    def merge(self, Trie other, bint overwrite=False):
        """Moves nodes from other trie into this one (structure-level merge).

        Note that the other trie is cleared afterwards.  Raises TypeError
        when merging is not possible between the two types.
        """
        if isinstance(self, type(other)):
            self._merge_impl(self, other, overwrite)
        else:
            other._merge_impl(self, other, overwrite)
        other.clear()

    @classmethod
    def _merge_impl(cls, Trie dst, Trie src, bint overwrite):
        dst._root.merge(src._root, overwrite)

    def copy(self, make_copy=None):
        """Returns a shallow copy of the object."""
        if make_copy is None:
            make_copy = lambda x: x
        cdef Trie cpy = <Trie>type(self)()
        cpy._separator = self._separator
        cpy._sorted = self._sorted
        cpy._per_char = self._per_char
        cpy._root = self._root.copy(make_copy)
        return cpy

    def __copy__(self):
        return self.copy()

    def __deepcopy__(self, memo):
        return self.copy(lambda x: _copy.deepcopy(x, memo))

    @classmethod
    def fromkeys(cls, keys, value=None):
        """Creates a new trie with given keys set."""
        trie = cls()
        for key in keys:
            trie[key] = value
        return trie

    cdef list _path(self, object key):
        """Converts a user visible key (or _MISSING) to internal path list."""
        if self._per_char:
            if key is _MISSING:
                return []
            return list(key)
        if type(key) is not str:
            if key is _MISSING:
                return []
            raise TypeError(key)
        return PyUnicode_Split(key, self._separator, -1)

    cdef str _key(self, list path):
        return PyUnicode_Join(self._separator, path)

    cpdef str _key_from_path(self, list path):
        return self._key(path)

    cdef _Node _find(self, object key):
        """只读查找, 不构造 trace."""
        cdef _Node node = self._root
        cdef list path = self._path(key)
        cdef str step
        cdef _Node child
        for step in path:
            child = node.children.get(step)
            if child is None:
                raise KeyError(key)
            node = child
        return node

    cdef _Node _walk(self, object key, list steps):
        """查找并回填 steps(对应 _get_node 的路径部分), 缺失时抛 KeyError."""
        cdef _Node node = self._root
        cdef list path = self._path(key)
        cdef str step
        cdef _Node child
        for step in path:
            child = node.children.get(step)
            if child is None:
                raise KeyError(key)
            node = child
            steps.append(step)
        return node

    cdef _Node _walk_full(self, object key, list trace):
        """查找并回填 (step, node) 元组 trace, 缺失时抛 KeyError."""
        cdef _Node node = self._root
        cdef list path = self._path(key)
        cdef str step
        cdef _Node child
        for step in path:
            child = node.children.get(step)
            if child is None:
                raise KeyError(key)
            node = child
            trace.append((step, node))
        return node

    cdef _Node _set_node(self, object key, object value, bint only_if_missing=0):
        """Sets value for a given key, creating nodes as needed."""
        cdef _Node node = self._root
        cdef list path = self._path(key)
        cdef str step
        for step in path:
            node = node.children.require(node, step)
        if node.value is _MISSING or not only_if_missing:
            node.value = value
        return node

    def _set_node_if_no_prefix(self, object key):
        """Sets given key to True but only if none of its prefixes are present."""
        cdef list path = self._path(key)
        cdef _Node node = self._root
        cdef Py_ssize_t i = 0
        cdef Py_ssize_t n = PyList_GET_SIZE(path)
        while node.value is _MISSING:
            if i == n:
                node.value = True
                node.children = _NO_CHILDREN
                return
            node = node.children.require(node, path[i])
            i += 1

    cdef object _pop_trace(self, list trace):
        """删除 trace 末节点的值并自底向上裁剪空节点(对应 _pop_value).

        trace 元素为 (step, node), step 是从父节点进入 node 的步骤。
        """
        cdef _Node node
        cdef _Node parent
        cdef object step
        cdef object value
        cdef Py_ssize_t i = PyList_GET_SIZE(trace)
        if i:
            step, node = trace[i - 1]
        else:
            step = None
            node = self._root
        value, node.value = node.value, _MISSING
        while i > 0 and node.value is _MISSING and not node.children:
            i -= 1
            step = trace[i][0]  # 被裁剪节点的进入步骤
            if i > 0:
                parent = trace[i - 1][1]
                parent.children.delete(parent, step)
                node = parent
            else:
                self._root.children.delete(self._root, step)
                node = self._root
        return value

    def __iter__(self):
        return self.iterkeys()

    def iteritems(self, prefix=_MISSING, bint shallow=False):
        """Yields all nodes with associated values with given prefix."""
        cdef _Node node
        cdef list path = []
        if prefix is _MISSING:
            node = self._root
        else:
            node = self._walk(prefix, path)
        for p, value in node.iterate(path, shallow, self._sorted):
            yield self._key(p), value

    def iterkeys(self, prefix=_MISSING, bint shallow=False):
        """Yields all keys having associated values with given prefix."""
        cdef _Node node
        cdef list path = []
        if prefix is _MISSING:
            node = self._root
        else:
            node = self._walk(prefix, path)
        for p, _ in node.iterate(path, shallow, self._sorted):
            yield self._key(p)

    def itervalues(self, prefix=_MISSING, bint shallow=False):
        """Yields all values associated with keys with given prefix."""
        cdef _Node node
        cdef list path = []
        if prefix is _MISSING:
            node = self._root
        else:
            node = self._walk(prefix, path)
        for _, value in node.iterate(path, shallow, self._sorted):
            yield value

    def items(self, prefix=_MISSING, bint shallow=False):
        """Returns a list of ``(key, value)`` pairs in given subtrie."""
        return list(self.iteritems(prefix, shallow))

    def keys(self, prefix=_MISSING, bint shallow=False):
        """Returns a list of all the keys, with given prefix, in the trie."""
        return list(self.iterkeys(prefix, shallow))

    def values(self, prefix=_MISSING, bint shallow=False):
        """Returns a list of values in given subtrie."""
        return list(self.itervalues(prefix, shallow))

    def __len__(self):
        """Returns number of values in a trie (expensive: full traversal)."""
        return sum(1 for _ in self.itervalues())

    def __bool__(self):
        return self._root.value is not _MISSING or bool(self._root.children)

    def has_node(self, object key):
        """Returns whether given node is in the trie (bit-field of HAS_VALUE/HAS_SUBTRIE)."""
        try:
            node = self._find(key)
        except KeyError:
            return 0
        return (self.HAS_VALUE * (node.value is not _MISSING)) | (
            self.HAS_SUBTRIE * bool(node.children)
        )

    def has_key(self, object key):
        """Indicates whether given key has value associated with it."""
        try:
            return self._find(key).value is not _MISSING
        except KeyError:
            return False

    def __contains__(self, object key):
        """Dict-style membership test (delegates to has_key, O(len(key)))."""
        return self.has_key(key)

    def has_subtrie(self, object key):
        """Returns whether given key is a prefix of another key in the trie."""
        return bool(self.has_node(key) & self.HAS_SUBTRIE)

    def __getitem__(self, key_or_slice):
        """Returns value associated with given key; slice returns a value generator."""
        cdef object start = key_or_slice
        if type(start) is slice:
            if start.stop is not None or start.step is not None:
                raise TypeError(start)
            return self.itervalues(start.start)
        cdef _Node node = self._find(start)
        if node.value is _MISSING:
            raise ShortKeyError(start)
        return node.value

    def __setitem__(self, key_or_slice, value):
        """Sets value; a ``[key:]`` slice additionally clears the subtrie."""
        cdef bint is_slice = 0
        cdef object key = key_or_slice
        if type(key) is slice:
            if key.stop is not None or key.step is not None:
                raise TypeError(key)
            key = key.start
            is_slice = 1
        cdef _Node node = self._set_node(key, value, 0)
        if is_slice:
            node.children = _NO_CHILDREN

    def setdefault(self, key, default=None):
        """Sets value of a given node if not set already.  Also returns it."""
        return self._set_node(key, default, 1).value

    def pop(self, object key, default=_MISSING):
        """Deletes value associated with given key and returns it."""
        try:
            value = self._pop_with_trace(key)
        except KeyError:
            if default is not _MISSING:
                return default
            raise
        if value is not _MISSING:
            return value
        if default is not _MISSING:
            return default
        raise ShortKeyError()

    cdef object _pop_with_trace(self, object key):
        cdef list trace = []
        self._walk_full(key, trace)
        return self._pop_trace(trace)

    def popitem(self):
        """Deletes an arbitrary value from the trie and returns it."""
        if not self:
            raise KeyError()
        cdef _Node node = self._root
        cdef list trace = []
        cdef list steps = []
        while node.value is _MISSING:
            step, node = node.children.pick()
            steps.append(step)
            trace.append((step, node))
        key = self._key(steps)
        return key, self._pop_trace(trace)

    def __delitem__(self, key_or_slice):
        """Deletes value associated with given key; slice deletes whole subtrie."""
        cdef bint is_slice = 0
        cdef object key = key_or_slice
        if type(key_or_slice) is slice:
            if key_or_slice.stop is not None or key_or_slice.step is not None:
                raise TypeError(key_or_slice)
            key = key_or_slice.start
            is_slice = 1
        cdef list trace = []
        cdef _Node node = self._walk_full(key, trace)
        if is_slice:
            node.children = _NO_CHILDREN
        elif node.value is _MISSING:
            raise ShortKeyError(key)
        self._pop_trace(trace)

    def walk_towards(self, object key):
        """Yields nodes on the path to given node as _Step objects."""
        cdef _Node node = self._root
        cdef list path = self._path(key)
        cdef Py_ssize_t pos = 0
        cdef Py_ssize_t n = PyList_GET_SIZE(path)
        while True:
            yield _Step(self, path, pos, node)
            if pos == n:
                break
            node = node.children.get(path[pos])
            if node is None:
                raise KeyError(key)
            pos += 1

    def prefixes(self, object key):
        """Walks towards the node specified by key and yields all found items."""
        try:
            for step in self.walk_towards(key):
                if step.is_set:
                    yield step
        except KeyError:
            pass

    def shortest_prefix(self, object key):
        """Finds the shortest prefix of a key with a value."""
        return next(self.prefixes(key), _NONE_STEP)

    def longest_prefix(self, object key):
        """Finds the longest prefix of a key with a value."""
        ret = _NONE_STEP
        for ret in self.prefixes(key):
            pass
        return ret

    def strictly_equals(self, other):
        """Checks whether tries are equal with the same structure and type."""
        if self is other:
            return True
        if type(self) is not type(other):
            return False
        result = self._eq_impl(other)
        if result is NotImplemented:
            return False
        return result

    def __eq__(self, other):
        """Compares this trie's mapping with another mapping (structure-insensitive)."""
        if self is other:
            return True
        if type(other) is type(self):
            result = self._eq_impl(other)
            if result is not NotImplemented:
                return result
        return NotImplemented

    def _eq_impl(self, Trie other):
        return self._root.equals(other._root)

    def __ne__(self, other):
        return not self == other

    def _str_items(self, fmt="{k}: {v}"):
        return ", ".join(fmt.format(k=item[0], v=item[1]) for item in self.iteritems())

    def __str__(self):
        return f"{self.__class__.__name__}({self._str_items()})"

    def __repr__(self):
        return f"{self.__class__.__name__}([{self._str_items('({k!r}: {v!r})')}])"

    def traverse(self, node_factory, prefix=_MISSING):
        """Traverses the tree using node_factory object."""
        cdef list steps = []
        cdef _Node node = self._walk(prefix, steps)
        return node.traverse(
            node_factory,
            self._key_from_path,
            steps,
            self._sorted,
        )

    def _count_nodes(self):
        """诊断用: 返回结构中的 _Node 总数(空 trie 应为 1, 即根节点)."""
        cdef _Node node = self._root
        cdef list stack = [node]
        cdef list steps, nodes
        cdef Py_ssize_t count = 0
        while stack:
            node = stack.pop()
            count += 1
            steps, nodes = node.children.sequences(False)
            stack.extend(nodes)
        return count


def _rebuild_trie(cls, separator, sorted_flag, root_state):
    trie = cls(separator=separator)
    trie.enable_sorting(sorted_flag)
    trie._root.__setstate__(root_state)
    return trie


Mapping.register(Trie)


cdef class CharTrie(Trie):
    """A variant of Trie which accepts strings as keys, per-character paths."""


cdef class StringTrie(Trie):
    """Trie variant accepting strings with a separator as keys."""

    def __init__(self, other=None, str separator="/", **kwargs):
        if not isinstance(separator, str):
            raise TypeError("separator must be a string")
        if not separator:
            raise ValueError("separator can not be empty")
        self._separator = separator
        self._root = _Node()
        self._sorted = 0
        self._per_char = 0
        self.update(other, **kwargs)

    @classmethod
    def fromkeys(cls, keys, value=None, separator="/"):
        trie = cls(separator=separator)
        for key in keys:
            trie[key] = value
        return trie

    @classmethod
    def _merge_impl(cls, Trie dst, Trie src, bint overwrite):
        if not isinstance(dst, StringTrie):
            raise TypeError(f"{src.__class__.__name__} cannot be merged into a {dst.__class__.__name__}")
        Trie._merge_impl(dst, src, overwrite)

    def __str__(self):
        if not self:
            return f"{self.__class__.__name__}(separator={self._separator!r})"
        return f"{self.__class__.__name__}({self._str_items()!r}, separator={self._separator!r})"

    def __repr__(self):
        return f"{self.__class__.__name__}([{self._str_items('({k!r}: {v!r})')}], separator={self._separator!r})"

    def _eq_impl(self, other):
        # If separators differ, fall back to generic comparison: keys may still
        # be equal even though the structure differs.
        if not isinstance(other, StringTrie):
            return NotImplemented
        if self._separator != (<StringTrie>other)._separator:
            return NotImplemented
        return Trie._eq_impl(self, other)
