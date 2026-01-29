cimport numpy as np
cimport cython
from libc.math cimport fabs
from .common cimport OUTSIDE, INSIDE, has_converged

import numpy as np
from cython.parallel import prange


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
def solve_2d(
    unsigned int[:] neighbours,
    double tolerance,
    int max_iterations,
    double[:] spacing,
) -> tuple[np.typing.NDArray, int, double]:
    cdef int n_points = neighbours.shape[0] // 4

    cdef np.ndarray[double, ndim=1] result_flat = np.full(n_points, 0.5, dtype=np.float64)

    cdef Py_ssize_t i
    cdef int iteration = 0
    cdef double hi, hj, hi2, hj2, factor, value, prev_value, v0, v1, v2, v3, error
    cdef Py_ssize_t n0, n1, n2, n3

    hi = spacing[0]
    hj = spacing[1]
    hi2 = hi ** 2
    hj2 = hj ** 2

    factor = 1. / 4

    error = tolerance + 1
    while error > tolerance and iteration < max_iterations:
        iteration += 1
        error = 0.
        for i in range(n_points):
            # This is not DRY, but I did not manage to factorize this without quitting
            # "pure-C" mode
            n0 = neighbours[i * 4]
            n1 = neighbours[i * 4 + 1]
            n2 = neighbours[i * 4 + 2]
            n3 = neighbours[i * 4 + 3]

            if n0 == INSIDE:
                v0 = 0.
            elif n0 == OUTSIDE:
                v0 = 1.
            else:
                v0 = result_flat[n0]

            if n1 == INSIDE:
                v1 = 0.
            elif n1 == OUTSIDE:
                v1 = 1.
            else:
                v1 = result_flat[n1]

            if n2 == INSIDE:
                v2 = 0.
            elif n2 == OUTSIDE:
                v2 = 1.
            else:
                v2 = result_flat[n2]

            if n3 == INSIDE:
                v3 = 0.
            elif n3 == OUTSIDE:
                v3 = 1.
            else:
                v3 = result_flat[n3]

            value = ((v0 + v1) / hi2 +
                     (v2 + v3) / hj2) * factor
            prev_value = result_flat[i]
            error = max(error, fabs((prev_value - value) / (prev_value + 1e-10)))
            result_flat[i] = value

    return result_flat, iteration, error


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
def solve_3d(
    unsigned int[:] neighbours,
    double tolerance,
    int max_iterations,
    double[:] spacing,
) -> tuple[np.typing.NDArray, int, double]:
    cdef int n_points = neighbours.shape[0] // 6

    cdef np.ndarray[double, ndim=1] result_flat = np.full(n_points, 0.5, dtype=np.float64)
    cdef double[:] errors = np.empty(n_points, np.float64)

    cdef Py_ssize_t i
    cdef int iteration = 0
    cdef double hi, hj, hk, hi2, hj2, hk2, factor, value, prev_value, v0, v1, v2, v3, v4, v5
    cdef Py_ssize_t n0, n1, n2, n3, n4, n5

    cdef bint convergence = False

    hi = spacing[0]
    hj = spacing[1]
    hk = spacing[2]
    hi2 = hi ** 2
    hj2 = hj ** 2
    hk2 = hk ** 2

    factor = (hi2 * hj2 * hk2) / (2 * (hi2 * hj2 + hi2 * hk2 + hj2 * hk2))

    while not convergence and iteration < max_iterations:
        iteration += 1
        for i in prange(n_points, nogil=True):
            # This is not DRY, but I did not manage to factorize this without quitting
            # "pure-C" mode
            n0 = neighbours[i * 6]
            n1 = neighbours[i * 6 + 1]
            n2 = neighbours[i * 6 + 2]
            n3 = neighbours[i * 6 + 3]
            n4 = neighbours[i * 6 + 4]
            n5 = neighbours[i * 6 + 5]

            if n0 == INSIDE:
                v0 = 0.
            elif n0 == OUTSIDE:
                v0 = 1.
            else:
                v0 = result_flat[n0]

            if n1 == INSIDE:
                v1 = 0.
            elif n1 == OUTSIDE:
                v1 = 1.
            else:
                v1 = result_flat[n1]

            if n2 == INSIDE:
                v2 = 0.
            elif n2 == OUTSIDE:
                v2 = 1.
            else:
                v2 = result_flat[n2]

            if n3 == INSIDE:
                v3 = 0.
            elif n3 == OUTSIDE:
                v3 = 1.
            else:
                v3 = result_flat[n3]

            if n4 == INSIDE:
                v4 = 0.
            elif n4 == OUTSIDE:
                v4 = 1.
            else:
                v4 = result_flat[n4]

            if n5 == INSIDE:
                v5 = 0.
            elif n5 == OUTSIDE:
                v5 = 1.
            else:
                v5 = result_flat[n5]

            value = ((v0 + v1) / hi2 +
                     (v2 + v3) / hj2 +
                     (v4 + v5) / hk2) * factor
            prev_value = result_flat[i]
            errors[i] = fabs((prev_value - value) / (prev_value + 1e-10))
            result_flat[i] = value

        if iteration == 1:
            convergence = False
        else:
            convergence = has_converged(errors, n_points, tolerance)

    return result_flat, iteration, np.nanmax(errors)
