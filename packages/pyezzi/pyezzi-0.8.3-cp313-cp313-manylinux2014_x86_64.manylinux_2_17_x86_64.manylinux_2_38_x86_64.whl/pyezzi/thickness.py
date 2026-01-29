import logging
from dataclasses import dataclass
from typing import Collection

import numpy as np

from . import (  # type:ignore[attr-defined]
    flatten,
    laplace,
    yezzi,
)
from .grad import gradient_flat  # type:ignore
from .misc import get_2d_domain, keep_biggest_cc, timeit


@dataclass
class Domain:
    """
    This class defines the *domain*, i.e., the regular grid defining the entity
    which thickness we want to measure.

    # Implementation details

    For performance, `pyezzi` works on a 1D ("flat") representation of the domain.
    This class handles going from a "full" (2D or 3D) to a "flat" (1D) representation
    of the domain.

    >>> endo, epi = get_2d_domain()
    >>> epi.astype(np.uint8)
    array([[0, 1, 1, 1, 1, 1, 0],
           [1, 1, 1, 1, 1, 1, 1],
           [1, 1, 1, 1, 1, 1, 1],
           [1, 1, 1, 1, 1, 1, 1],
           [1, 1, 1, 1, 1, 1, 1],
           [1, 1, 1, 1, 1, 1, 1],
           [0, 1, 1, 1, 1, 1, 0]], dtype=uint8)
    >>> endo.astype(np.uint8)
    array([[0, 0, 0, 0, 0, 0, 0],
           [0, 1, 1, 1, 0, 0, 0],
           [0, 1, 1, 1, 0, 0, 0],
           [0, 1, 1, 1, 0, 0, 0],
           [0, 0, 0, 0, 0, 0, 0],
           [0, 0, 0, 0, 0, 0, 0],
           [0, 0, 0, 0, 0, 0, 0]], dtype=uint8)

    >>> domain = Domain(endo, epi, [1, 1])
    >>> domain.wall.astype(np.uint8)
    array([[0, 1, 1, 1, 1, 1, 0],
           [1, 0, 0, 0, 1, 1, 1],
           [1, 0, 0, 0, 1, 1, 1],
           [1, 0, 0, 0, 1, 1, 1],
           [1, 1, 1, 1, 1, 1, 1],
           [1, 1, 1, 1, 1, 1, 1],
           [0, 1, 1, 1, 1, 1, 0]], dtype=uint8)

    >>> bool(domain.n == domain.wall.sum())
    True

    >>> domain.restore_flat(np.arange(1, domain.n + 1).astype(np.float64))
    array([[ 0.,  1.,  2.,  3.,  4.,  5.,  0.],
           [ 6.,  0.,  0.,  0.,  7.,  8.,  9.],
           [10.,  0.,  0.,  0., 11., 12., 13.],
           [14.,  0.,  0.,  0., 15., 16., 17.],
           [18., 19., 20., 21., 22., 23., 24.],
           [25., 26., 27., 28., 29., 30., 31.],
           [ 0., 32., 33., 34., 35., 36.,  0.]])

    """

    endo: np.typing.NDArray[np.bool]
    r"""
    2D or 3D boolean mask representing the inner boundary of the domain: $\partial_0 R$

    All pixels (or voxels) "inside" must be set to `True`.
    """
    epi: np.typing.NDArray[np.bool]
    r"""
    2D or 3D boolean mask representing the outer boundary of the domain: $\partial_1 R$

    All pixels (or voxels) "inside" must be set to `True`, such that `endo` $\subset$ `epi`
    """
    spacing: Collection[float]
    """
    2 or 3 values representing the pixel or pixel (resp, voxel) spacing along the 3 axis of the domain.

    NB: anisotropic pixels (resp, voxels) are supported, but lead to very approximate results,
    consider resampling your domain to a uniform spacing beforehand.
    """

    weights: np.typing.NDArray[np.float64] | None = None
    r"""
    Float 2D or 3D array representing the "thickness weights", i.e. $f(x)$ in
    [the article](https://nicoco.fr/weighted-thickness/).

    Passing `None` is equivalent to passing an 3D array filled with `1`.
    """

    @property
    def ndim(self) -> int:
        return self.endo.ndim

    @property
    def wall(self) -> np.typing.NDArray[np.bool]:
        return self.endo ^ self.epi

    def __post_init__(self) -> None:
        self.epi = self.epi.astype(bool)
        self.endo = self.endo.astype(bool)

        if self.weights is not None:
            self.weights = self.weights.astype(np.float64)

        self.spacing = np.asarray(self.spacing, np.float64)

        self.__flatten = getattr(flatten, f"flatten_{self.ndim}d")
        self.__unflatten = getattr(flatten, f"unflatten_{self.ndim}d")

        self.indices, self.neighbours = self.__flatten(self.epi, self.endo)
        self.n = len(self.indices) // self.ndim
        """
        Number of elements in the domain.
        """

    def restore_flat(
        self,
        flat_values: np.typing.NDArray[np.float64],
        outside: float = 0,
        inside: float = 0,
    ) -> np.typing.NDArray[np.float64]:
        """
        Go back from a "flat" (1D) to a "full" (2D or 3D) representation of values

        :param flat_values: flat (1D) representation of the values on the domain
        :param outside: value to be set outside the outer boundary of the domain
        :param inside: value to be set inside the inner boundary of the domain
        :return: A 2D or 3D array where domain voxels are filled with `flat_values`
        """
        out = np.empty_like(self.endo, np.float64)
        out[self.endo] = inside
        out[~self.epi] = outside
        self.__unflatten(flat_values, self.indices, out)
        return out


class ThicknessSolver:
    """
    Main class implementing the computation of weighted tissue thickness.

    Refer to `compute_thickness` and `compute_thickness_cardiac` for
    functional interfaces.
    """

    DEFAULT_TOLERANCE = 1e-6
    """Default relative tolerance convergence criterion."""
    DEFAULT_MAX_ITER = 5000
    """Default maximum iterations before giving up reaching the tolerance criterion."""

    def __init__(self, domain: Domain):
        """
        :param domain: The domain over which the thickness should be computed
        """
        self.domain = domain
        self.flat_laplace: np.typing.NDArray[np.float64] | None = None
        """Flat (1D) representation of the output of the heat equation solving"""
        self.flat_l0: np.typing.NDArray[np.float64] | None = None
        """Flat (1D) representation of $L_0$"""
        self.flat_l1: np.typing.NDArray[np.float64] | None = None
        """Flat (1D) representation of $L_1$"""
        self.flat_thickness: np.typing.NDArray[np.float64] | None = None
        """Flat (1D) representation of the thickness $W(x)$"""

    @timeit
    def solve_laplacian(
        self, tol: float | None = None, max_iter: int | None = None
    ) -> None:
        r"""
        Solve the heat equation over the domain.

        $\Delta u = 0$ with $u(\partial_0 R) = 0$ and $u(\partial_1 R) = 1$

        This is then used to compute the "tangent vector field":
        $\overrightarrow{T} = \frac{\nabla u}{|| \nabla u ||}$

        :param tol: relative error convergence criterion
        :param max_iter: maximum iterations
        """
        log.info("Solving Laplacian...")
        laplace_flat, iterations, max_error = getattr(
            laplace, f"solve_{self.domain.ndim}d"
        )(
            self.domain.neighbours,
            self.DEFAULT_TOLERANCE if tol is None else tol,
            self.DEFAULT_MAX_ITER if max_iter is None else max_iter,
            self.domain.spacing,
        )
        self.flat_laplace = laplace_flat

        log.debug(f"Laplacian: {iterations} iterations, max_error = {max_error}")
        self._get_gradients()

    @timeit
    def _get_gradients(self) -> None:
        log.debug("Computing tangent vector field")
        self.flat_gradients = gradient_flat(
            self.flat_laplace,
            self.domain.neighbours,
            self.domain.spacing,
            self.domain.ndim,
        )

    @timeit
    def solve_thickness(
        self, tol: float | None = None, max_iter: int | None = None
    ) -> None:
        r"""
        Compute the thickness over the domain.

        $\nabla L_0 \cdot \overrightarrow{T} = 1$ with $L_0(\partial_0 R) = 0$

        $-\nabla L_1 \cdot \overrightarrow{T} = 1$ with $L_1(\partial_1 R) = 0$

        $W(x) = L_0(x) + L_1(x)$

        :param tol: relative error convergence criterion
        :param max_iter: maximum iterations
        """
        if self.flat_laplace is None:
            self.solve_laplacian()

        log.info("Computing L0 and L1...")

        if self.domain.weights is None:
            weights: np.typing.NDArray[np.float64] = np.full(
                self.domain.n, 1, dtype=np.float64
            )
        else:
            weights = self.domain.weights[self.domain.wall]

        l0_flat, l1_flat, iterations, max_error = getattr(
            yezzi, f"iterative_relaxation_{self.domain.ndim}d"
        )(
            self.domain.neighbours,
            self.flat_gradients,
            self.DEFAULT_TOLERANCE if tol is None else tol,
            self.DEFAULT_MAX_ITER if max_iter is None else max_iter,
            self.domain.spacing,
            weights,
        )
        log.debug(
            f"Thickness computation: {iterations} iterations, max_error = {max_error}"
        )

        self.flat_l0 = l0_flat
        self.flat_l1 = l1_flat
        self.flat_thickness = l0_flat + l1_flat

        if self.domain.weights is not None:
            # compensate for smaller values where weights < 1
            mean_spacing = np.mean(self.domain.spacing)  # type: ignore
            self.flat_thickness += mean_spacing - weights * mean_spacing

    @property
    def result(self) -> np.typing.NDArray[np.float64]:
        """
        2D or 3D representation of the thickness of the domain $W$

        >>> domain = Domain(*get_2d_domain(11), [1, 1])
        >>> domain.wall.astype(int)
        array([[0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0],
               [0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 0],
               [1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
               [1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
               [1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
               [1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
               [1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
               [1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1],
               [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
               [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
               [0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0]])
        >>> solver = ThicknessSolver(domain)
        >>> np.round(solver.result, 1)
        array([[nan, nan, 0.8, 1. , 1. , 1. , 1. , 1.5, 2. , nan, nan],
               [nan, 0.4, nan, nan, nan, nan, nan, 1.6, 2. , 2.2, nan],
               [0.8, nan, nan, nan, nan, nan, nan, nan, 2.3, 2.6, 2.9],
               [1. , nan, nan, nan, nan, nan, nan, nan, 2.8, 2.9, 3. ],
               [1. , nan, nan, nan, nan, nan, nan, nan, 3. , 3. , 3. ],
               [1. , nan, nan, nan, nan, nan, nan, nan, 3. , 3. , 3. ],
               [1. , nan, nan, nan, nan, nan, nan, nan, 3. , 3. , 3.1],
               [1.5, 1.6, nan, nan, nan, nan, nan, 3.1, 3.3, 3.3, 3.4],
               [2. , 2. , 2.3, 2.8, 3. , 3. , 3. , 3.3, 3.4, 3.5, 3.6],
               [nan, 2.2, 2.6, 2.9, 3. , 3. , 3. , 3.3, 3.5, 3.5, nan],
               [nan, nan, 2.9, 3. , 3. , 3. , 3.1, 3.4, 3.6, nan, nan]])

        """
        if self.flat_thickness is None:
            self.solve_thickness()
        assert self.flat_thickness is not None
        return self.domain.restore_flat(
            self.flat_thickness, outside=np.nan, inside=np.nan
        )

    @property
    def L0(self) -> np.typing.NDArray[np.float64]:
        r"""
        2D or 3D representation of distance $L_0$, from inner boundary $\partial_0 R$
        to a given voxel of the domain.
        """
        if self.flat_l0 is None:
            self.solve_thickness()
        assert self.flat_l0 is not None
        return self.domain.restore_flat(self.flat_l0)

    @property
    def L1(self) -> np.typing.NDArray[np.float64]:
        r"""
        2D or 3D representation of distance $L_1$, from outer boundary $\partial_1 R$
        to a given voxel of the domain.
        """
        if self.flat_l1 is None:
            self.solve_thickness()
        assert self.flat_l1 is not None
        return self.domain.restore_flat(self.flat_l1)

    @property
    def laplace_grid(self) -> np.typing.NDArray[np.float64]:
        """
        2D or 3D representation of $u$ (heat equation over the domain).

        >>> domain = Domain(*get_2d_domain(11), [1, 1])
        >>> domain.wall.astype(int)
        array([[0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0],
               [0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 0],
               [1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
               [1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
               [1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
               [1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
               [1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
               [1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1],
               [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
               [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
               [0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0]])
        >>> solver = ThicknessSolver(domain)
        >>> np.round(solver.laplace_grid, 1)
        array([[1. , 1. , 0.6, 0.5, 0.5, 0.5, 0.5, 0.7, 0.8, 1. , 1. ],
               [1. , 0.5, 0. , 0. , 0. , 0. , 0. , 0.3, 0.6, 0.8, 1. ],
               [0.6, 0. , 0. , 0. , 0. , 0. , 0. , 0. , 0.4, 0.7, 0.9],
               [0.5, 0. , 0. , 0. , 0. , 0. , 0. , 0. , 0.3, 0.6, 0.8],
               [0.5, 0. , 0. , 0. , 0. , 0. , 0. , 0. , 0.3, 0.6, 0.8],
               [0.5, 0. , 0. , 0. , 0. , 0. , 0. , 0. , 0.3, 0.6, 0.8],
               [0.5, 0. , 0. , 0. , 0. , 0. , 0. , 0. , 0.3, 0.6, 0.8],
               [0.7, 0.3, 0. , 0. , 0. , 0. , 0. , 0.2, 0.5, 0.7, 0.8],
               [0.8, 0.6, 0.4, 0.3, 0.3, 0.3, 0.3, 0.5, 0.6, 0.8, 0.9],
               [1. , 0.8, 0.7, 0.6, 0.6, 0.6, 0.6, 0.7, 0.8, 0.9, 1. ],
               [1. , 1. , 0.9, 0.8, 0.8, 0.8, 0.8, 0.8, 0.9, 1. , 1. ]])

        """
        if self.flat_laplace is None:
            self.solve_laplacian()
        assert self.flat_laplace is not None
        return self.domain.restore_flat(self.flat_laplace, outside=1)


@timeit
def compute_thickness(
    domain: Domain,
    laplace_tolerance: float = ThicknessSolver.DEFAULT_TOLERANCE,
    laplace_max_iter: int = ThicknessSolver.DEFAULT_MAX_ITER,
    yezzi_tolerance: float = ThicknessSolver.DEFAULT_TOLERANCE,
    yezzi_max_iter: int = ThicknessSolver.DEFAULT_MAX_ITER,
) -> np.typing.NDArray[np.float64]:
    """
    Returns wall thicknesses computed with Yezzi's method

    Easy-to-use, functional interface to the ThicknessSolver class.

    :param domain: The domain represented with the appropriate class.
    :param laplace_tolerance:float, optional
    Maximum error allowed for Laplacian resolution
    :param laplace_max_iter:int, optional
    Maximum iterations allowed for Laplacian resolution
    :param yezzi_tolerance:float, optional
    Maximum error allowed for thickness computation
    :param yezzi_max_iter:int, optional
    Maximum iterations allowed for thickness computation
    :return:np.ndarray
    3D array of floats, representing thickness at each wall point
    """

    solver = ThicknessSolver(domain)
    solver.solve_laplacian(laplace_tolerance, laplace_max_iter)
    solver.solve_thickness(yezzi_tolerance, yezzi_max_iter)
    return solver.result


def compute_thickness_cardiac(
    endo: np.typing.NDArray[np.bool],
    epi: np.typing.NDArray[np.bool],
    spacing: tuple[float, float, float] = (1, 1, 1),
    weights: np.typing.NDArray[np.float64] | None = None,
    laplace_tolerance: float = ThicknessSolver.DEFAULT_TOLERANCE,
    laplace_max_iter: int = ThicknessSolver.DEFAULT_MAX_ITER,
    yezzi_tolerance: float = ThicknessSolver.DEFAULT_TOLERANCE,
    yezzi_max_iter: int = ThicknessSolver.DEFAULT_MAX_ITER,
) -> np.typing.NDArray[np.float64]:
    r"""
    Similar to `compute_thickness` but fully functional, does not require
    instantiating a `Domain`.

    :param endo: The endocardial mask, representing $\partial_0 R$
    :param epi: The epicardial mask, representing $\partial_1 R$
    :param spacing: Spacing of the voxels in the domain. Should be homogeneous for
        better results
    :param weights: Thickness weights $f(x)$, cf [weighted tissue thickness](https://nicoco.fr/weighted-thickness/).
    :param laplace_tolerance:float, optional
    Maximum error allowed for Laplacian resolution
    :param laplace_max_iter:int, optional
    Maximum iterations allowed for Laplacian resolution
    :param yezzi_tolerance:float, optional
    Maximum error allowed for thickness computation
    :param yezzi_max_iter:int, optional
    Maximum iterations allowed for thickness computation
    :return:np.ndarray
    3D array of floats, representing thickness at each wall point
    """
    return compute_thickness(
        Domain(endo=keep_biggest_cc(endo), epi=epi, spacing=spacing, weights=weights),
        laplace_tolerance=laplace_tolerance,
        laplace_max_iter=laplace_max_iter,
        yezzi_tolerance=yezzi_tolerance,
        yezzi_max_iter=yezzi_max_iter,
    )


log = logging.getLogger(__name__)
