from __future__ import annotations

from typing import TYPE_CHECKING, cast

import hypothesis
import numpy as np
import pytest
import scipy

if TYPE_CHECKING:
    from collections.abc import Callable

    from numpy import floating
    from numpy.typing import NDArray

    from embcol.typing import Array1D, Array2D
    from tests._typing import ApproxDerivative

hypothesis.settings.register_profile(
    "default",
    deadline=None,
)
hypothesis.settings.register_profile(
    "long",
    parent=hypothesis.settings.get_profile("default"),
    max_examples=10000,
)


@pytest.fixture(scope="session")
def make_rng_seed() -> Callable[[], int | None]:
    def inner() -> int | None:
        profile = hypothesis.settings.get_profile(hypothesis.settings.get_current_profile_name())
        return 0 if profile.derandomize else None

    return inner


@pytest.fixture(scope="session")
def approx_derivative() -> ApproxDerivative:
    def inner(
        func: Callable[[Array1D[floating]], Array1D[floating]],
        x: Array1D[floating],
        max_dx: float = float("inf"),
        rel_tol: float = 1e-6,
        abs_tol: float = 1e-6,
    ) -> Array2D[floating]:
        step_direction = 0  # central difference
        order = 8  # must be even
        step_factor = 2.0
        maxiter = 10

        eps = np.finfo(x.dtype).eps
        xc = np.maximum(1.0, abs(x))
        estimated_optimal_h = eps**(1/(order+1)) * xc

        initial_step = estimated_optimal_h * step_factor**(0.5*maxiter)
        initial_step = np.minimum(initial_step, 2*max_dx/order)

        def vectorized_func(xi: NDArray[floating]) -> NDArray[floating]:
            return np.apply_along_axis(lambda xx: func(cast("Array1D[floating]", xx.copy())), 0, xi)

        result = scipy.differentiate.jacobian(
            vectorized_func,
            x,
            initial_step=initial_step,
            step_direction=step_direction,
            order=order,
            step_factor=step_factor,
            maxiter=maxiter,
            tolerances={"rtol": rel_tol, "atol": abs_tol},
        )
        if not result.success.all():
            message = "\n    ".join(
                [
                    "numerical differentiation was not converged:",
                    *(
                        f"element {index}: status={result.status[index]:d}, "
                        f"error={result.error[index]:e}"
                        for index in np.ndindex(result.success.shape)
                        if not result.success[index]
                    ),
                ],
            )
            raise RuntimeError(message)

        return cast("Array2D[floating]", result.df)

    return inner
