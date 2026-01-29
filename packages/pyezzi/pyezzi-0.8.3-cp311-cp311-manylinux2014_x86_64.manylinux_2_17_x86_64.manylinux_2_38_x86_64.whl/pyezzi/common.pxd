cimport numpy as cnp

cdef enum:
    OUTSIDE = 4294967293
    INSIDE = 4294967294

cdef bint has_converged(double[:] errors, int n, double tolerance)
