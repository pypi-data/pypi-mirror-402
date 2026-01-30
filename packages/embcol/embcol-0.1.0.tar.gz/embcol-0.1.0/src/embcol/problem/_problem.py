"""Embedding problem."""

from __future__ import annotations

from collections.abc import Collection, Mapping
import itertools
import math
from types import MappingProxyType
from typing import TYPE_CHECKING, cast, overload

import numpy as np
import scipy

from .._checking import (
    check_array,
    check_disjoint,
    check_number,
    check_number_set,
    check_size,
    check_type,
)
from .._exception import expr, invalid_size_error, invalid_value_error, out_of_range_error
from .._repr import Representor
from ..color._conversions import oklab_to_linear_srgb, oklch_chroma, oklch_hue
from ..color._difference import pairwise_sq_color_diffs
from ._bounds import Bounds
from ._constraints import Constraint

if TYPE_CHECKING:
    from typing import Literal

    from numpy import bool_, float64, floating, intp

    from .._typing_imports import Unpack
    from ..typing import Array1D, Array2D, Array3D, ArrayLike1D, ArrayLike2D

__all__ = ["Problem"]


class Problem:
    r"""Embedding problem.

    Parameters
    ----------
    dissimilarities : array-like of float
        Dissimilarities among samples. The shape must be ``((N-1)*N//2,)``, where ``N`` is
        the number of samples: items are off-diagonal elements above the main diagonal of
        a dissimilarity matrix in row-major order.
    weights : array-like of float, optional
        Weights of sample pairs. The shape must be ``((N-1)*N//2,)``, where ``N`` is the number of
        samples: items are off-diagonal elements above the main diagonal of a dissimilarity matrix
        in row-major order. If nothing is given, all pairs are equally weighted.
    fixed : mapping of int to array-like of float, optional
        Color-fixed samples. Map the index of a sample to an Oklab color.
    min_lightness : float, optional
        Lower bound of the lightness. The value must be in the range [0, 1).
    max_lightness : float, optional
        Upper bound of the lightness. The value must be in the range (0, 1].
    hue_groups : collection of collection of int, optional
        Groups of samples whose hues are equal. An item indicates a group. The item is a collection
        of indices of samples.
    hue_diff_tol : float, optional
        Tolerance for the hue difference within each group given by `hue_groups`.

    Notes
    -----
    An instance represents an optimization problem minimizing

    .. math::

       f(\vec{x}_1, \ldots, \vec{x}_N) = \frac{1}{2} \sum_{i=1}^{N-1} \sum_{j=i+1}^N w_{ij}
       \left[s \, \Delta E(\vec{x}_i, \vec{x}_j)^2 - d_{ij}^2\right]^2

    subject to

    .. math::

       0 \le (\vec{x}_i)_k \le 1, \quad i \in \{1, \ldots, N\}, k \in \{1, 2, 3\}

       \left|h(\vec{x}_i) - h(\vec{x}_j)\right| \le \epsilon, \quad
       i \in g, j \in g \setminus \{i\}, g \in G

    where :math:`\vec{x}_i` is an sRGB color of the :math:`i`\ th sample,
    :math:`\Delta E(\cdot, \cdot)` is the color difference between two colors, :math:`d_{ij}` is
    a dissimilarity between the :math:`i`\ th and :math:`j`\ th samples, :math:`w_{ij}` is a weight
    of the pair of the :math:`i`\ th and :math:`j`\ th samples, :math:`s` is a scaling factor,
    :math:`h(\cdot)` is the hue of a color, :math:`\epsilon` is a tolerance for the hue difference,
    :math:`G` is a set of sets of sample indices, and :math:`N` is the number of samples.

    The weights, :math:`\{w_{ij}\}`, are normalized so that the mean is equal to one.

    The scaling factor, :math:`s`, is determined so that the partial sum of :math:`f` among
    color-fixed samples are minimized. If the number of color-fixed samples are less than two,
    :math:`s` is set to one.
    """

    _n_samples: int
    _dissimilarities: Array1D[float64]
    _weights: Array1D[float64]
    _scale: float | None
    _fixed: dict[int, Array1D[float64]]
    _unfixed_indices: Array1D[intp]
    _is_fixed_pair: Array1D[bool_]
    _min_lightness: float
    _max_lightness: float
    _hue_groups: tuple[tuple[int, int, Unpack[tuple[int, ...]]], ...]
    _hue_diff_tol: float
    _bounds: Bounds | None
    _effective_bounds: Bounds | None
    _constraints: tuple[Constraint, ...] | None

    def __init__(  # noqa: C901, PLR0912, PLR0915
        self,
        dissimilarities: ArrayLike1D[float, floating],
        weights: ArrayLike1D[float, floating] | None = None,
        fixed: Mapping[int, ArrayLike1D[float, floating]] | None = None,
        min_lightness: float = 0.0,
        max_lightness: float = 1.0,
        hue_groups: Collection[Collection[int]] = (),
        hue_diff_tol: float = 0.07,
    ) -> None:
        dissimilarities = np.asarray(dissimilarities, dtype=np.float64, copy=True)
        check_array(dissimilarities, shape=(-1,), target=expr("dissimilarities"))
        if not scipy.spatial.distance.is_valid_y(dissimilarities):
            raise invalid_size_error(
                len(dissimilarities),
                target=expr("dissimilarities"),
                descr="the number of sample pairs",
            )
        for item in dissimilarities:
            check_number(
                item,
                lower_bound=0,
                upper_bound=float("inf"),
                allow_upper_bound=False,
                allow_nan=False,
                target=f"item of {expr('dissimilarities')}",
            )
        dissimilarities = cast("Array1D[float64]", dissimilarities)

        n_samples = scipy.spatial.distance.num_obs_y(dissimilarities)

        if weights is None:
            weights = [1.0] * len(dissimilarities)
        weights = np.asarray(weights, dtype=np.float64, copy=True)
        check_array(
            weights,
            shape=(len(dissimilarities),),
            target=expr("weights"),
            size_descrs={0: f"the size of {expr('dissimilarities')}"},
        )
        for item in weights:
            check_number(
                item,
                lower_bound=0,
                upper_bound=float("inf"),
                allow_upper_bound=False,
                allow_nan=False,
                target=f"item of {expr('weights')}",
            )
        weights = cast("Array1D[float64]", weights)
        mean = weights.mean()
        if not mean:
            raise invalid_value_error(0, target=f"mean of {expr('weights')}")
        weights /= mean

        check_type(fixed, [Mapping, None], target=expr("fixed"))
        if fixed is None:
            fixed = {}
        for key in fixed:
            check_number_set(key, "integers", target=f"key of {expr('fixed')}")
            check_number(
                key,
                lower_bound=0,
                upper_bound=n_samples,
                allow_upper_bound=False,
                target=f"key of {expr('fixed')}",
                upper_bound_descr="the number of samples",
            )
        check_size(
            fixed,
            upper_bound=n_samples,
            allow_upper_bound=False,
            target=expr("fixed"),
            upper_bound_descr="the number of samples",
        )
        fixed = {
            int(i): cast("Array1D[float64]", np.asarray(fixed[i], dtype=np.float64, copy=True))
            for i in sorted(fixed)
        }
        for value in fixed.values():
            check_array(value, shape=(3,), target=f"value of {expr('fixed')}")

        check_number_set(min_lightness, "real_numbers", target=expr("min_lightness"))
        check_number(
            min_lightness,
            lower_bound=0,
            upper_bound=1,
            allow_upper_bound=False,
            allow_nan=False,
            target=expr("min_lightness"),
        )
        min_lightness = float(min_lightness)

        check_number_set(max_lightness, "real_numbers", target=expr("max_lightness"))
        check_number(
            max_lightness,
            lower_bound=min_lightness,
            allow_lower_bound=False,
            upper_bound=1,
            allow_nan=False,
            target=expr("max_lightness"),
            lower_bound_descr=expr("min_lightness"),
        )
        max_lightness = float(max_lightness)

        check_type(hue_groups, [Collection], target=expr("hue_groups"))
        for item in hue_groups:
            check_type(item, [Collection], target=f"item of {expr('hue_groups')}")
            for item_item in item:
                check_number_set(
                    item_item,
                    "integers",
                    target=f"item of item of {expr('hue_groups')}",
                )
                check_number(
                    item_item,
                    lower_bound=0,
                    upper_bound=n_samples,
                    allow_upper_bound=False,
                    target=f"item of item of {expr('hue_groups')}",
                    upper_bound_descr="the number of samples",
                )
        check_disjoint(hue_groups, targets=f"items of {expr('hue_groups')}")
        hue_groups = tuple(
            sorted(
                cast("tuple[int, int, Unpack[tuple[int, ...]]]", tuple(sorted(int(i) for i in g)))
                for group in hue_groups
                if 2 <= len(g := set(group))
            ),
        )

        check_number_set(hue_diff_tol, "real_numbers", target=expr("hue_diff_tol"))
        check_number(
            hue_diff_tol,
            lower_bound=0,
            allow_lower_bound=False,
            allow_nan=False,
            target=expr("hue_diff_tol"),
        )
        hue_diff_tol = float(hue_diff_tol)

        for group in hue_groups:
            fixed_indices = [i for i in group if i in fixed]
            if len(fixed_indices) < 2:
                continue
            fixed_hues = oklch_hue(
                cast("Array2D[float64]", np.vstack([fixed[i] for i in fixed_indices])),
            )
            for (k1, hue1), (k2, hue2) in itertools.combinations(enumerate(fixed_hues), 2):
                if hue_diff_tol < (hue_diff := abs((hue1-hue2+np.pi)%(2*np.pi)-np.pi)):
                    target = (
                        f"hue difference between {expr(f'fixed[{fixed_indices[k1]}]')} and "
                        f"{expr(f'fixed[{fixed_indices[k2]}]')}"
                    )
                    raise out_of_range_error(
                        float(hue_diff),
                        "<=",
                        hue_diff_tol,
                        target=target,
                        descr=expr("hue_diff_tol"),
                    )

        unfixed_indices = cast(
            "Array1D[intp]",
            np.array(sorted(set(range(n_samples)).difference(fixed)), dtype=np.intp),
        )

        triu_indices = np.triu_indices(n_samples, k=1)
        is_fixed_pair = cast(
            "Array1D[bool_]",
            (
                np.isin(triu_indices[0], list(fixed))
                & np.isin(triu_indices[1], list(fixed))
            ),
        )

        self._n_samples = n_samples
        self._dissimilarities = dissimilarities
        self._weights = weights
        self._scale = None
        self._fixed = fixed
        self._unfixed_indices = unfixed_indices
        self._is_fixed_pair = is_fixed_pair
        self._min_lightness = min_lightness
        self._max_lightness = max_lightness
        self._hue_groups = hue_groups
        self._hue_diff_tol = hue_diff_tol
        self._bounds = None
        self._effective_bounds = None
        self._constraints = None

        for array in [
            self._dissimilarities,
            self._weights,
            *self._fixed.values(),
            self._unfixed_indices,
            self._is_fixed_pair,
        ]:
            array.setflags(write=False)

    def __repr__(self) -> str:
        r = Representor(max_n_lines=4)
        return r.repr_constructor(
            "Problem",
            self._dissimilarities.tolist(),
            weights=self._weights.tolist(),
            fixed={i: tuple(oklab.tolist()) for i, oklab in self._fixed.items()},
            min_lightness=self._min_lightness,
            max_lightness=self._max_lightness,
            hue_groups=[set(group) for group in self._hue_groups],
            hue_diff_tol=self._hue_diff_tol,
        )

    def __eq__(self, other: object) -> bool:
        return (
            type(other) is Problem
            and np.array_equal(self._dissimilarities, other._dissimilarities)
            and np.array_equal(self._weights, other._weights)
            and self._fixed.keys() == other._fixed.keys()
            and all(np.array_equal(self._fixed[i], other._fixed[i]) for i in self._fixed)  # noqa: SLF001
            and self._min_lightness == other._min_lightness
            and self._max_lightness == other._max_lightness
            and self._hue_groups == other._hue_groups
            and self._hue_diff_tol == other._hue_diff_tol
        )

    def __hash__(self) -> int:
        return hash(
            (
                tuple(self._dissimilarities),
                tuple(self._weights),
                tuple((i, tuple(oklab)) for i, oklab in self._fixed.items()),
                self._min_lightness,
                self._max_lightness,
                self._hue_groups,
                self._hue_diff_tol,
            ),
        )

    def __getstate__(self) -> dict[str, object]:
        state = self.__dict__.copy()
        for key in ["_scale", "_bounds", "_effective_bounds", "_constraints"]:
            state[key] = None
        return state

    @property
    def n_samples(self) -> int:
        """Number of samples."""
        return self._n_samples

    @property
    def n_params(self) -> int:
        """Number of parameters."""
        return len(self._unfixed_indices) * 3

    @property
    def dissimilarities(self) -> Array1D[float64]:
        """Dissimilarities among samples."""
        return self._dissimilarities

    @property
    def weights(self) -> Array1D[float64]:
        """Weights of sample pairs."""
        return self._weights

    @property
    def scale(self) -> float:
        """Scaling factor."""
        if self._scale is None:
            self._scale = 1.0
            if self._weights[self._is_fixed_pair].any():
                fixed_sqrt_weights = np.sqrt(self._weights[self._is_fixed_pair])
                fixed_sq_color_diffs = (
                    fixed_sqrt_weights
                    * pairwise_sq_color_diffs(
                        cast("Array2D[float64]", np.vstack(list(self._fixed.values()))),
                    )
                )
                if (de := np.linalg.norm(fixed_sq_color_diffs)):
                    fixed_sq_dissimilarities = (
                        fixed_sqrt_weights * self._dissimilarities[self._is_fixed_pair]**2
                    )
                    self._scale = float(
                        np.sqrt(np.dot(fixed_sq_color_diffs, fixed_sq_dissimilarities))/de,
                    )
        return self._scale

    @property
    def fixed(self) -> MappingProxyType[int, Array1D[float64]]:
        """Color-fixed samples."""
        return MappingProxyType(self._fixed)

    @property
    def unfixed_indices(self) -> Array1D[intp]:
        """Indices of color-unfixed samples."""
        return self._unfixed_indices

    @property
    def min_lightness(self) -> float:
        """Lower bound of the lightness."""
        return self._min_lightness

    @property
    def max_lightness(self) -> float:
        """Upper bound of the lightness."""
        return self._max_lightness

    @property
    def hue_groups(self) -> tuple[tuple[int, int, Unpack[tuple[int, ...]]], ...]:
        """Groups of samples whose hues are equal."""
        return self._hue_groups

    @property
    def hue_diff_tol(self) -> float:
        """Tolerance for the hue difference."""
        return self._hue_diff_tol

    @property
    def bounds(self) -> Bounds:
        """Bounds of parameters.

        Values for unbounded parameters are infinity.
        """
        if self._bounds is None:
            self._bounds = Bounds(
                self.oklabs_to_params(
                    cast(
                        "Array2D[float64]",
                        np.tile(
                            np.array([self._min_lightness, -np.inf, -np.inf], dtype=np.float64),
                            [self._n_samples, 1],
                        ),
                    ),
                ),
                self.oklabs_to_params(
                    cast(
                        "Array2D[float64]",
                        np.tile(
                            np.array([self._max_lightness, np.inf, np.inf], dtype=np.float64),
                            [self._n_samples, 1],
                        ),
                    ),
                ),
            )
        return self._bounds

    @property
    def effective_bounds(self) -> Bounds:
        """Effective bounds of parameters.

        Values are finite even for unbounded parameters by taking the gamut of the sRGB color space
        into account.
        """
        if self._effective_bounds is None:
            self._effective_bounds = Bounds(
                self.oklabs_to_params(
                    cast(
                        "Array2D[float64]",
                        np.tile(
                            np.array([self._min_lightness, -0.234, -0.312], dtype=np.float64),
                            [self._n_samples, 1],
                        ),
                    ),
                ),
                self.oklabs_to_params(
                    cast(
                        "Array2D[float64]",
                        np.tile(
                            np.array([self._max_lightness, 0.277, 0.199], dtype=np.float64),
                            [self._n_samples, 1],
                        ),
                    ),
                ),
            )
        return self._effective_bounds

    @property
    def constraints(self) -> tuple[Constraint, ...]:
        """Constraints."""
        if self._constraints is None:
            constraints = [
                Constraint(
                    self._linear_srgb,
                    lambda params: self._linear_srgb(params, return_jacobian=True)[1],
                    lambda params: self._linear_srgb(params, return_hessian=True)[1],
                    len(self._unfixed_indices)*3,
                    lower_bound=0.0,
                    upper_bound=1.0,
                ),
            ]
            if self._hue_groups:
                constraints.append(
                    Constraint(
                        self._hue_similarities,
                        lambda params: self._hue_similarities(params, return_jacobian=True)[1],
                        lambda params: self._hue_similarities(params, return_hessian=True)[1],
                        sum(math.comb(len(group), 2) for group in self._hue_groups),
                        lower_bound=(
                            self._hue_differences_to_similarities(
                                cast("Array1D[float64]", np.array([self._hue_diff_tol])),
                            )
                            [0]
                        ),
                    ),
                )
            self._constraints = tuple(constraints)
        return self._constraints

    def oklabs_to_params(self, oklabs: ArrayLike2D[float, floating]) -> Array1D[float64]:
        """Convert Oklab colors of samples to parameters.

        Parameters
        ----------
        oklabs : array-like of float
            Oklab colors of samples. The shape must be ``(N, 3)``, where ``N`` is the number of
            samples.

        Returns
        -------
        numpy.ndarray of float
            Parameters.
        """
        oklabs = np.asarray(oklabs, dtype=np.float64)
        check_array(
            oklabs,
            shape=(self._n_samples, 3),
            target=expr("oklabs"),
            size_descrs={0: "the number of samples"},
        )

        return oklabs[self._unfixed_indices, :].reshape(-1, copy=True)

    def params_to_oklabs(self, params: ArrayLike1D[float, floating]) -> Array2D[float64]:
        """Convert parameters to Oklab colors of samples.

        Parameters
        ----------
        params : array-like of float
            Parameters.

        Returns
        -------
        numpy.ndarray of float
            Oklab colors of samples. The shape is ``(N, 3)``, where ``N`` is the number of samples.
        """
        params = np.asarray(params)
        check_array(
            params,
            shape=(self.n_params,),
            target=expr("params"),
            size_descrs={0: "the number of parameters"},
        )

        oklabs = np.empty((self._n_samples, 3), dtype=np.float64)
        for i, oklab in self._fixed.items():
            oklabs[i, :] = oklab
        oklabs[self._unfixed_indices, :] = params.reshape((-1, 3))
        return oklabs

    @overload
    def cost(
        self,
        params: ArrayLike1D[float, floating],
        *,
        return_jacobian: Literal[False] = ...,
        return_hessian: Literal[False] = ...,
    ) -> float:
        ...
    @overload
    def cost(
        self,
        params: ArrayLike1D[float, floating],
        *,
        return_jacobian: Literal[True],
        return_hessian: Literal[False] = ...,
    ) -> tuple[float, Array1D[float64]]:
        ...
    @overload
    def cost(
        self,
        params: ArrayLike1D[float, floating],
        *,
        return_jacobian: Literal[False] = ...,
        return_hessian: Literal[True],
    ) -> tuple[float, Array2D[float64]]:
        ...
    @overload
    def cost(
        self,
        params: ArrayLike1D[float, floating],
        *,
        return_jacobian: Literal[True],
        return_hessian: Literal[True],
    ) -> tuple[float, Array1D[float64], Array2D[float64]]:
        ...
    @overload
    def cost(
        self,
        params: ArrayLike1D[float, floating],
        *,
        return_jacobian: bool,
        return_hessian: bool,
    ) -> (
        float
        | tuple[float, Array1D[float64]]
        | tuple[float, Array2D[float64]]
        | tuple[float, Array1D[float64], Array2D[float64]]
    ):
        ...

    def cost(
        self,
        params: ArrayLike1D[float, floating],
        *,
        return_jacobian: bool = False,
        return_hessian: bool = False,
    ) -> (
        float
        | tuple[float, Array1D[float64]]
        | tuple[float, Array2D[float64]]
        | tuple[float, Array1D[float64], Array2D[float64]]
    ):
        """Evaluate a cost.

        Parameters
        ----------
        params : array-like of float
            Parameters.
        return_jacobian : bool, optional
            If ``True`` is given, a Jacobian matrix is also returned.
        return_hessian : bool, optional
            If ``True`` is given, a Hessian matrix is also returned.

        Returns
        -------
        value : float
            Cost. The partial sum among color-fixed samples is excluded.
        jacobian : numpy.ndarray of float
            Jacobian matrix. Returned only if `return_jacobian` is ``True``. The shape is ``(M,)``,
            where ``M`` is the number of parameters.
        hessian : numpy.ndarray of float
            Hessian matrix. Returned only if `return_hessian` is ``True``. The shape is ``(M, M)``,
            where ``M`` is the number of parameters.
        """
        oklabs = self.params_to_oklabs(params)

        if not return_hessian:
            if not return_jacobian:
                sq_color_diffs = pairwise_sq_color_diffs(oklabs)
            else:
                sq_color_diffs, sq_color_diff_jacobians = pairwise_sq_color_diffs(
                    oklabs,
                    return_jacobian=True,
                )
        else:
            (
                sq_color_diffs,
                sq_color_diff_jacobians,
                sq_color_diff_hessians,
            ) = pairwise_sq_color_diffs(oklabs, return_jacobian=True, return_hessian=True)

        sq_scale = self.scale ** 2
        residuals = sq_scale*sq_color_diffs - self._dissimilarities**2

        value = float(
            0.5*(self._weights[~self._is_fixed_pair]*residuals[~self._is_fixed_pair]**2).sum(),
        )

        if return_jacobian:
            jacobian = np.zeros((len(oklabs), 3))
            for i_pair, (i, j) in enumerate(itertools.combinations(range(len(oklabs)), 2)):
                jacobian[[i, j], :] += (
                    self._weights[i_pair]
                    * residuals[i_pair]
                    * sq_scale
                    * sq_color_diff_jacobians[i_pair, :, :]
                )

            jacobian = jacobian[self._unfixed_indices, :]
            jacobian = jacobian.reshape(-1)

        if return_hessian:
            hessian = np.zeros((len(oklabs), 3, len(oklabs), 3))
            for i_pair, (i, j) in enumerate(itertools.combinations(range(len(oklabs)), 2)):
                hessian[[[i], [j]], :, [i, j], :] += (
                    self._weights[i_pair]
                    * sq_scale
                    * (
                        sq_scale
                        * sq_color_diff_jacobians[i_pair, :, np.newaxis, :, np.newaxis]
                        * sq_color_diff_jacobians[i_pair, np.newaxis, :, np.newaxis, :]
                        + residuals[i_pair]*sq_color_diff_hessians[i_pair, [[0], [1]], :, [0, 1], :]
                    )
                )

            hessian = hessian[self._unfixed_indices, :, :, :][:, :, self._unfixed_indices, :]
            hessian = hessian.reshape((self.n_params, self.n_params))

        if not return_hessian:
            if not return_jacobian:
                return value
            return value, jacobian
        if not return_jacobian:
            return value, hessian
        return value, jacobian, hessian

    @overload
    def _linear_srgb(
        self,
        params: Array1D[floating],
        *,
        return_jacobian: Literal[False] = ...,
        return_hessian: Literal[False] = ...,
    ) -> Array1D[float64]:
        ...
    @overload
    def _linear_srgb(
        self,
        params: Array1D[floating],
        *,
        return_jacobian: Literal[True],
        return_hessian: Literal[False] = ...,
    ) -> tuple[Array1D[float64], Array2D[float64]]:
        ...
    @overload
    def _linear_srgb(
        self,
        params: Array1D[floating],
        *,
        return_jacobian: Literal[False] = ...,
        return_hessian: Literal[True],
    ) -> tuple[Array1D[float64], Array3D[float64]]:
        ...
    @overload
    def _linear_srgb(
        self,
        params: Array1D[floating],
        *,
        return_jacobian: Literal[True],
        return_hessian: Literal[True],
    ) -> tuple[Array1D[float64], Array2D[float64], Array3D[float64]]:
        ...
    @overload
    def _linear_srgb(
        self,
        params: Array1D[floating],
        *,
        return_jacobian: bool,
        return_hessian: bool,
    ) -> (
        Array1D[float64]
        | tuple[Array1D[float64], Array2D[float64]]
        | tuple[Array1D[float64], Array3D[float64]]
        | tuple[Array1D[float64], Array2D[float64], Array3D[float64]]
    ):
        ...

    def _linear_srgb(
        self,
        params: Array1D[floating],
        *,
        return_jacobian: bool = False,
        return_hessian: bool = False,
    ) -> (
        Array1D[float64]
        | tuple[Array1D[float64], Array2D[float64]]
        | tuple[Array1D[float64], Array3D[float64]]
        | tuple[Array1D[float64], Array2D[float64], Array3D[float64]]
    ):
        """Compute linear sRGB components of color-unfixed samples.

        Parameters
        ----------
        params : numpy.ndarray of float
            Parameters.
        return_jacobian : bool, optional
            If ``True`` is given, a Jacobian matrix is also returned.
        return_hessian : bool, optional
            If ``True`` is given, a Hessian matrix is also returned.

        Returns
        -------
        values : numpy.ndarray of float
            Linear sRGB components of color-unfixed samples. The shape is ``(3*n,)``, where ``n`` is
            the number of color-unfixed samples.
        jacobian : numpy.ndarray of float
            Jacobian matrix. Returned only if `return_jacobian` is ``True``. The shape is
            ``(3*n, M)``, where ``n`` is the number of color-unfixed samples and ``M`` is the number
            of parameters.
        hessian : numpy.ndarray of float
            Hessian matrix. Returned only if `return_hessian` is ``True``. The shape is
            ``(3*n, M, M)``, where ``n`` is the number of color-unfixed samples and ``M`` is
            the number of parameters.
        """
        oklabs = self.params_to_oklabs(params)
        oklabs = cast("Array2D[float64]", oklabs[self._unfixed_indices, :])
        if not return_hessian:
            if not return_jacobian:
                linear_srgbs = oklab_to_linear_srgb(oklabs)
            else:
                linear_srgbs, jacobians = oklab_to_linear_srgb(oklabs, return_jacobian=True)
        elif not return_jacobian:
            linear_srgbs, hessians = oklab_to_linear_srgb(oklabs, return_hessian=True)
        else:
            linear_srgbs, jacobians, hessians = oklab_to_linear_srgb(
                oklabs,
                return_jacobian=True,
                return_hessian=True,
            )

        values = linear_srgbs.reshape(-1)

        if return_jacobian:
            jacobian = np.zeros((len(linear_srgbs), 3, len(linear_srgbs), 3))
            indices = np.arange(len(linear_srgbs))
            jacobian[indices, :, indices, :] = jacobians
            jacobian = jacobian.reshape((len(values), len(params)))

        if return_hessian:
            hessian = np.zeros((len(linear_srgbs), 3, len(linear_srgbs), 3, len(linear_srgbs), 3))
            indices = np.arange(len(linear_srgbs))
            hessian[indices, :, indices, :, indices, :] = hessians
            hessian = hessian.reshape((len(values), len(params), len(params)))

        if not return_hessian:
            if not return_jacobian:
                return values
            return values, jacobian
        if not return_jacobian:
            return values, hessian
        return values, jacobian, hessian

    @overload
    def _hue_similarities(
        self,
        params: Array1D[floating],
        *,
        return_jacobian: Literal[False] = ...,
        return_hessian: Literal[False] = ...,
    ) -> Array1D[float64]:
        ...
    @overload
    def _hue_similarities(
        self,
        params: Array1D[floating],
        *,
        return_jacobian: Literal[True],
        return_hessian: Literal[False] = ...,
    ) -> tuple[Array1D[float64], Array2D[float64]]:
        ...
    @overload
    def _hue_similarities(
        self,
        params: Array1D[floating],
        *,
        return_jacobian: Literal[False] = ...,
        return_hessian: Literal[True],
    ) -> tuple[Array1D[float64], Array3D[float64]]:
        ...
    @overload
    def _hue_similarities(
        self,
        params: Array1D[floating],
        *,
        return_jacobian: Literal[True],
        return_hessian: Literal[True],
    ) -> tuple[Array1D[float64], Array2D[float64], Array3D[float64]]:
        ...
    @overload
    def _hue_similarities(
        self,
        params: Array1D[floating],
        *,
        return_jacobian: bool,
        return_hessian: bool,
    ) -> (
        Array1D[float64]
        | tuple[Array1D[float64], Array2D[float64]]
        | tuple[Array1D[float64], Array3D[float64]]
        | tuple[Array1D[float64], Array2D[float64], Array3D[float64]]
    ):
        ...

    def _hue_similarities(  # noqa: C901, PLR0912
        self,
        params: Array1D[floating],
        *,
        return_jacobian: bool = False,
        return_hessian: bool = False,
    ) -> (
        Array1D[float64]
        | tuple[Array1D[float64], Array2D[float64]]
        | tuple[Array1D[float64], Array3D[float64]]
        | tuple[Array1D[float64], Array2D[float64], Array3D[float64]]
    ):
        """Compute similarities of the hue among hue-constrained samples.

        Parameters
        ----------
        params : numpy.ndarray of float
            Parameters.
        return_jacobian : bool, optional
            If ``True`` is given, an array of Jacobian matrices is also returned.
        return_hessian : bool, optional
            If ``True`` is given, an array of Hessian matrices is also returned.

        Returns
        -------
        values : numpy.ndarray of float
            Similarities of the hue among hue-constrained samples. The shape is ``(K,)``, where
            ``K`` is the number of pairs of hue-constrained samples.
        jacobians : numpy.ndarray of float
            Jacobian matrices. Returned only if `return_jacobian` is ``True``. The shape is
            ``(K, M)``, where ``K`` is the number of pairs of hue-constrained samples and ``M`` is
            the number of parameters.
        hessians : numpy.ndarray of float
            Hessian matrices. Returned only if `return_hessian` is ``True``. The shape is
            ``(K, M, M)``, where ``K`` is the number of pairs of hue-constrained samples and ``M``
            is the number of parameters.
        """
        oklabs = self.params_to_oklabs(params)

        if not return_hessian:
            if not return_jacobian:
                hues = oklch_hue(oklabs)
            else:
                hues, hue_jacobians = oklch_hue(oklabs, return_jacobian=True)
        else:
            hues, hue_jacobians, hue_hessians = oklch_hue(
                oklabs,
                return_jacobian=True,
                return_hessian=True,
            )

        chromas = oklch_chroma(oklabs)
        hue_diffs = cast(
            "Array1D[float64]",
            np.array(
                [
                    hues[i]-hues[j] if chromas[i] and chromas[j] else 0.0
                    for group in self._hue_groups
                    for i, j in itertools.combinations(group, 2)
                ],
            ),
        )

        if not return_hessian:
            if not return_jacobian:
                values = self._hue_differences_to_similarities(hue_diffs)
            else:
                values, hue_diff_jacobians = self._hue_differences_to_similarities(
                    hue_diffs,
                    return_jacobian=True,
                )
        else:
            values, hue_diff_jacobians, hue_diff_hessians = self._hue_differences_to_similarities(
                hue_diffs,
                return_jacobian=True,
                return_hessian=True,
            )

        if return_jacobian:
            jacobians = np.zeros((len(values), len(hues), 3))
            i_pair = 0
            for group in self._hue_groups:
                for i, j in itertools.combinations(group, 2):
                    jacobians[i_pair, i, :] = hue_diff_jacobians[i_pair] * hue_jacobians[i, :]
                    jacobians[i_pair, j, :] = -hue_diff_jacobians[i_pair] * hue_jacobians[j, :]
                    i_pair += 1
            jacobians = jacobians[:, self._unfixed_indices, :]
            jacobians = jacobians.reshape((len(values), len(params)))

        if return_hessian:
            temp = np.zeros((len(values), len(hues), 3, len(hues), 3))
            i_pair = 0
            for group in self._hue_groups:
                for i, j in itertools.combinations(group, 2):
                    temp[i_pair, i, :, i, :] = (
                        hue_diff_hessians[i_pair]
                        * hue_jacobians[i, :, np.newaxis]
                        * hue_jacobians[i, np.newaxis, :]
                        + hue_diff_jacobians[i_pair]*hue_hessians[i, :, :]
                    )
                    temp[i_pair, i, :, j, :] = (
                        -hue_diff_hessians[i_pair]
                        * hue_jacobians[i, :, np.newaxis]
                        * hue_jacobians[j, np.newaxis, :]
                    )
                    temp[i_pair, j, :, i, :] = (
                        -hue_diff_hessians[i_pair]
                        * hue_jacobians[j, :, np.newaxis]
                        * hue_jacobians[i, np.newaxis, :]
                    )
                    temp[i_pair, j, :, j, :] = (
                        hue_diff_hessians[i_pair]
                        * hue_jacobians[j, :, np.newaxis]
                        * hue_jacobians[j, np.newaxis, :]
                        - hue_diff_jacobians[i_pair]*hue_hessians[j, :, :]
                    )
                    i_pair += 1

            hessians = np.zeros(
                (len(values), len(self._unfixed_indices), 3, len(self._unfixed_indices), 3),
            )
            indices = np.arange(len(self._unfixed_indices))
            hessians[:, indices[:, np.newaxis], :, indices, :] = (
                temp[:, self._unfixed_indices[:, np.newaxis], :, self._unfixed_indices, :]
            )
            hessians = hessians.reshape((len(values), len(params), len(params)))

        if not return_hessian:
            if not return_jacobian:
                return values
            return values, jacobians
        if not return_jacobian:
            return values, hessians
        return values, jacobians, hessians

    @overload
    def _hue_differences_to_similarities(
        self,
        differences: Array1D[floating],
        *,
        return_jacobian: Literal[False] = ...,
        return_hessian: Literal[False] = ...,
    ) -> Array1D[float64]:
        ...
    @overload
    def _hue_differences_to_similarities(
        self,
        differences: Array1D[floating],
        *,
        return_jacobian: Literal[True],
        return_hessian: Literal[False] = ...,
    ) -> tuple[Array1D[float64], Array1D[float64]]:
        ...
    @overload
    def _hue_differences_to_similarities(
        self,
        differences: Array1D[floating],
        *,
        return_jacobian: Literal[False] = ...,
        return_hessian: Literal[True],
    ) -> tuple[Array1D[float64], Array1D[float64]]:
        ...
    @overload
    def _hue_differences_to_similarities(
        self,
        differences: Array1D[floating],
        *,
        return_jacobian: Literal[True],
        return_hessian: Literal[True],
    ) -> tuple[Array1D[float64], Array1D[float64], Array1D[float64]]:
        ...
    @overload
    def _hue_differences_to_similarities(
        self,
        differences: Array1D[floating],
        *,
        return_jacobian: bool,
        return_hessian: bool,
    ) -> (
        Array1D[float64]
        | tuple[Array1D[float64], Array1D[float64]]
        | tuple[Array1D[float64], Array1D[float64], Array1D[float64]]
    ):
        ...

    def _hue_differences_to_similarities(
        self,
        differences: Array1D[floating],
        *,
        return_jacobian: bool = False,
        return_hessian: bool = False,
    ) -> (
        Array1D[float64]
        | tuple[Array1D[float64], Array1D[float64]]
        | tuple[Array1D[float64], Array1D[float64], Array1D[float64]]
    ):
        """Convert differences of the hue to similarities.

        Parameters
        ----------
        differences : numpy.ndarray of float
            Differences of the hue.
        return_jacobian : bool, optional
            If ``True`` is given, an array of Jacobian matrices is also returned.
        return_hessian : bool, optional
            If ``True`` is given, an array of Hessian matrices is also returned.

        Returns
        -------
        values : numpy.ndarray of float
            Similarities of the hue. The shape is the same as `differences`.
        jacobians : numpy.ndarray of float
            Jacobian matrices. Returned only if `return_jacobian` is ``True``. The shape is the same
            as `differences`.
        hessians : numpy.ndarray of float
            Hessian matrices. Returned only if `return_hessian` is ``True``. The shape is the same
            as `differences`.
        """
        values: Array1D[float64] = np.cos(differences)

        if return_jacobian:
            jacobians = -np.sin(differences)

        if return_hessian:
            hessians = -values

        if not return_hessian:
            if not return_jacobian:
                return values
            return values, jacobians
        if not return_jacobian:
            return values, hessians
        return values, jacobians, hessians
