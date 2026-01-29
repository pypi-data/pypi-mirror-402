import logging
from argparse import ArgumentParser

import SimpleITK as sitk

from . import __version__
from .thickness import compute_thickness_cardiac


def main() -> None:
    logging.basicConfig(level=logging.DEBUG)

    parser = ArgumentParser(
        description="A command-line interface to compute weighted tissue thickness on medical images."
    )

    parser.add_argument(
        "ENDO",
        help="Path to the segmentation of the outer layer. "
        "In a cardiac context, this would be the ventricle blood pool, a.k.a. 'endocardial mask'.",
    )
    parser.add_argument(
        "EPI",
        help="Path to the segmentation of the outer layer. "
        "In a cardiac context, this would be the whole ventricle myocardium + its blood pool, "
        "a.k.a. 'epicardial mask'.",
    )
    parser.add_argument("OUTPUT")
    parser.add_argument(
        "--weights",
        "-w",
        help="Path to a float image representing the thickness weights.",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s version {__version__}"
    )
    args = parser.parse_args()

    print("Reading images")
    endo_sitk = sitk.ReadImage(args.ENDO)
    epi_sitk = sitk.ReadImage(args.EPI)
    if args.weights:
        weights = sitk.GetArrayFromImage(sitk.ReadImage(args.weights))
    else:
        weights = None

    endo = sitk.GetArrayFromImage(endo_sitk).astype(bool)
    epi = sitk.GetArrayFromImage(epi_sitk).astype(bool)

    thickness = compute_thickness_cardiac(
        endo,
        epi,
        endo_sitk.GetSpacing()[::-1],  # type:ignore
        weights,
    )

    thickness_sitk = sitk.GetImageFromArray(thickness)
    thickness_sitk.CopyInformation(endo_sitk)  # type:ignore

    print("Writing result")
    sitk.WriteImage(thickness_sitk, args.OUTPUT, True)


if __name__ == "__main__":
    main()
