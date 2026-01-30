"""Constraint."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import numpy as np

from .._checking import check_number, check_number_set, check_type
from .._exception import expr, invalid_value_error
from .._repr import Representor

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Literal

    from numpy import float64, floating

    from ..typing import Array1D, Array2D, Array3D, ArrayLike1D

__all__ = ["Constraint"]


class Constraint:
    r"""Constraint for parameters.

    Parameters
    ----------
    function : callable
        Constraint function. The signature must be ``(params) -> values``, where ``params`` is
        a one-dimensional array of parameters and ``values`` is a one-dimensional array of
        constrained values.
    jacobian : callable
        Jacobian of a constraint function. The signature must be ``(params) -> values``, where
        ``params`` is a one-dimensional array of parameters and ``values`` is a Jacobian matrix.
        ``values[i, k]`` is a derivative of the ``i``\ th output with respect to the ``k``\ th
        parameter.
    hessian : callable
        Hessian of a constraint function. The signature must be ``(params) -> values``, where
        ``params`` is a one-dimensional array of parameters and ``values`` is a Hessian matrix.
        ``values[i, k1, k2]`` is a second derivative of the ``i``\ th output with respect to
        the ``k1``\ th and ``k2``\ th parameters.
    n_outputs : int
        Number of outputs of a constraint function.
    lower_bound : float, optional
        Lower bound of a constraint function.
    upper_bound : float, optional
        Upper bound of a constraint function.
    """

    _function: Callable[[Array1D[floating]], Array1D[float64]]
    _jacobian: Callable[[Array1D[floating]], Array2D[float64]]
    _hessian: Callable[[Array1D[floating]], Array3D[float64]]
    _n_outputs: int
    _lower_bound: float
    _upper_bound: float

    def __init__(
        self,
        function: Callable[[Array1D[floating]], Array1D[float64]],
        jacobian: Callable[[Array1D[floating]], Array2D[float64]],
        hessian: Callable[[Array1D[floating]], Array3D[float64]],
        n_outputs: int,
        lower_bound: float = -float("inf"),
        upper_bound: float = float("inf"),
    ) -> None:
        check_type(function, ["callable"], target=expr("function"))

        check_type(jacobian, ["callable"], target=expr("jacobian"))

        check_type(hessian, ["callable"], target=expr("hessian"))

        check_number_set(n_outputs, "integers", target=expr("n_outputs"))
        check_number(n_outputs, lower_bound=0, target=expr("n_outputs"))
        n_outputs = int(n_outputs)

        check_number_set(lower_bound, "real_numbers", target=expr("lower_bound"))
        check_number(
            lower_bound,
            upper_bound=float("inf"),
            allow_upper_bound=False,
            allow_nan=False,
            target=expr("lower_bound"),
        )
        lower_bound = float(lower_bound)

        check_number_set(upper_bound, "real_numbers", target=expr("upper_bound"))
        check_number(
            upper_bound,
            lower_bound=lower_bound,
            allow_lower_bound=False,
            allow_nan=False,
            target=expr("upper_bound"),
            lower_bound_descr=expr("lower_bound"),
        )
        upper_bound = float(upper_bound)

        self._function = function
        self._jacobian = jacobian
        self._hessian = hessian
        self._n_outputs = n_outputs
        self._lower_bound = lower_bound
        self._upper_bound = upper_bound

    def __repr__(self) -> str:
        r = Representor()
        return r.repr_constructor(
            "Constraint",
            self._function,
            self._jacobian,
            self._hessian,
            self._n_outputs,
            lower_bound=self._lower_bound,
            upper_bound=self._upper_bound,
        )

    def __eq__(self, other: object) -> bool:
        return (
            type(other) is Constraint
            and self._function is other._function
            and self._jacobian is other._jacobian
            and self._hessian is other._hessian
            and self._n_outputs == other._n_outputs
            and self._lower_bound == other._lower_bound
            and self._upper_bound == other._upper_bound
        )

    def __hash__(self) -> int:
        return hash(
            (
                self._function,
                self._jacobian,
                self._hessian,
                self._n_outputs,
                self._lower_bound,
                self._upper_bound,
            ),
        )

    @property
    def function(self) -> Callable[[Array1D[floating]], Array1D[float64]]:
        """Constraint function."""
        return self._function

    @property
    def jacobian(self) -> Callable[[Array1D[floating]], Array2D[float64]]:
        """Jacobian of a constraint function."""
        return self._jacobian

    @property
    def hessian(self) -> Callable[[Array1D[floating]], Array3D[float64]]:
        """Hessian of a constraint function."""
        return self._hessian

    @property
    def n_outputs(self) -> int:
        """Number of outputs of a constraint function."""
        return self._n_outputs

    @property
    def lower_bound(self) -> float:
        """Lower bound of a constraint function."""
        return self._lower_bound

    @property
    def upper_bound(self) -> float:
        """Upper bound of a constraint function."""
        return self._upper_bound

    def violation(self, params: ArrayLike1D[float, floating]) -> Array1D[float64]:
        """Measure degrees of the constraint violation.

        A degree of the violation is zero for an output within bounds and is positive for an output
        out of bounds.

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

        value = self._function(params)

        is_less = value < self._lower_bound
        is_greater = self._upper_bound < value
        value[is_less] = self._lower_bound - value[is_less]
        value[is_greater] -= self._upper_bound
        value[~is_less & ~is_greater] = 0.0

        return value

    def transform(self, feasible: Literal["nonnegative", "nonpositive"]) -> list[Constraint]:
        """Transform a constraint for adjusting a feasible region.

        Parameters
        ----------
        feasible : {'nonnegative', 'nonpositive'}
            Feasible region after the transform.

        Returns
        -------
        list of embcol.problem.Constraint
            Transformed constrains.

        Examples
        --------
        >>> import numpy as np
        >>> original = Constraint(
        ...     lambda params: 2*params,
        ...     lambda params: 2*np.eye(len(params)),
        ...     lambda params: np.zeros((len(params),)*3),
        ...     3,
        ...     lower_bound=-1.0,
        ...     upper_bound=1.0,
        ... )
        >>> transformed = original.transform("nonnegative")
        >>> params = np.array([-1.0, 0.0, 2.0])

        Only ``params[1]`` is feasible for the original constraint.

        >>> original.function(params)
        array([-2.,  0.,  4.])
        >>> original.violation(params) == 0
        array([False,  True, False])

        Only the feasible parameter gives nonnegative constrained values for all transformed
        constraints.

        >>> [t.function(params) for t in transformed]
        [array([-1.,  1.,  5.]), array([ 3.,  1., -3.])]
        """
        constraints: list[Constraint] = []
        match feasible:
            case "nonnegative":
                if not np.isinf(self._lower_bound):
                    constraints.append(
                        Constraint(
                            lambda params: cast(
                                "Array1D[float64]",
                                self._function(params)-self._lower_bound,
                            ),
                            self._jacobian,
                            self._hessian,
                            self._n_outputs,
                            lower_bound=0.0,
                        ),
                    )
                if not np.isinf(self._upper_bound):
                    constraints.append(
                        Constraint(
                            lambda params: cast(
                                "Array1D[float64]",
                                self._upper_bound-self._function(params),
                            ),
                            lambda params: -self._jacobian(params),
                            lambda params: -self._hessian(params),
                            self._n_outputs,
                            lower_bound=0.0,
                        ),
                    )
            case "nonpositive":
                if not np.isinf(self._lower_bound):
                    constraints.append(
                        Constraint(
                            lambda params: cast(
                                "Array1D[float64]",
                                self._lower_bound-self._function(params),
                            ),
                            lambda params: -self._jacobian(params),
                            lambda params: -self._hessian(params),
                            self._n_outputs,
                            upper_bound=0.0,
                        ),
                    )
                if not np.isinf(self._upper_bound):
                    constraints.append(
                        Constraint(
                            lambda params: cast(
                                "Array1D[float64]",
                                self._function(params)-self._upper_bound,
                            ),
                            self._jacobian,
                            self._hessian,
                            self._n_outputs,
                            upper_bound=0.0,
                        ),
                    )
            case _:
                raise invalid_value_error(
                    feasible,
                    ["nonnegative", "nonpositive"],
                    target=expr("feasible"),
                )

        return constraints
