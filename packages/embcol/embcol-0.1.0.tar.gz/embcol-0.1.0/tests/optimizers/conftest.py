from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

if TYPE_CHECKING:
    from collections.abc import Callable

    from numpy import float64

    from embcol.problem._problem import Problem
    from embcol.typing import Array1D
    from tests._typing import MakeAssertionCallback


@pytest.fixture(scope="session")
def make_assertion_callback() -> MakeAssertionCallback:
    return _AssertionCallback


@pytest.fixture(scope="session")
def check_oklabs() -> Callable[[object, Problem], None]:
    def inner(oklabs: object, problem: Problem) -> None:
        assert isinstance(oklabs, np.ndarray)
        assert oklabs.shape == (problem.n_samples, 3)
        for i, oklab in problem.fixed.items():
            assert oklabs[i, :] == pytest.approx(oklab, rel=1e-6, abs=1e-6)

    return inner


class _AssertionCallback:

    _problem: Problem
    _assert_cost_decreasing: bool
    _last_cost: float

    def __init__(self, problem: Problem, *, assert_cost_decreasing: bool = True) -> None:
        self._problem = problem
        self._assert_cost_decreasing = assert_cost_decreasing
        self._last_cost = float("inf")

    def __call__(self, params: Array1D[float64], cost: float, state: dict[str, float]) -> None:
        self._check_args(params, cost, state)
        self._last_cost = cost

    def _check_args(self, params: object, cost: object, state: object) -> None:
        assert isinstance(params, np.ndarray)
        assert params.shape == (self._problem.n_params,)

        assert isinstance(cost, float)
        if self._assert_cost_decreasing:
            assert cost <= self._last_cost

        assert isinstance(state, dict)
        for key, value in state.items():
            assert isinstance(key, str)
            assert isinstance(value, float)
