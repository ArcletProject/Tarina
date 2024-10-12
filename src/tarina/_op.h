#pragma once

#include <Python.h>

#ifndef LINEAR_PROBES
#define LINEAR_PROBES 9
#endif

/* This must be >= 1 */
#define PERTURB_SHIFT 5

static inline Py_ssize_t tuplesize(PyObject *ob) {
    PyVarObject *var_ob = (PyVarObject*)ob;
    return var_ob->ob_size;
}

static inline PyObject * tupleitem(PyObject *a, Py_ssize_t i)
{
    return ((PyTupleObject*)a)->ob_item[i];
}

// #include "stringlib/asciilib.h"
// #include "stringlib/fastsearch.h"
// #include "stringlib/partition.h"
// #include "stringlib/split.h"
// #include "stringlib/count.h"
// #include "stringlib/find.h"
// #include "stringlib/find_max_char.h"
// #include "stringlib/undef.h"

// #include "stringlib/ucs1lib.h"
// #include "stringlib/fastsearch.h"
// #include "stringlib/partition.h"
// #include "stringlib/split.h"
// #include "stringlib/count.h"
// #include "stringlib/find.h"
// #include "stringlib/replace.h"
// #include "stringlib/find_max_char.h"
// #include "stringlib/undef.h"

// #include "stringlib/ucs2lib.h"
// #include "stringlib/fastsearch.h"
// #include "stringlib/partition.h"
// #include "stringlib/split.h"
// #include "stringlib/count.h"
// #include "stringlib/find.h"
// #include "stringlib/replace.h"
// #include "stringlib/find_max_char.h"
// #include "stringlib/undef.h"

// #include "stringlib/ucs4lib.h"
// #include "stringlib/fastsearch.h"
// #include "stringlib/partition.h"
// #include "stringlib/split.h"
// #include "stringlib/count.h"
// #include "stringlib/find.h"
// #include "stringlib/replace.h"
// #include "stringlib/find_max_char.h"
// #include "stringlib/undef.h"

// static inline Py_ssize_t
// findchar(const void *s, int kind, Py_ssize_t size, Py_UCS4 ch)
// {
//     switch (kind) {
//     case PyUnicode_1BYTE_KIND:
//         if ((Py_UCS1) ch != ch)
//             return -1;
//         return ucs1lib_find_char((const Py_UCS1 *) s, size, (Py_UCS1) ch);
//     case PyUnicode_2BYTE_KIND:
//         if ((Py_UCS2) ch != ch)
//             return -1;
//         return ucs2lib_find_char((const Py_UCS2 *) s, size, (Py_UCS2) ch);
//     case PyUnicode_4BYTE_KIND:
//         return ucs4lib_find_char((const Py_UCS4 *) s, size, ch);
//     default:
//         Py_UNREACHABLE();
//     }
// }

// static int contains(PyObject *str, Py_UCS4 ch) {
//     const void *buf;
//     int result, kind, len;
//     kind = PyUnicode_KIND(str);
//     len = PyUnicode_GET_LENGTH(str);
//     buf = PyUnicode_DATA(str);
//     result = findchar((const char *)buf, kind, len, ch) != -1;
//     return result;
// }

Py_LOCAL_INLINE(int)
unicode_eq(PyObject *str1, PyObject *str2)
{
    Py_ssize_t len = PyUnicode_GET_LENGTH(str1);
    if (PyUnicode_GET_LENGTH(str2) != len) {
        return 0;
    }

    int kind = PyUnicode_KIND(str1);
    if (PyUnicode_KIND(str2) != kind) {
        return 0;
    }

    const void *data1 = PyUnicode_DATA(str1);
    const void *data2 = PyUnicode_DATA(str2);
    return (memcmp(data1, data2, len * kind) == 0);
}


static setentry *
set_lookkey(PySetObject *so, PyObject *key, Py_hash_t hash)
{
    setentry *table;
    setentry *entry;
    size_t perturb = hash;
    size_t mask = so->mask;
    size_t i = (size_t)hash & mask; /* Unsigned for defined overflow behavior */
    int probes;
    int cmp;

    while (1) {
        entry = &so->table[i];
        probes = (i + LINEAR_PROBES <= mask) ? LINEAR_PROBES: 0;
        do {
            if (entry->hash == 0 && entry->key == NULL)
                return entry;
            if (entry->hash == hash) {
                PyObject *startkey = entry->key;
                assert(startkey != dummy);
                if (startkey == key)
                    return entry;
                if (PyUnicode_CheckExact(startkey)
                    && PyUnicode_CheckExact(key)
                    && unicode_eq(startkey, key))
                    return entry;
                table = so->table;
                Py_INCREF(startkey);
                cmp = PyObject_RichCompareBool(startkey, key, Py_EQ);
                Py_DECREF(startkey);
                if (cmp < 0)
                    return NULL;
                if (table != so->table || entry->key != startkey)
                    return set_lookkey(so, key, hash);
                if (cmp > 0)
                    return entry;
                mask = so->mask;
            }
            entry++;
        } while (probes--);
        perturb >>= PERTURB_SHIFT;
        i = (i * 5 + 1 + perturb) & mask;
    }
}


static int
set_contains_key(PyObject *so, PyObject *key)
{
    Py_hash_t hash;
    setentry *entry;

    if (!PyUnicode_CheckExact(key) ||
        (hash = ((PyASCIIObject *)key)->hash) == -1) {
        hash = PyObject_Hash(key);
        if (hash == -1)
            return -1;
    }

    entry = set_lookkey(((PySetObject *)so), key, hash);
    if (entry != NULL)
        return entry->key != NULL;
    return -1;
}