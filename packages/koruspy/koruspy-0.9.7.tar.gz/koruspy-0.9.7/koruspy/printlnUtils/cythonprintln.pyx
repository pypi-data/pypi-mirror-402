# koruspy.pyx
from libc.stdio cimport printf, stdout, fflush
import cython

from cpython.object cimport PyObject_Print
from cpython.float cimport PyFloat_Check, PyFloat_AsDouble
from cpython.long cimport PyLong_Check, PyLong_AsLongLong
from cpython.unicode cimport PyUnicode_Check, PyUnicode_AsUTF8
from cpython.tuple cimport PyTuple_GET_SIZE, PyTuple_GET_ITEM
from cpython.bool cimport PyBool_Check

@cython.boundscheck(False)
@cython.wraparound(False)
def println(*args):
    """Cython-accelerated print function"""
    cdef object arg
    cdef Py_ssize_t i 
    cdef Py_ssize_t n = PyTuple_GET_SIZE(args)
    
    for i in range(n):
        arg = <object>PyTuple_GET_ITEM(args, i)
        
        if PyBool_Check(arg):
            printf("%s\n", "True" if arg else "False")
        elif PyUnicode_Check(arg):
            printf("%s\n", PyUnicode_AsUTF8(arg))
        elif PyFloat_Check(arg):
            printf("%g\n", PyFloat_AsDouble(arg))
        elif PyLong_Check(arg):
            printf("%lld\n", PyLong_AsLongLong(arg))
        elif arg is None:
            printf("None\n")
        else:
            PyObject_Print(arg, stdout, 0)
            printf("\n")
    
    fflush(stdout)
