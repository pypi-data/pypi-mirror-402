"""

Implementation of [weighted tissue thickness](https://nicoco.fr/weighted-thickness/).

Homepage: [gitlab.inria.fr](https://gitlab.inria.fr/ncedilni/pyezzi)

## Quickstart

The higher level interface is in `compute_thickness_cardiac`.

>>> from pathlib import Path
>>> import numpy as np
>>> import SimpleITK as sitk

Load relevant data:

>>> data_dir = Path(__file__).parent.parent / "test" / "data"
>>> endo = sitk.ReadImage(data_dir / "endo.mha")
>>> epi = sitk.ReadImage(data_dir / "epi.mha")

We use numpy conventions for axis order, not ITK's, so spacing must be reversed.
NB: it is recommended to resample the masks to a homogeneous spacing anyway.

>>> result = compute_thickness_cardiac(
...     sitk.GetArrayViewFromImage(endo),
...     sitk.GetArrayViewFromImage(epi),
...     spacing=endo.GetSpacing()[::-1],
... )

Let's see what the average wall thickness is (voxels outside the wall are filled with
`NaN`):

>>> wall = sitk.GetArrayViewFromImage(endo) ^ sitk.GetArrayViewFromImage(epi)
>>> round(float(np.nanmean(result)), 1)
16.7

"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("pyezzi")
except PackageNotFoundError:
    __version__ = "DEV"

from .thickness import (
    Domain,
    ThicknessSolver,
    compute_thickness,
    compute_thickness_cardiac,
)

__all__ = (
    "Domain",
    "ThicknessSolver",
    "compute_thickness",
    "compute_thickness_cardiac",
    "__version__",
)
