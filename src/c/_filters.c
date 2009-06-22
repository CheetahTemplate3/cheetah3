/*
 * C-version of the src/Filters.py module
 *
 * (c) 2009, R. Tyler Ballance <tyler@slide.com>
 */
#include <Python.h>

#include "Cheetah.h"

#include <stdbool.h>

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
static struct PyMethodDef _filters_methods[] = {
    {NULL}
};

PyMODINIT_FUNC init_filters()
{
    PyObject *module = Py_InitModule3("_filters", _filters_methods, _filtersdoc);

    PyFilterType.tp_new = PyType_GenericNew;
    if (PyType_Ready(&PyFilterType) < 0)
        return;

    Py_INCREF(&PyFilterType);

    PyModule_AddObject(module, "Filter", (PyObject *)(&PyFilterType));
}

#ifdef __cplusplus
}
#endif
