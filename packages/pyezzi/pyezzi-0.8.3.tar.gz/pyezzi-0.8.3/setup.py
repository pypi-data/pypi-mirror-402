# I did not manage to move everything to pyproject, because of the need
# to use np.get_include()
# It is apparently relatively standard, cf
# https://packaging.python.org/en/latest/guides/modernize-setup-py-project/#should-setup-py-be-deleted

from codecs import open
from pathlib import Path

import numpy as np
from Cython.Build import cythonize
from Cython.Distutils import build_ext
from setuptools import Extension, setup

here = Path(__file__).parent

extensions = cythonize(
    list(
        Extension(
            f"pyezzi.{p.stem}",
            [p.relative_to(here)],
            extra_compile_args=["-fopenmp", "-O3"],
            extra_link_args=["-fopenmp"],
            define_macros=[("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")],
        )
        for p in here.glob("pyezzi/*.pyx")
    ),
    compiler_directives={"language_level": "3"},
)

cmdclass = {"build_ext": build_ext}

setup(
    ext_modules=extensions,
    packages=["pyezzi"],
    cmdclass=cmdclass,
    include_dirs=[np.get_include()],
)
