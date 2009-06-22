/*
 * (c) 2009, R. Tyler Ballance <tyler@slide.com>
 */

#ifndef _CHEETAH_H_
#define _CHEETAH_H_

#include <Python.h>

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Python 2.3 compatibility
 */
#ifndef Py_RETURN_TRUE
#define Py_RETURN_TRUE Py_INCREF(Py_True);\
    return Py_True
#endif
#ifndef Py_RETURN_FALSE
#define Py_RETURN_FALSE Py_INCREF(Py_False);\
    return Py_False
#endif 
#ifndef Py_RETURN_NONE
#define Py_RETURN_NONE Py_INCREF(Py_None);\
    return Py_None
#endif


/*
 * Filter Module
 */
typedef struct {
    PyObject_HEAD
    /* type specific fields */
} PyFilter;

static PyObject *py_filter(PyObject *self, PyObject *args, PyObject *kwargs);

static struct PyMethodDef py_filtermethods[] = {
    {"filter", (PyCFunction)(py_filter), METH_VARARGS | METH_KEYWORDS,
            PyDoc_STR("Filter stuff")},
    {NULL},
};
static PyTypeObject PyFilterType = {
    PyObject_HEAD_INIT(NULL)
    0,                         /*ob_size*/
    "_filters.Filter",             /*tp_name*/
    sizeof(PyFilter), /*tp_basicsize*/
    0,                         /*tp_itemsize*/
    0,                         /*tp_dealloc*/
    0,                         /*tp_print*/
    0,                         /*tp_getattr*/
    0,                         /*tp_setattr*/
    0,                         /*tp_compare*/
    0,                         /*tp_repr*/
    0,                         /*tp_as_number*/
    0,                         /*tp_as_sequence*/
    0,                         /*tp_as_mapping*/
    0,                         /*tp_hash */
    0,                         /*tp_call*/
    0,                         /*tp_str*/
    0,                         /*tp_getattro*/
    0,                         /*tp_setattro*/
    0,                         /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT,        /*tp_flags*/
    "Filter object",           /* tp_doc */
    0,                     /* tp_traverse */
    0,                     /* tp_clear */
    0,                     /* tp_richcompare */
    0,                     /* tp_weaklistoffset */
    0,                     /* tp_iter */
    0,                     /* tp_iternext */
    py_filtermethods,             /* tp_methods */
#if 0
    py_filtermembers,             /* tp_members */
    0,                         /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    (initproc)Noddy_init,      /* tp_init */
    0,                         /* tp_alloc */
    NULL,                 /* tp_new */
#endif
};

/*
 * End Filter Module 
 */

#ifdef __cplusplus
}
#endif

#endif
