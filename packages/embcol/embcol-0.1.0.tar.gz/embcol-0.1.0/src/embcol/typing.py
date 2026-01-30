"""Type hints."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Protocol, SupportsIndex, TypeVar

import numpy as np

from ._typing_imports import TypeAliasType

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Any

    from numpy import dtype, ndarray

__all__ = [
    "Array1D",
    "Array2D",
    "Array3D",
    "Array4D",
    "Array5D",
    "ArrayLike1D",
    "ArrayLike2D",
    "Callback",
    "RNGLike",
    "SequenceND",
    "SupportsArray",
]

_T = TypeVar("_T")
_T_co = TypeVar("_T_co", covariant=True)

_ScalarT = TypeVar("_ScalarT", bound=np.generic)
_ScalarT_co = TypeVar("_ScalarT_co", bound=np.generic, covariant=True)

_ShapeT_co = TypeVar("_ShapeT_co", bound=tuple[int, ...], covariant=True)


class SequenceND(Protocol[_T_co]):
    """Protocol for a multi-dimensional sequence."""

    def __len__(self) -> int: ...

    def __getitem__(self: SequenceND[_T_co], key: SupportsIndex) -> _T_co | SequenceND[_T_co]: ...

    def __iter__(self: SequenceND[_T_co]) -> Iterator[_T_co] | Iterator[SequenceND[_T_co]]: ...

    def __reversed__(self: SequenceND[_T_co]) -> Iterator[_T_co] | Iterator[SequenceND[_T_co]]: ...

    def __contains__(self, item: object) -> bool: ...

    def count(self, value: object, /) -> int:
        """Count a given object along the first dimension."""
        ...

    def index(
        self,
        value: object,
        start: SupportsIndex = ...,
        stop: SupportsIndex | None = ...,
    ) -> int:
        """Return an index of the first occurrence of a given object along the first dimension."""
        ...


class SupportsArray(Protocol[_ShapeT_co, _ScalarT_co]):
    """Protocol supporting the ``__array__`` method."""

    def __array__(
        self,
        dtype: None = ...,
        /,
        *,
        copy: Any = ...,  # noqa: ANN401
    ) -> ndarray[_ShapeT_co, dtype[_ScalarT_co]]:
        ...


ArrayLike1D = TypeAliasType(
    "ArrayLike1D",
    Sequence[_T] | SupportsArray[tuple[int], _ScalarT],
    type_params=(_T, _ScalarT),
)  #: :meta public:
ArrayLike2D = TypeAliasType(
    "ArrayLike2D",
    Sequence[ArrayLike1D[_T, _ScalarT]] | SupportsArray[tuple[int, int], _ScalarT],
    type_params=(_T, _ScalarT),
)  #: :meta public:

Array1D = TypeAliasType(
    "Array1D",
    np.ndarray[tuple[int], np.dtype[_ScalarT]],
    type_params=(_ScalarT,),
)  #: :meta public:
Array2D = TypeAliasType(
    "Array2D",
    np.ndarray[tuple[int, int], np.dtype[_ScalarT]],
    type_params=(_ScalarT,),
)  #: :meta public:
Array3D = TypeAliasType(
    "Array3D",
    np.ndarray[tuple[int, int, int], np.dtype[_ScalarT]],
    type_params=(_ScalarT,),
)  #: :meta public:
Array4D = TypeAliasType(
    "Array4D",
    np.ndarray[tuple[int, int, int, int], np.dtype[_ScalarT]],
    type_params=(_ScalarT,),
)  #: :meta public:
Array5D = TypeAliasType(
    "Array5D",
    np.ndarray[tuple[int, int, int, int, int], np.dtype[_ScalarT]],
    type_params=(_ScalarT,),
)  #: :meta public:

RNGLike = TypeAliasType(
    "RNGLike",
    (
        int
        | np.integer
        | SequenceND[int]
        | np.ndarray[tuple[int, ...], np.dtype[np.integer]]
        | np.random.SeedSequence
        | np.random.BitGenerator
        | np.random.Generator
        | None
    ),
)  #: :meta public:

Callback = TypeAliasType(
    "Callback",
    Callable[[Array1D[np.float64], float, dict[str, float]], None],
)  #: :meta public:
