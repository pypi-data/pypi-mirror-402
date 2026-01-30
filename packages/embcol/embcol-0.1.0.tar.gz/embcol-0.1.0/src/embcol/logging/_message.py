"""Logging message."""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from .._repr import Representor

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = ["ProgressMessage"]


class ProgressMessage:
    """Structured message for optimization progress.

    Parameters
    ----------
    iteration : int
        Iteration number.
    cost : float
        Cost.
    max_constr_vio : float
        Maximum constraint violation.
    state : mapping of str to float
        Other values detailing an optimization state.
    """

    _iteration: int
    _cost: float
    _max_constr_vio: float
    _state: dict[str, float]

    def __init__(
        self,
        iteration: int,
        cost: float,
        max_constr_vio: float,
        state: Mapping[str, float],
    ) -> None:
        self._iteration = int(iteration)
        self._cost = float(cost)
        self._max_constr_vio = float(max_constr_vio)
        self._state = {str(key): float(value) for key, value in state.items()}

    def __repr__(self) -> str:
        r = Representor(max_n_lines=len(self._state)+2)
        return r.repr_constructor(
            "ProgressMessage",
            self._iteration,
            self._cost,
            self._max_constr_vio,
            self._state,
        )

    def __str__(self) -> str:
        items = [
            ("cost", self._cost),
            ("max. constraint violation", self._max_constr_vio),
            *self._state.items(),
        ]
        items_str = ", ".join(f"{key}={value}" for key, value in items)
        return f"iteration {self._iteration}: {items_str}"

    def __eq__(self, other: object) -> bool:
        return (
            type(other) is ProgressMessage
            and self._iteration == other._iteration
            and self._cost == other._cost
            and self._max_constr_vio == other._max_constr_vio
            and self._state == other._state
        )

    def __hash__(self) -> int:
        return hash(
            (
                self._iteration,
                self._cost,
                self._max_constr_vio,
                tuple(sorted(self._state.items())),
            ),
        )

    @property
    def iteration(self) -> int:
        """Iteration number."""
        return self._iteration

    @property
    def cost(self) -> float:
        """Cost."""
        return self._cost

    @property
    def max_constr_vio(self) -> float:
        """Maximum constraint violation."""
        return self._max_constr_vio

    @property
    def state(self) -> MappingProxyType[str, float]:
        """Other values detailing an optimization state."""
        return MappingProxyType(self._state)
