/* *************************************************************************** */
#include "Python.h"             /* Python header files */
#include <string.h>
#include <stdio.h>
#include <stdlib.h>


static PyObject *ErrorObject;   /* locally-raised exception */

#define onError(message) \
    { PyErr_SetString(ErrorObject, message); return NULL; }

/* *************************************************************************** */
/* Exported module method-functions */


static PyObject *
namemapper_valueForKey(PyObject *self, PyObject *args)       /* args: (string) */
{
  PyObject *obj;
  PyObject *theValue;
  char *key;
  static char *underscore = "_";
  char *underscoreKey;

  if (!PyArg_ParseTuple(args, "Os", &obj, &key)) {
    return NULL;
  }

  if (PyObject_HasAttrString(obj, key)) {
    return PyObject_GetAttrString(obj, key);
  } else if (PyMapping_Check(obj) && PyMapping_HasKeyString(obj, key)) {
    return PyMapping_GetItemString(obj, key);
  }

  underscoreKey = malloc(strlen(key) + strlen(underscore) + 1);
  strcpy(underscoreKey, underscore);
  strcat(underscoreKey, key);

  if (PyObject_HasAttrString(obj, underscoreKey)) {
    theValue = PyObject_GetAttrString(obj, underscoreKey);
  } else {
    theValue = Py_BuildValue(""); //actually I just want to raise an error
  }
  free(underscoreKey);
  return theValue;
}

static PyObject *
namemapper_valueForKey2(PyObject *self, PyObject *args, PyObject *keywds)       /* args: (string) */
{

  PyObject *obj;
  PyObject *theValue;
  PyObject *theDefault;
  char *key;
  static char *underscore = "_";
  char *underscoreKey;

  static char *kwlist[] = {"obj", "key", "default", NULL};

  if (!PyArg_ParseTupleAndKeywords(args, keywds, "Os|O", kwlist,  &obj, &key, &theDefault)) {
    return NULL;
  }

  if (PyObject_HasAttrString(obj, key)) {
    return PyObject_GetAttrString(obj, key);
  } else if (PyMapping_Check(obj) && PyMapping_HasKeyString(obj, key)) {
    return PyMapping_GetItemString(obj, key);
  }

  theDefault = Py_BuildValue("s", "NoDefaultGiven");
  underscoreKey = malloc(strlen(key) + strlen(underscore) + 1);
  strcpy(underscoreKey, underscore);
  strcat(underscoreKey, key);

  if (PyObject_HasAttrString(obj, underscoreKey)) {
    theValue = PyObject_GetAttrString(obj, underscoreKey);
  } else {
    theValue = theDefault;
  }
  free(underscoreKey);
  return theValue;
  
}

/* *************************************************************************** */
/* Method registration table: name-string -> function-pointer */

static struct PyMethodDef namemapper_methods[] = {
  {"valueForKey", namemapper_valueForKey,  1},
  {"valueForKey2", (PyCFunction)namemapper_valueForKey2,  METH_VARARGS|METH_KEYWORDS},
  {NULL,         NULL}
};


/* *************************************************************************** */
/* Initialization function (import-time) */

void init_namemapper()
{
  PyObject *m, *d;

  /* create the module and add the functions */
  m = Py_InitModule("_namemapper", namemapper_methods);        /* registration hook */
  
  /* add symbolic constants to the module */
  d = PyModule_GetDict(m);
  ErrorObject = Py_BuildValue("s", "namemapper.error");   /* export exception */
  PyDict_SetItemString(d, "error", ErrorObject);       /* add more if need */
  
  /* check for errors */
  if (PyErr_Occurred())
    Py_FatalError("can't initialize module spam");
}


