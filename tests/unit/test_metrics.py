import numpy as np

from ml.evaluation.metrics import (
    mae,
    nmae,
    rmse,
)


def test_mae():
    result = mae(
        [1, 2, 3],
        [1, 4, 2],
    )

    assert result == 1.0


def test_rmse():
    result = rmse(
        [1, 2],
        [1, 4],
    )

    assert np.isclose(
        result,
        np.sqrt(2),
    )


def test_nmae():
    result = nmae(
        [10, 20],
        [12, 18],
    )

    assert np.isclose(
        result,
        2 / 15,
    )