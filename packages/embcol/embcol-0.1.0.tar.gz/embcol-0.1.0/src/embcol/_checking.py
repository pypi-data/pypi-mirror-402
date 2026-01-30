"""Argument checking."""

from __future__ import annotations

from collections.abc import Iterable
import itertools
import math
import operator
from typing import TYPE_CHECKING, SupportsFloat, SupportsIndex, SupportsInt

import numpy as np

from ._exception import (
    invalid_dtype_error,
    invalid_n_dimensions_error,
    invalid_size_error,
    invalid_type_error,
    invalid_value_error,
    out_of_number_set_error,
    out_of_range_error,
    out_of_range_size_error,
    overlapping_collections_error,
)
from ._typing_imports import assert_never
from ._utils import is_iterable

if TYPE_CHECKING:
    from collections.abc import Collection, Mapping, Sequence, Sized
    from typing import Literal

    from numpy import dtype, generic
    from numpy.typing import NDArray

    from ._typing_imports import Unpack

__all__ = [
    "check_array",
    "check_disjoint",
    "check_number",
    "check_number_set",
    "check_size",
    "check_type",
    "check_value",
]


def check_type(
    obj: object,
    valid: Sequence[type | Literal["callable"] | None],
    *,
    target: str = "object",
) -> None:
    """Check if a type is valid.

    Parameters
    ----------
    obj : object
        Target object to be checked.
    valid : sequence of {type, 'callable', None}
        Valid types.
    target : str, optional
        Explanation about a target object.

    Raises
    ------
    TypeError
        If the type is not valid.
    """
    valid_types = [t for t in valid if isinstance(t, type) and t is not Iterable]
    if not (
        (is_iterable(obj) and Iterable in valid)
        or (callable(obj) and "callable" in valid)
        or (obj is None and None in valid)
        or isinstance(obj, tuple(valid_types))
    ):
        raise invalid_type_error(obj, valid, target=target)


def check_value(
    obj: object,
    valid: Sequence[object],
    *,
    target: str = "object",
    descr: str = "",
) -> None:
    """Check if a value is valid.

    Parameters
    ----------
    obj : object
        Target object to be checked.
    valid : sequence
        Valid values.
    target : str, optional
        Explanation about a target object.

    Raises
    ------
    ValueError
        If the value is not valid.
    """
    if obj not in valid:
        raise invalid_value_error(obj, valid, target=target, descr=descr)


def check_number_set(
    obj: object,
    valid: Literal["integers", "real_numbers"],
    *,
    target: str = "object",
) -> None:
    """Check if an object is in a valid number set.

    Parameters
    ----------
    obj : object
        Target object to be checked.
    valid : {'integers', 'real_numbers'}
        Valid number set.
    target : str, optional
        Explanation about a target object.

    Raises
    ------
    ValueError
        If a target object is out of a valid number set.
    """
    match valid:
        case "integers":
            if not (isinstance(obj, (SupportsInt, SupportsIndex)) and int(obj) == obj):
                raise out_of_number_set_error(obj, "integers", target=target)
        case "real_numbers":
            if not (
                isinstance(obj, (SupportsFloat, SupportsIndex))
                and (float(obj) == obj or math.isnan(obj))
            ):
                raise out_of_number_set_error(obj, "real_numbers", target=target)
        case _:
            assert_never(valid)


def check_number(  # noqa: C901
    number: float,
    *,
    lower_bound: float = -float("inf"),
    allow_lower_bound: bool = True,
    upper_bound: float = float("inf"),
    allow_upper_bound: bool = True,
    allow_nan: bool = True,
    target: str = "number",
    lower_bound_descr: str = "",
    upper_bound_descr: str = "",
) -> None:
    """Check if a number is in a valid range.

    Parameters
    ----------
    number : float
        Target object to be checked.
    lower_bound : float, optional
        Lower bound of a valid range.
    allow_lower_bound : bool, optional
        If ``True`` is given, the lower bound is inclusive.
    upper_bound : float, optional
        Upper bound of a valid range.
    allow_upper_bound : bool, optional
        If ``True`` is given, the upper bound is inclusive.
    allow_nan : bool, optional
        If ``True`` is given, NaN is valid.
    target : str, optional
        Explanation about a target object.
    lower_bound_descr : str, optional
        Description of the lower bound.
    upper_bound_descr : str, optional
        Description of the upper bound.

    Raises
    ------
    ValueError
        If a target object is out of range.
    """
    if math.isnan(number):
        if not allow_nan:
            raise invalid_value_error(number, target=target)
        return

    if lower_bound == upper_bound and allow_lower_bound and allow_upper_bound:
        if number != lower_bound:
            raise invalid_value_error(number, [lower_bound], target=target, descr=lower_bound_descr)
        return

    relation: Literal["<", "<=", ">", ">="]

    if lower_bound == -float("inf") and not allow_lower_bound:
        if number == -float("inf"):
            raise invalid_value_error(number, target=target, descr=lower_bound_descr)
    else:
        relation, op = (">=", operator.ge) if allow_lower_bound else (">", operator.gt)
        if not op(number, lower_bound):
            raise out_of_range_error(
                number,
                relation,
                lower_bound,
                target=target,
                descr=lower_bound_descr,
            )

    if upper_bound == float("inf") and not allow_upper_bound:
        if number == float("inf"):
            raise invalid_value_error(number, target=target, descr=upper_bound_descr)
    else:
        relation, op = ("<=", operator.le) if allow_upper_bound else ("<", operator.lt)
        if not op(number, upper_bound):
            raise out_of_range_error(
                number,
                relation,
                upper_bound,
                target=target,
                descr=upper_bound_descr,
            )


def check_size(
    obj: Sized,
    *,
    lower_bound: int = 0,
    allow_lower_bound: bool = True,
    upper_bound: int | None = None,
    allow_upper_bound: bool = True,
    target: str = "object",
    lower_bound_descr: str = "",
    upper_bound_descr: str = "",
) -> None:
    """Check if the size of an object is in a valid range.

    Parameters
    ----------
    obj : object
        Target object to be checked.
    lower_bound : int, optional
        Lower bound of a valid range.
    allow_lower_bound : bool, optional
        If ``True`` is given, the lower bound is inclusive.
    upper_bound : int, optional
        Upper bound of a valid range. If nothing is given, the upper bound does not exist.
    allow_upper_bound : bool, optional
        If ``True`` is given, the upper bound is inclusive.
    target : str, optional
        Explanation about a target object.
    lower_bound_descr : str, optional
        Description of the lower bound.
    upper_bound_descr : str, optional
        Description of the upper bound.

    Raises
    ------
    ValueError
        If the size is out of range.
    """
    size = len(obj)

    if lower_bound == upper_bound and allow_lower_bound and allow_upper_bound:
        if size != lower_bound:
            raise invalid_size_error(size, [lower_bound], target=target, descr=lower_bound_descr)
        return

    relation: Literal["<", "<=", ">", ">="]

    relation, op = (">=", operator.ge) if allow_lower_bound else (">", operator.gt)
    if not op(size, lower_bound):
        raise out_of_range_size_error(
            size,
            relation,
            lower_bound,
            target=target,
            descr=lower_bound_descr,
        )

    if upper_bound is not None:
        relation, op = ("<=", operator.le) if allow_upper_bound else ("<", operator.lt)
        if not op(size, upper_bound):
            raise out_of_range_size_error(
                size,
                relation,
                upper_bound,
                target=target,
                descr=upper_bound_descr,
            )


def check_array(
    array: NDArray[generic],
    *,
    shape: Sequence[int] | None = None,
    dtypes: Sequence[type[generic] | dtype[generic]] = (),
    target: str = "array",
    n_dimensions_descr: str = "",
    size_descrs: Mapping[int, str] | None = None,
) -> None:
    """Check if an array has a valid shape and a valid data type.

    Parameters
    ----------
    array : numpy.ndarray
        Target object to be checked.
    shape : sequence of int, optional
        Valid shape. An item of ``-1`` means that any size is allowed along that axis. If nothing is
        given, the shape is not checked.
    dtypes : sequence of {type, numpy.dtype}, optional
        Valid data types. If nothing is given, the data type is not checked.
    target : str, optional
        Explanation about a target object.
    n_dimensions_descr : str, optional
        Description of the number of dimensions.
    size_descrs : mapping of int to str, optional
        Descriptions of the sizes along axes.

    Raises
    ------
    ValueError
        If the number of dimensions is not valid. If the size along an axis is not valid.
    TypeError
        If the data type is not valid.
    """
    if size_descrs is None:
        size_descrs = {}

    if shape is not None:
        if array.ndim != len(shape):
            raise invalid_n_dimensions_error(
                array.ndim,
                [len(shape)],
                target=target,
                descr=n_dimensions_descr,
            )

        for axis, (actual, valid) in enumerate(zip(array.shape, shape, strict=True)):
            if valid == -1:
                continue
            if actual != valid:
                raise invalid_size_error(
                    actual,
                    [valid],
                    axis=(axis if 2 <= array.ndim else None),
                    target=target,
                    descr=size_descrs.get(axis, ""),
                )

    if dtypes and not any(np.issubdtype(array.dtype, dtype) for dtype in dtypes):
        raise invalid_dtype_error(array.dtype, dtypes, target=target)


def check_disjoint(
    collections: Collection[Collection[object]],
    *,
    targets: str | tuple[str, str, Unpack[tuple[str, ...]]] = "collections",
) -> None:
    """Check if collections are disjoint.

    Parameters
    ----------
    collections : collection of collection
        Set of target objects to be checked.
    targets : str, tuple of str, optional
        Explanation about target objects. If a `str` object is given, it is an explanation about
        a set of target objects. If a `tuple` object is given, its item is an explanation about each
        target object.

    Raises
    ------
    ValueError
        If target objects are not disjoint.
    """
    for collection1, collection2 in itertools.combinations(collections, 2):
        if any(item1 in collection2 for item1 in collection1):
            raise overlapping_collections_error(collection1, collection2, targets=targets)
