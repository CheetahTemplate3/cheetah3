
#include <Python.h>

#include <stdbool.h>
#include <stdlib.h>
#include <stdio.h>

#ifdef __cplusplus
extern "C" {
#endif

static PyObject *typesModule = NULL;

static PyObject *_errorMessage(char *arg, char *legalTypes, char *extra)
{
    return PyString_FromFormat("Argument '%s' must be %s\n", arg, legalTypes);
}

static PyObject *py_verifytype(PyObject *self, PyObject *args, PyObject *kwargs)
{
    PyObject *argument, *legalTypes;
    char *arg_string, *types_string;
    char *extra = NULL;
    PyObject *iterator, *item;
    bool rc = false;
    static char *kwlist[] = {"argument", "argument_name", "legalType",
                "types_string", "errmsgExtra", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "OsOs|s", kwlist, &argument, 
                &arg_string, &legalTypes, &types_string, &extra)) {
        return NULL;
    }

    iterator = PyObject_GetIter(legalTypes);
    if (iterator == NULL) {
        Py_RETURN_FALSE;
    }

    while (item = PyIter_Next(iterator)) {
        if (argument->ob_type == item) {
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

static const char _verifytypedoc[] = "\
\n\
";
static struct PyMethodDef _verifytype_methods[] = {
    {"verifyType", py_verifytype, METH_VARARGS | METH_KEYWORDS, NULL},
    {NULL}
};

PyMODINIT_FUNC init_verifytype()
{
    PyObject *module = Py_InitModule3("_verifytype", _verifytype_methods,
            _verifytypedoc);
    typesModule = PyImport_ImportModule("types");
}

#ifdef __cplusplus
}
#endif
