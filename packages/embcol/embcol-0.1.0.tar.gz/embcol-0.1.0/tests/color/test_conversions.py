from __future__ import annotations

from typing import TYPE_CHECKING, cast

import hypothesis
import hypothesis.strategies as st
import numpy as np
import pytest

from embcol.color._conversions import (
    linear_srgb_to_oklab,
    linear_srgb_to_srgb,
    oklab_to_linear_srgb,
    oklch_chroma,
    oklch_hue,
    srgb_to_linear_srgb,
)

if TYPE_CHECKING:
    from hypothesis.strategies import SearchStrategy
    from numpy import bool_, float64

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


def _is_away_from_hue_branch_cut(oklab: Array1D[float64], tol: float) -> bool_:
    return (
        tol < cast("float64", oklch_chroma(oklab.reshape((1, 3)))[0])
        and (0.0 < cast("float64", oklab[1]) or tol < abs(cast("float64", oklab[2])))
    )


@pytest.mark.parametrize(
    ("srgbs", "expected"),
    [
        (np.array([[0.0, 0.0, 0.0]]), np.array([[0.0, 0.0, 0.0]])),
        (np.array([[1.0, 1.0, 1.0]]), np.array([[1.0, 1.0, 1.0]])),
        (np.array([[1.0, 0.0, 0.0]]), np.array([[1.0, 0.0, 0.0]])),
        (np.array([[0.0, 1.0, 0.0]]), np.array([[0.0, 1.0, 0.0]])),
        (np.array([[0.0, 0.0, 1.0]]), np.array([[0.0, 0.0, 1.0]])),
        (np.array([[-1.0, 0.0, 0.0]]), np.array([[-1.0, 0.0, 0.0]])),
        (np.array([[0.0, -1.0, 0.0]]), np.array([[0.0, -1.0, 0.0]])),
        (np.array([[0.0, 0.0, -1.0]]), np.array([[0.0, 0.0, -1.0]])),
    ],
)
def test_srgb_to_linear_srgb(srgbs: Array2D[float64], expected: Array2D[float64]) -> None:
    actual = srgb_to_linear_srgb(srgbs)
    assert actual == pytest.approx(expected, rel=1e-6, abs=1e-6)


@pytest.mark.parametrize(
    ("linear_srgbs", "expected"),
    [
        (np.array([[0.0, 0.0, 0.0]]), np.array([[0.0, 0.0, 0.0]])),
        (np.array([[1.0, 1.0, 1.0]]), np.array([[1.0, 1.0, 1.0]])),
        (np.array([[1.0, 0.0, 0.0]]), np.array([[1.0, 0.0, 0.0]])),
        (np.array([[0.0, 1.0, 0.0]]), np.array([[0.0, 1.0, 0.0]])),
        (np.array([[0.0, 0.0, 1.0]]), np.array([[0.0, 0.0, 1.0]])),
        (np.array([[-1.0, 0.0, 0.0]]), np.array([[-1.0, 0.0, 0.0]])),
        (np.array([[0.0, -1.0, 0.0]]), np.array([[0.0, -1.0, 0.0]])),
        (np.array([[0.0, 0.0, -1.0]]), np.array([[0.0, 0.0, -1.0]])),
    ],
)
def test_linear_srgb_to_srgb(linear_srgbs: Array2D[float64], expected: Array2D[float64]) -> None:
    actual = linear_srgb_to_srgb(linear_srgbs)
    assert actual == pytest.approx(expected, rel=1e-6, abs=1e-6)


@pytest.mark.parametrize(
    ("linear_srgbs", "expected"),
    [
        (np.array([[0.0, 0.0, 0.0]]), np.array([[0.0, 0.0, 0.0]])),
        (np.array([[1.0, 1.0, 1.0]]), np.array([[1.0, 0.0, 0.0]])),
        (np.array([[1.0, 0.0, 0.0]]), np.array([[0.627955, 0.224863, 0.125846]])),
        (np.array([[0.0, 1.0, 0.0]]), np.array([[0.866440, -0.233888, 0.179498]])),
        (np.array([[0.0, 0.0, 1.0]]), np.array([[0.452014, -0.032457, -0.311528]])),
        (np.array([[-1.0, 0.0, 0.0]]), np.array([[-0.627955, -0.224863, -0.125846]])),
        (np.array([[0.0, -1.0, 0.0]]), np.array([[-0.866440, 0.233888, -0.179498]])),
        (np.array([[0.0, 0.0, -1.0]]), np.array([[-0.452014, 0.032457, 0.311528]])),
    ],
)
def test_linear_srgb_to_oklab(linear_srgbs: Array2D[float64], expected: Array2D[float64]) -> None:
    actual = linear_srgb_to_oklab(linear_srgbs)
    assert actual == pytest.approx(expected, rel=1e-6, abs=1e-6)


class TestOklabToLinearSRGB:

    @pytest.mark.parametrize(
        ("oklabs", "expected"),
        [
            (np.array([[0.0, 0.0, 0.0]]), np.array([[0.0, 0.0, 0.0]])),
            (np.array([[1.0, 0.0, 0.0]]), np.array([[1.0, 1.0, 1.0]])),
            (np.array([[0.5, 0.2, 0]]), np.array([[0.455023, 0.001820, 0.113273]])),
            (np.array([[0.5, 0, 0.2]]), np.array([[0.273955, 0.093775, -0.057921]])),
            (np.array([[0.5, -0.2, 0]]), np.array([[-0.132377, 0.227432, 0.137348]])),
            (np.array([[0.5, 0, -0.2]]), np.array([[0.043439, 0.082097, 0.649336]])),
        ],
    )
    def test_example(self, oklabs: Array2D[float64], expected: Array2D[float64]) -> None:
        actual = oklab_to_linear_srgb(oklabs)
        assert actual == pytest.approx(expected, rel=1e-6, abs=1e-6)

    @hypothesis.given(oklabs=st.tuples(_oklabs()))
    def test_jacobian(
        self,
        oklabs: tuple[Array1D[float64], ...],
        approx_derivative: ApproxDerivative,
    ) -> None:
        _, actual = oklab_to_linear_srgb(
            cast("Array2D[float64]", np.array(oklabs)),
            return_jacobian=True,
        )
        expected = np.stack(
            [
                approx_derivative(
                    lambda x: oklab_to_linear_srgb(x.reshape((1, 3))).reshape(-1),
                    oklab,
                )
                .reshape((3, 3))
                for oklab in oklabs
            ],
            axis=0,
        )
        assert actual == pytest.approx(expected, rel=1e-6, abs=1e-6)

    @hypothesis.given(oklabs=st.tuples(_oklabs()))
    def test_hessian(
        self,
        oklabs: tuple[Array1D[float64], ...],
        approx_derivative: ApproxDerivative,
    ) -> None:
        _, actual = oklab_to_linear_srgb(
            cast("Array2D[float64]", np.array(oklabs)),
            return_hessian=True,
        )
        expected = np.stack(
            [
                approx_derivative(
                    lambda x: (
                        oklab_to_linear_srgb(x.reshape((1, 3)), return_jacobian=True)[1]
                        .reshape(-1)
                    ),
                    oklab,
                )
                .reshape((3, 3, 3))
                for oklab in oklabs
            ],
            axis=0,
        )
        assert actual == pytest.approx(expected, rel=1e-6, abs=1e-6)


@pytest.mark.parametrize(
    ("oklabs", "expected"),
    [
        (np.array([[0.0, 1.0, 0.0]]), np.array([1.0])),
        (np.array([[0.0, 0.0, 1.0]]), np.array([1.0])),
        (np.array([[0.0, -1.0, 0.0]]), np.array([1.0])),
        (np.array([[0.0, 0.0, -1.0]]), np.array([1.0])),
    ],
)
def test_oklch_chroma(oklabs: Array2D[float64], expected: Array1D[float64]) -> None:
    actual = oklch_chroma(oklabs)
    assert actual == pytest.approx(expected, rel=1e-6, abs=1e-6)


class TestOklchHue:

    @pytest.mark.parametrize(
        ("oklabs", "expected"),
        [
            (np.array([[0.0, 1.0, 0.0]]), np.array([0.0])),
            (np.array([[0.0, 0.0, 1.0]]), np.array([0.5*np.pi])),
            (np.array([[0.0, 0.0, -1.0]]), np.array([-0.5*np.pi])),
        ],
    )
    def test_example(self, oklabs: Array2D[float64], expected: Array1D[float64]) -> None:
        actual = oklch_hue(oklabs)
        assert actual == pytest.approx(expected, rel=1e-6, abs=1e-6)

    @hypothesis.given(
        oklabs=st.tuples(_oklabs().filter(lambda x: _is_away_from_hue_branch_cut(x, 1e-4))),
    )
    def test_jacobian(
        self,
        oklabs: tuple[Array1D[float64], ...],
        approx_derivative: ApproxDerivative,
    ) -> None:
        _, actual = oklch_hue(cast("Array2D[float64]", np.array(oklabs)), return_jacobian=True)
        expected = np.stack(
            [
                approx_derivative(lambda x: oklch_hue(x.reshape((1, 3))), oklab, max_dx=1e-4)
                .reshape(3)
                for oklab in oklabs
            ],
            axis=0,
        )
        assert actual == pytest.approx(expected, rel=1e-6, abs=1e-6)

    @hypothesis.given(
        oklabs=st.tuples(_oklabs().filter(lambda x: _is_away_from_hue_branch_cut(x, 1e-4))),
    )
    def test_hessian(
        self,
        oklabs: tuple[Array1D[float64], ...],
        approx_derivative: ApproxDerivative,
    ) -> None:
        _, actual = oklch_hue(cast("Array2D[float64]", np.array(oklabs)), return_hessian=True)
        expected = np.stack(
            [
                approx_derivative(
                    lambda x: oklch_hue(x.reshape((1, 3)), return_jacobian=True)[1].reshape(-1),
                    oklab,
                    max_dx=1e-4,
                    abs_tol=1e-5,
                )
                .reshape((3, 3))
                for oklab in oklabs
            ],
            axis=0,
        )
        assert actual == pytest.approx(expected, rel=1e-6, abs=1e-5)
