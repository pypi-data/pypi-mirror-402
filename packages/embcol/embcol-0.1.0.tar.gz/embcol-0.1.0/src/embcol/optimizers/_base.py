"""Abstract base classes for optimizers."""

from __future__ import annotations

import abc
from collections.abc import Iterable, Sequence
import logging
from typing import TYPE_CHECKING, cast

import numpy as np

from .._checking import check_array, check_number, check_number_set, check_type
from .._exception import expr
from .._repr import Representor
from ..logging._message import ProgressMessage
from ..problem._problem import Problem
from ..typing import Callback

if TYPE_CHECKING:
    from collections.abc import Mapping

    from numpy import float64, floating

    from .._typing_imports import Self
    from ..typing import Array1D, Array2D, ArrayLike2D

__all__ = ["BaseGlobalOptimizer", "BaseLocalOptimizer", "BaseOptimizer"]


class BaseOptimizer(abc.ABC):
    """Abstract base class for an optimizer.

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

    _problem: Problem
    _callback: _CallbackSequence
    _options: Mapping[str, object]

    def __init__(self, problem: Problem, callback: Callback | Sequence[Callback] = ()) -> None:
        check_type(problem, [Problem], target=expr("problem"))

        check_type(callback, ["callable", Sequence], target=expr("callback"))
        if callable(callback):
            callback = [callback]
        for item in callback:
            check_type(item, ["callable"], target=f"item of {expr('callback')}")
        callback = _CallbackSequence([_LoggingCallback(self.__module__, problem), *callback])

        self._problem = problem
        self._callback = callback
        self._options = {}

    def __repr__(self) -> str:
        r = Representor(max_n_lines=4)
        return r.repr_constructor(
            type(self).__name__,
            self._problem,
            callback=[cb for cb in self._callback if not isinstance(cb, _LoggingCallback)],
            **self._options,
        )

    def _log_start(self, *, resume: bool) -> None:
        """Log a start of an optimization.

        Parameters
        ----------
        resume : bool
            If ``True`` is given, an optimization is assumed to be resumed from the previous run.
        """
        if not resume:
            logging_callback = next(cb for cb in self._callback if isinstance(cb, _LoggingCallback))
            logging_callback.reset()

        message = (
            "optimization by %s was started"
            if not resume else
            "optimization by %s was resumed"
        )
        args: list[object] = [type(self).__name__]
        if self._options:
            message += ": " + ", ".join("%s=%r" for _ in range(len(self._options)))
            args.extend(x for item in self._options.items() for x in item)

        logger = logging.getLogger(self.__module__)
        logger.info(message, *args)

    def _log_termination(self, last_iteration: int, *, is_converged: bool) -> None:
        """Log a termination of an optimization.

        Parameters
        ----------
        last_iteration : int
            Last iteration number.
        is_converged : bool
            If ``True`` is given, an optimization is assumed to be converged.
        """
        cls_name = type(self).__name__

        logger = logging.getLogger(self.__module__)
        if is_converged:
            logger.info(
                "optimization by %s was converged after %d %s",
                cls_name,
                last_iteration,
                "iteration" if last_iteration == 1 else "iterations",
            )
        else:
            logger.warning(
                "optimization by %s was not converged within %d %s",
                cls_name,
                last_iteration,
                "iteration" if last_iteration == 1 else "iterations",
            )


class BaseLocalOptimizer(BaseOptimizer):
    """Abstract base class for a local optimizer."""

    def optimize(
        self,
        init_oklabs: ArrayLike2D[float, floating],
        max_n_iters: int = 1000,
    ) -> tuple[Array2D[float64], bool]:
        r"""Run an optimization.

        Parameters
        ----------
        init_oklabs : array-like of float
            Initial Oklab colors of samples. The shape must be ``(N, 3)``, where ``N`` is the number
            of samples.
        max_n_iters : int, optional
            Maximum number of iterations.

        Returns
        -------
        oklabs : numpy.ndarray of float
            Oklab colors of samples. The shape is ``(N, 3)``.
        is_converged : bool
            ``True`` if an optimization is converged.
        """
        init_oklabs = np.asarray(init_oklabs, dtype=np.float64, copy=True)
        check_array(
            init_oklabs,
            shape=(self._problem.n_samples, 3),
            target=expr("init_oklabs"),
            size_descrs={0: "the number of samples"},
        )
        init_oklabs = cast("Array2D[float64]", init_oklabs)

        check_number_set(max_n_iters, "integers", target=expr("max_n_iters"))
        check_number(max_n_iters, lower_bound=1, target=expr("max_n_iters"))
        max_n_iters = int(max_n_iters)

        self._log_start(resume=False)
        params, is_converged = self._optimize(
            self._problem.oklabs_to_params(init_oklabs),
            max_n_iters,
        )
        self._log_termination(
            next(cb for cb in self._callback if isinstance(cb, _LoggingCallback)).last_iteration,
            is_converged=is_converged,
        )

        oklabs = self._problem.params_to_oklabs(params)

        return oklabs, is_converged

    @abc.abstractmethod
    def _optimize(
        self,
        init_params: Array1D[float64],
        max_n_iters: int,
    ) -> tuple[Array1D[float64], bool]:
        """Core routine of an optimization.

        Parameters
        ----------
        init_params : numpy.ndarray of float
            Initial parameters.
        max_n_iters : int
            Maximum number of iterations

        Returns
        -------
        params : numpy.ndarray of float
            Parameters.
        is_converged : bool
            ``True`` if an optimization is converged.
        """


class BaseGlobalOptimizer(BaseOptimizer):
    """Abstract base class for a global optimizer."""

    def optimize(
        self,
        max_n_iters: int = 10000,
        *,
        resume: bool = False,
    ) -> tuple[Array2D[float64], bool]:
        r"""Run an optimization.

        Parameters
        ----------
        max_n_iters : int, optional
            Maximum number of iterations.
        resume : bool, optional
            If ``True`` is given, an optimization is resumed from the previous run.

        Returns
        -------
        oklabs : numpy.ndarray of float
            Oklab colors of samples. The shape is ``(N, 3)``, where ``N`` is the number of samples.
        is_converged : bool
            ``True`` if an optimization is converged.
        """
        check_number_set(max_n_iters, "integers", target=expr("max_n_iters"))
        check_number(max_n_iters, lower_bound=1, target=expr("max_n_iters"))
        max_n_iters = int(max_n_iters)

        self._log_start(resume=resume)
        params, is_converged = self._optimize(max_n_iters, resume=resume)
        self._log_termination(
            next(cb for cb in self._callback if isinstance(cb, _LoggingCallback)).last_iteration,
            is_converged=is_converged,
        )

        oklabs = self._problem.params_to_oklabs(params)

        return oklabs, is_converged

    @abc.abstractmethod
    def _optimize(self, max_n_iters: int, *, resume: bool) -> tuple[Array1D[float64], bool]:
        """Core routine of an optimization.

        Parameters
        ----------
        max_n_iters : int
            Maximum number of iterations
        resume : bool
            If ``True`` is given, an optimization is resumed from the previous run.

        Returns
        -------
        params : numpy.ndarray of float
            Parameters.
        is_converged : bool
            ``True`` if an optimization is converged.
        """


class _LoggingCallback:
    """Callback for logging.

    Parameters
    ----------
    name : str
        Name of a logger.
    problem : Problem
        Optimization problem.
    """

    _name: str
    _problem: Problem
    _last_iteration: int

    def __init__(self, name: str, problem: Problem) -> None:
        self._name = name
        self._problem = problem

        self.reset()

    def __call__(self, params: Array1D[floating], cost: float, state: dict[str, float]) -> None:
        max_constr_vio = max(
            constraint.violation(params).max()
            for constraint in self._problem.constraints
        )

        logger = logging.getLogger(self._name)
        logger.info(ProgressMessage(self._last_iteration+1, cost, max_constr_vio, state))

        self._last_iteration += 1

    @property
    def last_iteration(self) -> int:
        """Last iteration number."""
        return self._last_iteration

    def reset(self) -> None:
        """Reset a history of calling."""
        self._last_iteration = 0


class _CallbackSequence(tuple[Callback, ...]):
    """Callback for calling multiple callbacks at a time.

    Parameters
    ----------
    callbacks : iterable of callable, optional
        Callbacks to be called.
    """

    __slots__ = ()

    def __new__(cls, callbacks: Iterable[Callback] = ()) -> Self:
        return super().__new__(cls, callbacks)

    def __call__(self, params: Array1D[float64], cost: float, state: dict[str, float]) -> None:
        for callback in self:
            callback(params, cost, state)
