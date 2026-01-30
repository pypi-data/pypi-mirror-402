"""Random global optimizer."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

import numpy as np

from .._checking import check_number, check_number_set
from .._exception import expr
from .._typing_imports import override
from ..random import ParamsGenerator
from ._base import BaseGlobalOptimizer

if TYPE_CHECKING:
    from collections.abc import Sequence

    from numpy import float64

    from ..problem._problem import Problem
    from ..typing import Array1D, Callback, RNGLike

__all__ = ["RandomGlobalOptimizer"]


class RandomGlobalOptimizer(BaseGlobalOptimizer):
    """Random global optimizer.

    Search a global optimum by the random sampling.

    Parameters
    ----------
    problem : embcol.problem.Problem
        Optimization problem.
    callback : callable or sequence of callable, optional
        Function(s) called after each iteration. The signature of a function must be
        ``(params, cost, state) -> None``, where ``params`` is a one-dimensional array of parameters
        of type `numpy.ndarray`, ``cost`` is a cost value of type `float`, and ``state`` is a `dict`
        object of `str` to `float` detailing an optimization state.
    cost_tol : float, optional
        Convergence tolerance for the cost.
    rng : rng-like, optional
        Random number generator. If nothing is given, a generator is initialized
        nondeterministically.
    """

    _options: _Options

    _generator: ParamsGenerator
    _best_params: Array1D[float64]
    _best_cost: float

    def __init__(
        self,
        problem: Problem,
        callback: Callback | Sequence[Callback] = (),
        cost_tol: float = 1e-8,
        rng: RNGLike = None,
    ) -> None:
        super().__init__(problem, callback=callback)

        check_number_set(cost_tol, "real_numbers", target=expr("cost_tol"))
        check_number(cost_tol, lower_bound=0, allow_nan=False, target=expr("cost_tol"))
        cost_tol = float(cost_tol)

        generator = ParamsGenerator(rng=rng)

        self._options["cost_tol"] = cost_tol
        self._options["rng"] = rng

        self._generator = generator
        self._best_params = np.empty(problem.n_params)
        self._best_cost = float("inf")

    @override
    def _optimize(self, max_n_iters: int, *, resume: bool) -> tuple[Array1D[float64], bool]:
        if not resume:
            self._best_cost = float("inf")

        for _ in range(max_n_iters):
            params = self._generator.random(self._problem)

            cost = self._problem.cost(params)

            if cost < self._best_cost:
                self._best_params[:] = params
                self._best_cost = cost

            self._callback(self._best_params, self._best_cost, {})

            if self._best_cost < self._options["cost_tol"]:
                return self._best_params, True

        return self._best_params, False


class _Options(TypedDict):

    cost_tol: float
    rng: RNGLike
