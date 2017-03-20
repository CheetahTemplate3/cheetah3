/*
 * C-version of the src/Filters.py module
 *
 * (c) 2009, R. Tyler Ballance <tyler@slide.com>
 */
#include <Python.h>

#include "_filters.h"

#if __STDC_VERSION__ >= 199901L
#include <stdbool.h>
#else
typedef enum { false, true } bool;
#endif

#ifdef __cplusplus
extern "C" {
#endif


static PyObject *py_filter(PyObject *self, PyObject *args, PyObject *kwargs)
{
    Py_RETURN_FALSE;
}

static const char _filtersdoc[] = "\
\n\
";
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

PyMODINIT_FUNC init_filters()
{
    PyObject *module = Py_InitModule3("_filters", py_filtermethods, _filtersdoc);

    PyFilterType.tp_new = PyType_GenericNew;
    if (PyType_Ready(&PyFilterType) < 0)
        return;

    Py_INCREF(&PyFilterType);

    PyModule_AddObject(module, "Filter", (PyObject *)(&PyFilterType));
}

#ifdef __cplusplus
}
#endif
