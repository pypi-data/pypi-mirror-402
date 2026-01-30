"""SLSQP local optimizer."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict, cast

import scipy

from .._typing_imports import override
from ._base import BaseLocalOptimizer

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any, Literal

    from numpy import float64, floating

    from .._typing_imports import NotRequired, Unpack
    from ..typing import Array1D, Array2D

__all__ = ["SLSQPLocalOptimizer"]


class SLSQPLocalOptimizer(BaseLocalOptimizer):
    """SLSQP local optimizer.

    Search a local optimum by the sequential least squares programming (SLSQP).

    Parameters
    ----------
    problem : embcol.problem.Problem
        Optimization problem.
    callback : callable or sequence of callable, optional
        Function(s) called after each iteration. The signature of a function must be
        ``(params, cost, state) -> None``, where ``params`` is a one-dimensional array of parameters
        of type `numpy.ndarray`, ``cost`` is a cost value of type `float`, and ``state`` is a `dict`
        object of `str` to `float` detailing an optimization state.
    """

    @override
    def _optimize(
        self,
        init_params: Array1D[float64],
        max_n_iters: int,
    ) -> tuple[Array1D[float64], bool]:
        def fun(x: Array1D[floating]) -> tuple[float, Array1D[float64]]:
            return self._problem.cost(x, return_jacobian=True)

        bounds = scipy.optimize.Bounds(lb=self._problem.bounds.lower, ub=self._problem.bounds.upper)

        constraints: list[_Constraint] = []
        for constraint in self._problem.constraints:
            cs = constraint.transform("nonnegative")
            if constraint.lower_bound == constraint.upper_bound:
                constraints.append({"type": "eq", "fun": cs[0].function, "jac": cs[0].jacobian})
            else:
                constraints.extend(
                    {"type": "ineq", "fun": c.function, "jac": c.jacobian}
                    for c in cs
                )

        def callback(xk: Array1D[float64]) -> None:
            self._callback(xk, self._problem.cost(xk), {})

        result = scipy.optimize.minimize(
            fun,
            init_params,
            jac=True,
            bounds=bounds,
            constraints=cast("Any", constraints),
            method="slsqp",
            options={"maxiter": max_n_iters},
            callback=callback,
        )

        return result.x, bool(result.success)


class _Constraint(TypedDict):

    type: Literal["eq", "ineq"]
    fun: Callable[[Array1D[floating], Unpack[tuple[Any, ...]]], Array1D[floating]]
    jac: NotRequired[Callable[[Array1D[floating], Unpack[tuple[Any, ...]]], Array2D[floating]]]
    args: NotRequired[tuple[Any, ...]]
