import os

# Ensure reproducibility by disabling parallelism.
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OMP_THREAD_LIMIT", "1")
os.environ.setdefault("OMP_PLACES", "cores")
os.environ.setdefault("OMP_PROC_BIND", "true")

from pathlib import Path

import numpy as np
import SimpleITK as sitk
from pytest import fixture
from skimage.io import imread

from pyezzi import Domain, ThicknessSolver

test_dir = Path(__file__).parent
example_dir = test_dir.parent / "example"
data_dir = test_dir / "data"


def read_array(path: Path):
    return sitk.GetArrayFromImage(sitk.ReadImage(str(path)))


@fixture(scope="session")
def example_reference():
    return np.load(test_dir / "data" / "3d_results.npz")


@fixture(scope="session")
def example_epi():
    return imread(example_dir / "epi.tif").astype(bool)


@fixture(scope="session")
def example_wall():
    return imread(example_dir / "wall.tif").astype(bool)


@fixture(scope="session")
def example_solver(example_epi, example_wall):
    solver = ThicknessSolver(
        Domain(epi=example_epi, endo=example_wall ^ example_epi, spacing=(1, 1, 1))
    )
    solver.solve_laplacian(0, 5000)
    solver.solve_thickness(0, 5000)
    return solver


@fixture(scope="session")
def example_weights():
    return read_array(data_dir / "weights.mha")


@fixture(scope="session")
def thickness_weights():
    return read_array(data_dir / "thickness_weights.mha")


@fixture(scope="session")
def realistic_endo():
    return read_array(data_dir / "endo.mha")


@fixture(scope="session")
def realistic_epi():
    return read_array(data_dir / "epi.mha")


@fixture(scope="session")
def realistic_thickness():
    return read_array(data_dir / "thickness_basic.mha")
