"""DE global optimizer."""

from __future__ import annotations

import itertools
from typing import TYPE_CHECKING, TypedDict, cast

import numpy as np

from .._checking import check_number, check_number_set, check_size, check_value
from .._exception import expr
from .._typing_imports import assert_never, override
from .._utils import is_iterable
from ..random import ParamsGenerator
from ._base import BaseGlobalOptimizer

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from typing import Literal, SupportsIndex

    from numpy import float64
    from numpy.random import Generator

    from ..problem import Problem
    from ..typing import Array1D, Array2D, Callback, RNGLike

__all__ = ["DEGlobalOptimizer"]


class DEGlobalOptimizer(BaseGlobalOptimizer):
    """DE global optimizer.

    Search a global optimum by the differential evolution (DE).

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
        Population size.
    mutation : {'best/1', 'rand/1'}, optional
        Mutation method.
    diff_weight : float or iterable of float, optional
        Differential weight. The value must be in the range [0, 2]. If an iterable is given,
        the size must be 2, which are lower and upper bounds for dithering.
    crossover_prob : float
        Crossover probability. The value must be in the range [0, 1].
    cost_tol : float, optional
        Convergence tolerance for the cost.
    cost_std_tol : float, optional
        Convergence tolerance for the standard deviation of costs of a population.
    rng : rng-like, optional
        Random number generator. If nothing is given, a generator is initialized
        nondeterministically.
    """

    _options: _Options

    _rng: Generator
    _generator: ParamsGenerator
    _population: _Population
    _mutate: Callable[[SupportsIndex, SupportsIndex], Array1D[float64]]

    def __init__(
        self,
        problem: Problem,
        callback: Callback | Sequence[Callback] = (),
        population_size: int = 20,
        mutation: Literal["best/1", "rand/1"] = "best/1",
        diff_weight: float | tuple[float, float] = (0.1, 0.3),
        crossover_prob: float = 0.05,
        cost_tol: float = 1e-8,
        cost_std_tol: float = 1e-8,
        rng: RNGLike = None,
    ) -> None:
        super().__init__(problem, callback=callback)

        check_number_set(population_size, "integers", target=expr("population_size"))
        check_number(population_size, lower_bound=4, target=expr("population_size"))
        population_size = int(population_size)

        check_value(mutation, ["best/1", "rand/1"], target=expr("mutation"))

        if not is_iterable(diff_weight):
            diff_weight = cast("float", diff_weight)
            check_number_set(diff_weight, "real_numbers", target=expr("diff_weight"))
            check_number(
                diff_weight,
                lower_bound=0,
                upper_bound=2,
                allow_nan=False,
                target=expr("diff_weight"),
            )
            diff_weight = float(diff_weight)
            diff_weight = (diff_weight, diff_weight)
        else:
            check_size(diff_weight, lower_bound=2, upper_bound=2, target=expr("diff_weight"))
            check_number_set(diff_weight[0], "real_numbers", target=expr("diff_weight[0]"))
            check_number(
                diff_weight[0],
                lower_bound=0,
                allow_lower_bound=False,
                upper_bound=2,
                allow_nan=False,
                target=expr("diff_weight[0]"),
            )
            check_number_set(diff_weight[1], "real_numbers", target=expr("diff_weight[1]"))
            check_number(
                diff_weight[1],
                lower_bound=diff_weight[0],
                upper_bound=2,
                allow_nan=False,
                target=expr("diff_weight[1]"),
                lower_bound_descr=expr("diff_weight[0]"),
            )
            diff_weight = (float(diff_weight[0]), float(diff_weight[1]))

        check_number_set(crossover_prob, "real_numbers", target=expr("crossover_prob"))
        check_number(
            crossover_prob,
            lower_bound=0,
            upper_bound=1,
            allow_nan=False,
            target=expr("crossover_prob"),
        )
        crossover_prob = float(crossover_prob)

        check_number_set(cost_tol, "real_numbers", target=expr("cost_tol"))
        check_number(
            cost_tol,
            lower_bound=0,
            allow_lower_bound=False,
            allow_nan=False,
            target=expr("cost_tol"),
        )
        cost_tol = float(cost_tol)

        check_number_set(cost_std_tol, "real_numbers", target=expr("cost_std_tol"))
        check_number(
            cost_std_tol,
            lower_bound=0,
            allow_lower_bound=False,
            allow_nan=False,
            target=expr("cost_std_tol"),
        )
        cost_std_tol = float(cost_std_tol)

        orig_rng = rng
        rng = np.random.default_rng(rng)

        generator = ParamsGenerator(rng=rng)
        population = _Population(
            population_size,
            problem.n_params,
            sum(constraint.n_outputs for constraint in problem.constraints),
        )

        match mutation:
            case "best/1":
                def mutate(i_target: SupportsIndex, i_best: SupportsIndex) -> Array1D[float64]:  # noqa: ARG001
                    return self._mutate_by_best_1(i_best)
            case "rand/1":
                def mutate(i_target: SupportsIndex, i_best: SupportsIndex) -> Array1D[float64]:  # noqa: ARG001
                    return self._mutate_by_rand_1(i_target)
            case _:
                assert_never(mutation)

        self._options["population_size"] = population_size
        self._options["mutation"] = mutation
        self._options["diff_weight"] = diff_weight
        self._options["crossover_prob"] = crossover_prob
        self._options["cost_tol"] = cost_tol
        self._options["cost_std_tol"] = cost_std_tol
        self._options["rng"] = orig_rng

        self._rng = rng
        self._generator = generator
        self._population = population
        self._mutate = mutate

    @override
    def _optimize(self, max_n_iters: int, *, resume: bool) -> tuple[Array1D[float64], bool]:
        if not resume:
            self._population.reset()

        if not np.isfinite(self._population.params).all():
            # initialize population
            for i_target in range(self._options["population_size"]):
                params = self._generator.random(self._problem)

                cost = self._problem.cost(params)
                constr_vios = cast(
                    "Array1D[float64]",
                    np.concat(
                        [constraint.violation(params) for constraint in self._problem.constraints],
                    ),
                )

                self._population.update(i_target, params, cost, constr_vios)

        i_best = int(np.argmin(self._population.costs))

        for i_target in itertools.islice(
            itertools.cycle(range(self._options["population_size"])),
            max_n_iters,
        ):
            trial = self._mutate(i_target, i_best)

            # binominal crossover
            crossover = (
                self._rng.random(size=self._problem.n_params) < self._options["crossover_prob"]
            )
            crossover[self._rng.integers(len(crossover))] = True
            trial = cast(
                "Array1D[float64]",
                np.where(crossover, trial, self._population.params[i_target, :]),
            )

            # limit within bounds
            mask = (
                (trial < self._problem.effective_bounds.lower)
                | (self._problem.effective_bounds.upper < trial)
            )
            trial[mask] = self._rng.uniform(
                low=self._problem.effective_bounds.lower[mask],
                high=self._problem.effective_bounds.upper[mask],
            )

            trial_constr_vios = cast(
                "Array1D[float64]",
                np.concat(
                    [constraint.violation(trial) for constraint in self._problem.constraints],
                ),
            )
            is_feasible_trial = not trial_constr_vios.any()

            trial_cost = self._problem.cost(trial) if is_feasible_trial else float("inf")

            if (
                (is_feasible_trial and self._population.constr_vios[i_target, :].any())
                or (is_feasible_trial and trial_cost < self._population.costs[i_best])
                or (
                    not is_feasible_trial
                    and (trial_constr_vios < self._population.constr_vios[i_target, :]).all()
                )
            ):
                self._population.update(i_target, trial, trial_cost, trial_constr_vios)
                if trial_cost < self._population.costs[i_best]:
                    i_best = i_target

            std = self._population.costs.std()

            self._callback(
                cast("Array1D[float64]", self._population.params[i_best, :]),
                self._population.costs[i_best],
                {"standard deviation": float(std)},
            )

            if (
                self._population.costs[i_best] < self._options["cost_tol"]
                or std < self._options["cost_std_tol"]
            ):
                return cast("Array1D[float64]", self._population.params[i_best, :]), True

        return cast("Array1D[float64]", self._population.params[i_best, :]), False

    def _mutate_by_best_1(self, i_best: SupportsIndex) -> Array1D[float64]:
        diff_weight = self._rng.uniform(
            low=self._options["diff_weight"][0],
            high=self._options["diff_weight"][1],
        )

        indices = [i for i in range(self._options["population_size"]) if i != i_best]
        x1, x2 = self._rng.choice(
            self._population.params[indices, :],
            axis=0,
            size=2,
            replace=False,
        )

        return cast("Array1D[float64]", self._population.params[i_best, :]+diff_weight*(x1-x2))

    def _mutate_by_rand_1(self, i_target: SupportsIndex) -> Array1D[float64]:
        diff_weight = self._rng.uniform(
            low=self._options["diff_weight"][0],
            high=self._options["diff_weight"][1],
        )

        indices = [i for i in range(self._options["population_size"]) if i != i_target]
        x0, x1, x2 = self._rng.choice(
            self._population.params[indices, :],
            axis=0,
            size=3,
            replace=False,
        )

        return cast("Array1D[float64]", x0+diff_weight*(x1-x2))


class _Options(TypedDict):

    population_size: int
    mutation: Literal["best/1", "rand/1"]
    diff_weight: tuple[float, float]
    crossover_prob: float
    cost_tol: float
    cost_std_tol: float
    rng: RNGLike


class _Population:
    """Population.

    Parameters
    ----------
    size : int
        Population size.
    n_params : int
        Number of parameters.
    n_constr_outputs : int
        Total number of outputs of constraints.
    """

    _params: Array2D[float64]
    _costs: Array1D[float64]
    _constr_vios: Array2D[float64]

    def __init__(self, size: int, n_params: int, n_constr_outputs: int) -> None:
        self._params = np.empty((size, n_params))
        self._costs = np.empty(size)
        self._constr_vios = np.empty((size, n_constr_outputs))

        self.reset()

    @property
    def params(self) -> Array2D[float64]:
        """Set of parameters."""
        return self._params

    @property
    def costs(self) -> Array1D[float64]:
        """Costs."""
        return self._costs

    @property
    def constr_vios(self) -> Array2D[float64]:
        """Degrees of the constraint violation."""
        return self._constr_vios

    def reset(self) -> None:
        """Reset a population."""
        self._params[:, :] = np.nan
        self._costs[:] = np.inf
        self._constr_vios[:, :] = np.inf

    def update(
        self,
        index: SupportsIndex,
        params: Array1D[float64],
        cost: float,
        constr_vios: Array1D[float64],
    ) -> None:
        """Update an individual.

        Parameters
        ----------
        index : int
            Index of an individual to be updated.
        params : numpy.ndarray of float
            Parameters of an individual.
        cost : float
            Cost of an individual.
        constr_vios : numpy.ndarray of float
            Degrees of the constraint violation of an individual.
        """
        self._params[index, :] = params
        self._costs[index] = cost
        self._constr_vios[index, :] = constr_vios
