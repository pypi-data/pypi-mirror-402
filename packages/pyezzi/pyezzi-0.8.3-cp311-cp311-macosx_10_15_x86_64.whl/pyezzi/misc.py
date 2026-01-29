import logging
from functools import wraps
from pathlib import Path
from time import monotonic
from typing import Any, Callable, TypeVar, cast

import numpy as np

try:
    from scipy.ndimage import label
except ImportError:
    label = None  # type:ignore

T = TypeVar("T", bound=Callable[..., Any])


def keep_biggest_cc(
    nda_image: np.typing.NDArray[np.bool],
) -> np.typing.NDArray[np.bool]:
    if label is None:
        log.warning("scipy is not installed")
        return nda_image
    labeled_img, n = label(nda_image)  # type:ignore
    sizes = [(labeled_img == i).sum() for i in range(1, labeled_img.max() + 1)]
    rankings = np.argsort(sizes)[::-1] + 1
    return cast(np.typing.NDArray[np.bool], labeled_img == rankings[0])


def timeit(func: T) -> T:
    @wraps(func)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        tik = monotonic()
        result = func(*args, **kwargs)
        log.debug("%s took %s seconds", func.__name__, monotonic() - tik)
        return result

    return cast(T, wrapped)


def save_array_as_image(array: np.typing.NDArray[np.generic], path: Path) -> None:
    import SimpleITK as sitk

    sitk.WriteImage(sitk.GetImageFromArray(array), str(path))


def get_2d_domain(
    size: int = 7, offset: int = 1
) -> tuple[np.typing.NDArray[np.bool], np.typing.NDArray[np.bool]]:
    from skimage.draw import disk

    shape = size, size
    rr, cc = disk((size // 2, size // 2), size // 2 + 1, shape=shape)  # type:ignore[no-untyped-call]
    epi = np.zeros(shape, dtype=bool)
    epi[rr, cc] = 1

    rr, cc = disk(  # type:ignore[no-untyped-call]
        (size // 2 - offset, size // 2 - offset), size // 2 - offset, shape=shape
    )
    endo = np.zeros(shape, dtype=bool)
    endo[rr, cc] = 1

    return endo, epi


log = logging.getLogger(__name__)
