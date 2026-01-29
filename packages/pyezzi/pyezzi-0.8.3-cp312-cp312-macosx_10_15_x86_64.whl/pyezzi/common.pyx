cimport cython

import numpy as np


@cython.boundscheck(False)
@cython.wraparound(False)
cdef bint has_converged(double[:] errors, int n, double tolerance):
    cdef bint res = True
    cdef Py_ssize_t i
    for i in range(n):
        if errors[i] > tolerance:
            res = False
            break
    return res


# dirty fix to get rid of annoying warnings
np.seterr(divide="ignore", invalid="ignore")
