/*
 * Implementing a few of the functions needed for Template.py in C
 *
 * (c) 2009, R. Tyler Ballance <tyler@slide.com>
 */
#include <Python.h>

#ifdef __cplusplus
extern "C" {
#endif

static PyObject *unspecifiedModule = NULL;
static PyObject *unspecified = NULL;

static PyObject *py_valordefault(PyObject *self, PyObject *args, PyObject *kwargs)
{
    PyObject *value, *def;

    if (!PyArg_ParseTuple(args, "OO", &value, &def))
        return NULL;

    if (value == unspecified) {
        Py_XINCREF(def);
        return def;
    }
    Py_XINCREF(value);
    return value;
}

static const char _template_doc[] = "\
\n\
";
static struct PyMethodDef _template_methods[] = {
    {"valOrDefault", (PyCFunction)py_valordefault, METH_VARARGS, NULL},
    {NULL}
};

PyMODINIT_FUNC init_template()
{
    PyObject *module = Py_InitModule3("_template", _template_methods,
            _template_doc);
    unspecifiedModule = PyImport_ImportModule("Cheetah.Unspecified");
    if ( (PyErr_Occurred()) || (!unspecifiedModule) )
        return;
    unspecified = PyObject_GetAttrString(unspecifiedModule, "Unspecified");
    if (PyErr_Occurred())
        return;
}

#ifdef __cplusplus
}
#endif
