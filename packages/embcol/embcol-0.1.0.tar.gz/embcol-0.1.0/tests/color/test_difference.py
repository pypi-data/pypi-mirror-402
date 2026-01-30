from __future__ import annotations

import itertools
from typing import TYPE_CHECKING, cast

import hypothesis
import hypothesis.strategies as st
import numpy as np
import pytest

from embcol.color._difference import pairwise_sq_color_diffs, sq_color_diffs

if TYPE_CHECKING:
    from hypothesis.strategies import SearchStrategy
    from numpy import float64

    from embcol.typing import Array1D, Array2D
    from tests._typing import ApproxDerivative


def _oklabs() -> SearchStrategy[Array1D[float64]]:
    return (
        st.tuples(
            st.floats(min_value=-0.1, max_value=1.1),
            st.floats(min_value=-0.24, max_value=0.28),
            st.floats(min_value=-0.32, max_value=0.20),
        )
        .map(lambda x: cast("Array1D[float64]", np.array(x)))
    )


class TestPairwiseSqColorDiffs:

    @hypothesis.given(oklabs=st.tuples(_oklabs(), _oklabs()))
    def test_value(self, oklabs: tuple[Array1D[float64], ...]) -> None:
        actual = pairwise_sq_color_diffs(cast("Array2D[float64]", np.array(oklabs)))
        expected = np.concat(
            [
                sq_color_diffs(
                    cast("Array2D[float64]", np.tile(oklabs[i], [len(oklabs)-i-1, 1])),
                    cast("Array2D[float64]", np.vstack(oklabs[i+1:])),
                )
                for i in range(len(oklabs)-1)
            ],
        )
        assert actual == pytest.approx(expected, rel=1e-6, abs=1e-6)

    @hypothesis.given(oklabs=st.tuples(_oklabs(), _oklabs()))
    def test_jacobian(
        self,
        oklabs: tuple[Array1D[float64], ...],
        approx_derivative: ApproxDerivative,
    ) -> None:
        _, actual = pairwise_sq_color_diffs(
            cast("Array2D[float64]", np.array(oklabs)),
            return_jacobian=True,
        )
        expected = np.stack(
            [
                approx_derivative(
                    lambda x: pairwise_sq_color_diffs(x.reshape((2, 3))),
                    cast("Array1D[float64]", np.concat((oklabs[i], oklabs[j]))),
                )
                .reshape((2, 3))
                for i, j in itertools.combinations(range(len(oklabs)), 2)
            ],
            axis=0,
        )
        assert actual == pytest.approx(expected, rel=1e-6, abs=1e-6)

    @hypothesis.given(oklabs=st.tuples(_oklabs(), _oklabs()))
    def test_hessian(
        self,
        oklabs: tuple[Array1D[float64], ...],
        approx_derivative: ApproxDerivative,
    ) -> None:
        _, actual = pairwise_sq_color_diffs(
            cast("Array2D[float64]", np.array(oklabs)),
            return_hessian=True,
        )
        expected = np.stack(
            [
                approx_derivative(
                    lambda x: (
                        pairwise_sq_color_diffs(x.reshape((2, 3)), return_jacobian=True)
                        [1]
                        .reshape(-1)
                    ),
                    cast("Array1D[float64]", np.concat((oklabs[i], oklabs[j]))),
                )
                .reshape((2, 3, 2, 3))
                for i, j in itertools.combinations(range(len(oklabs)), 2)
            ],
            axis=0,
        )
        assert actual == pytest.approx(expected, rel=1e-6, abs=1e-6)
