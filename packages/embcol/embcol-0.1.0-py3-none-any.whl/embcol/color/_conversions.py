"""Color conversions."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, cast, overload

import numpy as np

if TYPE_CHECKING:
    from typing import Literal

    from ..typing import Array1D, Array2D, Array3D, Array4D

__all__ = [
    "linear_srgb_to_oklab",
    "linear_srgb_to_srgb",
    "oklab_to_linear_srgb",
    "oklch_chroma",
    "oklch_hue",
    "oklch_to_oklab",
    "srgb_to_linear_srgb",
]

_FloatingT = TypeVar("_FloatingT", bound=np.floating)


def srgb_to_linear_srgb(srgbs: Array2D[_FloatingT]) -> Array2D[_FloatingT]:
    r"""Convert sRGB colors to linear sRGB colors.

    Parameters
    ----------
    srgbs : numpy.ndarray of float
        sRGB colors. The shape must be ``(N, 3)``, where ``N`` is the number of colors. The gamut of
        the sRGB color space is [0, 1]\ :sup:`3`. A given object is overwritten with an output.

    Returns
    -------
    numpy.ndarray of float
        Linear sRGB colors. The shape is ``(N, 3)``. The gamut of the linear sRGB color space is
        [0, 1]\ :sup:`3`.
    """
    values = srgbs

    a = abs(values)
    mask = a <= 0.04045
    values[mask] /= 12.92
    values[~mask] = np.sign(values[~mask]) * ((a[~mask]+0.055)/1.055)**2.4

    return values


def linear_srgb_to_srgb(linear_srgbs: Array2D[_FloatingT]) -> Array2D[_FloatingT]:
    r"""Convert linear sRGB colors to sRGB colors.

    Parameters
    ----------
    linear_srgbs : numpy.ndarray of float
        Linear sRGB colors. The shape must be ``(N, 3)``, where ``N`` is the number of colors.
        The gamut of the linear sRGB color space is [0, 1]\ :sup:`3`. A given object is overwritten
        with an output.

    Returns
    -------
    numpy.ndarray of float
        sRGB colors. The shape is ``(N, 3)``. The gamut of the sRGB color space is [0, 1]\ :sup:`3`.
    """
    values = linear_srgbs

    a = abs(values)
    mask = a <= 0.0031308
    values[mask] *= 12.92
    values[~mask] = np.sign(values[~mask]) * (1.055*a[~mask]**(1/2.4)-0.055)

    return values


def linear_srgb_to_oklab(linear_srgbs: Array2D[_FloatingT]) -> Array2D[_FloatingT]:
    r"""Convert linear sRGB colors to Oklab colors.

    Parameters
    ----------
    linear_srgbs : numpy.ndarray of float
        Linear sRGB colors. The shape must be ``(N, 3)``, where ``N`` is the number of colors.
        The gamut of the linear sRGB color space is [0, 1]\ :sup:`3`. A given object is overwritten
        with an output.

    Returns
    -------
    numpy.ndarray of float
        Oklab colors. The shape is ``(N, 3)``.
    """
    values = linear_srgbs

    # to LMS
    values @= [
        [0.4122214708, 0.2119034982, 0.0883024619],
        [0.5363325363, 0.6806995451, 0.2817188376],
        [0.0514459929, 0.1073969566, 0.6299787005],
    ]
    np.cbrt(values, out=values)

    # to Oklab
    values @= [
        [0.2104542553, 1.9779984951, 0.0259040371],
        [0.7936177850, -2.4285922050, 0.7827717662],
        [-0.0040720468, 0.4505937099, -0.8086757660],
    ]

    return values


@overload
def oklab_to_linear_srgb(
    oklabs: Array2D[_FloatingT],
    *,
    return_jacobian: Literal[False] = ...,
    return_hessian: Literal[False] = ...,
) -> Array2D[_FloatingT]:
    ...
@overload
def oklab_to_linear_srgb(
    oklabs: Array2D[_FloatingT],
    *,
    return_jacobian: Literal[True],
    return_hessian: Literal[False] = ...,
) -> tuple[Array2D[_FloatingT], Array3D[_FloatingT]]:
    ...
@overload
def oklab_to_linear_srgb(
    oklabs: Array2D[_FloatingT],
    *,
    return_jacobian: Literal[False] = ...,
    return_hessian: Literal[True],
) -> tuple[Array2D[_FloatingT], Array4D[_FloatingT]]:
    ...
@overload
def oklab_to_linear_srgb(
    oklabs: Array2D[_FloatingT],
    *,
    return_jacobian: Literal[True],
    return_hessian: Literal[True],
) -> tuple[Array2D[_FloatingT], Array3D[_FloatingT], Array4D[_FloatingT]]:
    ...
@overload
def oklab_to_linear_srgb(
    oklabs: Array2D[_FloatingT],
    *,
    return_jacobian: bool,
    return_hessian: bool,
) -> (
    Array2D[_FloatingT]
    | tuple[Array2D[_FloatingT], Array3D[_FloatingT]]
    | tuple[Array2D[_FloatingT], Array4D[_FloatingT]]
    | tuple[Array2D[_FloatingT], Array3D[_FloatingT], Array4D[_FloatingT]]
):
    ...

def oklab_to_linear_srgb(
    oklabs: Array2D[_FloatingT],
    *,
    return_jacobian: bool = False,
    return_hessian: bool = False,
) -> (
    Array2D[_FloatingT]
    | tuple[Array2D[_FloatingT], Array3D[_FloatingT]]
    | tuple[Array2D[_FloatingT], Array4D[_FloatingT]]
    | tuple[Array2D[_FloatingT], Array3D[_FloatingT], Array4D[_FloatingT]]
):
    r"""Convert Oklab colors to linear sRGB colors.

    Parameters
    ----------
    oklabs : numpy.ndarray of float
        Oklab colors. The shape must be ``(N, 3)``, where ``N`` is the number of colors. A given
        object is overwritten with a `values` output.
    return_jacobian : bool, optional
        If ``True`` is given, an array of Jacobian matrices is also returned.
    return_hessian : bool, optional
        If ``True`` is given, an array of Hessian matrices is also returned.

    Returns
    -------
    values : numpy.ndarray of float
        Linear sRGB colors. The shape is ``(N, 3)``. The gamut of the linear sRGB color space is
        [0, 1]\ :sup:`3`.
    jacobians : numpy.ndarray of float
        Jacobian matrices. Returned only if `return_jacobian` is ``True``. The shape is
        ``(N, 3, 3)``. ``jacobians[i, j, k]`` is a derivative of the ``j``th linear sRGB component
        with respect to the ``k``th Oklab component about the ``i``th color.
    hessians : numpy.ndarray of float
        Hessian matrices. Returned only if `return_hessian` is ``True``. The shape is
        ``(N, 3, 3, 3)``. ``hessians[i, j, k1, k2]`` is a second derivative of the ``j``th linear
        sRGB component with respect to the ``k1``th and ``k2``th Oklab components about the ``i``th
        color.
    """
    values = oklabs

    # to LMS
    m = np.array(
        [
            [1.0, 1.0, 1.0],
            [0.3963377774, -0.1055613458, -0.0894841775],
            [0.2158037573, -0.0638541728, -1.2914855480],
        ],
        dtype=oklabs.dtype,
    )
    values @= m
    if return_hessian:
        hessians = cast(
            "Array4D[_FloatingT]",
            (
                6
                * values[:, np.newaxis, np.newaxis, :]
                * m[np.newaxis, :, np.newaxis, :]
                * m[np.newaxis, np.newaxis, :, :]
            ),
        )
    if return_jacobian:
        jacobians = cast("Array3D[_FloatingT]", 3*values[:, np.newaxis, :]**2*m)
    values **= 3

    # to linear sRGB
    m = np.array(
        [
            [4.0767416621, -1.2684380046, -0.0041960863],
            [-3.3077115913, 2.6097574011, -0.7034186147],
            [0.2309699292, -0.3413193965, 1.7076147010],
        ],
        dtype=oklabs.dtype,
    )
    if return_hessian:
        hessians @= m
    if return_jacobian:
        jacobians @= m
    values @= m

    if return_jacobian:
        jacobians = np.swapaxes(jacobians, 1, 2)
    if return_hessian:
        hessians = cast("Array4D[_FloatingT]", np.moveaxis(hessians, 3, 1))

    if not return_hessian:
        if not return_jacobian:
            return values
        return values, jacobians
    if not return_jacobian:
        return values, hessians
    return values, jacobians, hessians


def oklch_chroma(oklabs: Array2D[_FloatingT]) -> Array1D[_FloatingT]:
    """Convert Oklab colors to chromas of Oklch colors.

    Parameters
    ----------
    oklabs : numpy.ndarray of float
        Oklab colors. The shape must be ``(N, 3)``, where ``N`` is the number of colors.

    Returns
    -------
    numpy.ndarray of float
        Chromas of Oklch colors. The shape is ``(N,)``.
    """
    return cast("Array1D[_FloatingT]", np.linalg.norm(oklabs[:, [1, 2]], axis=1))


@overload
def oklch_hue(
    oklabs: Array2D[_FloatingT],
    *,
    return_jacobian: Literal[False] = ...,
    return_hessian: Literal[False] = ...,
) -> Array1D[_FloatingT]:
    ...
@overload
def oklch_hue(
    oklabs: Array2D[_FloatingT],
    *,
    return_jacobian: Literal[True],
    return_hessian: Literal[False] = ...,
) -> tuple[Array1D[_FloatingT], Array2D[_FloatingT]]:
    ...
@overload
def oklch_hue(
    oklabs: Array2D[_FloatingT],
    *,
    return_jacobian: Literal[False] = ...,
    return_hessian: Literal[True],
) -> tuple[Array1D[_FloatingT], Array3D[_FloatingT]]:
    ...
@overload
def oklch_hue(
    oklabs: Array2D[_FloatingT],
    *,
    return_jacobian: Literal[True],
    return_hessian: Literal[True],
) -> tuple[Array1D[_FloatingT], Array2D[_FloatingT], Array3D[_FloatingT]]:
    ...
@overload
def oklch_hue(
    oklabs: Array2D[_FloatingT],
    *,
    return_jacobian: bool,
    return_hessian: bool,
) -> (
    Array1D[_FloatingT]
    | tuple[Array1D[_FloatingT], Array2D[_FloatingT]]
    | tuple[Array1D[_FloatingT], Array3D[_FloatingT]]
    | tuple[Array1D[_FloatingT], Array2D[_FloatingT], Array3D[_FloatingT]]
):
    ...

def oklch_hue(
    oklabs: Array2D[_FloatingT],
    *,
    return_jacobian: bool = False,
    return_hessian: bool = False,
) -> (
    Array1D[_FloatingT]
    | tuple[Array1D[_FloatingT], Array2D[_FloatingT]]
    | tuple[Array1D[_FloatingT], Array3D[_FloatingT]]
    | tuple[Array1D[_FloatingT], Array2D[_FloatingT], Array3D[_FloatingT]]
):
    """Convert Oklab colors to hues of Oklch colors.

    Parameters
    ----------
    oklabs : numpy.ndarray of float
        Oklab colors. The shape must be ``(N, 3)``, where ``N`` is the number of colors.
    return_jacobian : bool, optional
        If ``True`` is given, an array of Jacobian matrices is also returned.
    return_hessian : bool, optional
        If ``True`` is given, an array of Hessian matrices is also returned.

    Returns
    -------
    values : numpy.ndarray of float
        Hues of Oklch colors. The shape is ``(N,)``.
    jacobians : numpy.ndarray of float
        Jacobian matrices. Returned only if `return_jacobian` is ``True``. The shape is ``(N, 3)``.
        ``jacobians[i, k]`` is a derivative of a hue with respect to the ``k``th Oklab component
        about the ``i``th color.
    hessians : numpy.ndarray of float
        Hessian matrices. Returned only if `return_hessian` is ``True``. The shape is ``(N, 3, 3)``.
        ``hessians[i, k1, k2]`` is a second derivative of a hue with respect to the ``k1``th and
        ``k2``th Oklab components about the ``i``th color.
    """
    values: Array1D[_FloatingT] = np.atan2(oklabs[:, 2], oklabs[:, 1])

    if not (return_jacobian or return_hessian):
        return values

    temp = oklabs[:, 1]**2 + oklabs[:, 2]**2

    if return_jacobian:
        mask = temp != 0

        jacobians = np.zeros((len(values), 3), dtype=oklabs.dtype)
        jacobians[mask, 1] = -oklabs[mask, 2] / temp[mask]
        jacobians[mask, 2] = oklabs[mask, 1] / temp[mask]

    if return_hessian:
        mask = temp**2 != 0

        hessians = np.zeros((len(values), 3, 3), dtype=oklabs.dtype)
        hessians[mask, 1, 1] = 2 * oklabs[mask, 1] * oklabs[mask, 2] / temp[mask]**2
        hessians[mask, 1, 2] = (-temp[mask]+2*oklabs[mask, 2]**2) / temp[mask]**2
        hessians[mask, 2, 1] = (temp[mask]-2*oklabs[mask, 1]**2) / temp[mask]**2
        hessians[mask, 2, 2] = -2 * oklabs[mask, 1] * oklabs[mask, 2] / temp[mask]**2

    if not return_hessian:
        return values, jacobians
    if not return_jacobian:
        return values, hessians
    return values, jacobians, hessians


def oklch_to_oklab(oklchs: Array2D[_FloatingT]) -> Array2D[_FloatingT]:
    """Convert Oklch colors to Oklab colors.

    Parameters
    ----------
    oklchs : numpy.ndarray of float
        Oklch colors. The shape must be ``(N, 3)``, where ``N`` is the number of colors. A given
        object is overwritten with an output.

    Returns
    -------
    numpy.ndarray of float
        Oklab colors. The shape is ``(N, 3)``.
    """
    values = oklchs
    values[:, 1], values[:, 2] = (
        values[:, 1]*np.cos(values[:, 2]),
        values[:, 1]*np.sin(values[:, 2]),
    )
    return values
