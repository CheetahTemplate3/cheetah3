/* *************************************************************************** */
#include "Python.h"             /* Python header files */
#include <string.h>
#include <stdlib.h>


static PyObject *NotFound;   /* locally-raised exception */
static PyObject *TooManyPeriods;   /* locally-raised exception */

#define notFound(message) { PyErr_SetString(NotFound, message); return NULL; }
#define MAXCHUNKS 15		/* max num of nameChunks for the arrays */
#define TRUE 1
#define FALSE 0

/* *************************************************************************** */
/* First the c versions of the functions */
/* *************************************************************************** */


static int getNameChunks(char *nameChunks[], char *name, char *nameCopy) 
{
  char c;
  char *currChunk;
  int currChunkNum = 0;
  
  currChunk = nameCopy;
  while ('\0' != (c = *nameCopy)){
    if ('.' == c) {
      if (currChunkNum >= (MAXCHUNKS-2)) { /* avoid overflowing nameChunks[] */
	PyErr_SetString(TooManyPeriods, name); 
	return 0;
      }

      *nameCopy ='\0';
      nameChunks[currChunkNum++] = currChunk;
      nameCopy++;
      currChunk = nameCopy;
    } else 
      nameCopy++;
  }
  if (nameCopy > currChunk) {
    nameChunks[currChunkNum++] = currChunk;
  }
  return currChunkNum;
} /* end - getNameChunks */


static int 
hasKey(PyObject *obj, char *key)
{
  const char *underscore = "_";
  char *underscoreKey = NULL;

  if (PyObject_HasAttrString(obj, key)) {
    return TRUE;
  } else if (PyMapping_Check(obj) && PyMapping_HasKeyString(obj, key)) {
    return TRUE;
  } else {
    underscoreKey = malloc(strlen(key) + 2); /* 1 for \0 and 1 for '_' */
    strcpy(underscoreKey, underscore);
    strcat(underscoreKey, key);

    if (PyObject_HasAttrString(obj, underscoreKey)) {
      free(underscoreKey);
      return TRUE;
    } else {
      free(underscoreKey);
      return FALSE;
    }
  }
} /* end - hasKey */


static PyObject *
PyNamemapper_valueForKey(PyObject *obj, char *key)
{
  PyObject *theValue = NULL;
  const char *underscore = "_";
  char *underscoreKey = NULL;

  if (PyObject_HasAttrString(obj, key)) {
    theValue = PyObject_GetAttrString(obj, key);
  } else if (PyMapping_Check(obj) && PyMapping_HasKeyString(obj, key)) {
    theValue = PyMapping_GetItemString(obj, key);
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
  }
  return theValue;
} /* end - PyNamemapper_valueForKey */

static PyObject *
PyNamemapper_valueForName(PyObject *obj, char *nameChunks[], 
			  int numChunks, 
			  int executeCallables)
{
  int i;
  char *currentKey;
  PyObject *currentVal = NULL;
  PyObject *nextVal = NULL;
  const char *underscore = "_";
  char *underscoreKey = NULL;

  currentVal = obj;
  for (i=0; i < numChunks;i++) {
    currentKey = nameChunks[i];
    
    if (PyObject_HasAttrString(currentVal, currentKey)) {
      nextVal = PyObject_GetAttrString(currentVal, currentKey);
    } else if (PyMapping_Check(currentVal) && PyMapping_HasKeyString(currentVal, currentKey)) {
      nextVal = PyMapping_GetItemString(currentVal, currentKey);
    } else {
      
      underscoreKey = malloc(strlen(currentKey) + 2); /* 1 for \0 and 1 for '_' */
      strcpy(underscoreKey, underscore);
      strcat(underscoreKey, currentKey);
      
      if (PyObject_HasAttrString(currentVal, underscoreKey)) {
	nextVal = PyObject_GetAttrString(currentVal, underscoreKey);
	free(underscoreKey);
      } else {
	if (i>0) {
	  Py_DECREF(currentVal);
	}
	free(underscoreKey);
	notFound(currentKey);
      }
    }
    if (i>0) {
      Py_DECREF(currentVal);
    }
    if (executeCallables && PyCallable_Check(nextVal) && (!PyInstance_Check(nextVal)) 
	&& (!PyClass_Check(nextVal)) ) {
      if (!(currentVal = PyObject_CallObject(nextVal, NULL))){
	Py_DECREF(nextVal);
	return NULL;
      };
      Py_DECREF(nextVal);
    } else {
      currentVal = nextVal;
    }
  }

  return currentVal;
} /* end - PyNamemapper_valueForName */


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
  char *tmpPntr1 = NULL;
  char *tmpPntr2 = NULL;
  char *nameChunks[MAXCHUNKS];
  int numChunks;

  PyObject *theValue;

  static char *kwlist[] = {"obj", "name", "executeCallables", NULL};

  if (!PyArg_ParseTupleAndKeywords(args, keywds, "Os|i", kwlist,  &obj, &name, &executeCallables)) {
    return NULL;
  }
  
  nameCopy = malloc(strlen(name) + 1);
  tmpPntr1 = name; tmpPntr2 = nameCopy;
  while ((*tmpPntr2++ = *tmpPntr1++));

  numChunks = getNameChunks(nameChunks, name, nameCopy);
  if (PyErr_Occurred()) { 	/* there might have been TooManyPeriods */
    free(nameCopy);
    return NULL;
  }

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
  char *tmpPntr1 = NULL;
  char *tmpPntr2 = NULL;
  char *nameChunks[MAXCHUNKS];
  int numChunks;

  PyObject *nameSpace = NULL;
  PyObject *theValue = NULL;
  int i;
  int listLen;

  static char *kwlist[] = {"searchList", "name", "executeCallables", NULL};

  if (!PyArg_ParseTupleAndKeywords(args, keywds, "Os|i", kwlist,  &searchList, &name, 
				   &executeCallables)) {
    return NULL;
  }

  nameCopy = malloc(strlen(name) + 1);
  tmpPntr1 = name; tmpPntr2 = nameCopy;
  while ((*tmpPntr2++ = *tmpPntr1++));

  numChunks = getNameChunks(nameChunks, name, nameCopy);
  if (PyErr_Occurred()) { 	/* there might have been TooManyPeriods */
    free(nameCopy);
    return NULL;
  }

  listLen = PyList_Size(searchList);
  for (i=0; i < listLen; i++){
    nameSpace = PyList_GetItem(searchList, i);
    if ( hasKey(nameSpace, nameChunks[0]) ) {
      theValue = PyNamemapper_valueForName(nameSpace, nameChunks, numChunks, executeCallables);
      free(nameCopy);
      return theValue;
    } 
  }
  free(nameCopy);
  notFound(name);
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
  NotFound = PyErr_NewException("NameMapper.NotFound",NULL,NULL);
  TooManyPeriods = PyErr_NewException("NameMapper.TooManyPeriodsInName",NULL,NULL);
  PyDict_SetItemString(d, "NotFound", NotFound);
  PyDict_SetItemString(d, "TooManyPeriodsInName", TooManyPeriods);

  /* check for errors */
  if (PyErr_Occurred())
    Py_FatalError("Can't initialize module _namemapper");
}


