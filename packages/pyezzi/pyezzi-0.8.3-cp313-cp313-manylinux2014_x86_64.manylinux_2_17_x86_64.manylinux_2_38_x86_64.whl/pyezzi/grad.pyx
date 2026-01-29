cimport numpy as cnp
cimport cython
from libc.math cimport sqrt
from .common cimport OUTSIDE, INSIDE

import numpy as np


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
def gradient_flat(
    double[:] data,
    unsigned int[:] neighbours,
    double[:] spacing,
    int ndim,
) -> np.typing.NDArray:

    cdef Py_ssize_t c, cc
    cdef unsigned int left_idx, right_idx
    cdef double left_value, right_value
    cdef double v, norm, norm2

    cdef cnp.ndarray[double, ndim=1] res = np.empty(len(data) * ndim, dtype=np.float64)

    for c in range(len(data)):
        norm2 = 0
        for cc in range(ndim):
            right_idx = neighbours[c * ndim * 2 + cc * 2]
            left_idx = neighbours[c * ndim * 2 + cc * 2 + 1]

            if left_idx == INSIDE:
                left_value = 0
            elif left_idx == OUTSIDE:
                left_value = 1
            else:
                left_value = data[left_idx]

            if right_idx == INSIDE:
                right_value = 0
            elif right_idx == OUTSIDE:
                right_value = 1
            else:
                right_value = data[right_idx]

            v = (right_value - left_value) / spacing[cc]
            norm2 += v ** 2
            res[c * ndim + cc] = v

        norm = sqrt(norm2)

        for cc in range(ndim):
            res[c * ndim + cc] /= norm

    return res
