"""Color difference."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, cast, overload

import numpy as np
import scipy

if TYPE_CHECKING:
    from typing import Literal

    from numpy import floating

    from ..typing import Array1D, Array2D, Array3D, Array5D

__all__ = ["pairwise_sq_color_diffs", "sq_color_diffs"]

_FloatingT = TypeVar("_FloatingT", bound=np.floating)


def sq_color_diffs(oklab1s: Array2D[floating], oklab2s: Array2D[floating]) -> Array1D[floating]:
    """Measure squared color differences between two sets of colors.

    Parameters
    ----------
    oklab1s : numpy.ndarray of float
        First set of Oklab colors. The shape must be ``(N, 3)``, where ``N`` is the number of pairs.
    oklab2s : numpy.ndarray of float
        Second set of Oklab colors. The shape must be ``(N, 3)``, where ``N`` is the number of
        pairs.

    Returns
    -------
    numpy.ndarray of float
        Squared color differences. The shape is ``(N,)``.
    """
    return cast("Array1D[floating]", ((oklab1s-oklab2s)**2).sum(axis=1))


@overload
def pairwise_sq_color_diffs(
    oklabs: Array2D[_FloatingT],
    *,
    return_jacobian: Literal[False] = ...,
    return_hessian: Literal[False] = ...,
) -> Array1D[_FloatingT]:
    ...
@overload
def pairwise_sq_color_diffs(
    oklabs: Array2D[_FloatingT],
    *,
    return_jacobian: Literal[True],
    return_hessian: Literal[False] = ...,
) -> tuple[Array1D[_FloatingT], Array3D[_FloatingT]]:
    ...
@overload
def pairwise_sq_color_diffs(
    oklabs: Array2D[_FloatingT],
    *,
    return_jacobian: Literal[False] = ...,
    return_hessian: Literal[True],
) -> tuple[Array1D[_FloatingT], Array5D[_FloatingT]]:
    ...
@overload
def pairwise_sq_color_diffs(
    oklabs: Array2D[_FloatingT],
    *,
    return_jacobian: Literal[True],
    return_hessian: Literal[True],
) -> tuple[Array1D[_FloatingT], Array3D[_FloatingT], Array5D[_FloatingT]]:
    ...
@overload
def pairwise_sq_color_diffs(
    oklabs: Array2D[_FloatingT],
    *,
    return_jacobian: bool,
    return_hessian: bool,
) -> (
    Array1D[_FloatingT]
    | tuple[Array1D[_FloatingT], Array3D[_FloatingT]]
    | tuple[Array1D[_FloatingT], Array5D[_FloatingT]]
    | tuple[Array1D[_FloatingT], Array3D[_FloatingT], Array5D[_FloatingT]]
):
    ...

def pairwise_sq_color_diffs(
    oklabs: Array2D[_FloatingT],
    *,
    return_jacobian: bool = False,
    return_hessian: bool = False,
) -> (
    Array1D[_FloatingT]
    | tuple[Array1D[_FloatingT], Array3D[_FloatingT]]
    | tuple[Array1D[_FloatingT], Array5D[_FloatingT]]
    | tuple[Array1D[_FloatingT], Array3D[_FloatingT], Array5D[_FloatingT]]
):
    """Measure squared color differences among a set of colors.

    Parameters
    ----------
    oklabs : numpy.ndarray of float
        Set of Oklab colors. The shape must be ``(N, 3)``, where ``N`` is the number of colors.
    return_jacobian : bool, optional
        If ``True`` is given, an array of Jacobian matrices is also returned.
    return_hessian : bool, optional
        If ``True`` is given, an array of Hessian matrices is also returned.

    Returns
    -------
    values : numpy.ndarray of float
        Squared color differences. The shape is ``((N-1)*N//2,)``: only off-diagonal elements above
        the main diagonal of a squared distance matrix is returned in row-major order.
    jacobians : numpy.ndarray of float
        Jacobian matrices. Returned only if `return_jacobian` is ``True``. The shape is
        ``(N, 2, 3)``. ``jacobians[ij, 0, k]`` is a derivative of a squared color difference between
        the ``i``th and ``j``th colors with respect to the ``k``th Oklab component of the ``i``th
        color, where ``ij`` is an index of a pair of the ``i``th and ``j``th colors and ``i`` <
        ``j``. Similarly, ``jacobians[ij, 1, k]`` is a derivative with respect to the ``k``th Oklab
        component of the ``j``th color.
    hessians : numpy.ndarray of float
        Hessian matrices. Returned only if `return_hessian` is ``True``. The shape is
        ``(N, 2, 3, 2, 3)``. ``hessians[ij, 0, k1, 0, k2]`` is a second derivative of a squared
        color difference between the ``i``th and ``j``th colors with respect to the ``k1``th Oklab
        component of the ``i``th color and the ``k2``th Oklab component of the ``i``th color, where
        ``ij`` is an index of a pair of the ``i``th and ``j``th colors and ``i`` < ``j``. Similarly,
        ``hessians[ij, 0, k1, 1, k2]`` is a derivative with respect to the ``k1``th Oklab component
        of the ``i``th color and the ``k2``th Oklab component of the ``j``th color,
        ``hessians[ij, 1, k1, 0, k2]`` is a derivative with respect to the ``k1``th Oklab component
        of the ``j``th color and the ``k2``th Oklab component of the ``i``th color, and
        ``hessians[ij, 1, k1, 1, k2]`` is a derivative with respect to the ``k1``th Oklab component
        of the ``j``th color and the ``k2``th Oklab component of the ``j``th color.
    """
    values = scipy.spatial.distance.pdist(oklabs, metric="sqeuclidean")
    values = values.astype(oklabs.dtype, copy=False)

    if return_jacobian:
        jacobians = np.empty((len(values), 2, 3), dtype=oklabs.dtype)
        for i in range(len(oklabs)):
            pair_indices = i*(2*len(oklabs)-i-1)//2 + np.arange(len(oklabs)-i-1)
            jacobians[pair_indices, 0, :] = 2 * (oklabs[i, :]-oklabs[i+1:, :])
        jacobians[:, 1, :] = -jacobians[:, 0, :]

    if return_hessian:
        hessians = np.zeros((len(values), 2, 3, 2, 3), dtype=oklabs.dtype)
        hessians[:, 0, np.arange(3), 0, np.arange(3)] = 2
        hessians[:, 0, np.arange(3), 1, np.arange(3)] = -2
        hessians[:, 1, np.arange(3), 0, np.arange(3)] = -2
        hessians[:, 1, np.arange(3), 1, np.arange(3)] = 2

    if not return_hessian:
        if not return_jacobian:
            return values
        return values, jacobians
    if not return_jacobian:
        return values, hessians
    return values, jacobians, hessians
