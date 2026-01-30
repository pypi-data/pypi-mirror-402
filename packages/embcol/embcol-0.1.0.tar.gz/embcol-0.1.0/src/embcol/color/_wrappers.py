"""Utilities wrapping low-level functions."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, cast, overload

import numpy as np

from .._checking import check_array, check_size
from .._exception import expr, invalid_n_dimensions_error
from ._conversions import (
    linear_srgb_to_oklab,
    linear_srgb_to_srgb,
    oklab_to_linear_srgb,
    oklch_chroma,
    oklch_hue,
    oklch_to_oklab as oklch_to_oklab_,
    srgb_to_linear_srgb,
)
from ._difference import pairwise_sq_color_diffs
from ._mapping import gamut_map as gamut_map_

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from numpy import float64, floating
    from numpy.typing import NDArray

    from ..typing import Array1D, Array2D, ArrayLike1D, ArrayLike2D, SupportsArray

__all__ = [
    "gamut_map",
    "oklab_to_oklch",
    "oklab_to_srgb",
    "oklch_to_oklab",
    "pairwise_color_diffs",
    "srgb_to_oklab",
]

_FloatingT = TypeVar("_FloatingT", bound=np.floating)


@overload
def srgb_to_oklab(srgb: Sequence[float], *, copy: bool | None = ...) -> Array1D[float64]: ...
@overload
def srgb_to_oklab(
    srgb: SupportsArray[tuple[int], _FloatingT],
    *,
    copy: bool | None = ...,
) -> Array1D[_FloatingT]:
    ...
@overload
def srgb_to_oklab(
    srgb: ArrayLike1D[float, _FloatingT],
    *,
    copy: bool | None = ...,
) -> Array1D[float64 | _FloatingT]:
    ...
@overload
def srgb_to_oklab(srgb: Sequence[Sequence[float]], *, copy: bool | None = ...) -> Array2D[float64]:
    ...
@overload
def srgb_to_oklab(
    srgb: (
        Sequence[SupportsArray[tuple[int], _FloatingT]]
        | SupportsArray[tuple[int, int], _FloatingT]
    ),
    *,
    copy: bool | None = ...,
) -> Array2D[_FloatingT]:
    ...
@overload
def srgb_to_oklab(
    srgb: ArrayLike2D[float, _FloatingT],
    *,
    copy: bool | None = ...,
) -> Array2D[float64 | _FloatingT]:
    ...

def srgb_to_oklab(
    srgb: ArrayLike1D[float, _FloatingT] | ArrayLike2D[float, _FloatingT],
    *,
    copy: bool | None = True,
) -> Array1D[float64 | _FloatingT] | Array2D[float64 | _FloatingT]:
    r"""Convert sRGB colors to Oklab colors.

    Parameters
    ----------
    srgb : array-like of float
        sRGB colors. The shape must be ``(3,)`` or ``(N, 3)``, where ``N`` is the number of colors.
        The gamut of the sRGB color space is [0, 1]\ :sup:`3`. A given object can be overwritten
        with an output if `copy` is not ``True``.
    copy : bool or None, optional
        If ``True`` is given, `srgb` is always copied. If ``None`` is given, `srgb` is copied only
        if needed. If ``False`` is given, `srgb` is not copied and an error is raised if copying is
        needed.

    Returns
    -------
    numpy.ndarray of float
        Oklab colors. The shape is the same as `srgb`.
    """
    srgb = np.asarray(srgb, copy=copy)
    _check_color(srgb, target=expr("srgb"))
    srgb = cast("Array1D[float64 | _FloatingT] | Array2D[float64 | _FloatingT]", srgb)

    return _convert(srgb, [srgb_to_linear_srgb, linear_srgb_to_oklab])


@overload
def oklab_to_srgb(oklab: Sequence[float], *, copy: bool | None = ...) -> Array1D[float64]: ...
@overload
def oklab_to_srgb(
    oklab: SupportsArray[tuple[int], _FloatingT],
    *,
    copy: bool | None = ...,
) -> Array1D[_FloatingT]:
    ...
@overload
def oklab_to_srgb(
    oklab: ArrayLike1D[float, _FloatingT],
    *,
    copy: bool | None = ...,
) -> Array1D[float64 | _FloatingT]:
    ...
@overload
def oklab_to_srgb(oklab: Sequence[Sequence[float]], *, copy: bool | None = ...) -> Array2D[float64]:
    ...
@overload
def oklab_to_srgb(
    oklab: (
        Sequence[SupportsArray[tuple[int], _FloatingT]]
        | SupportsArray[tuple[int, int], _FloatingT]
    ),
    *,
    copy: bool | None = ...,
) -> Array2D[_FloatingT]:
    ...
@overload
def oklab_to_srgb(
    oklab: ArrayLike2D[float, _FloatingT],
    *,
    copy: bool | None = ...,
) -> Array2D[float64 | _FloatingT]:
    ...

def oklab_to_srgb(
    oklab: ArrayLike1D[float, _FloatingT] | ArrayLike2D[float, _FloatingT],
    *,
    copy: bool | None = True,
) -> Array1D[float64 | _FloatingT] | Array2D[float64 | _FloatingT]:
    r"""Convert Oklab colors to sRGB colors.

    Parameters
    ----------
    oklab : array-like of float
        Oklab colors. The shape must be ``(3,)`` or ``(N, 3)``, where ``N`` is the number of colors.
        A given object can be overwritten with an output if `copy` is not ``True``.
    copy : bool or None, optional
        If ``True`` is given, `oklab` is always copied. If ``None`` is given, `oklab` is copied only
        if needed. If ``False`` is given, `oklab` is not copied and an error is raised if copying is
        needed.

    Returns
    -------
    numpy.ndarray of float
        sRGB colors. The shape is the same as `oklab`. The gamut of the sRGB color space is
        [0, 1]\ :sup:`3`.
    """
    oklab = np.asarray(oklab, copy=copy)
    _check_color(oklab, target=expr("oklab"))
    oklab = cast("Array1D[float64 | _FloatingT] | Array2D[float64 | _FloatingT]", oklab)

    return _convert(oklab, [oklab_to_linear_srgb, linear_srgb_to_srgb])


@overload
def oklab_to_oklch(oklab: Sequence[float], *, copy: bool | None = ...) -> Array1D[float64]: ...
@overload
def oklab_to_oklch(
    oklab: SupportsArray[tuple[int], _FloatingT],
    *,
    copy: bool | None = ...,
) -> Array1D[_FloatingT]:
    ...
@overload
def oklab_to_oklch(
    oklab: ArrayLike1D[float, _FloatingT],
    *,
    copy: bool | None = ...,
) -> Array1D[float64 | _FloatingT]:
    ...
@overload
def oklab_to_oklch(
    oklab: Sequence[Sequence[float]],
    *,
    copy: bool | None = ...,
) -> Array2D[float64]:
    ...
@overload
def oklab_to_oklch(
    oklab: (
        Sequence[SupportsArray[tuple[int], _FloatingT]]
        | SupportsArray[tuple[int, int], _FloatingT]
    ),
    *,
    copy: bool | None = ...,
) -> Array2D[_FloatingT]:
    ...
@overload
def oklab_to_oklch(
    oklab: ArrayLike2D[float, _FloatingT],
    *,
    copy: bool | None = ...,
) -> Array2D[float64 | _FloatingT]:
    ...

def oklab_to_oklch(
    oklab: ArrayLike1D[float, _FloatingT] | ArrayLike2D[float, _FloatingT],
    *,
    copy: bool | None = True,
) -> Array1D[float64 | _FloatingT] | Array2D[float64 | _FloatingT]:
    """Convert Oklab colors to Oklch colors.

    Parameters
    ----------
    oklab : array-like of float
        Oklab colors. The shape must be ``(3,)`` or ``(N, 3)``, where ``N`` is the number of colors.
        A given object can be overwritten with an output if `copy` is not ``True``.
    copy : bool or None, optional
        If ``True`` is given, `oklab` is always copied. If ``None`` is given, `oklab` is copied only
        if needed. If ``False`` is given, `oklab` is not copied and an error is raised if copying is
        needed.

    Returns
    -------
    numpy.ndarray of float
        Oklch colors. The shape is the same as `oklab`.
    """
    oklab = np.asarray(oklab, copy=copy)
    _check_color(oklab, target=expr("oklab"))
    oklab = cast("Array1D[float64 | _FloatingT] | Array2D[float64 | _FloatingT]", oklab)

    def func(oklabs: Array2D[float64 | _FloatingT]) -> Array2D[float64 | _FloatingT]:
        values = oklabs
        values[:, 1], values[:, 2] = oklch_chroma(oklabs), oklch_hue(oklabs)
        return values

    return _convert(oklab, [func])


@overload
def oklch_to_oklab(oklch: Sequence[float], *, copy: bool | None = ...) -> Array1D[float64]: ...
@overload
def oklch_to_oklab(
    oklch: SupportsArray[tuple[int], _FloatingT],
    *,
    copy: bool | None = ...,
) -> Array1D[_FloatingT]:
    ...
@overload
def oklch_to_oklab(
    oklch: ArrayLike1D[float, _FloatingT],
    *,
    copy: bool | None = ...,
) -> Array1D[float64 | _FloatingT]:
    ...
@overload
def oklch_to_oklab(
    oklch: Sequence[Sequence[float]],
    *,
    copy: bool | None = ...,
) -> Array2D[float64]:
    ...
@overload
def oklch_to_oklab(
    oklch: (
        Sequence[SupportsArray[tuple[int], _FloatingT]]
        | SupportsArray[tuple[int, int], _FloatingT]
    ),
    *,
    copy: bool | None = ...,
) -> Array2D[_FloatingT]:
    ...
@overload
def oklch_to_oklab(
    oklch: ArrayLike2D[float, _FloatingT],
    *,
    copy: bool | None = ...,
) -> Array2D[float64 | _FloatingT]:
    ...

def oklch_to_oklab(
    oklch: ArrayLike1D[float, _FloatingT] | ArrayLike2D[float, _FloatingT],
    *,
    copy: bool | None = True,
) -> Array1D[float64 | _FloatingT] | Array2D[float64 | _FloatingT]:
    """Convert Oklch colors to Oklab colors.

    Parameters
    ----------
    oklch : array-like of float
        Oklch colors. The shape must be ``(3,)`` or ``(N, 3)``, where ``N`` is the number of colors.
        A given object can be overwritten with an output if `copy` is not ``True``.
    copy : bool or None, optional
        If ``True`` is given, `oklch` is always copied. If ``None`` is given, `oklch` is copied only
        if needed. If ``False`` is given, `oklch` is not copied and an error is raised if copying is
        needed.

    Returns
    -------
    numpy.ndarray of float
        Oklab colors. The shape is the same as `oklch`.
    """
    oklch = np.asarray(oklch, copy=copy)
    _check_color(oklch, target=expr("oklch"))
    oklch = cast("Array1D[float64 | _FloatingT] | Array2D[float64 | _FloatingT]", oklch)

    return _convert(oklch, [oklch_to_oklab_])


@overload
def gamut_map(oklab: Sequence[float], *, copy: bool | None = ...) -> Array1D[float64]: ...
@overload
def gamut_map(
    oklab: SupportsArray[tuple[int], _FloatingT],
    *,
    copy: bool | None = ...,
) -> Array1D[_FloatingT]:
    ...
@overload
def gamut_map(
    oklab: ArrayLike1D[float, _FloatingT],
    *,
    copy: bool | None = ...,
) -> Array1D[float64 | _FloatingT]:
    ...
@overload
def gamut_map(oklab: Sequence[Sequence[float]], *, copy: bool | None = ...) -> Array2D[float64]: ...
@overload
def gamut_map(
    oklab: (
        Sequence[SupportsArray[tuple[int], _FloatingT]]
        | SupportsArray[tuple[int, int], _FloatingT]
    ),
    *,
    copy: bool | None = ...,
) -> Array2D[_FloatingT]:
    ...
@overload
def gamut_map(
    oklab: ArrayLike2D[float, _FloatingT],
    *,
    copy: bool | None = ...,
) -> Array2D[float64 | _FloatingT]:
    ...

def gamut_map(
    oklab: ArrayLike1D[float, _FloatingT] | ArrayLike2D[float, _FloatingT],
    *,
    copy: bool | None = True,
) -> Array1D[float64 | _FloatingT] | Array2D[float64 | _FloatingT]:
    """Map Oklab colors into the gamut of the sRGB color space.

    Parameters
    ----------
    oklab : array-like of float
        Oklab colors to be mapped. The shape must be ``(3,)`` or ``(N, 3)``, where ``N`` is
        the number of colors. A given object can be overwritten with an output if `copy` is not
        ``True``.
    copy : bool or None, optional
        If ``True`` is given, `oklab` is always copied. If ``None`` is given, `oklab` is copied only
        if needed. If ``False`` is given, `oklab` is not copied and an error is raised if copying is
        needed.

    Returns
    -------
    numpy.ndarray of float
        Mapped Oklab colors. The shape is the same as `oklab`.
    """
    oklab = np.asarray(oklab, copy=copy)
    _check_color(oklab, target=expr("oklab"))
    oklab = cast("Array1D[float64 | _FloatingT] | Array2D[float64 | _FloatingT]", oklab)

    oklab[...] = _convert(oklab, [gamut_map_])

    return oklab


@overload
def pairwise_color_diffs(
    oklabs: Sequence[Sequence[float]],
    *,
    squared: bool = ...,
) -> Array1D[float64]:
    ...
@overload
def pairwise_color_diffs(
    oklabs: (
        Sequence[SupportsArray[tuple[int], _FloatingT]]
        | SupportsArray[tuple[int, int], _FloatingT]
    ),
    *,
    squared: bool = ...,
) -> Array1D[_FloatingT]:
    ...
@overload
def pairwise_color_diffs(
    oklabs: ArrayLike2D[float, _FloatingT],
    *,
    squared: bool = ...,
) -> Array1D[float64 | _FloatingT]:
    ...

def pairwise_color_diffs(
    oklabs: ArrayLike2D[float, _FloatingT],
    *,
    squared: bool = False,
) -> Array1D[float64 | _FloatingT]:
    """Measure color differences among a set of colors.

    Parameters
    ----------
    oklabs : array-like of float
        Set of Oklab colors. The shape must be ``(N, 3)``, where ``N`` is the number of colors.
    squared : bool, optional
        If ``True`` is given, squared values are returned.

    Returns
    -------
    numpy.ndarray of float
        Color differences. If `squared` is ``True``, values are squared color differences instead.
        The shape is ``((N-1)*N//2,)``: only off-diagonal elements above the main diagonal of
        a distance matrix is returned. Items are in row-major order.
    """
    oklabs = np.asarray(oklabs)
    check_array(oklabs, shape=(-1, 3), dtypes=[np.floating], target=expr("oklabs"))
    oklabs = cast("Array2D[float64 | _FloatingT]", oklabs)

    sq_color_diffs = pairwise_sq_color_diffs(oklabs)

    if squared:
        return sq_color_diffs
    return cast("Array1D[_FloatingT]", np.sqrt(sq_color_diffs))


def _check_color(color: NDArray[floating], *, target: str = "color") -> None:
    """Check if an object is a valid color array.

    Parameters
    ----------
    color : numpy.ndarray
        Target object to be checked.
    target : str, optional
        Explanation about a target object.

    Raises
    ------
    ValueError
        If the shape is not valid.
    TypeError
        If the data type is not valid.
    """
    match color.ndim:
        case 1:
            check_size(color, lower_bound=3, upper_bound=3, target=f"1-dimensional {target}")
        case 2:
            check_array(color, shape=(-1, 3), target=f"2-dimensional {target}")
        case _:
            raise invalid_n_dimensions_error(color.ndim, [1, 2], target=target)

    check_array(color, dtypes=[np.floating], target=target)


@overload
def _convert(
    color: Array1D[_FloatingT],
    funcs: Sequence[Callable[[Array2D[_FloatingT]], Array2D[_FloatingT]]],
) -> Array1D[_FloatingT]:
    ...
@overload
def _convert(
    color: Array2D[_FloatingT],
    funcs: Sequence[Callable[[Array2D[_FloatingT]], Array2D[_FloatingT]]],
) -> Array2D[_FloatingT]:
    ...
@overload
def _convert(
    color: Array1D[_FloatingT] | Array2D[_FloatingT],
    funcs: Sequence[Callable[[Array2D[_FloatingT]], Array2D[_FloatingT]]],
) -> Array1D[_FloatingT] | Array2D[_FloatingT]:
    ...

def _convert(
    color: Array1D[_FloatingT] | Array2D[_FloatingT],
    funcs: Sequence[Callable[[Array2D[_FloatingT]], Array2D[_FloatingT]]],
) -> Array1D[_FloatingT] | Array2D[_FloatingT]:
    """Apply conversion functions sequentially.

    Parameters
    ----------
    color : numpy.ndarray of float
        Color array to be converted. The shape must be ``(3,)`` or ``(N, 3)``, where ``N`` is
        the number of colors. A given object is not copied before conversions.
    funcs : sequence of callable
        Conversion functions. The first function is applied first.

    Returns
    -------
    numpy.ndarray of float
        Color array after conversions. The shape is the same as `color`.
    """
    out = color.reshape((-1, 3))
    for func in funcs:
        out = func(out)

    if color.ndim == 1:
        return out.reshape(3)
    return out
