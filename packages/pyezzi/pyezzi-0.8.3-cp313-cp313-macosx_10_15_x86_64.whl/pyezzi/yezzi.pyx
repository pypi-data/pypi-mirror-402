cimport numpy as cnp
cimport cython
from libc.math cimport fabs
from .common cimport OUTSIDE, has_converged

import numpy as np
from cython.parallel import prange


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
def iterative_relaxation_2d(unsigned int[:] neighbours,
                            double[:] vectors,
                            double tolerance,
                            int max_iterations,
                            double[:] spacing,
                            double[:] weights):
    cdef double hi, hj
    hi, hj = spacing

    cdef size_t n_points = neighbours.shape[0] // 4

    cdef cnp.ndarray[double] abs_vectors = np.abs(vectors).astype(np.float64)
    cdef double[:] sum_abs_vectors = (
            abs_vectors[0::2] / hi
            + abs_vectors[1::2] / hj).astype(np.float64)

    cdef double neg_half_mean_spacing = -np.mean(spacing) * 0.5

    cdef cnp.ndarray[double] L0 = np.zeros(n_points, np.float64)
    cdef cnp.ndarray[double] L1 = np.zeros(n_points, np.float64)

    cdef size_t n0, n1, n2, n3

    cdef int iteration = 0

    cdef size_t n
    cdef double L0_i, L0_j, L1_i, L1_j, prev_L0, prev_L1
    cdef double L0_value, L1_value, sum_abs_vector

    cdef double error = tolerance + 1

    while error > tolerance and iteration < max_iterations:
        iteration += 1
        error = 0
        for n in range(n_points):
            n0 = neighbours[n * 4]
            n1 = neighbours[n * 4 + 1]
            n2 = neighbours[n * 4 + 2]
            n3 = neighbours[n * 4 + 3]

            if vectors[n * 2] > 0:
                L0_i = abs_vectors[n * 2] * (L0[n1] if n1 < OUTSIDE else neg_half_mean_spacing)
                L1_i = abs_vectors[n * 2] * (L1[n0] if n0 < OUTSIDE else neg_half_mean_spacing)
            else:
                L0_i = abs_vectors[n * 2] * (L0[n0] if n0 < OUTSIDE else neg_half_mean_spacing)
                L1_i = abs_vectors[n * 2] * (L1[n1] if n1 < OUTSIDE else neg_half_mean_spacing)

            if vectors[n * 2 + 1] > 0:
                L0_j = abs_vectors[n * 2 + 1] * (L0[n3] if n3 < OUTSIDE else neg_half_mean_spacing)
                L1_j = abs_vectors[n * 2 + 1] * (L1[n2] if n2 < OUTSIDE else neg_half_mean_spacing)
            else:
                L0_j = abs_vectors[n * 2 + 1] * (L0[n2] if n2 < OUTSIDE else neg_half_mean_spacing)
                L1_j = abs_vectors[n * 2 + 1] * (L1[n3] if n3 < OUTSIDE else neg_half_mean_spacing)

            sum_abs_vector = sum_abs_vectors[n]
            prev_L0 = L0[n]
            prev_L1 = L1[n]
            L0_value = ((L0_i / hi
                         + L0_j / hj
                         + weights[n])
                        / sum_abs_vector)
            L1_value = ((L1_i / hi
                         + L1_j / hj
                         + weights[n])
                        / sum_abs_vector)

            error = max(error, fabs((prev_L0 - L0_value) / (prev_L0 + 1e-10)))
            error = max(error, fabs((prev_L1 - L1_value) / (prev_L1 + 1e-10)))

            L0[n] = L0_value
            L1[n] = L1_value

    return L0, L1, iteration, error


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
def iterative_relaxation_3d(unsigned int[:] neighbours,
                            double[:] vectors,
                            double tolerance,
                            int max_iterations,
                            double[:] spacing,
                            double[:] weights):
    cdef double hi, hj, hk
    hi, hj, hk = spacing

    cdef size_t n_points = neighbours.shape[0] // 6

    cdef cnp.ndarray[double] abs_vectors = np.abs(vectors).astype(np.float64)
    cdef double[:] sum_abs_vectors = (
            abs_vectors[0::3] / hi
            + abs_vectors[1::3] / hj
            + abs_vectors[2::3] / hk).astype(np.float64)

    cdef size_t n_points2 = n_points * 2

    cdef double neg_half_mean_spacing = -np.mean(spacing) * 0.5

    cdef cnp.ndarray[double] L0 = np.zeros(n_points, np.float64)
    cdef cnp.ndarray[double] L1 = np.zeros(n_points, np.float64)

    cdef double[:] errors = np.zeros(n_points2, np.float64)

    cdef bint convergence = False

    cdef size_t n0, n1, n2, n3, n4, n5

    cdef int iteration = 0

    cdef size_t n, nn
    cdef double L0_i, L0_j, L0_k, L1_i, L1_j, L1_k, prev_L0, prev_L1
    cdef double L0_value, L1_value, sum_abs_vector

    while not convergence and iteration < max_iterations:
        iteration += 1
        for n in prange(n_points, nogil=True):
            n0 = neighbours[n * 6]
            n1 = neighbours[n * 6 + 1]
            n2 = neighbours[n * 6 + 2]
            n3 = neighbours[n * 6 + 3]
            n4 = neighbours[n * 6 + 4]
            n5 = neighbours[n * 6 + 5]

            if vectors[n * 3] > 0:
                L0_i = abs_vectors[n * 3] * (L0[n1] if n1 < OUTSIDE else neg_half_mean_spacing)
                L1_i = abs_vectors[n * 3] * (L1[n0] if n0 < OUTSIDE else neg_half_mean_spacing)
            else:
                L0_i = abs_vectors[n * 3] * (L0[n0] if n0 < OUTSIDE else neg_half_mean_spacing)
                L1_i = abs_vectors[n * 3] * (L1[n1] if n1 < OUTSIDE else neg_half_mean_spacing)

            if vectors[n * 3 + 1] > 0:
                L0_j = abs_vectors[n * 3 + 1] * (L0[n3] if n3 < OUTSIDE else neg_half_mean_spacing)
                L1_j = abs_vectors[n * 3 + 1] * (L1[n2] if n2 < OUTSIDE else neg_half_mean_spacing)
            else:
                L0_j = abs_vectors[n * 3 + 1] * (L0[n2] if n2 < OUTSIDE else neg_half_mean_spacing)
                L1_j = abs_vectors[n * 3 + 1] * (L1[n3] if n3 < OUTSIDE else neg_half_mean_spacing)

            if vectors[n * 3 + 2] > 0:
                L0_k = abs_vectors[n * 3 + 2] * (L0[n5] if n5 < OUTSIDE else neg_half_mean_spacing)
                L1_k = abs_vectors[n * 3 + 2] * (L1[n4] if n4 < OUTSIDE else neg_half_mean_spacing)
            else:
                L0_k = abs_vectors[n * 3 + 2] * (L0[n4] if n4 < OUTSIDE else neg_half_mean_spacing)
                L1_k = abs_vectors[n * 3 + 2] * (L1[n5] if n5 < OUTSIDE else neg_half_mean_spacing)

            sum_abs_vector = sum_abs_vectors[n]
            prev_L0 = L0[n]
            prev_L1 = L1[n]
            L0_value = ((L0_i / hi
                         + L0_j / hj
                         + L0_k / hk
                         + weights[n])
                        / sum_abs_vector)
            L1_value = ((L1_i / hi
                         + L1_j / hj
                         + L1_k / hk
                         + weights[n])
                        / sum_abs_vector)
            if prev_L0 == 0:
                errors[n] = 1
            else:
                errors[n] = fabs((prev_L0 - L0_value) / prev_L0)
            nn = n + n_points
            if prev_L1 == 0:
                errors[nn] = 1
            else:
                errors[nn] = fabs((prev_L1 - L1_value) / prev_L1)
            L0[n] = L0_value
            L1[n] = L1_value
        if iteration == 1:
            convergence = False
        else:
            convergence = has_converged(errors, n_points2, tolerance)

    return L0, L1, iteration, np.nanmax(errors)
