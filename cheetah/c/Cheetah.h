/*
 * (c) 2009, R. Tyler Ballance <tyler@slide.com>
 */

#ifndef _CHEETAH_H_
#define _CHEETAH_H_

#include <Python.h>

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Python 2.3 compatibility
 */
#ifndef Py_RETURN_TRUE
#define Py_RETURN_TRUE Py_INCREF(Py_True);\
    return Py_True
#endif
#ifndef Py_RETURN_FALSE
#define Py_RETURN_FALSE Py_INCREF(Py_False);\
    return Py_False
#endif 
#ifndef Py_RETURN_NONE
#define Py_RETURN_NONE Py_INCREF(Py_None);\
    return Py_None
#endif


/*
 * Filter Module
 */
typedef struct {
    PyObject_HEAD
    /* type specific fields */
} PyFilter;

/*
 * End Filter Module 
 */

#ifdef __cplusplus
}
#endif

#endif
