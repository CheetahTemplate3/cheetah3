/* *************************************************************************** */
#include "Python.h"             /* Python header files */
#include <string.h>
#include <stdio.h>
#include <stdlib.h>


static PyObject *ErrorObject;   /* locally-raised exception */

#define onError(message) \
    { PyErr_SetString(ErrorObject, message); return NULL; }

#define MAXCHUNKS 25		/* max num of nameChunks for the arrays */

/* *************************************************************************** */
/* First the c versions of the functions */
/* *************************************************************************** */

static PyObject *
PyNamemapper_valueForKey(PyObject *obj, char *key)
{
  PyObject *theValue;
  const char *underscore = "_";
  static char * underscoreKey = NULL;
  static int bufSize = 0;
  static int newBufSize = 0;

  if (PyObject_HasAttrString(obj, key)) {
    theValue = PyObject_GetAttrString(obj, key);
  } else if (PyMapping_Check(obj) && PyMapping_HasKeyString(obj, key)) {
    theValue =  PyMapping_GetItemString(obj, key);
  } else {

    newBufSize = strlen(key) + 2; /* +1 for "_", +1 for \0 terminator */
    if(newBufSize>bufSize) {
      bufSize = newBufSize;
      if(underscoreKey) {
	underscoreKey = realloc(underscoreKey, bufSize);
      } else {
	underscoreKey = malloc(bufSize);
      }
    }

    strcpy(underscoreKey, underscore);
    strcat(underscoreKey, key);

    if (PyObject_HasAttrString(obj, underscoreKey)) {
      theValue = PyObject_GetAttrString(obj, underscoreKey);
    } else {
      onError(key);
    }
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

  firstKey = nameChunks[0];

  if (! (binding = PyNamemapper_valueForKey(obj, firstKey))){
    return NULL;
  }
  
  if (executeCallables && PyCallable_Check(binding) && (!PyInstance_Check(binding)) 
      && (!PyClass_Check(binding)) ) {
    binding = PyObject_CallObject(binding, NULL);
  }
  
  if (numChunks > 1) {

    if (!(binding = PyNamemapper_valueForName(binding, nameChunks+1, 
					      numChunks - 1, executeCallables))) {
      return NULL;
    }
    return binding;
  } else {
    return binding;
  }
}

static PyObject *
PyNamemapper_valueFromSearchList(PyObject *searchList, 
				 char *nameChunks[], 
				 int numChunks, 
				 int executeCallables)
{
  PyObject *nameSpace;
  PyObject *theValue;
  int i;
  int listLen;

  listLen = PyList_Size(searchList);

  for (i=0; i < listLen; i++){
    nameSpace = PyList_GetItem(searchList, i);
    theValue = PyNamemapper_valueForName(nameSpace, nameChunks, 
					 numChunks, executeCallables);
    if (theValue) {		/* it might be NULL */
      PyErr_Clear();		/* clear possible NotFound errors */
      return theValue;
    }
  }
  return NULL;
}

/* *************************************************************************** */
/* Now the wrapper functions to export into the Python module */
/* *************************************************************************** */

static PyObject *
namemapper_valueForKey(PyObject *self, PyObject *args)
{
  PyObject *obj;
  char *key;

  if (!PyArg_ParseTuple(args, "Os", &obj, &key)) {
    return NULL;
  }

  return PyNamemapper_valueForKey(obj, key);
}

static PyObject *
namemapper_valueForName(PyObject *self, PyObject *args, PyObject *keywds)
{

  PyObject *obj;
  char *name;
  int executeCallables = 0;

  static char *copyOfName = NULL;
  static int bufSize = 0;
  static int newBufSize = 0;

  const char *dot = ".";
  char *nameChunks[MAXCHUNKS];
  int numChunks = 1;
  char *nextChunk;

  static char *kwlist[] = {"obj", "name", "executeCallables", NULL};

  if (!PyArg_ParseTupleAndKeywords(args, keywds, "Os|i", kwlist,  &obj, &name, &executeCallables)) {
    return NULL;
  }

  newBufSize = strlen(name) + 1; /* +1 for \0 terminator */
  if (newBufSize > bufSize) {
    bufSize = newBufSize;
    if (copyOfName) {
      copyOfName = realloc(copyOfName, bufSize);
    } else {
      copyOfName = malloc(bufSize);
    }
  }

  copyOfName = strcpy(copyOfName, name);
  nameChunks[0] = strtok(copyOfName, dot);
  while ((nextChunk = strtok(NULL, dot)) != NULL) {
    nameChunks[numChunks++] = nextChunk;
  }
  return PyNamemapper_valueForName(obj, nameChunks, numChunks, executeCallables);
}


static PyObject *
namemapper_valueFromSearchList(PyObject *self, PyObject *args, PyObject *keywds)
{

  PyObject *searchList;
  const char *name;
  int executeCallables = 0;

  static char *copyOfName = NULL;
  static int bufSize = 0;
  static int newBufSize = 0;

  const char *dot = ".";
  char *nameChunks[MAXCHUNKS];
  int numChunks = 1;
  char *nextChunk;

  static char *kwlist[] = {"searchList", "name", "executeCallables", NULL};

  if (!PyArg_ParseTupleAndKeywords(args, keywds, "Os|i", kwlist,  &searchList, &name, 
				   &executeCallables)) {
    return NULL;
  }

  newBufSize = strlen(name) + 1; /* +1 for \0 terminator */
  if (newBufSize > bufSize) {
    bufSize = newBufSize;
    if (copyOfName) {
      copyOfName = realloc(copyOfName, bufSize);
    } else {
      copyOfName = malloc(bufSize);
    }
  }
  copyOfName = strcpy(copyOfName, name);

  nameChunks[0] = strtok(copyOfName, dot);
  while ((nextChunk = strtok(NULL, dot)) != NULL) {
    nameChunks[numChunks++] = nextChunk;
  }
  return PyNamemapper_valueFromSearchList(searchList, nameChunks, numChunks, executeCallables);
}

/* *************************************************************************** */
/* Method registration table: name-string -> function-pointer */

static struct PyMethodDef namemapper_methods[] = {
  {"valueForKey", namemapper_valueForKey,  1},
  {"valueForName", (PyCFunction)namemapper_valueForName,  METH_VARARGS|METH_KEYWORDS},
  {"valueFromSearchList", (PyCFunction)namemapper_valueFromSearchList,  METH_VARARGS|METH_KEYWORDS},
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
    Py_FatalError("can't initialize module _namemapper");
}


