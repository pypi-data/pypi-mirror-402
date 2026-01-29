import numpy as np

from pyezzi.flatten import flatten_3d, unflatten_3d


def test_flatten(example_epi, example_wall):
    endo = example_wall ^ example_epi
    indices, neighbours = flatten_3d(example_epi, endo)
    assert indices.ndim == 1

    n = example_wall.sum()

    assert len(indices) == n * 3
    assert len(neighbours) == n * 6

    values_flat = np.arange(n).astype(float)

    values1 = np.zeros_like(example_wall, float)
    values1[example_wall] = values_flat

    values2 = np.zeros_like(example_wall, float)
    unflatten_3d(values_flat, indices, values2)

    assert np.all(values1 == values2)

    for c in range(0, n * 3, 3):
        i, j, k = indices[c : c + 3]
        assert values_flat[c // 3] == values2[i, j, k]
