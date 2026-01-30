"""Gamut mapping."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, cast

import numpy as np

from ._conversions import (
    linear_srgb_to_oklab,
    oklab_to_linear_srgb,
    oklch_chroma,
    oklch_hue,
    oklch_to_oklab,
)
from ._difference import sq_color_diffs

if TYPE_CHECKING:
    from numpy import bool_

    from ..typing import Array1D, Array2D

__all__ = ["gamut_map"]

_FloatingT = TypeVar("_FloatingT", bound=np.floating)


def gamut_map(oklabs: Array2D[_FloatingT]) -> Array2D[_FloatingT]:  # noqa: PLR0915
    """Map Oklab colors into the gamut of the sRGB color space.

    Parameters
    ----------
    oklabs : numpy.ndarray of float
        Oklab colors to be mapped. The shape must be ``(N, 3)``, where ``N`` is the number of
        colors. A given object is overwritten with an output.

    Returns
    -------
    numpy.ndarray of float
        Oklab colors after the gamut mapping. The shape is ``(N, 3)``.
    """
    jnd = 0.02
    eps = 1e-4

    mapped_oklabs = np.empty_like(oklabs)
    is_done: Array1D[bool_] = np.zeros(len(oklabs), dtype=np.bool_)

    oklchs = np.empty_like(oklabs)
    linear_srgbs = np.empty_like(oklabs)
    clipped_oklabs = np.empty_like(oklabs)

    lower_chromas = np.empty(len(oklabs), dtype=oklabs.dtype)
    upper_chromas = np.empty(len(oklabs), dtype=oklabs.dtype)
    is_in_gamut_lower = np.empty(len(oklabs), dtype=np.bool_)

    # map colors whose lightness < 0 to black
    mask = oklabs[:, 0] < 0.0
    mapped_oklabs[mask, :] = 0.0
    is_done[mask] = True

    # map colors whose lightness > 1 to white
    mask = 1.0 < oklabs[:, 0]
    mapped_oklabs[mask, :] = [1.0, 0.0, 0.0]
    is_done[mask] = True

    # don't map colors if they are already in gamut
    mask = ~is_done
    linear_srgbs[mask, :] = oklab_to_linear_srgb(
        cast("Array2D[_FloatingT]", oklabs[mask, :]).copy(),
    )
    mask[mask] = ((0.0 <= linear_srgbs[mask, :])&(linear_srgbs[mask, :] <= 1.0)).all(axis=1)
    mapped_oklabs[mask, :] = oklabs[mask, :]
    is_done[mask] = True

    # don't map colors if clipped colors are close to the originals
    mask = ~is_done
    clipped_oklabs[mask, :] = linear_srgb_to_oklab(
        cast("Array2D[_FloatingT]", np.clip(linear_srgbs[mask, :].copy(), 0.0, 1.0)),
    )
    color_diffs = np.sqrt(
        sq_color_diffs(
            cast("Array2D[_FloatingT]", oklabs[mask, :]),
            cast("Array2D[_FloatingT]", clipped_oklabs[mask, :]),
        ),
    )
    mask[mask] = color_diffs < jnd
    mapped_oklabs[mask, :] = clipped_oklabs[mask, :]
    is_done[mask] = True

    oklchs[~is_done, :] = np.column_stack(
        (
            oklabs[~is_done, 0],
            oklch_chroma(cast("Array2D[_FloatingT]", oklabs[~is_done, :])),
            oklch_hue(cast("Array2D[_FloatingT]", oklabs[~is_done, :])),
        ),
    )

    lower_chromas[~is_done] = 0.0
    upper_chromas[~is_done] = oklchs[~is_done, 1]
    is_in_gamut_lower[~is_done] = True

    # binary search
    while not is_done.all():
        # whether chromas are converged
        mask = ~is_done
        mask[mask] = upper_chromas[mask]-lower_chromas[mask] <= eps
        mapped_oklabs[mask, :] = clipped_oklabs[mask, :]
        is_done[mask] = True

        oklchs[~is_done, 1] = 0.5 * (lower_chromas[~is_done]+upper_chromas[~is_done])
        oklabs[~is_done, :] = oklch_to_oklab(
            cast("Array2D[_FloatingT]", oklchs[~is_done, :]).copy(),
        )
        linear_srgbs[~is_done, :] = oklab_to_linear_srgb(
            cast("Array2D[_FloatingT]", oklabs[~is_done, :]).copy(),
        )

        # whether colors are in gamut
        is_in_gamut = ~is_done & is_in_gamut_lower
        is_in_gamut[is_in_gamut] = (
            ((0.0 <= linear_srgbs[is_in_gamut, :])&(linear_srgbs[is_in_gamut, :] <= 1.0))
            .all(axis=1)
        )
        lower_chromas[is_in_gamut] = oklchs[is_in_gamut, 1]

        m = cast("Array1D[bool_]", ~is_done&~is_in_gamut)
        clipped_oklabs[m, :] = linear_srgb_to_oklab(
            cast("Array2D[_FloatingT]", np.clip(linear_srgbs[m, :], 0.0, 1.0)),
        )
        color_diffs = np.sqrt(
            sq_color_diffs(
                cast("Array2D[_FloatingT]", oklabs[m, :]),
                cast("Array2D[_FloatingT]", clipped_oklabs[m, :]),
            ),
        )
        m1 = color_diffs < jnd
        m2 = jnd-color_diffs < eps

        # whether color differences to clipped colors are almost JND
        mask = m.copy()
        mask[m] = m1 & m2
        mapped_oklabs[mask, :] = clipped_oklabs[mask, :]
        is_done[mask] = True

        # whether clipped colors are too close to the original
        mask = m.copy()
        mask[mask] = m1 & ~m2
        is_in_gamut_lower[mask] = False
        lower_chromas[mask] = oklchs[mask, 1]

        # whether clipped colors are away from the original
        mask = m.copy()
        mask[mask] = ~m1
        upper_chromas[mask] = oklchs[mask, 1]

    return mapped_oklabs
