from __future__ import annotations

from typing import TYPE_CHECKING

import hypothesis
import hypothesis.strategies as st
import numpy as np
import pytest

from embcol.problem._bounds import Bounds

if TYPE_CHECKING:
    from hypothesis.strategies import DrawFn


@st.composite
def _bounds(draw: DrawFn) -> Bounds:
    n_params = draw(st.integers(min_value=0, max_value=9))
    lower = draw(
        st.lists(
            st.floats(max_value=float("inf"), exclude_max=True),
            min_size=n_params,
            max_size=n_params,
        ),
    )
    upper = [draw(st.floats(min_value=lb, exclude_min=True)) for lb in lower]
    return Bounds(lower, upper)


class TestBounds:

    @pytest.mark.parametrize(
        ("bounds", "expected"),
        [
            pytest.param(Bounds([-1.0], [1.0]), "Bounds([-1], [1])", id="single_line"),
            pytest.param(
                Bounds(-np.arange(1.0, 11.0), np.arange(1.0, 11.0)),
                (
                    "Bounds(\n"
                    "    [-1, -2, -3, -4, -5, -6, -7, -8, -9, -10],\n"
                    "    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],\n"
                    ")"
                ),
                id="multiple_lines_without_omission",
            ),
            pytest.param(
                Bounds(-np.arange(1.0, 18.0), np.arange(1.0, 18.0)),
                (
                    "Bounds(\n"
                    "    [-1, -2, -3, -4, -5, -6, -7, -8, -9, -10, -11, -12, -13, -14, -15, ...],\n"
                    "    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17],\n"
                    ")"
                ),
                id="multiple_lines_with_omission",
            ),
        ],
    )
    def test_repr(self, bounds: Bounds, expected: str) -> None:
        assert repr(bounds) == expected

    @hypothesis.given(bounds=_bounds())
    def test_eq(self, bounds: Bounds) -> None:
        # recreate from attributes to prevent numerical error
        objs = [Bounds(bounds.lower, bounds.upper) for _ in range(2)]
        assert objs[0] == objs[1]

    @hypothesis.given(bounds=_bounds())
    def test_hash(self, bounds: Bounds) -> None:
        hash(bounds)

    @hypothesis.given(value=st.floats(allow_infinity=False, allow_nan=False))
    def test_violation(self, value: float) -> None:
        bounds = Bounds(
            [0.0, 0.0, -float("inf"), -float("inf")],
            [1.0, float("inf"), 1.0, float("inf")],
        )
        actual = bounds.violation([value]*4)
        expected = np.array(
            [
                -value if value < 0.0 else value-1.0 if 1.0 < value else 0.0,
                -value if value < 0.0 else 0.0,
                value-1.0 if 1.0 < value else 0.0,
                0.0,
            ],
        )
        assert actual == pytest.approx(expected, rel=1e-6, abs=1e-6)
