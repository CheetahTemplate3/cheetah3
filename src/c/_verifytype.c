/*
 * C-version of the src/Utils/VerifyType.py module.
 *
 * (c) 2009, R. Tyler Ballance <tyler@slide.com>
 */
#include <Python.h>
#if __STDC_VERSION__ >= 199901L
#include <stdbool.h>
#else
typedef enum { false, true } bool;
#endif

#include "Cheetah.h"

#ifdef __cplusplus
extern "C" {
#endif

static PyObject *_errorMessage(char *arg, char *legalTypes, char *extra)
{
    return PyString_FromFormat("Argument '%s' must be %s\n", arg, legalTypes);
}

static PyObject *py_verifytype(PyObject *self, PyObject *args, PyObject *kwargs)
{
    PyObject *argument, *legalTypes;
    char *arg_string, *types_string, *extra;
    PyObject *iterator, *item;
    bool rc = false;
    char *kwlist[] = {"argument", "argument_name", "legalType",
                "types_string", "errmsgExtra", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "OsOs|s", kwlist, &argument, 
                &arg_string, &legalTypes, &types_string, &extra))
        return NULL;

    iterator = PyObject_GetIter(legalTypes);
    if (iterator == NULL) {
        Py_RETURN_FALSE;
    }

    while (item = PyIter_Next(iterator)) {
        if ((PyObject *)argument->ob_type == item) {
            rc = true;
            Py_DECREF(item);
            break;
        }
        Py_DECREF(item);
    }
    Py_DECREF(iterator);

    if (rc)
        Py_RETURN_TRUE;

    PyErr_SetObject(PyExc_TypeError, _errorMessage(arg_string,
            types_string, extra));
    return NULL;
}

static PyObject *py_verifytypeclass(PyObject *self, PyObject *args, PyObject *kwargs) 
{
    PyObject *argument, *legalTypes, *klass;
    PyObject *verifyTypeArgs, *v;
    char *arg_string, *types_string, *extra;
    bool rc = false;

    char *kwlist[] = {"argument", "argument_name", "legalTypes", 
           "types_string", "klass", "errmsgExtra", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "OsOsO|s", kwlist, &argument,
                &arg_string, &legalTypes, &types_string, &klass, &extra))
        return NULL;

    verifyTypeArgs = Py_BuildValue("OsOs", argument, arg_string, legalTypes, 
            types_string);
    v = py_verifytype(self, verifyTypeArgs, NULL);

    if (PyErr_Occurred())
        return NULL;

    if (PyClass_Check(argument) && (!PyClass_IsSubclass(argument, klass)) ) {
        PyErr_SetObject(PyExc_TypeError, _errorMessage(arg_string,
                types_string, extra));
        return NULL;
    }
    Py_RETURN_TRUE;
}

static const char _verifytypedoc[] = "\
\n\
";
static struct PyMethodDef _verifytype_methods[] = {
    {"verifyType", (PyCFunction)py_verifytype, METH_VARARGS | METH_KEYWORDS, NULL},
    {"verifyTypeClass", (PyCFunction)py_verifytypeclass, METH_VARARGS | METH_KEYWORDS, NULL},
    {NULL}
};

PyMODINIT_FUNC init_verifytype()
{
    PyObject *module = Py_InitModule3("_verifytype", _verifytype_methods,
            _verifytypedoc);
}

#ifdef __cplusplus
}
#endif
