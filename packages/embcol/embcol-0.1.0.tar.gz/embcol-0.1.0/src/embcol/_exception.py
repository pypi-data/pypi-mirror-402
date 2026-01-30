"""Error object generation."""

from __future__ import annotations

from collections.abc import Collection, Iterable, Mapping, Sequence
from typing import TYPE_CHECKING

import numpy as np

from ._typing_imports import assert_never
from ._utils import connect_words

if TYPE_CHECKING:
    from typing import Literal

    from numpy import dtype, generic

    from ._typing_imports import Unpack

__all__ = [
    "invalid_dtype_error",
    "invalid_n_dimensions_error",
    "invalid_size_error",
    "invalid_type_error",
    "invalid_value_error",
    "out_of_number_set_error",
    "out_of_range_error",
    "out_of_range_size_error",
    "overlapping_collections_error",
]


def invalid_type_error(
    actual_obj: object,
    valid: Sequence[type | Literal["callable"] | None] = (),
    *,
    target: str = "object",
) -> TypeError:
    """Make an error object for an invalid type.

    Parameters
    ----------
    actual_obj : object
        Target object whose type is invalid.
    valid : sequence of {type, 'callable', None}, optional
        Valid types.
    target : str, optional
        Explanation about a target object.

    Returns
    -------
    TypeError
        Error object.
    """
    actual_str = (
        "callable"
        if callable(actual_obj) else
        "None"
        if actual_obj is None else
        type(actual_obj).__name__
    )
    if valid:
        valid_str = connect_words(
            [
                "mapping"
                if t is Mapping else
                "sequence"
                if t is Sequence else
                "collection"
                if t is Collection else
                "iterable"
                if t is Iterable else
                "callable"
                if t == "callable" else
                "None"
                if t is None else
                t.__name__
                for t in valid
            ],
            "or",
        )
        message = f"{target} must be {valid_str}, got {actual_str}"
    else:
        message = f"{target} must not be {actual_str}"
    return TypeError(message)


def invalid_dtype_error(
    actual: dtype[generic],
    valid: Sequence[type[generic] | dtype[generic]] = (),
    *,
    target: str = "array",
) -> TypeError:
    """Make an error object for an invalid data type.

    Parameters
    ----------
    actual : numpy.dtype
        Invalid data type of a target object.
    valid : sequence of {type, numpy.dtype}, optional
        Valid data types.
    target : str, optional
        Explanation about a target object.

    Returns
    -------
    TypeError
        Error object.
    """
    if valid:
        valid_str = connect_words(
            [str(t) if isinstance(t, np.dtype) else t.__name__ for t in valid],
            "or",
        )
        message = f"dtype of {target} must be {valid_str}, got {actual}"
    else:
        message = f"dtype of {target} must not be {actual}"
    return TypeError(message)


def invalid_value_error(
    actual: object,
    valid: Sequence[object] = (),
    *,
    target: str = "object",
    descr: str = "",
) -> ValueError:
    """Make an error object for an invalid value.

    Parameters
    ----------
    actual : object
        Target object whose value is invalid.
    valid : sequence, optional
        Valid values.
    target : str, optional
        Explanation about a target object.
    descr : str, optional
        Description of valid values.

    Returns
    -------
    ValueError
        Error object.
    """
    if valid:
        valid_str = connect_words([repr(v) for v in valid], "or")
        message = (
            f"{target} must be equal to {descr} ({valid_str}), got {actual!r}"
            if descr else
            f"{target} must be {valid_str}, got {actual!r}"
        )
    elif descr:
        message = f"{target} must be equal to {descr}, got {actual!r}"
    else:
        message = f"{target} must not be {actual!r}"
    return ValueError(message)


def out_of_range_error(
    actual: object,
    relation: Literal["<", "<=", ">", ">="],
    bound: object,
    *,
    target: str = "object",
    descr: str = "",
) -> ValueError:
    """Make an error object for a value out of range.

    Parameters
    ----------
    actual : object
        Target object out of range.
    relation : {'<', '<=', '>', '>='}
        Relation between valid values and a bound.
    bound : object
        Bound of valid values. A bound is on the right-hand side of an inequality.
    target : str, optional
        Explanation about a target object.
    descr : str, optional
        Description of a bound of valid values.

    Returns
    -------
    ValueError
        Error object.
    """
    message = (
        f"{target} must be {relation} {descr} ({bound!r}), got {actual!r}"
        if descr else
        f"{target} must be {relation} {bound!r}, got {actual!r}"
    )
    return ValueError(message)


def out_of_number_set_error(
    actual: object,
    valid: Literal["integers", "real_numbers"],
    *,
    target: str = "object",
) -> ValueError:
    """Make an error object for an object out of a number set.

    Parameters
    ----------
    actual : object
        Target object out of a number set.
    valid : {'integers', 'real_numbers'}
        Number set whose members are valid.
    target : str, optional
        Explanation about a target object.

    Returns
    -------
    ValueError
        Error object.
    """
    match valid:
        case "integers":
            valid_str = "an integer"
        case "real_numbers":
            valid_str = "a real number"
        case _:
            assert_never(valid)
    message = f"{target} must be {valid_str}, got {actual!r}"
    return ValueError(message)


def invalid_n_dimensions_error(
    actual: int,
    valid: Sequence[int] = (),
    *,
    target: str = "object",
    descr: str = "",
) -> ValueError:
    """Make an error object for an invalid number of dimensions.

    Parameters
    ----------
    actual : object
        Invalid number of dimensions of a target object.
    valid : sequence of int, optional
        Valid numbers of dimensions.
    target : str, optional
        Explanation about a target object.
    descr : str, optional
        Description of valid numbers of dimensions.

    Returns
    -------
    ValueError
        Error object.
    """
    return invalid_value_error(
        actual,
        valid,
        target=f"number of dimensions of {target}",
        descr=descr,
    )


def invalid_size_error(
    actual: int,
    valid: Sequence[int] = (),
    *,
    axis: int | None = None,
    target: str = "object",
    descr: str = "",
) -> ValueError:
    """Make an error object for an invalid size.

    Parameters
    ----------
    actual : object
        Invalid size of a target object.
    valid : sequence of int, optional
        Valid sizes.
    axis : int, optional
        Axis along which the size is invalid. If nothing is given, a target object is regarded as
        one-dimensional.
    target : str, optional
        Explanation about a target object.
    descr : str, optional
        Description of valid size.

    Returns
    -------
    ValueError
        Error object.
    """
    return invalid_value_error(
        actual,
        valid,
        target=_size_of_target(target, axis=axis),
        descr=descr,
    )


def out_of_range_size_error(
    actual: int,
    relation: Literal["<", "<=", ">", ">="],
    bound: int,
    *,
    axis: int | None = None,
    target: str = "object",
    descr: str = "",
) -> ValueError:
    """Make an error object for a size out of range.

    Parameters
    ----------
    actual : object
        Size of a target object out of range.
    relation : {'<', '<=', '>', '>='}
        Relation between valid sizes and a bound.
    bound : object
        Bound of valid sizes. A bound is on the right-hand side of an inequality.
    axis : int, optional
        Axis along which the size is out of range. If nothing is given, a target object is regarded
        as one-dimensional.
    target : str, optional
        Explanation about a target object.
    descr : str, optional
        Description of a bound of valid sizes.

    Returns
    -------
    ValueError
        Error object.
    """
    return out_of_range_error(
        actual,
        relation,
        bound,
        target=_size_of_target(target, axis=axis),
        descr=descr,
    )


def overlapping_collections_error(
    actual1: Collection[object],
    actual2: Collection[object],
    *,
    targets: str | tuple[str, str, Unpack[tuple[str, ...]]] = "collections",
) -> ValueError:
    """Make an error object for overlapping collections.

    Parameters
    ----------
    actual1 : object
        First target object overlapping with the second target object.
    actual2 : object
        Second target object overlapping with the first target object.
    targets : str or tuple of str, optional
        Explanation about target objects. If a `str` object is given, it is an explanation about
        a set of target objects. If a `tuple` object is given, its item is an explanation about each
        target object.

    Returns
    -------
    ValueError
        Error object.
    """
    targets_str = connect_words(targets, "and") if isinstance(targets, tuple) else targets
    message = f"{targets_str} must be disjoint, got {actual1!r} and {actual2!r}"
    return ValueError(message)


def expr(text: str) -> str:
    """Format a text of an expression to be suitable for an error message.

    Parameters
    ----------
    text : str
        Text of an expression.

    Returns
    -------
    str
        Formatted text.
    """
    return f"'{text}'"


def _size_of_target(target: str, *, axis: int | None = None) -> str:
    return f"size of {target}" if axis is None else f"size of {target} along axis {axis}"
