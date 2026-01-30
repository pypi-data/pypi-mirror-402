from __future__ import annotations

import math
from typing import TYPE_CHECKING

import hypothesis
import hypothesis.strategies as st
import numpy as np

from embcol.color._wrappers import oklab_to_srgb, oklch_to_oklab
from embcol.problem._problem import Problem
from embcol.random import OklchGenerator, ParamsGenerator

if TYPE_CHECKING:
    from collections.abc import Callable

    from hypothesis.strategies import DrawFn


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


class TestOklchGenerator:

    @hypothesis.given(
        n=(st.integers(min_value=0, max_value=9) | st.none()),
        lightness_bounds=(
            st.lists(st.floats(min_value=0.0, max_value=1.0), min_size=2, max_size=2)
            .map(lambda x: tuple(sorted(x)))
        ),
        min_hue=st.floats(min_value=-np.pi, max_value=np.pi),
        hue_ptp=st.floats(min_value=0.0, max_value=2*np.pi),
    )
    def test_random(
        self,
        n: int | None,
        lightness_bounds: tuple[float, float],
        min_hue: float,
        hue_ptp: float,
        make_rng_seed: Callable[[], int | None],
    ) -> None:
        tol = 1e-6

        max_hue = min_hue + hue_ptp

        generator = OklchGenerator(rng=make_rng_seed())
        actual = generator.random(
            n=n,
            min_lightness=lightness_bounds[0],
            max_lightness=lightness_bounds[1],
            min_hue=min_hue,
            max_hue=max_hue,
        )

        if n is not None:
            assert actual.shape == (n, 3)
        else:
            assert actual.shape == (3,)

        assert (lightness_bounds[0] <= actual[..., 0]).all()
        assert (actual[..., 0] <= lightness_bounds[1]).all()

        actual_hue = np.where(actual[..., 2] < min_hue-tol, actual[..., 2]+2*np.pi, actual[..., 2])
        assert (min_hue-tol < actual_hue).all()
        assert (actual_hue < max_hue+tol).all()

        actual_srgb = oklab_to_srgb(oklch_to_oklab(actual))
        assert ((0.0 <= actual_srgb)&(actual_srgb <= 1.0)).all()


class TestParamsGenerator:

    @hypothesis.given(problem=_problems())
    def test_random(self, problem: Problem, make_rng_seed: Callable[[], int | None]) -> None:
        generator = ParamsGenerator(rng=make_rng_seed())
        actual = generator.random(problem)

        assert actual.shape == (problem.n_params,)
        assert not problem.bounds.violation(actual).any()

        for constraint in problem.constraints:
            assert not constraint.violation(actual).any()
