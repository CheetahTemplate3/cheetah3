/* *************************************************************************** */
#include "Python.h"             /* Python header files */
#include <string.h>
#include <stdio.h>
#include <stdlib.h>


static PyObject *NotFound;   /* locally-raised exception */

#define notFound(message) \
    { PyErr_SetString(NotFound, message); return NULL; }

#define MAXCHUNKS 25		/* max num of nameChunks for the arrays */

/* *************************************************************************** */
/* First the c versions of the functions */
/* *************************************************************************** */

static PyObject *
PyNamemapper_valueForKey(PyObject *obj, char *key)
{
  PyObject *theValue = NULL;
  const char *underscore = "_";
  char *underscoreKey = NULL;

  if (PyObject_HasAttrString(obj, key)) {
    return PyObject_GetAttrString(obj, key);
  } else if (PyMapping_Check(obj) && PyMapping_HasKeyString(obj, key)) {
    return  PyMapping_GetItemString(obj, key);
  } else {

    underscoreKey = malloc(strlen(key) + 2); /* 1 for \0 and 1 for '_' */
    strcpy(underscoreKey, underscore);
    strcat(underscoreKey, key);

    if (PyObject_HasAttrString(obj, underscoreKey)) {
      theValue = PyObject_GetAttrString(obj, underscoreKey);
      free(underscoreKey);
    } else {
      free(underscoreKey);
      notFound(key);
    }
    return theValue;
    /* @@ Do I need to: Py_INCREF(theValue); */
  }
  notFound(key);		/* we shouldn't have gotten here - so raise error */


}

static PyObject *
PyNamemapper_valueForName(PyObject *obj, char *nameChunks[], 
			  int numChunks, 
			  int executeCallables)
{
  char *firstKey;
  PyObject *theValue = NULL;

  firstKey = nameChunks[0];
  if (!(theValue = PyNamemapper_valueForKey(obj, firstKey))){
    return NULL;
  }
    
  if (executeCallables && PyCallable_Check(theValue) && (!PyInstance_Check(theValue)) 
      && (!PyClass_Check(theValue)) ) {
    theValue = PyObject_CallObject(theValue, NULL);
  }
  
  if (numChunks > 1) {
    theValue = PyNamemapper_valueForName(theValue, nameChunks+1, 
					 numChunks - 1, executeCallables);
  }
  return theValue;
}

static PyObject *
PyNamemapper_valueFromSearchList(PyObject *searchList, 
				 char *nameChunks[], 
				 int numChunks, 
				 int executeCallables)
{
  PyObject *nameSpace = NULL;
  PyObject *theValue = NULL;
  int i;
  int listLen;

  listLen = PyList_Size(searchList);

  for (i=0; i < listLen; i++){
    nameSpace = PyList_GetItem(searchList, i);
    theValue = PyNamemapper_valueForName(nameSpace, nameChunks, numChunks, executeCallables);

    if (theValue) {		/* it might be NULL */
      PyErr_Clear();		/* clear possible NotFound errors */
      return theValue;
    } else if (PyErr_Occurred() != NotFound) {
      return NULL;
    }
  }
  return NULL;	/* the first key wasn't found in any namespace -- NotFound is raised */
}




static int getNameChunks(char *nameChunks[], char *name) 
{
  char c;
  char *currChunk;
  int currChunkNum = 0;
  
  currChunk = name;
  while ((c = *name) != '\0'){
    if (c == '.') {
      *name ='\0';
      nameChunks[currChunkNum++] = currChunk;
      name++;
      currChunk = name;
    } else 
      name++;
  }
  if (name > currChunk) 
    nameChunks[currChunkNum++] = currChunk;
  return currChunkNum;
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

  char *nameCopy = NULL;
  char *pa = NULL;
  char c;
  char *nameChunks[MAXCHUNKS];
  int numChunks;

  PyObject *theValue;

  static char *kwlist[] = {"obj", "name", "executeCallables", NULL};

  if (!PyArg_ParseTupleAndKeywords(args, keywds, "Os|i", kwlist,  &obj, &name, &executeCallables)) {
    return NULL;
  }
  
  nameCopy = malloc(strlen(name) + 1);
  pa = nameCopy;
  while ((c = *name++)) {
    if (!isspace(c)) {
      *pa++ = c;
    }
  }
  *pa = '\0';
  numChunks = getNameChunks(nameChunks, nameCopy);

  theValue = PyNamemapper_valueForName(obj, nameChunks, numChunks, executeCallables);
  free(nameCopy);
  return theValue;
}

static PyObject *
namemapper_valueFromSearchList(PyObject *self, PyObject *args, PyObject *keywds)
{

  PyObject *searchList;
  char *name;
  int executeCallables = 0;

  char *nameCopy = NULL;
  char *pa = NULL;
  char c;
  char *nameChunks[MAXCHUNKS];
  int numChunks;

  PyObject *theValue;

  static char *kwlist[] = {"searchList", "name", "executeCallables", NULL};

  if (!PyArg_ParseTupleAndKeywords(args, keywds, "Os|i", kwlist,  &searchList, &name, 
				   &executeCallables)) {
    return NULL;
  }

  nameCopy = malloc(strlen(name) + 1);
  pa = nameCopy;
  while ((c = *name++)) {
    if (!isspace(c)) {
      *pa++ = c;
    }
  }
  *pa = '\0';
  numChunks = getNameChunks(nameChunks, nameCopy);

  theValue = PyNamemapper_valueFromSearchList(searchList, nameChunks, numChunks, executeCallables);
  if (theValue) {
    free(nameCopy);
    return theValue;
  } else {
    free(nameCopy);
    notFound(name);
  }
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
  NotFound = Py_BuildValue("s", "namemapper.NotFound");   /* export exception */
  PyDict_SetItemString(d, "NotFound", NotFound);       /* add more if need */
  
  /* check for errors */
  if (PyErr_Occurred())
    Py_FatalError("can't initialize module _namemapper");
}


