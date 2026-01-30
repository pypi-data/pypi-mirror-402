"""CMA-ES global optimizer."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict, cast
import warnings

import numpy as np

from .._checking import check_number, check_number_set
from .._exception import expr
from .._typing_imports import override
from ._base import BaseGlobalOptimizer

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", message="Could not import matplotlib.pyplot")
    import cma
import cma.constraints_handler
import cma.logger

if TYPE_CHECKING:
    from collections.abc import Sequence

    from cma import CMAEvolutionStrategy
    from numpy import float64
    from numpy.random import Generator
    from numpy.typing import NDArray

    from ..problem import Problem
    from ..problem._bounds import Bounds
    from ..typing import Array1D, Callback, RNGLike

__all__ = ["CMAESGlobalOptimizer"]

# prevent creation of a log directory
cma.constraints_handler._Logger = cma.logger.LoggerDummy  # type: ignore[assignment, misc]  # noqa: SLF001


class CMAESGlobalOptimizer(BaseGlobalOptimizer):
    """CMA-ES global optimizer.

    Search a global optimum by the covariance matrix adaption evolution strategy (CMA-ES).

    Parameters
    ----------
    problem : embcol.problem.Problem
        Optimization problem.
    callback : callable or sequence of callable, optional
        Function(s) called after each iteration. The signature of a function must be
        ``(params, cost, state) -> None``, where ``params`` is a one-dimensional array of parameters
        of type `numpy.ndarray`, ``cost`` is a cost value of type `float`, and ``state`` is a `dict`
        object of `str` to `float` detailing an optimization state.
    population_size : int, optional
        Population size. If nothing is given, set to ``floor(4+3*log(M))``, where ``log(M)`` is
        a natural logarithm of the number of parameters.
    color_diff_tol : float, optional
        Convergence tolerance for color differences among the population.
    cost_tol : float, optional
        Convergence tolerance for the cost.
    rng : rng-like, optional
        Random number generator. If nothing is given, a generator is initialized
        nondeterministically.
    """

    _options: _Options

    _rng: Generator
    _solver: _Solver | None

    def __init__(
        self,
        problem: Problem,
        callback: Callback | Sequence[Callback] = (),
        population_size: int | None = None,
        color_diff_tol: float = 0.02,
        cost_tol: float = 1e-8,
        rng: RNGLike = None,
    ) -> None:
        super().__init__(problem, callback=callback)

        if population_size is None:
            population_size = int(4+3*np.log(problem.n_params))
        check_number_set(population_size, "integers", target=expr("population_size"))
        check_number(population_size, lower_bound=2, target=expr("population_size"))
        population_size = int(population_size)

        check_number_set(color_diff_tol, "real_numbers", target=expr("color_diff_tol"))
        check_number(
            color_diff_tol,
            lower_bound=0,
            allow_lower_bound=False,
            allow_nan=False,
            target=expr("color_diff_tol"),
        )
        color_diff_tol = float(color_diff_tol)

        check_number_set(cost_tol, "real_numbers", target=expr("cost_tol"))
        check_number(
            cost_tol,
            lower_bound=0,
            allow_lower_bound=False,
            allow_nan=False,
            target=expr("cost_tol"),
        )
        cost_tol = float(cost_tol)

        generator = np.random.default_rng(rng)

        self._options["population_size"] = population_size
        self._options["color_diff_tol"] = color_diff_tol
        self._options["cost_tol"] = cost_tol
        self._options["rng"] = rng

        self._rng = generator
        self._solver = None

    @override
    def _optimize(self, max_n_iters: int, *, resume: bool) -> tuple[Array1D[float64], bool]:
        if self._solver is None or not resume:
            self._solver = _Solver(
                self._options["population_size"],
                self._problem.effective_bounds,
                self._options["color_diff_tol"],
                self._options["cost_tol"],
                self._rng,
            )

        constraints = [
            c
            for constraint in self._problem.constraints
            for c in constraint.transform("nonpositive")
        ]

        for _ in range(max_n_iters):
            params = self._solver.ask()

            cost = self._problem.cost(params)
            constr_values = cast(
                "Array1D[float64]",
                np.concat([c.function(params) for c in constraints]),
            )

            self._solver.tell(cost, constr_values)

            self._callback(self._solver.best_params, self._solver.best_cost, self._solver.state)

            if self._solver.is_converged():
                break

        return self._solver.best_params, self._solver.is_converged()


class _Options(TypedDict):

    population_size: int
    color_diff_tol: float
    cost_tol: float
    rng: RNGLike


class _Solver:
    """CMA-ES solver.

    Parameters
    ----------
    population_size : int
        Population size.
    bounds : embcol.problem.Bounds
        Bounds of parameters. All values must be finite.
    color_diff_tol : float
        Convergence tolerance for color difference among a population.
    cost_tol : float
        Convergence tolerance for the cost.
    rng : numpy.random.Generator
        Random number generator.
    """

    _es: CMAEvolutionStrategy
    _rng: Generator
    _next_params: list[Array1D[float64]]
    _next_costs: list[float]
    _next_constr_values: list[Array1D[float64]]
    _best_params: Array1D[float64]
    _best_cost: float

    def __init__(
        self,
        population_size: int,
        bounds: Bounds,
        color_diff_tol: float,
        cost_tol: float,
        rng: Generator,
    ) -> None:
        x0 = 0.5 * (bounds.lower+bounds.upper)
        sigma0 = (
            np.min(bounds.upper-bounds.lower) / 6  # so that 3-sigma region <= bounds
            or
            np.finfo(float).eps
        )
        inopts = {
            "bounds": [bounds.lower, bounds.upper],
            "BoundaryHandler": cma.BoundTransform,
            "popsize": population_size,
            "tolx": color_diff_tol/6,  # stop if 3-sigma region of population < 'color_diff_tol'
            "tolfun": cost_tol,
            "tolstagnation": 0,
            "seed": np.nan,
            "randn": self._randn,
            "verbose": -10,
        }
        self._es = cma.CMAEvolutionStrategy(x0, sigma0, inopts=inopts)

        self._rng = rng

        self._next_params = []
        self._next_costs = []
        self._next_constr_values = []
        self._best_params = np.full(population_size, np.nan)
        self._best_cost = float("inf")

        self._best_params.setflags(write=False)

    @property
    def best_params(self) -> Array1D[float64]:
        """Parameters for a best solution."""
        return self._best_params

    @property
    def best_cost(self) -> float:
        """Cost for a best solution."""
        return self._best_cost

    @property
    def state(self) -> dict[str, float]:
        """Values detailing a solver state."""
        return {
            "max. standard deviation": float(
                (self._es.sigma*(self._es.sigma_vec.scaling*np.sqrt(self._es.dC))).max(),
            ),
            "fitness range": float(np.ptp(self._es.fit.fit)) if self._es.fit.fit else float("nan"),  # type: ignore[attr-defined]
        }

    def ask(self) -> Array1D[float64]:
        """Ask parameters to be evaluated next.

        Returns
        -------
        numpy.ndarray of float
            Parameters.
        """
        if not self._next_params:
            self._next_params.extend(self._es.ask())

        return self._next_params[len(self._next_costs)]

    def tell(self, cost: float, constr_values: Array1D[float64]) -> None:
        """Tell an evaluation result to a solver.

        Parameters
        ----------
        cost : float
            Cost value.
        constr_values : numpy.ndarray of float
            Constraint values.
        """
        self._next_costs.append(cost)
        self._next_constr_values.append(constr_values)

        if cost < self._best_cost:
            self._best_params = self._next_params[len(self._next_costs)-1].copy()
            self._best_params.setflags(write=False)

            self._best_cost = cost

        if len(self._next_costs) == len(self._next_params):
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="``import moarchiving`` failed")
                self._es.tell(
                    self._next_params,
                    self._next_costs,
                    constraints_values=self._next_constr_values,
                )

            self._next_params.clear()
            self._next_costs.clear()
            self._next_constr_values.clear()

    def is_converged(self) -> bool:
        """Return the state of the convergence.

        Returns
        -------
        bool
            ``True`` if converged.
        """
        return bool(self._es.stop())

    def _randn(self, *dimensions: int) -> NDArray[float64]:
        """Sample from the standard normal distribution.

        This method is a replacement of the legacy `numpy.random.randn` function.
        """
        return self._rng.normal(size=dimensions)
