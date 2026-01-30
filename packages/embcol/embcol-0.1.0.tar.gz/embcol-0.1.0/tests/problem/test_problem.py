from __future__ import annotations

import math
import pickle
from typing import TYPE_CHECKING, cast

import hypothesis
import hypothesis.strategies as st
import numpy as np
import pytest

from embcol.color._wrappers import oklab_to_oklch, oklch_to_oklab
from embcol.problem._problem import Problem

if TYPE_CHECKING:
    from collections.abc import Mapping

    from hypothesis.strategies import DrawFn, SearchStrategy
    from numpy import bool_, float64, floating

    from embcol.typing import Array1D, Array2D, ArrayLike2D
    from tests._typing import ApproxDerivative


def _oklabs() -> SearchStrategy[Array1D[float64]]:
    return (
        st.tuples(
            st.floats(min_value=-0.1, max_value=1.1),
            st.floats(min_value=-0.24, max_value=0.28),
            st.floats(min_value=-0.32, max_value=0.20),
        )
        .map(lambda x: cast("Array1D[float64]", np.array(x)))
    )


@st.composite
def _problems(draw: DrawFn, n_unfixed: int | None = None) -> Problem:
    if n_unfixed is None:
        n_unfixed = draw(st.integers(min_value=1, max_value=9))
    elif n_unfixed < 1:
        pytest.fail("'n_unfixed' must be >= 1")

    n_fixed = draw(st.integers(min_value=max(0, 2-n_unfixed), max_value=9))
    n_samples = n_fixed + n_unfixed
    n_pairs = math.comb(n_samples, 2)

    dissimilarities = draw(
        st.lists(st.floats(min_value=0.0, max_value=2.0), min_size=n_pairs, max_size=n_pairs),
    )

    weights = (
        draw(
            st.lists(st.floats(min_value=0.0, max_value=2.0), min_size=n_pairs, max_size=n_pairs)
            .filter(lambda x: bool(np.mean(x))),
        )
        if draw(st.booleans()) else
        None
    )

    fixed = (
        {i: oklch_to_oklab([0.5, 0.01*(i+1), 0.0]).tolist() for i in range(n_fixed)}
        if n_fixed else
        None
    )

    min_lightness = draw(st.floats(min_value=0.0, max_value=1.0-1e-4))
    max_lightness = draw(st.floats(min_value=min_lightness+1e-4, max_value=1.0))

    hue_groups = [list(range(n_fixed+1))] if draw(st.booleans()) else []
    hue_diff_tol = draw(st.floats(min_value=1e-4, max_value=np.pi))

    return Problem(
        dissimilarities,
        weights=weights,
        fixed=fixed,
        min_lightness=min_lightness,
        max_lightness=max_lightness,
        hue_groups=hue_groups,
        hue_diff_tol=hue_diff_tol,
    )


def _hue_differences(
    min_size: int = 0,
    max_size: int | None = None,
) -> SearchStrategy[Array1D[float64]]:
    return (
        st.lists(
            st.floats(min_value=-2*np.pi, max_value=2*np.pi),
            min_size=min_size,
            max_size=max_size,
        )
        .map(lambda x: cast("Array1D[float64]", np.array(x)))
    )


def _is_nonzero_chroma(oklab: Array1D[float64], tol: float) -> bool_:
    return tol < cast("float64", oklab_to_oklch(oklab)[1])


class TestProblem:

    @pytest.mark.parametrize(
        ("problem", "expected"),
        [
            pytest.param(
                Problem([1.0]),
                (
                    "Problem(\n"
                    "    [1],\n"
                    "    weights=[1],\n"
                    "    fixed={},\n"
                    "    min_lightness=0,\n"
                    "    max_lightness=1,\n"
                    "    hue_groups=[],\n"
                    "    hue_diff_tol=0.07,\n"
                    ")"
                ),
                id="without_optional",
            ),
            pytest.param(
                Problem(
                    list(range(496)),
                    weights=[1.0]*496,
                    fixed=dict.fromkeys(range(9), (0.5, 0.1, 0.2)),
                    min_lightness=0.1,
                    max_lightness=0.9,
                    hue_groups=[[i, i+1] for i in range(0, 32, 2)],
                    hue_diff_tol=0.1,
                ),
                (
                    "Problem(\n"
                    "    [\n"
                    "        0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19,"
                    "\n"
                    "        20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, "
                    "...\n"
                    "    ],\n"
                    "    weights=[\n"
                    "        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, "
                    "1,\n"
                    "        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, ..."
                    "\n"
                    "    ],\n"
                    "    fixed={\n"
                    "        0: (0.5, 0.1, 0.2), 1: (0.5, 0.1, 0.2), 2: (0.5, 0.1, 0.2),\n"
                    "        3: (0.5, 0.1, 0.2), 4: (0.5, 0.1, 0.2), 5: (0.5, 0.1, 0.2), ...\n"
                    "    },\n"
                    "    min_lightness=0.1,\n"
                    "    max_lightness=0.9,\n"
                    "    hue_groups=[\n"
                    "        {0, 1}, {2, 3}, {4, 5}, {6, 7}, {8, 9}, {10, 11}, {12, 13}, "
                    "{14, 15},\n"
                    "        {16, 17}, {18, 19}, {20, 21}, {22, 23}, {24, 25}, {26, 27}, ...\n"
                    "    ],\n"
                    "    hue_diff_tol=0.1,\n"
                    ")"
                ),
                id="with_optional",
            ),
        ],
    )
    def test_repr(self, problem: Problem, expected: str) -> None:
        assert repr(problem) == expected

    @hypothesis.given(problem=_problems())
    def test_eq(self, problem: Problem) -> None:
        # recreate from attributes to prevent numerical error
        objs = [
            Problem(
                problem.dissimilarities,
                weights=problem.weights,
                fixed=problem.fixed,
                min_lightness=problem.min_lightness,
                max_lightness=problem.max_lightness,
                hue_groups=problem.hue_groups,
                hue_diff_tol=problem.hue_diff_tol,
            )
            for _ in range(2)
        ]
        assert objs[0] == objs[1]

    @hypothesis.given(problem=_problems())
    def test_hash(self, problem: Problem) -> None:
        hash(problem)

    @hypothesis.given(problem=_problems())
    def test_pickle(self, problem: Problem) -> None:
        actual = pickle.loads(pickle.dumps(problem))  # noqa: S301
        assert actual == problem

    @hypothesis.given(problem=_problems())
    def test_constraints(self, problem: Problem) -> None:
        params = np.zeros(problem.n_params)

        for constraint in problem.constraints:
            actual = constraint.function(params)
            assert actual.shape == (constraint.n_outputs,)

            actual = constraint.jacobian(params)
            assert actual.shape == (constraint.n_outputs, problem.n_params)

            actual = constraint.hessian(params)
            assert actual.shape == (constraint.n_outputs, problem.n_params, problem.n_params)

    @hypothesis.given(problem=_problems())
    def test_oklabs_to_params(self, problem: Problem) -> None:
        oklabs = _merge_oklabs(problem.fixed, np.empty((len(problem.unfixed_indices), 3)))
        actual = problem.oklabs_to_params(oklabs)

        assert actual.shape == (problem.n_params,)

    @hypothesis.given(
        problem=_problems(n_unfixed=2),
        unfixed_oklabs=st.tuples(_oklabs(), _oklabs()),
    )
    def test_params_to_oklabs(
        self,
        problem: Problem,
        unfixed_oklabs: tuple[Array1D[float64], Array1D[float64]],
    ) -> None:
        expected = _merge_oklabs(problem.fixed, unfixed_oklabs)
        actual = problem.params_to_oklabs(problem.oklabs_to_params(expected))
        assert actual == pytest.approx(expected, rel=1e-6, abs=1e-6)

    class TestCost:

        @hypothesis.given(
            problem=_problems(n_unfixed=2),
            unfixed_oklabs=st.tuples(_oklabs(), _oklabs()),
        )
        def test_jacobian(
            self,
            problem: Problem,
            unfixed_oklabs: tuple[Array1D[float64], Array1D[float64]],
            approx_derivative: ApproxDerivative,
        ) -> None:
            oklabs = _merge_oklabs(problem.fixed, unfixed_oklabs)
            params = problem.oklabs_to_params(oklabs)

            _, actual = problem.cost(params, return_jacobian=True)
            expected = (
                approx_derivative(
                    lambda ps: cast("Array1D[float64]", np.array([problem.cost(ps)])),
                    params,
                )
                .reshape(-1)
            )
            assert actual == pytest.approx(expected, rel=1e-6, abs=1e-5)

        @hypothesis.given(
            problem=_problems(n_unfixed=2),
            unfixed_oklabs=st.tuples(_oklabs(), _oklabs()),
        )
        def test_hessian(
            self,
            problem: Problem,
            unfixed_oklabs: tuple[Array1D[float64], Array1D[float64]],
            approx_derivative: ApproxDerivative,
        ) -> None:
            oklabs = _merge_oklabs(problem.fixed, unfixed_oklabs)
            params = problem.oklabs_to_params(oklabs)

            _, actual = problem.cost(params, return_hessian=True)
            expected = (
                approx_derivative(
                    lambda ps: problem.cost(ps, return_jacobian=True)[1],
                    params,
                    abs_tol=1e-4,
                )
                .reshape((len(params), len(params)))
            )
            assert actual == pytest.approx(expected, rel=1e-6, abs=1e-4)

    class TestLinearSRGB:

        @hypothesis.given(
            problem=_problems(n_unfixed=2),
            unfixed_oklabs=st.tuples(_oklabs(), _oklabs()),
        )
        def test_jacobian(
            self,
            problem: Problem,
            unfixed_oklabs: tuple[Array1D[float64], Array1D[float64]],
            approx_derivative: ApproxDerivative,
        ) -> None:
            oklabs = _merge_oklabs(problem.fixed, unfixed_oklabs)
            params = problem.oklabs_to_params(oklabs)

            _, actual = problem._linear_srgb(params, return_jacobian=True)
            expected = approx_derivative(lambda ps: problem._linear_srgb(ps), params)
            assert actual == pytest.approx(expected, rel=1e-6, abs=1e-6)

        @hypothesis.given(
            problem=_problems(n_unfixed=2),
            unfixed_oklabs=st.tuples(_oklabs(), _oklabs()),
        )
        def test_hessian(
            self,
            problem: Problem,
            unfixed_oklabs: tuple[Array1D[float64], Array1D[float64]],
            approx_derivative: ApproxDerivative,
        ) -> None:
            oklabs = _merge_oklabs(problem.fixed, unfixed_oklabs)
            params = problem.oklabs_to_params(oklabs)

            _, actual = problem._linear_srgb(params, return_hessian=True)
            expected = (
                approx_derivative(
                    lambda ps: problem._linear_srgb(ps, return_jacobian=True)[1].reshape(-1),
                    params,
                )
                .reshape((-1, len(params), len(params)))
            )
            assert actual == pytest.approx(expected, rel=1e-6, abs=1e-6)

    class TestHueSimilarities:

        @hypothesis.given(
            problem=_problems(n_unfixed=2),
            unfixed_oklabs=st.tuples(
                _oklabs().filter(lambda x: _is_nonzero_chroma(x, 1e-4)),
                _oklabs().filter(lambda x: _is_nonzero_chroma(x, 1e-4)),
            ),
        )
        def test_jacobian(
            self,
            problem: Problem,
            unfixed_oklabs: tuple[Array1D[float64], Array1D[float64]],
            approx_derivative: ApproxDerivative,
        ) -> None:
            oklabs = _merge_oklabs(problem.fixed, unfixed_oklabs)
            params = problem.oklabs_to_params(oklabs)

            _, actual = problem._hue_similarities(params, return_jacobian=True)
            expected = approx_derivative(
                lambda ps: problem._hue_similarities(ps),
                params,
                max_dx=1e-4,
            )
            assert actual == pytest.approx(expected, rel=1e-6, abs=1e-6)

        @hypothesis.given(
            problem=_problems(n_unfixed=2),
            unfixed_oklabs=st.tuples(
                _oklabs().filter(lambda x: _is_nonzero_chroma(x, 1e-4)),
                _oklabs().filter(lambda x: _is_nonzero_chroma(x, 1e-4)),
            ),
        )
        def test_hessian(
            self,
            problem: Problem,
            unfixed_oklabs: tuple[Array1D[float64], Array1D[float64]],
            approx_derivative: ApproxDerivative,
        ) -> None:
            oklabs = _merge_oklabs(problem.fixed, unfixed_oklabs)
            params = problem.oklabs_to_params(oklabs)

            _, actual = problem._hue_similarities(params, return_hessian=True)
            expected = (
                approx_derivative(
                    lambda ps: problem._hue_similarities(ps, return_jacobian=True)[1].reshape(-1),
                    params,
                    max_dx=1e-4,
                )
                .reshape((-1, len(params), len(params)))
            )
            assert actual == pytest.approx(expected, rel=1e-6, abs=1e-6)

    class TestHueDifferenceToSimilarity:

        @hypothesis.given(
            problem=_problems(),
            differences=_hue_differences(min_size=1, max_size=10),
        )
        def test_jacobian(
            self,
            problem: Problem,
            differences: Array1D[float64],
            approx_derivative: ApproxDerivative,
        ) -> None:
            _, actual = problem._hue_differences_to_similarities(
                differences,
                return_jacobian=True,
            )
            expected = (
                approx_derivative(
                    lambda ds: problem._hue_differences_to_similarities(ds),
                    differences,
                )
                .diagonal()
            )
            assert actual == pytest.approx(expected, rel=1e-6, abs=1e-6)

        @hypothesis.given(
            problem=_problems(),
            differences=_hue_differences(min_size=1, max_size=10),
        )
        def test_hessian(
            self,
            problem: Problem,
            differences: Array1D[float64],
            approx_derivative: ApproxDerivative,
        ) -> None:
            _, actual = problem._hue_differences_to_similarities(differences, return_hessian=True)
            expected = (
                approx_derivative(
                    lambda ds: (
                        problem._hue_differences_to_similarities(ds, return_jacobian=True)[1]
                    ),
                    differences,
                )
                .diagonal()
            )
            assert actual == pytest.approx(expected, rel=1e-6, abs=1e-6)


def _merge_oklabs(
    fixed: Mapping[int, Array1D[float64]],
    unfixed: ArrayLike2D[float, floating],
) -> Array2D[float64]:
    unfixed = np.asarray(unfixed)

    n_samples = len(fixed) + len(unfixed)
    is_fixed = np.isin(np.arange(n_samples), list(fixed))

    oklabs = np.empty((n_samples, 3))
    for i, oklab in fixed.items():
        oklabs[i, :] = oklab
    oklabs[~is_fixed, :] = unfixed

    return oklabs
