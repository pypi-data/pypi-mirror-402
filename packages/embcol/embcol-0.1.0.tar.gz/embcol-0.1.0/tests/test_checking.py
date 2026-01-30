from __future__ import annotations

from collections.abc import Collection, Iterable, Mapping, Sequence
import re
from typing import TYPE_CHECKING

import numpy as np
import pytest

from embcol._checking import (
    check_array,
    check_disjoint,
    check_number,
    check_number_set,
    check_size,
    check_type,
    check_value,
)

if TYPE_CHECKING:
    from typing import Literal

    from numpy import dtype, generic


class TestCheckType:

    @pytest.mark.parametrize(
        ("obj", "valid"),
        [
            (0, [int]),
            (abs, ["callable"]),
            ([], [Iterable]),
            (None, [None]),
            (0, [int, None]),
        ],
    )
    def test_passing(self, obj: object, valid: Sequence[type | Literal["callable"] | None]) -> None:
        check_type(obj, valid)

    @pytest.mark.parametrize(
        ("obj", "valid", "message"),
        [
            pytest.param(0, [], "object must not be int", id="0"),
            pytest.param(0, [str], "object must be str, got int", id="0-str"),
            pytest.param(0, [Iterable], "object must be iterable, got int", id="0-Iterable"),
            pytest.param(0, [Collection], "object must be collection, got int", id="0-Collection"),
            pytest.param(0, [Sequence], "object must be sequence, got int", id="0-Sequence"),
            pytest.param(0, [Mapping], "object must be mapping, got int", id="0-Mapping"),
            pytest.param(0, ["callable"], "object must be callable, got int", id="0-callable"),
            pytest.param(0, [None], "object must be None, got int", id="0-None"),
            pytest.param(0, [str, None], "object must be str or None, got int", id="0-str_None"),
            pytest.param(
                0,
                [str, bytes, None],
                "object must be str, bytes, or None, got int",
                id="0-str_bytes_None",
            ),
            pytest.param(abs, [str], "object must be str, got callable", id="callable-str"),
            pytest.param(None, [str], "object must be str, got None", id="None-str"),
        ],
    )
    def test_error(
        self,
        obj: object,
        valid: Sequence[type | Literal["callable"] | None],
        message: str,
    ) -> None:
        with pytest.raises(TypeError, match=f"^{re.escape(message)}$"):
            check_type(obj, valid)


class TestCheckValue:

    @pytest.mark.parametrize(
        ("obj", "valid"),
        [
            (0, [0]),
            (0, [0, 1]),
            (None, [None]),
        ],
    )
    def test_passing(self, obj: object, valid: Sequence[object]) -> None:
        check_value(obj, valid)

    @pytest.mark.parametrize(
        ("obj", "valid", "message"),
        [
            pytest.param(0, [], "object must not be 0", id="0"),
            pytest.param(0, [1], "object must be 1, got 0", id="0-1"),
            pytest.param(0, [1, 2], "object must be 1 or 2, got 0", id="0-1_2"),
            pytest.param(0, [1, 2, 3], "object must be 1, 2, or 3, got 0", id="0-1_2_3"),
        ],
    )
    def test_error(self, obj: object, valid: Sequence[object], message: str) -> None:
        with pytest.raises(ValueError, match=f"^{re.escape(message)}$"):
            check_value(obj, valid)


class TestCheckNumberSet:

    @pytest.mark.parametrize(
        ("obj", "valid"),
        [
            (0, "integers"),
            (0, "real_numbers"),
            (0.0, "integers"),
            (0.0, "real_numbers"),
            (float("inf"), "real_numbers"),
            (float("nan"), "real_numbers"),
        ],
    )
    def test_passing(self, obj: object, valid: Literal["integers", "real_numbers"]) -> None:
        check_number_set(obj, valid)

    @pytest.mark.parametrize(
        ("obj", "valid", "message"),
        [
            pytest.param(
                0.1,
                "integers",
                "object must be an integer, got 0.1",
                id="float-integers",
            ),
            pytest.param(
                1j,
                "real_numbers",
                "object must be a real number, got 1j",
                id="complex-real_numbers",
            ),
            pytest.param("0", "integers", "object must be an integer, got '0'", id="str-integers"),
            pytest.param(
                "0",
                "real_numbers",
                "object must be a real number, got '0'",
                id="str-real_numbers",
            ),
        ],
    )
    def test_error(
        self,
        obj: object,
        valid: Literal["integers", "real_numbers"],
        message: str,
    ) -> None:
        with pytest.raises(ValueError, match=f"^{re.escape(message)}$"):
            check_number_set(obj, valid)


class TestCheckNumber:

    @pytest.mark.parametrize(
        (
            "number",
            "lower_bound",
            "allow_lower_bound",
            "upper_bound",
            "allow_upper_bound",
            "allow_nan",
        ),
        [
            (0, -float("inf"), True, float("inf"), True, True),
            (0, -float("inf"), True, 0, True, True),
            (0, 0, True, float("inf"), True, True),
            (0, 0, True, 0, True, True),
            (0, -1, False, 1, False, True),
            (-float("inf"), -float("inf"), True, 0, True, True),
            (float("inf"), 0, True, float("inf"), True, True),
            (float("nan"), -1, True, 1, True, True),
        ],
    )
    def test_passing(
        self,
        number: float,
        lower_bound: float,
        allow_lower_bound: bool,
        upper_bound: float,
        allow_upper_bound: bool,
        allow_nan: bool,
    ) -> None:
        check_number(
            number,
            lower_bound=lower_bound,
            allow_lower_bound=allow_lower_bound,
            upper_bound=upper_bound,
            allow_upper_bound=allow_upper_bound,
            allow_nan=allow_nan,
        )

    @pytest.mark.parametrize(
        (
            "number",
            "lower_bound",
            "allow_lower_bound",
            "upper_bound",
            "allow_upper_bound",
            "allow_nan",
            "describe_bounds",
            "message",
        ),
        [
            pytest.param(
                0,
                -float("inf"),
                True,
                -1,
                True,
                True,
                False,
                "number must be <= -1, got 0",
                id="0--inf-True--1-True-True-False",
            ),
            pytest.param(
                0,
                -float("inf"),
                True,
                -1,
                False,
                True,
                False,
                "number must be < -1, got 0",
                id="0--inf-True--1-False-True-False",
            ),
            pytest.param(
                0,
                -float("inf"),
                True,
                -1,
                True,
                True,
                True,
                "number must be <= the upper bound (-1), got 0",
                id="0--inf-True--1-True-True-True",
            ),
            pytest.param(
                0,
                1,
                True,
                float("inf"),
                True,
                True,
                False,
                "number must be >= 1, got 0",
                id="0-1-True-inf-True-True-False",
            ),
            pytest.param(
                0,
                1,
                False,
                float("inf"),
                True,
                True,
                False,
                "number must be > 1, got 0",
                id="0-1-False-inf-True-True-False",
            ),
            pytest.param(
                0,
                1,
                True,
                float("inf"),
                True,
                True,
                True,
                "number must be >= the lower bound (1), got 0",
                id="0-1-True-inf-True-True-True",
            ),
            pytest.param(
                0,
                1,
                True,
                1,
                True,
                True,
                False,
                "number must be 1, got 0",
                id="0-1-True-1-True-True-False",
            ),
            pytest.param(
                0,
                1,
                True,
                1,
                True,
                True,
                True,
                "number must be equal to the lower bound (1), got 0",
                id="0-1-True-1-True-True-True",
            ),
            pytest.param(
                -float("inf"),
                -float("inf"),
                False,
                0,
                True,
                True,
                False,
                "number must not be -inf",
                id="-inf--inf-False-0-True-True-False",
            ),
            pytest.param(
                float("inf"),
                0,
                True,
                float("inf"),
                False,
                True,
                False,
                "number must not be inf",
                id="inf-0-True-inf-False-True-False",
            ),
            pytest.param(
                float("nan"),
                -1,
                True,
                1,
                True,
                False,
                False,
                "number must not be nan",
                id="nan--1-True-1-True-False-False",
            ),
        ],
    )
    def test_error(
        self,
        number: float,
        lower_bound: float,
        allow_lower_bound: bool,
        upper_bound: float,
        allow_upper_bound: bool,
        allow_nan: bool,
        describe_bounds: bool,
        message: str,
    ) -> None:
        with pytest.raises(ValueError, match=f"^{re.escape(message)}$"):
            check_number(
                number,
                lower_bound=lower_bound,
                allow_lower_bound=allow_lower_bound,
                upper_bound=upper_bound,
                allow_upper_bound=allow_upper_bound,
                allow_nan=allow_nan,
                lower_bound_descr=("the lower bound" if describe_bounds else ""),
                upper_bound_descr=("the upper bound" if describe_bounds else ""),
            )


class TestCheckSize:

    @pytest.mark.parametrize(
        ("size", "lower_bound", "allow_lower_bound", "upper_bound", "allow_upper_bound"),
        [
            (1, 0, True, None, True),
            (1, 0, True, 1, True),
            (1, 1, True, None, True),
            (1, 0, False, 2, False),
            (1, 1, True, 1, True),
        ],
    )
    def test_passing(
        self,
        size: int,
        lower_bound: int,
        allow_lower_bound: bool,
        upper_bound: int | None,
        allow_upper_bound: bool,
    ) -> None:
        obj = [None] * size
        check_size(
            obj,
            lower_bound=lower_bound,
            allow_lower_bound=allow_lower_bound,
            upper_bound=upper_bound,
            allow_upper_bound=allow_upper_bound,
        )

    @pytest.mark.parametrize(
        (
            "size",
            "lower_bound",
            "allow_lower_bound",
            "upper_bound",
            "allow_upper_bound",
            "describe",
            "message",
        ),
        [
            pytest.param(
                2,
                0,
                True,
                1,
                True,
                False,
                "size of object must be <= 1, got 2",
                id="2-0-True-1-True-False",
            ),
            pytest.param(
                2,
                0,
                True,
                1,
                False,
                False,
                "size of object must be < 1, got 2",
                id="2-0-True-1-False-False",
            ),
            pytest.param(
                2,
                0,
                True,
                1,
                True,
                True,
                "size of object must be <= the upper bound (1), got 2",
                id="2-0-True-1-True-True",
            ),
            pytest.param(
                0,
                1,
                True,
                None,
                True,
                False,
                "size of object must be >= 1, got 0",
                id="0-1-True-None-True-False",
            ),
            pytest.param(
                0,
                1,
                False,
                None,
                True,
                False,
                "size of object must be > 1, got 0",
                id="0-1-False-None-True-False",
            ),
            pytest.param(
                0,
                1,
                True,
                None,
                True,
                True,
                "size of object must be >= the lower bound (1), got 0",
                id="0-1-True-None-True-True",
            ),
            pytest.param(
                0,
                1,
                True,
                1,
                True,
                False,
                "size of object must be 1, got 0",
                id="0-1-True-1-True-False",
            ),
            pytest.param(
                0,
                1,
                True,
                1,
                True,
                True,
                "size of object must be equal to the lower bound (1), got 0",
                id="0-1-True-1-True-True",
            ),
        ],
    )
    def test_error(
        self,
        size: int,
        lower_bound: int,
        allow_lower_bound: bool,
        upper_bound: int | None,
        allow_upper_bound: bool,
        describe: bool,
        message: str,
    ) -> None:
        obj = [None] * size
        with pytest.raises(ValueError, match=f"^{re.escape(message)}$"):
            check_size(
                obj,
                lower_bound=lower_bound,
                allow_lower_bound=allow_lower_bound,
                upper_bound=upper_bound,
                allow_upper_bound=allow_upper_bound,
                lower_bound_descr=("the lower bound" if describe else ""),
                upper_bound_descr=("the upper bound" if describe else ""),
            )


class TestCheckArray:

    @pytest.mark.parametrize(
        ("array_shape", "array_dtype", "shape", "dtypes"),
        [
            ((1, 2), np.bool_, None, ()),
            ((), None, (), ()),
            ((0,), None, (0,), ()),
            ((1,), None, (1,), ()),
            ((1,), None, (-1,), ()),
            ((0, 0), None, (0, 0), ()),
            ((1, 2), None, (1, 2), ()),
            ((1, 2), None, (-1, 2), ()),
            ((1, 2), None, (-1, -1), ()),
            ((), np.float64, None, [np.float64]),
            ((), np.float64, None, [np.dtype(np.float64)]),
            ((), np.float64, None, [np.floating]),
            ((), np.float64, None, [np.floating, np.integer]),
        ],
    )
    def test_passing(
        self,
        array_shape: Sequence[int],
        array_dtype: generic | None,
        shape: Sequence[int] | None,
        dtypes: Sequence[type[generic] | dtype[generic]],
    ) -> None:
        array = np.empty(array_shape, dtype=array_dtype)
        check_array(array, shape=shape, dtypes=dtypes)

    @pytest.mark.parametrize(
        ("n_array_dimensions", "n_dimensions", "describe", "message"),
        [
            pytest.param(
                0,
                1,
                False,
                "number of dimensions of array must be 1, got 0",
                id="0-1-False",
            ),
            pytest.param(
                1,
                2,
                False,
                "number of dimensions of array must be 2, got 1",
                id="1-2-False",
            ),
            pytest.param(
                2,
                0,
                False,
                "number of dimensions of array must be 0, got 2",
                id="2-0-False",
            ),
            pytest.param(
                0,
                1,
                True,
                "number of dimensions of array must be equal to the number (1), got 0",
                id="0-1-True",
            ),
        ],
    )
    def test_n_dimensions_error(
        self,
        n_array_dimensions: int,
        n_dimensions: int,
        describe: bool,
        message: str,
    ) -> None:
        array = np.empty((0,)*n_array_dimensions)
        shape = (-1,) * n_dimensions
        with pytest.raises(ValueError, match=f"^{re.escape(message)}$"):
            check_array(array, shape=shape, n_dimensions_descr=("the number" if describe else ""))

    @pytest.mark.parametrize(
        ("array_shape", "shape", "describe", "message"),
        [
            pytest.param((1,), (0,), False, "size of array must be 0, got 1", id="1-0-False"),
            pytest.param(
                (1, 2),
                (0, 2),
                False,
                "size of array along axis 0 must be 0, got 1",
                id="1_2-0_2-False",
            ),
            pytest.param(
                (1, 2),
                (1, 3),
                False,
                "size of array along axis 1 must be 3, got 2",
                id="1_2-1_3-False",
            ),
            pytest.param(
                (1,),
                (0,),
                True,
                "size of array must be equal to the size (0), got 1",
                id="1-0-True",
            ),
        ],
    )
    def test_size_error(
        self,
        array_shape: Sequence[int],
        shape: Sequence[int],
        describe: bool,
        message: str,
    ) -> None:
        array = np.empty(array_shape)
        with pytest.raises(ValueError, match=f"^{re.escape(message)}$"):
            check_array(
                array,
                shape=shape,
                size_descrs=(dict.fromkeys(range(len(shape)), "the size") if describe else None),
            )

    @pytest.mark.parametrize(
        ("array_dtype", "dtypes", "message"),
        [
            pytest.param(
                np.float32,
                [np.float64],
                "dtype of array must be float64, got float32",
                id="float32-float64",
            ),
            pytest.param(
                np.float32,
                [np.str_],
                "dtype of array must be str_, got float32",
                id="float32-str_",
            ),
            pytest.param(
                np.float32,
                [np.dtype(np.str_)],
                "dtype of array must be <U0, got float32",
                id="float32-dtype_str_",
            ),
            pytest.param(
                np.float32,
                [np.float64, np.integer],
                "dtype of array must be float64 or integer, got float32",
                id="float32-float64_integer",
            ),
            pytest.param(
                np.float32,
                [np.float64, np.integer, np.bool_],
                "dtype of array must be float64, integer, or bool, got float32",
                id="float32-float64_integer_bool_",
            ),
        ],
    )
    def test_dtype_error(
        self,
        array_dtype: generic,
        dtypes: Sequence[type[generic] | dtype[generic]],
        message: str,
    ) -> None:
        array = np.empty((), dtype=array_dtype)
        with pytest.raises(TypeError, match=f"^{re.escape(message)}$"):
            check_array(array, dtypes=dtypes)


class TestCheckDisjoint:

    @pytest.mark.parametrize(
        "collections",
        [
            [{}, {}],
            [{}, {1}],
            [{0}, {1}],
            [{0, 1}, {2, 3}],
            [{0}, {1}, {2}],
            [{0}, [1, 1]],
        ],
    )
    def test_passing(self, collections: Collection[Collection[object]]) -> None:
        check_disjoint(collections)

    @pytest.mark.parametrize(
        ("collection1", "collection2", "message"),
        [
            pytest.param(
                {0},
                {0},
                "collections must be disjoint, got {0} and {0}",
                id="set_0-set_0",
            ),
            pytest.param(
                {0},
                {0, 1},
                "collections must be disjoint, got {0} and {0, 1}",
                id="set_0-set_0_1",
            ),
            pytest.param(
                {0},
                [0, 0],
                "collections must be disjoint, got {0} and [0, 0]",
                id="set_0-list_0_0",
            ),
        ],
    )
    def test_error(
        self,
        collection1: Collection[object],
        collection2: Collection[object],
        message: str,
    ) -> None:
        collections = [collection1, collection2]
        with pytest.raises(ValueError, match=f"^{re.escape(message)}$"):
            check_disjoint(collections)
