from __future__ import annotations

from typing import TYPE_CHECKING, cast

import hypothesis
import hypothesis.strategies as st
import numpy as np
import pytest

from embcol.problem._constraints import Constraint

if TYPE_CHECKING:
    from typing import Literal

    from hypothesis.strategies import DrawFn
    from numpy import float64, floating

    from embcol.typing import Array1D, Array2D, Array3D


@st.composite
def _constraints(  # noqa: C901
    draw: DrawFn,
    n_outputs: int | None = None,
    lower_bound: float | None = None,
    upper_bound: float | None = None,
) -> Constraint:
    if n_outputs is None:
        n_outputs = draw(st.integers(min_value=0, max_value=9))
    elif n_outputs < 0:
        pytest.fail("'n_outputs' must be >= 0")

    def function(params: Array1D[floating]) -> Array1D[float64]:
        if len(params) <= n_outputs:
            return cast("Array1D[floating]", params[:n_outputs]).astype(np.float64)
        out = np.zeros(n_outputs)
        out[:len(params)] = params
        return out

    def jacobian(params: Array1D[floating]) -> Array2D[float64]:
        return cast("Array2D[float64]", np.eye(n_outputs, len(params)))

    def hessian(params: Array1D[floating]) -> Array3D[float64]:
        return np.zeros((n_outputs, len(params), len(params)))

    if lower_bound is None:
        lower_bound = draw(st.floats(max_value=float("inf"), exclude_max=True))
    elif np.isposinf(lower_bound):
        pytest.fail("'lower_bound' must not be +inf")
    elif np.isnan(lower_bound):
        pytest.fail("'lower_bound' must not be nan")

    if upper_bound is None:
        upper_bound = draw(st.floats(min_value=lower_bound, exclude_min=True))
    elif np.isneginf(upper_bound):
        pytest.fail("'upper_bound' must not be -inf")
    elif np.isnan(upper_bound):
        pytest.fail("'upper_bound' must not be nan")

    return Constraint(
        function,
        jacobian,
        hessian,
        n_outputs,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
    )


class TestConstraint:

    @pytest.mark.parametrize(
        ("n_outputs", "lower_bound", "upper_bound", "template"),
        [
            pytest.param(
                1,
                -float("inf"),
                float("inf"),
                (
                    "Constraint(\n"
                    "    {!r},\n"
                    "    {!r},\n"
                    "    {!r},\n"
                    "    1,\n"
                    "    lower_bound=-inf,\n"
                    "    upper_bound=inf,\n"
                    ")"
                ),
                id="1--inf-inf",
            ),
            pytest.param(
                2,
                -1.0,
                1.0,
                (
                    "Constraint(\n"
                    "    {!r},\n"
                    "    {!r},\n"
                    "    {!r},\n"
                    "    2,\n"
                    "    lower_bound=-1,\n"
                    "    upper_bound=1,\n"
                    ")"
                ),
                id="2--1.0-1.0",
            ),
        ],
    )
    def test_repr(
        self,
        n_outputs: int,
        lower_bound: float,
        upper_bound: float,
        template: str,
    ) -> None:
        def function(_: Array1D[floating]) -> Array1D[float64]:
            return np.zeros(n_outputs)

        def jacobian(params: Array1D[floating]) -> Array2D[float64]:
            return np.zeros((n_outputs, len(params)))

        def hessian(params: Array1D[floating]) -> Array3D[float64]:
            return np.zeros((n_outputs, len(params), len(params)))

        constraint = Constraint(
            function,
            jacobian,
            hessian,
            n_outputs,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
        )

        actual = repr(constraint)
        expected = template.format(function, jacobian, hessian)
        assert actual == expected

    @hypothesis.given(constraint=_constraints())
    def test_eq(self, constraint: Constraint) -> None:
        # recreate from attributes to prevent numerical error
        objs = [
            Constraint(
                constraint.function,
                constraint.jacobian,
                constraint.hessian,
                constraint.n_outputs,
                lower_bound=constraint.lower_bound,
                upper_bound=constraint.upper_bound,
            )
            for _ in range(2)
        ]
        assert objs[0] == objs[1]

    @hypothesis.given(constraint=_constraints())
    def test_hash(self, constraint: Constraint) -> None:
        hash(constraint)

    class TestViolation:

        @hypothesis.given(
            constraint=_constraints(n_outputs=1),
            value=st.floats(min_value=-1e+15, max_value=1e+15),
        )
        def test_both_bounded(self, constraint: Constraint, value: float) -> None:
            actual = constraint.violation([value])
            expected = (
                np.array([constraint.lower_bound-value])
                if value < constraint.lower_bound else
                np.array([value-constraint.upper_bound])
                if constraint.upper_bound < value else
                np.array([0.0])
            )
            assert actual == pytest.approx(expected, rel=1e-6, abs=1e-6)

        @hypothesis.given(
            constraint=_constraints(n_outputs=1, upper_bound=float("inf")),
            value=st.floats(min_value=-1e+15, max_value=1e+15),
        )
        def test_lower_bounded(self, constraint: Constraint, value: float) -> None:
            actual = constraint.violation([value])
            expected = (
                np.array([constraint.lower_bound-value])
                if value < constraint.lower_bound else
                np.array([0.0])
            )
            assert actual == pytest.approx(expected, rel=1e-6, abs=1e-6)

        @hypothesis.given(
            constraint=_constraints(n_outputs=1, lower_bound=-float("inf")),
            value=st.floats(min_value=-1e+15, max_value=1e+15),
        )
        def test_upper_bounded(self, constraint: Constraint, value: float) -> None:
            actual = constraint.violation([value])
            expected = (
                np.array([value-constraint.upper_bound])
                if constraint.upper_bound < value else
                np.array([0.0])
            )
            assert actual == pytest.approx(expected, rel=1e-6, abs=1e-6)

        @hypothesis.given(
            constraint=_constraints(
                n_outputs=1,
                lower_bound=-float("inf"),
                upper_bound=float("inf"),
            ),
            value=st.floats(min_value=-1e+15, max_value=1e+15),
        )
        def test_neither_bounded(self, constraint: Constraint, value: float) -> None:
            actual = constraint.violation([value])
            expected = np.array([0.0])
            assert actual == pytest.approx(expected, rel=1e-6, abs=1e-6)

    @hypothesis.given(
        constraint=_constraints(n_outputs=1),
        feasible=(st.just("nonnegative") | st.just("nonpositive")),
        value=st.floats(min_value=-1e+15, max_value=1e+15),
    )
    def test_transform(
        self,
        constraint: Constraint,
        feasible: Literal["nonnegative", "nonpositive"],
        value: float,
    ) -> None:
        violation = constraint.violation([value])[0]
        nonzero_transformed_violations = [
            v
            for c in constraint.transform(feasible)
            if (v := c.violation([value])[0])
        ]

        if violation:
            assert len(nonzero_transformed_violations) == 1
            assert nonzero_transformed_violations[0] == pytest.approx(violation, rel=1e-6, abs=1e-6)
        else:
            assert not nonzero_transformed_violations
