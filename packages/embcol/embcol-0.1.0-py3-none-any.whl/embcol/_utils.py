"""Utilities."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from typing import Any

    from ._typing_imports import TypeIs

__all__ = ["connect_words", "is_iterable"]


def is_iterable(obj: object) -> TypeIs[Iterable[Any]]:
    """Check if an object is an iterable.

    A `str` object is not regarded as an iterable.

    Parameters
    ----------
    obj : object
        Object to be checked.

    Returns
    -------
    bool
        ``True`` if an object is an iterable.
    """
    try:
        iter(obj)  # type: ignore[call-overload]
    except TypeError:
        return False
    return not isinstance(obj, str)


def connect_words(words: Sequence[str], conj: str) -> str:
    """Connect words using a conjunction.

    Parameters
    ----------
    words : sequence of str
        Words to be connected.
    conj : str
        Conjunction connecting words.

    Returns
    -------
    str
        Connected text.
    """
    match len(words):
        case 0:
            return ""
        case 1:
            return words[0]
        case 2:
            return f"{words[0]} {conj} {words[1]}"
        case _:
            return f"{', '.join(words[:-1])}, {conj} {words[-1]}"
