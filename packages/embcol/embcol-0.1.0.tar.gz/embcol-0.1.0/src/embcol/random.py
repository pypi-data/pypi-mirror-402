"""Random sampling."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast, overload

import numpy as np

from ._checking import check_number, check_number_set, check_type
from ._exception import expr
from .color._conversions import oklab_to_linear_srgb, oklch_hue, oklch_to_oklab
from .problem._problem import Problem

if TYPE_CHECKING:
    from numpy import float64
    from numpy.random import Generator

    from .typing import Array1D, Array2D, RNGLike

__all__ = ["OklchGenerator", "ParamsGenerator"]


class OklchGenerator:
    """Random Oklch color generator.

    Parameters
    ----------
    rng : rng-like, optional
        Random number generator. If nothing is given, a generator is initialized
        nondeterministically.
    """

    _rng: Generator

    def __init__(self, rng: RNGLike = None) -> None:
        rng = np.random.default_rng(rng)

        self._rng = rng

    @overload
    def random(
        self,
        n: None = ...,
        min_lightness: float = ...,
        max_lightness: float = ...,
        min_hue: float = ...,
        max_hue: float = ...,
    ) -> Array1D[float64]:
        ...
    @overload
    def random(
        self,
        n: int,
        min_lightness: float = ...,
        max_lightness: float = ...,
        min_hue: float = ...,
        max_hue: float = ...,
    ) -> Array2D[float64]:
        ...
    @overload
    def random(
        self,
        n: int | None,
        min_lightness: float = ...,
        max_lightness: float = ...,
        min_hue: float = ...,
        max_hue: float = ...,
    ) -> Array1D[float64] | Array2D[float64]:
        ...

    def random(
        self,
        n: int | None = None,
        min_lightness: float = 0.0,
        max_lightness: float = 1.0,
        min_hue: float = -np.pi,
        max_hue: float = np.pi,
    ) -> Array1D[float64] | Array2D[float64]:
        """Generate Oklch colors randomly.

        Parameters
        ----------
        n : int, optional
            Number of generated colors. If nothing is given, one color is generated.
        min_lightness : float, optional
            Lower bound of the lightness component.
        max_lightness : float, optional
            Upper bound of the lightness component.
        min_hue : float, optional
            Lower bound of the hue component.
        max_hue : float, optional
            Upper bound of the hue component.

        Returns
        -------
        numpy.ndarray of float
            Oklch colors. All colors are within the gamut of the sRGB color space. If `n` is given,
            the shape is ``(n, 3)``. Otherwise, the shape is ``(3,)``.
        """
        max_chroma = 0.323

        if n is not None:
            check_number_set(n, "integers", target=expr("n"))
            check_number(n, lower_bound=0, target=expr("n"))
            n = int(n)

        check_number_set(min_lightness, "real_numbers", target=expr("min_lightness"))
        check_number(
            min_lightness,
            lower_bound=0,
            upper_bound=1,
            allow_nan=False,
            target=expr("min_lightness"),
        )
        min_lightness = float(min_lightness)

        check_number_set(max_lightness, "real_numbers", target=expr("max_lightness"))
        check_number(
            max_lightness,
            lower_bound=min_lightness,
            upper_bound=1,
            allow_nan=False,
            target=expr("max_lightness"),
            lower_bound_descr=expr("min_lightness"),
        )
        max_lightness = float(max_lightness)

        check_number_set(min_hue, "real_numbers", target=expr("min_hue"))
        check_number(
            min_hue,
            lower_bound=-float("inf"),
            allow_lower_bound=False,
            upper_bound=float("inf"),
            allow_upper_bound=False,
            allow_nan=False,
            target=expr("min_hue"),
        )
        min_hue = float(min_hue)

        check_number_set(max_hue, "real_numbers", target=expr("max_hue"))
        check_number(
            max_hue,
            lower_bound=min_hue,
            upper_bound=min_hue+2*np.pi,
            allow_nan=False,
            target=expr("max_hue"),
            lower_bound_descr=expr("min_hue"),
            upper_bound_descr=f"{expr('min_hue')} + 2 pi",
        )
        max_hue = float(max_hue)

        shape = (n, 3) if n is not None else (1, 3)

        oklchs = cast(
            "Array2D[float64]",
            self._rng.uniform(
                low=[min_lightness, 0.0, min_hue],
                high=[max_lightness, max_chroma, max_hue],
                size=shape,
            ),
        )
        is_in_gamut = np.zeros(len(oklchs), dtype=np.bool_)
        while True:
            linear_srgbs = oklab_to_linear_srgb(
                oklch_to_oklab(cast("Array2D[float64]", oklchs[~is_in_gamut, :]).copy()),
            )
            is_in_gamut[~is_in_gamut] = ((0.0 <= linear_srgbs)&(linear_srgbs <= 1.0)).all(axis=1)
            if is_in_gamut.all():
                break
            oklchs[~is_in_gamut, 1] = self._rng.uniform(low=0.0, high=oklchs[~is_in_gamut, 1])

        if n is None:
            return cast("Array1D[float64]", oklchs[0, :])
        return oklchs


class ParamsGenerator:
    """Random parameter set generator for an optimization problem..

    Parameters
    ----------
    rng : rng-like, optional
        Random number generator. If nothing is given, a generator is initialized
        nondeterministically.
    """

    _rng: Generator
    _generator: OklchGenerator

    def __init__(self, rng: RNGLike = None) -> None:
        rng = np.random.default_rng(rng)
        generator = OklchGenerator(rng=rng)

        self._rng = rng
        self._generator = generator

    def random(self, problem: Problem) -> Array1D[float64]:
        """Generate a parameter set for an optimization problem.

        Parameters
        ----------
        problem : embcol.problem.Problem
            Optimization problem.

        Returns
        -------
        numpy.ndarray of float
            Parameter set satisfying constraints of a given optimization problem.
        """
        check_type(problem, [Problem], target=expr("problem"))

        oklabs = np.empty((problem.n_samples, 3))

        is_done = np.zeros(problem.n_samples, dtype=np.bool_)
        for i, oklab in problem.fixed.items():
            oklabs[i, :] = oklab
            is_done[i] = True

        for group in problem.hue_groups:
            if (is_fixed := np.isin(group, list(problem.fixed))).any():
                fixed_hues = oklch_hue(
                    cast("Array2D[float64]", oklabs[np.compress(is_fixed, group), :]),
                )

                # add/subtract 2 pi to minimize difference
                fixed_hues[fixed_hues-fixed_hues[0] < -np.pi] += 2 * np.pi
                fixed_hues[np.pi < fixed_hues-fixed_hues[0]] -= 2 * np.pi

                min_hue = fixed_hues.min()
                max_hue = fixed_hues.max()
                indices = [i for i, condition in zip(group, ~is_fixed, strict=True) if condition]
            else:
                min_hue = max_hue = self._rng.uniform(low=-np.pi, high=np.pi)
                indices = list(group)

            oklabs[indices, :] = oklch_to_oklab(
                self._generator.random(
                    n=len(indices),
                    min_lightness=problem.min_lightness,
                    max_lightness=problem.max_lightness,
                    min_hue=min_hue,
                    max_hue=max_hue,
                ),
            )
            is_done[indices] = True

        oklabs[~is_done, :] = oklch_to_oklab(
            self._generator.random(
                n=(~is_done).sum(),
                min_lightness=problem.min_lightness,
                max_lightness=problem.max_lightness,
            ),
        )

        return problem.oklabs_to_params(oklabs)
