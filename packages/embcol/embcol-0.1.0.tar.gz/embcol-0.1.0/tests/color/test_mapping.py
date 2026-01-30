from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

from embcol.color._mapping import gamut_map

if TYPE_CHECKING:
    from numpy import floating

    from embcol.typing import Array2D


@pytest.mark.parametrize(
    ("oklabs", "expected"),
    [
        (np.array([[0.5, 0.0, 0.0]]), np.array([[0.5, 0.0, 0.0]])),
        (np.array([[1.1, 0.1, 0.1]]), np.array([[1.0, 0.0, 0.0]])),
        (np.array([[-0.1, 0.1, 0.1]]), np.array([[0.0, 0.0, 0.0]])),
        (np.array([[0.7, 0.2, 0.1]]), np.array([[0.683104, 0.184037, 0.091524]])),
        (np.array([[0.7, -0.2, 0.1]]), np.array([[0.709171, -0.168166, 0.095444]])),
        (np.array([[0.7, -0.1, -0.2]]), np.array([[0.699623, -0.076235, -0.152839]])),
        (np.array([[0.3, 0.2, 0.1]]), np.array([[0.313270, 0.112178, 0.062781]])),
        (np.array([[0.3, -0.2, 0.1]]), np.array([[0.308924, -0.076754, 0.049453]])),
        (np.array([[0.3, -0.1, -0.2]]), np.array([[0.308275, -0.028421, -0.088092]])),
    ],
)
def test_gamut_map(oklabs: Array2D[floating], expected: Array2D[floating]) -> None:
    actual = gamut_map(oklabs)
    assert actual == pytest.approx(expected, rel=1e-6, abs=1e-6)
