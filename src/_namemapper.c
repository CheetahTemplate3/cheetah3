/* *************************************************************************** */
#include "Python.h"             /* Python header files */
#include <string.h>
#include <stdio.h>
#include <stdlib.h>


static PyObject *ErrorObject;   /* locally-raised exception */

#define onError(message) \
    { PyErr_SetString(ErrorObject, message); return NULL; }

#define MAXCHUNKS 50		/* max num of nameChunks for the arrays */

/* *************************************************************************** */
/* First the c versions of the functions */
/* *************************************************************************** */

static PyObject *
PyNamemapper_valueForKey(PyObject *obj, char *key)
{
  PyObject *theValue;
  const char *underscore = "_";
  char *underscoreKey;

  if (PyObject_HasAttrString(obj, key)) {
    theValue = PyObject_GetAttrString(obj, key);
  } else if (PyMapping_Check(obj) && PyMapping_HasKeyString(obj, key)) {
    theValue =  PyMapping_GetItemString(obj, key);
  } else {
    underscoreKey = malloc(strlen(key) + strlen(underscore) + 1);
    strcpy(underscoreKey, underscore);
    strcat(underscoreKey, key);

    if (PyObject_HasAttrString(obj, underscoreKey)) {
      theValue = PyObject_GetAttrString(obj, underscoreKey);
    } else {
      onError(key);
    }
    free(underscoreKey);
  }
  /* @@ Do I need to: Py_INCREF(theValue); */
  return theValue;		
}

static PyObject *
PyNamemapper_valueForName(PyObject *obj, char *nameChunks[], 
			  int numChunks, 
			  int executeCallables)
{
  char *firstKey;
  PyObject *binding;
  char *remainingChunks[MAXCHUNKS]; 
  int i;

  firstKey = nameChunks[0];

  if (! (binding = PyNamemapper_valueForKey(obj, firstKey))){
    return NULL;
  }
  
  if (executeCallables && PyCallable_Check(binding) && (!PyInstance_Check(binding)) 
      && (!PyClass_Check(binding)) ) {
    binding = PyObject_CallObject(binding, NULL);
  }
  
  if (numChunks > 1) {
    for (i=1; i < numChunks; i++) {
      remainingChunks[i-1] = nameChunks[i];
    }
    if (!(binding = PyNamemapper_valueForName(binding, remainingChunks, 
					      numChunks - 1, executeCallables))) {
      return NULL;
    }
    return binding;
  } else {
    return binding;
  }
}

/* *************************************************************************** */
/* Now the module functions to export into Python */
/* *************************************************************************** */

static PyObject *
namemapper_valueForKey(PyObject *self, PyObject *args)       /* args: (string) */
{
  PyObject *obj;
  char *key;

  if (!PyArg_ParseTuple(args, "Os", &obj, &key)) {
    return NULL;
  }

  return PyNamemapper_valueForKey(obj, key);
}

static PyObject *
namemapper_valueForName(PyObject *self, PyObject *args, PyObject *keywds)       /* args: (string) */
{

  PyObject *obj;
  const char *name;
  int executeCallables = 0;

  char *dot = ".";
  char *copyOfName;
  char *nameChunks[MAXCHUNKS];
  int numChunks = 1;
  char *nextChunk;

  static char *kwlist[] = {"obj", "name", "executeCallables", NULL};

  if (!PyArg_ParseTupleAndKeywords(args, keywds, "Os|i", kwlist,  &obj, &name, &executeCallables)) {
    return NULL;
  }

  copyOfName = malloc(strlen(name) + 1);
  copyOfName = strcpy(copyOfName, name);

  nameChunks[0] = strtok(copyOfName, dot);
  while ((nextChunk = strtok(NULL, dot)) != NULL) {
    nameChunks[numChunks++] = nextChunk;
  }
  /* @@ DO I NEED TO: free(copyOfName); */

  return PyNamemapper_valueForName(obj, nameChunks, numChunks, executeCallables);
}

/* *************************************************************************** */
/* Method registration table: name-string -> function-pointer */

static struct PyMethodDef namemapper_methods[] = {
  {"valueForKey", namemapper_valueForKey,  1},
  {"valueForName", (PyCFunction)namemapper_valueForName,  METH_VARARGS|METH_KEYWORDS},
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
  PyDict_SetItemString(d, "NotFound", ErrorObject);       /* add more if need */
  
  /* check for errors */
  if (PyErr_Occurred())
    Py_FatalError("can't initialize module spam");
}


