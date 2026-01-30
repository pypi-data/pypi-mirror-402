from __future__ import annotations

from typing import TYPE_CHECKING, cast

import hypothesis
import hypothesis.strategies as st
import numpy as np
import pytest

from embcol.color._wrappers import (
    gamut_map,
    oklab_to_oklch,
    oklab_to_srgb,
    oklch_to_oklab,
    pairwise_color_diffs,
    srgb_to_oklab,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from hypothesis.strategies import SearchStrategy
    from numpy import float64

    from embcol.typing import Array1D


def _oklabs() -> SearchStrategy[Array1D[float64]]:
    return (
        st.tuples(
            st.floats(min_value=-0.1, max_value=1.1),
            st.floats(min_value=-0.24, max_value=0.28),
            st.floats(min_value=-0.32, max_value=0.20),
        )
        .map(lambda x: cast("Array1D[float64]", np.array(x)))
    )


class TestSRGBToOklab:

    @pytest.mark.parametrize(
        ("srgb", "expected"),
        [
            ([0.0, 0.0, 0.0], np.array([0.0, 0.0, 0.0])),
            ([1.0, 1.0, 1.0], np.array([1.0, 0.0, 0.0])),
            ([1.0, 0.0, 0.0], np.array([0.627955, 0.224863, 0.125846])),
            ([0.0, 1.0, 0.0], np.array([0.866440, -0.233888, 0.179498])),
            ([0.0, 0.0, 1.0], np.array([0.452014, -0.032457, -0.311528])),
            ([-1.0, 0.0, 0.0], np.array([-0.627955, -0.224863, -0.125846])),
            ([0.0, -1.0, 0.0], np.array([-0.866440, 0.233888, -0.179498])),
            ([0.0, 0.0, -1.0], np.array([-0.452014, 0.032457, 0.311528])),
        ],
    )
    def test_example(self, srgb: Sequence[float], expected: Array1D[float64]) -> None:
        actual = srgb_to_oklab(srgb)
        assert actual == pytest.approx(expected, rel=1e-6, abs=1e-6)

    def test_array_like_2d(self) -> None:
        actual = srgb_to_oklab([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]])
        expected = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
        assert actual == pytest.approx(expected, rel=1e-6, abs=1e-6)

    @pytest.mark.parametrize("copy", [False, True])
    def test_copy(self, *, copy: bool) -> None:
        before = cast("Array1D[float64]", np.array([1.0, 0.0, 0.0]))
        after = srgb_to_oklab(before, copy=copy)
        assert np.array_equal(before, after) is not copy


class TestOklabToSRGB:

    @pytest.mark.parametrize(
        ("oklab", "expected"),
        [
            ([0.0, 0.0, 0.0], np.array([0.0, 0.0, 0.0])),
            ([1.0, 0.0, 0.0], np.array([1.0, 1.0, 1.0])),
            ([0.5, 0.2, 0.0], np.array([0.704917, 0.023514, 0.370735])),
            ([0.5, 0.0, 0.2], np.array([0.560109, 0.338510, -0.266934])),
            ([0.5, -0.2, 0.0], np.array([-0.399299, 0.514212, 0.406330])),
            ([0.5, 0.0, -0.2], np.array([0.230562, 0.317296, 0.826282])),
        ],
    )
    def test_example(self, oklab: Sequence[float], expected: Array1D[float64]) -> None:
        actual = oklab_to_srgb(oklab)
        assert actual == pytest.approx(expected, rel=1e-6, abs=1e-6)

    def test_array_like_2d(self) -> None:
        actual = oklab_to_srgb([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
        expected = np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]])
        assert actual == pytest.approx(expected, rel=1e-6, abs=1e-6)

    @pytest.mark.parametrize("copy", [False, True])
    def test_copy(self, *, copy: bool) -> None:
        before = cast("Array1D[float64]", np.array([0.5, 0.2, 0.0]))
        after = oklab_to_srgb(before, copy=copy)
        assert np.array_equal(before, after) is not copy


class TestOklabToOklch:

    @pytest.mark.parametrize(
        ("oklab", "expected"),
        [
            ([0.0, 0.0, 0.0], np.array([0.0, 0.0, 0.0])),
            ([1.0, 0.0, 0.0], np.array([1.0, 0.0, 0.0])),
            ([0.5, 0.2, 0.0], np.array([0.5, 0.2, 0.0])),
            ([0.5, 0.0, 0.2], np.array([0.5, 0.2, 0.5*np.pi])),
            ([0.5, 0.0, -0.2], np.array([0.5, 0.2, -0.5*np.pi])),
        ],
    )
    def test_example(self, oklab: Sequence[float], expected: Array1D[float64]) -> None:
        actual = oklab_to_oklch(oklab)
        assert actual == pytest.approx(expected, rel=1e-6, abs=1e-6)

    def test_array_like_2d(self) -> None:
        actual = oklab_to_oklch([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
        expected = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
        assert actual == pytest.approx(expected, rel=1e-6, abs=1e-6)

    @pytest.mark.parametrize("copy", [False, True])
    def test_copy(self, copy: bool) -> None:
        before = cast("Array1D[float64]", np.array([0.5, 0.0, 0.2]))
        after = oklab_to_srgb(before, copy=copy)
        assert np.array_equal(before, after) is not copy


class TestOklchToOklab:

    @pytest.mark.parametrize(
        ("oklch", "expected"),
        [
            ([0.0, 0.0, 0.0], np.array([0.0, 0.0, 0.0])),
            ([1.0, 0.0, 0.0], np.array([1.0, 0.0, 0.0])),
            ([0.5, 0.2, 0.0], np.array([0.5, 0.2, 0.0])),
            ([0.5, 0.2, 0.5*np.pi], np.array([0.5, 0.0, 0.2])),
            ([0.5, 0.2, np.pi], np.array([0.5, -0.2, 0.0])),
            ([0.5, 0.2, -0.5*np.pi], np.array([0.5, 0.0, -0.2])),
        ],
    )
    def test_example(self, oklch: Sequence[float], expected: Array1D[float64]) -> None:
        actual = oklch_to_oklab(oklch)
        assert actual == pytest.approx(expected, rel=1e-6, abs=1e-6)

    def test_array_like_2d(self) -> None:
        actual = oklch_to_oklab([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
        expected = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
        assert actual == pytest.approx(expected, rel=1e-6, abs=1e-6)

    @pytest.mark.parametrize("copy", [False, True])
    def test_copy(self, copy: bool) -> None:
        before = cast("Array1D[float64]", np.array([0.5, 0.2, 0.5*np.pi]))
        after = oklch_to_oklab(before, copy=copy)
        assert np.array_equal(before, after) is not copy


class TestGamutMap:

    @pytest.mark.parametrize(
        ("oklab", "expected"),
        [
            ([0.5, 0.0, 0.0], np.array([0.5, 0.0, 0.0])),
            ([1.1, 0.1, 0.1], np.array([1.0, 0.0, 0.0])),
            ([-0.1, 0.1, 0.1], np.array([0.0, 0.0, 0.0])),
            ([0.7, 0.2, 0.1], np.array([0.683104, 0.184037, 0.091524])),
            ([0.7, -0.2, 0.1], np.array([0.709171, -0.168166, 0.095444])),
            ([0.7, -0.1, -0.2], np.array([0.699623, -0.076235, -0.152839])),
            ([0.3, 0.2, 0.1], np.array([0.313270, 0.112178, 0.062781])),
            ([0.3, -0.2, 0.1], np.array([0.308924, -0.076754, 0.049453])),
            ([0.3, -0.1, -0.2], np.array([0.308275, -0.028421, -0.088092])),
        ],
    )
    def test_example(self, oklab: Sequence[float], expected: Array1D[float64]) -> None:
        actual = gamut_map(oklab)
        assert actual == pytest.approx(expected, rel=1e-6, abs=1e-6)

    def test_array_like_2d(self) -> None:
        actual = gamut_map([[0.5, 0.0, 0.0], [1.1, 0.1, 0.1]])
        expected = np.array([[0.5, 0.0, 0.0], [1.0, 0.0, 0.0]])
        assert actual == pytest.approx(expected, rel=1e-6, abs=1e-6)

    @pytest.mark.parametrize("copy", [False, True])
    def test_copy(self, copy: bool) -> None:
        before = cast("Array1D[float64]", np.array([1.1, 0.1, 0.1]))
        after = gamut_map(before, copy=copy)
        assert np.array_equal(before, after) is not copy


class TestPairwiseColorDiffs:

    @pytest.mark.parametrize(
        ("oklabs", "expected"),
        [
            ([[1.0, 0.0, 0.0], [1.0, 0.0, 0.0]], np.array([0.0])),
            ([[0.0, 0.0, 0.0], [0.0, 0.3, 0.4]], np.array([0.5])),
            ([[0.0, 0.0, 0.0], [1.2, 0.0, 0.0], [1.2, 0.3, 0.4]], np.array([1.2, 1.3, 0.5])),
        ],
    )
    def test_example(self, oklabs: Sequence[Sequence[float64]], expected: Array1D[float64]) -> None:
        actual = pairwise_color_diffs(oklabs)
        assert actual == pytest.approx(expected, rel=1e-6, abs=1e-6)

    @hypothesis.given(oklabs=st.tuples(_oklabs(), _oklabs()))
    def test_squared(self, oklabs: tuple[Array1D[float64], ...]) -> None:
        actual = pairwise_color_diffs(oklabs, squared=True)
        expected = pairwise_color_diffs(oklabs) ** 2
        assert actual == pytest.approx(expected, rel=1e-6, abs=1e-6)
