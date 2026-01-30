from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Callable

    from numpy import floating

    from embcol.problem._problem import Problem
    from embcol.typing import Array1D, Array2D, Callback


class ApproxDerivative(Protocol):

    def __call__(
        self,
        func: Callable[[Array1D[floating]], Array1D[floating]],
        x: Array1D[floating],
        max_dx: float = ...,
        rel_tol: float = ...,
        abs_tol: float = ...,
    ) -> Array2D[floating]:
        ...


class MakeAssertionCallback(Protocol):

    def __call__(self, problem: Problem, *, assert_cost_decreasing: bool = True) -> Callback: ...
