"""Bounds of parameters."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import numpy as np

from .._checking import check_array, check_number
from .._exception import expr
from .._repr import Representor

if TYPE_CHECKING:
    from numpy import float64, floating

    from ..typing import Array1D, ArrayLike1D

__all__ = ["Bounds"]


class Bounds:
    """Bounds of parameters.

    Parameters
    ----------
    lower : array-like of float
        Lower bounds of parameters. The shape must be ``(N,)``, where ``N`` is the number of
        parameters.
    upper : array-like of float
        Upper bounds of parameters. The shape must be ``(N,)``, where ``N`` is the number of
        parameters.
    """

    _lower: Array1D[float64]
    _upper: Array1D[float64]

    def __init__(
        self,
        lower: ArrayLike1D[float, floating],
        upper: ArrayLike1D[float, floating],
    ) -> None:
        lower = np.asarray(lower, dtype=np.float64)
        check_array(lower, shape=(-1,), target=expr("lower"))
        for item in lower:
            check_number(
                item,
                upper_bound=float("inf"),
                allow_upper_bound=False,
                allow_nan=False,
                target=f"item of {expr('lower')}",
            )
        lower = cast("Array1D[float64]", lower)

        upper = np.asarray(upper, dtype=np.float64)
        check_array(
            upper,
            shape=(len(lower),),
            target=expr("upper"),
            size_descrs={0: f"the size of {expr('lower')}"},
        )
        for lower_item, upper_item in zip(lower, upper, strict=True):
            check_number(
                upper_item,
                lower_bound=lower_item,
                allow_lower_bound=False,
                allow_nan=False,
                target=f"item of {expr('upper')}",
                lower_bound_descr=f"a corresponding item of {expr('lower')}",
            )
        upper = cast("Array1D[float64]", upper)

        self._lower = lower
        self._upper = upper

        for array in [self._lower, self._upper]:
            array.setflags(write=False)

    def __repr__(self) -> str:
        r = Representor()
        return r.repr_constructor("Bounds", self._lower.tolist(), self._upper.tolist())

    def __eq__(self, other: object) -> bool:
        return (
            type(other) is Bounds
            and np.array_equal(self._lower, other._lower)
            and np.array_equal(self._upper, other._upper)
        )

    def __hash__(self) -> int:
        return hash((tuple(self._lower), tuple(self._upper)))

    @property
    def lower(self) -> Array1D[float64]:
        """Lower bounds of parameters."""
        return self._lower

    @property
    def upper(self) -> Array1D[float64]:
        """Upper bounds of parameters."""
        return self._upper

    def violation(self, params: ArrayLike1D[float, floating]) -> Array1D[float64]:
        """Measure degrees of the bound violation.

        A degree of the violation is zero for a parameter within bounds and is positive for
        a parameter out of bounds.

        Parameters
        ----------
        params : array-like of float
            Parameters.

        Returns
        -------
        numpy.ndarray of float
            Degrees of the violation.
        """
        params = cast("Array1D[floating]", np.asarray(params))

        values = np.empty(params.shape)

        is_less = params < self._lower
        values[is_less] = self._lower[is_less] - params[is_less]

        is_greater = self._upper < params
        values[is_greater] = params[is_greater] - self._upper[is_greater]

        values[~is_less & ~is_greater] = 0.0

        return values
