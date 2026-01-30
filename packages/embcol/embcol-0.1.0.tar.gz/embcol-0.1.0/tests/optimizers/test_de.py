from __future__ import annotations

import math
from typing import TYPE_CHECKING

import hypothesis
import hypothesis.strategies as st
import numpy as np
import pytest

from embcol.color._wrappers import oklch_to_oklab
from embcol.optimizers._de import DEGlobalOptimizer
from embcol.problem._problem import Problem

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Literal

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


class TestDEGlobalOptimizer:

    @pytest.mark.parametrize(
        ("optimizer", "expected"),
        [
            pytest.param(
                DEGlobalOptimizer(Problem([1.0])),
                (
                    "DEGlobalOptimizer(\n"
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
                    "    population_size=20,\n"
                    "    mutation='best/1',\n"
                    "    diff_weight=(0.1, 0.3),\n"
                    "    crossover_prob=0.05,\n"
                    "    cost_tol=1e-08,\n"
                    "    cost_std_tol=1e-08,\n"
                    "    rng=None,\n"
                    ")"
                ),
                id="without_optional",
            ),
            pytest.param(
                DEGlobalOptimizer(
                    Problem([1.0]),
                    callback=[_null_callback],
                    population_size=4,
                    mutation="rand/1",
                    diff_weight=(0.7, 0.9),
                    crossover_prob=0.9,
                    cost_tol=0.001,
                    cost_std_tol=0.001,
                    rng=0,
                ),
                (
                    "DEGlobalOptimizer(\n"
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
                    "    population_size=4,\n"
                    "    mutation='rand/1',\n"
                    "    diff_weight=(0.7, 0.9),\n"
                    "    crossover_prob=0.9,\n"
                    "    cost_tol=0.001,\n"
                    "    cost_std_tol=0.001,\n"
                    "    rng=0,\n"
                    ")"
                ),
                id="with_optional",
            ),
        ],
    )
    def test_repr(self, optimizer: DEGlobalOptimizer, expected: str) -> None:
        assert repr(optimizer) == expected

    @hypothesis.given(
        problem=_problems(),
        population_size=st.integers(min_value=4, max_value=100),
        mutation=st.sampled_from(["best/1", "rand/1"]),
        diff_weight=(
            st.floats(min_value=0.0, exclude_min=True, max_value=2.0)
            | (
                st.lists(
                    st.floats(min_value=0.0, exclude_min=True, max_value=2.0),
                    min_size=2,
                    max_size=2,
                )
                .map(lambda x: tuple(sorted(x)))
            )
        ),
        crossover_prob=st.floats(min_value=0.0, max_value=1.0),
    )
    def test_optimize(
        self,
        problem: Problem,
        population_size: int,
        mutation: Literal["best/1", "rand/1"],
        diff_weight: float | tuple[float, float],
        crossover_prob: float,
        make_assertion_callback: MakeAssertionCallback,
        make_rng_seed: Callable[[], int | None],
        check_oklabs: Callable[[object, Problem], None],
    ) -> None:
        max_n_iters = 5

        optimizer = DEGlobalOptimizer(
            problem,
            callback=make_assertion_callback(problem),
            population_size=population_size,
            mutation=mutation,
            diff_weight=diff_weight,
            crossover_prob=crossover_prob,
            rng=make_rng_seed(),
        )

        oklabs, is_converged = optimizer.optimize(max_n_iters=max_n_iters)
        check_oklabs(oklabs, problem)
        assert isinstance(is_converged, bool)

        oklabs, is_converged = optimizer.optimize(max_n_iters=max_n_iters, resume=True)
        check_oklabs(oklabs, problem)
        assert isinstance(is_converged, bool)
