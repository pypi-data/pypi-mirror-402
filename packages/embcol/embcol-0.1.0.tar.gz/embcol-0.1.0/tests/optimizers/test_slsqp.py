from __future__ import annotations

import math
from typing import TYPE_CHECKING

import hypothesis
import hypothesis.strategies as st
import numpy as np
import pytest

from embcol.color._wrappers import oklch_to_oklab
from embcol.optimizers._slsqp import SLSQPLocalOptimizer
from embcol.problem._problem import Problem
from embcol.random import ParamsGenerator

if TYPE_CHECKING:
    from collections.abc import Callable

    from hypothesis.strategies import DrawFn
    from numpy import float64

    from embcol.typing import Array1D
    from tests._typing import MakeAssertionCallback


@st.composite
def _problems(draw: DrawFn) -> Problem:
    n_unfixed = draw(st.integers(min_value=1, max_value=9))

    n_fixed = draw(st.integers(min_value=max(0, 2-n_unfixed), max_value=9))
    n_samples = n_fixed + n_unfixed
    n_pairs = math.comb(n_samples, 2)

    dissimilarities = draw(
        st.lists(st.floats(min_value=0.0, max_value=2.0), min_size=n_pairs, max_size=n_pairs),
    )

    weights = (
        draw(
            st.lists(st.floats(min_value=0.0, max_value=2.0), min_size=n_pairs, max_size=n_pairs)
            .filter(any),
        )
        if draw(st.booleans()) else
        None
    )

    fixed = (
        {i: oklch_to_oklab([0.5, 0.01*(i+1), 0.0]).tolist() for i in range(n_fixed)}
        if n_fixed else
        None
    )

    min_lightness = draw(st.floats(min_value=0.0, max_value=1.0-1e-4))
    max_lightness = draw(st.floats(min_value=min_lightness+1e-4, max_value=1.0))

    hue_groups = [list(range(n_fixed+1))] if draw(st.booleans()) else []
    hue_diff_tol = draw(st.floats(min_value=1e-4, max_value=np.pi))

    return Problem(
        dissimilarities,
        weights=weights,
        fixed=fixed,
        min_lightness=min_lightness,
        max_lightness=max_lightness,
        hue_groups=hue_groups,
        hue_diff_tol=hue_diff_tol,
    )


def _null_callback(params: Array1D[float64], cost: float, state: dict[str, float]) -> None:
    pass


class TestSLSQPLocalOptimizer:

    @pytest.mark.parametrize(
        ("optimizer", "expected"),
        [
            pytest.param(
                SLSQPLocalOptimizer(Problem([1.0])),
                (
                    "SLSQPLocalOptimizer(\n"
                    "    Problem(\n"
                    "        [1],\n"
                    "        weights=[1],\n"
                    "        fixed={},\n"
                    "        min_lightness=0,\n"
                    "        max_lightness=1,\n"
                    "        hue_groups=[],\n"
                    "        hue_diff_tol=0.07,\n"
                    "    ),\n"
                    "    callback=[],\n"
                    ")"
                ),
                id="without_optional",
            ),
            pytest.param(
                SLSQPLocalOptimizer(Problem([1.0]), callback=[_null_callback]),
                (
                    "SLSQPLocalOptimizer(\n"
                    "    Problem(\n"
                    "        [1],\n"
                    "        weights=[1],\n"
                    "        fixed={},\n"
                    "        min_lightness=0,\n"
                    "        max_lightness=1,\n"
                    "        hue_groups=[],\n"
                    "        hue_diff_tol=0.07,\n"
                    "    ),\n"
                    f"    callback=[{_null_callback!r}],\n"
                    ")"
                ),
                id="with_optional",
            ),
        ],
    )
    def test_repr(self, optimizer: SLSQPLocalOptimizer, expected: str) -> None:
        assert repr(optimizer) == expected

    @pytest.mark.filterwarnings(
        "ignore:Values in x were outside bounds during a minimize step, clipping to bounds",
    )
    @hypothesis.given(problem=_problems())
    def test_optimize(
        self,
        problem: Problem,
        make_assertion_callback: MakeAssertionCallback,
        make_rng_seed: Callable[[], int | None],
        check_oklabs: Callable[[object, Problem], None],
    ) -> None:
        max_n_iters = 5

        optimizer = SLSQPLocalOptimizer(
            problem,
            callback=make_assertion_callback(problem, assert_cost_decreasing=False),
        )

        generator = ParamsGenerator(make_rng_seed())
        init_oklabs = problem.params_to_oklabs(generator.random(problem))

        oklabs, is_converged = optimizer.optimize(init_oklabs, max_n_iters=max_n_iters)
        check_oklabs(oklabs, problem)
        assert isinstance(is_converged, bool)
