"""Trust-region local optimizer."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict, cast

import numpy as np
import scipy

from .._checking import check_number, check_number_set
from .._exception import expr
from .._typing_imports import override
from ._base import BaseLocalOptimizer

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from typing import Any

    from numpy import float64, floating
    from scipy.optimize import OptimizeResult

    from ..problem._problem import Problem
    from ..typing import Array1D, Array2D, Array3D, Callback

__all__ = ["TrustRegionLocalOptimizer"]


class TrustRegionLocalOptimizer(BaseLocalOptimizer):
    """Trust-region local optimizer.

    Search a local optimum by the trust-region method.

    Parameters
    ----------
    problem : embcol.problem.Problem
        Optimization problem.
    callback : callable or sequence of callable, optional
        Function(s) called after each iteration. The signature of a function must be
        ``(params, cost, state) -> None``, where ``params`` is a one-dimensional array of parameters
        of type `numpy.ndarray`, ``cost`` is a cost value of type `float`, and ``state`` is a `dict`
        object of `str` to `float` detailing an optimization state.
    color_diff_rms_tol : float, optional
        Convergence tolerance for the root mean square of color differences among samples.
    """

    _options: _Options

    def __init__(
        self,
        problem: Problem,
        callback: Callback | Sequence[Callback] = (),
        color_diff_rms_tol: float = 0.02,
    ) -> None:
        super().__init__(problem, callback=callback)

        check_number_set(color_diff_rms_tol, "real_numbers", target=expr("color_diff_rms_tol"))
        check_number(
            color_diff_rms_tol,
            lower_bound=0,
            allow_lower_bound=False,
            allow_nan=False,
            target=expr("color_diff_rms_tol"),
        )
        color_diff_rms_tol = float(color_diff_rms_tol)

        self._options["color_diff_rms_tol"] = color_diff_rms_tol

    @override
    def _optimize(
        self,
        init_params: Array1D[float64],
        max_n_iters: int,
    ) -> tuple[Array1D[float64], bool]:
        def fun(x: Array1D[floating]) -> tuple[float, Array1D[float64]]:
            return self._problem.cost(x, return_jacobian=True)

        def hess(x: Array1D[floating]) -> Array2D[float64]:
            _, hessian = self._problem.cost(x, return_hessian=True)
            return hessian

        bounds = scipy.optimize.Bounds(lb=self._problem.bounds.lower, ub=self._problem.bounds.upper)

        constraints = [
            scipy.optimize.NonlinearConstraint(
                constraint.function,
                constraint.lower_bound,
                constraint.upper_bound,
                jac=constraint.jacobian,
                hess=cast("Any", _make_hessp(constraint.hessian)),
            )
            for constraint in self._problem.constraints
        ]

        xtol = (
            0.5 * np.sqrt(len(self._problem.unfixed_indices)) * self._options["color_diff_rms_tol"]
        )

        def callback(intermediate_result: OptimizeResult) -> None:
            self._callback(
                intermediate_result.x,
                intermediate_result.fun,
                {
                    "trust-region radius": intermediate_result.tr_radius,
                    "barrier parameter": intermediate_result.barrier_parameter,
                },
            )

        result = scipy.optimize.minimize(
            fun,
            init_params,
            jac=True,
            hess=hess,
            bounds=bounds,
            constraints=constraints,
            method="trust-constr",
            options={
                "xtol": xtol,
                "maxiter": max_n_iters,
            },
            callback=callback,
        )

        return result.x, bool(result.success)


class _Options(TypedDict):

    color_diff_rms_tol: float


def _make_hessp(
    hessian: Callable[[Array1D[floating]], Array3D[float64]],
) -> Callable[[Array1D[floating], Array1D[floating]], Array2D[floating]]:
    """Make a function applying a Hessian to a vector.

    Parameters
    ----------
    hessian : callable
        Hessian.

    Returns
    -------
    callable
        Function applying `hessian` to a vector.
    """
    def hess(x: Array1D[floating], v: Array1D[floating]) -> Array2D[floating]:
        return np.tensordot(hessian(x), v, axes=(0, 0))

    return hess
