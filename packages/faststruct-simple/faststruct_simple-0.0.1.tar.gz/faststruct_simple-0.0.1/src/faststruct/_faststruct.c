#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdint.h>
#include <string.h>
#include <arpa/inet.h>   // htonl / ntohl

typedef struct {
    const char* k_ptr;
    Py_ssize_t  k_len;
    Py_buffer   vbuf;    // holds exporter ref
} Entry;

// -------------------- helper functions --------------------
static inline int read_u32(const char* buf, Py_ssize_t L, Py_ssize_t* off, uint32_t* out) {
    if (*off + 4 > L) return -1;
    uint32_t tmp;
    memcpy(&tmp, buf + *off, 4);
    *out = ntohl(tmp);
    *off += 4;
    return 0;
}

static inline int write_u32(char* buf, Py_ssize_t L, Py_ssize_t* off, uint32_t x) {
    if (*off + 4 > L) return -1;
    uint32_t tmp = htonl(x);
    memcpy(buf + *off, &tmp, 4);
    *off += 4;
    return 0;
}

// --------------------- serialize ------------------------
static PyObject* serialize(PyObject* self, PyObject* args) {
    PyObject* dict;
    if (!PyArg_ParseTuple(args, "O!", &PyDict_Type, &dict)) return NULL;

    Py_ssize_t n = PyDict_Size(dict);
    if (n < 0) return NULL;

    Entry* entries = NULL;
    if (n > 0) {
        entries = (Entry*)PyMem_Malloc((size_t)n * sizeof(Entry));
        if (!entries) return PyErr_NoMemory();
    }

    PyObject *key, *value;
    Py_ssize_t pos = 0;
    Py_ssize_t i = 0;
    Py_ssize_t total_body = 0;

    while (PyDict_Next(dict, &pos, &key, &value)) {
        if (!PyUnicode_Check(key)) {
            PyErr_SetString(PyExc_TypeError, "All keys must be str");
            goto error;
        }
        Py_ssize_t k_len;
        const char* k_ptr = PyUnicode_AsUTF8AndSize(key, &k_len);
        if (!k_ptr) goto error;

        Py_buffer vbuf;
        if (PyObject_GetBuffer(value, &vbuf, PyBUF_CONTIG_RO) < 0) {
            PyErr_SetString(PyExc_TypeError, "All values must support contiguous buffer (PyBUF_CONTIG_RO)");
            goto error;
        }

        entries[i].k_ptr = k_ptr;
        entries[i].k_len = k_len;
        entries[i].vbuf  = vbuf;
        i++;

        total_body += 4 + k_len + 4 + vbuf.len;
    }

    if (i != n) {
        PyErr_SetString(PyExc_RuntimeError, "Dict changed size during iteration");
        goto error;
    }

    Py_ssize_t total = 4 + total_body;
    PyObject* out = PyBytes_FromStringAndSize(NULL, total);
    if (!out) goto error;

    char* buf = PyBytes_AS_STRING(out);
    Py_ssize_t off = 0;

    if (write_u32(buf, total, &off, (uint32_t)n) < 0) {
        Py_DECREF(out);
        PyErr_SetString(PyExc_ValueError, "Internal write error");
        goto error;
    }

    for (Py_ssize_t j = 0; j < n; j++) {
        const char* k_ptr = entries[j].k_ptr;
        Py_ssize_t  k_len = entries[j].k_len;
        const char* v_ptr = (const char*)entries[j].vbuf.buf;
        Py_ssize_t  v_len = entries[j].vbuf.len;

        if (k_len < 0 || k_len > UINT32_MAX || v_len < 0 || v_len > UINT32_MAX) {
            Py_DECREF(out);
            PyErr_SetString(PyExc_OverflowError, "Key/value too large for uint32 length");
            goto error;
        }

        if (write_u32(buf, total, &off, (uint32_t)k_len) < 0) { Py_DECREF(out); goto error_short; }
        memcpy(buf + off, k_ptr, (size_t)k_len); off += k_len;

        if (write_u32(buf, total, &off, (uint32_t)v_len) < 0) { Py_DECREF(out); goto error_short; }
        memcpy(buf + off, v_ptr, (size_t)v_len); off += v_len;
    }

    for (Py_ssize_t j = 0; j < n; j++) PyBuffer_Release(&entries[j].vbuf);
    PyMem_Free(entries);
    return out;

error_short:
    PyErr_SetString(PyExc_ValueError, "Internal buffer overflow");
error:
    if (entries) {
        for (Py_ssize_t j = 0; j < i; j++) PyBuffer_Release(&entries[j].vbuf);
        PyMem_Free(entries);
    }
    return NULL;
}

// --------------------- deserialize ------------------------
static PyObject* deserialize(PyObject* self, PyObject* args) {
    PyObject* payload_obj;

    if (!PyArg_ParseTuple(args, "O!", &PyBytes_Type, &payload_obj)) return NULL;

    char* buf = PyBytes_AS_STRING(payload_obj);
    Py_ssize_t L = PyBytes_GET_SIZE(payload_obj);
    Py_ssize_t off = 0;

    uint32_t count_u32;
    if (read_u32(buf, L, &off, &count_u32) < 0) goto malformed;

    Py_ssize_t count = (Py_ssize_t)count_u32;

    PyObject* dict = PyDict_New();
    if (!dict) return NULL;

    for (Py_ssize_t i = 0; i < count; i++) {
        uint32_t k_len, v_len;

        if (read_u32(buf, L, &off, &k_len) < 0) goto error;
        if (off + (Py_ssize_t)k_len > L) goto error;

        PyObject* key = PyUnicode_DecodeUTF8(buf + off, (Py_ssize_t)k_len, "strict");
        off += (Py_ssize_t)k_len;
        if (!key) goto error;

        if (read_u32(buf, L, &off, &v_len) < 0) { Py_DECREF(key); goto error; }
        if (off + (Py_ssize_t)v_len > L) { Py_DECREF(key); goto error; }

        PyObject* val = PyBytes_FromStringAndSize(buf + off, (Py_ssize_t)v_len);
        if (!val) { Py_DECREF(key); goto error; }

        off += (Py_ssize_t)v_len;

        if (PyDict_SetItem(dict, key, val) < 0) {
            Py_DECREF(key);
            Py_DECREF(val);
            goto error;
        }

        Py_DECREF(key);
        Py_DECREF(val);
    }

    return dict;

malformed:
error:
    PySys_WriteStderr("❌ Malformed serialized payload! off=%zd, L=%zd, count=%u\n", off, L, count_u32);
    PyErr_SetString(PyExc_ValueError, "Malformed serialized payload");
    return NULL;
}

// --------------------- Module definition ------------------------
static PyMethodDef FastStructMethods[] = {
    {"serialize",   (PyCFunction)serialize,   METH_VARARGS, "Serialize dict into binary (with count header)"},
    {"deserialize", (PyCFunction)deserialize, METH_VARARGS, "Deserialize binary payload"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef faststructmodule = {
    PyModuleDef_HEAD_INIT,
    "_faststruct",
    "Ultra-fast binary serializer (simple / experimental)",
    -1,
    FastStructMethods
};

PyMODINIT_FUNC PyInit__faststruct(void) {
    return PyModule_Create(&faststructmodule);
}
