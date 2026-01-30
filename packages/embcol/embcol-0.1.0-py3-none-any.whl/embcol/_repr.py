"""Text representation of objects."""

from __future__ import annotations

import itertools
from typing import TYPE_CHECKING, ClassVar

from ._checking import check_number, check_number_set
from ._exception import expr

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = ["Representor"]


class Representor:
    """Class for representing objects in texts.

    Parameters
    ----------
    max_width : int, optional
        Maximum width of lines.
    max_n_lines : int, optional
        Maximum number of lines.

    Notes
    -----
    The width of a line may exceed the `max_width` argument if a long text cannot be separate into
    multiple lines.
    """

    INDENT: ClassVar[str] = " " * 4
    OMISSION: ClassVar[str] = "..."

    _max_width: int
    _max_n_lines: int

    def __init__(self, max_width: int = 79, max_n_lines: int = 1) -> None:
        check_number_set(max_width, "integers", target=expr("max_width"))
        check_number(max_width, lower_bound=1, target=expr("max_width"))
        max_width = int(max_width)

        check_number_set(max_n_lines, "integers", target=expr("max_n_lines"))
        check_number(max_n_lines, lower_bound=1, target=expr("max_n_lines"))
        max_n_lines = int(max_n_lines)

        self._max_width = max_width
        self._max_n_lines = max_n_lines

    def repr(self, obj: object, level: int = 0, prefix: str = "", suffix: str = "") -> str:
        """Represent an object in a text.

        Parameters
        ----------
        obj : object
            Object to be represented in a text.
        level : int, optional
            Indentation level.
        prefix : str, optional
            Prefix of a text.
        suffix : str, optional
            Suffix of a text.

        Returns
        -------
        str
            Text representation of an object.
        """
        return "\n".join(
            f"{self.INDENT*level}{line}"
            for line in self._get_lines(obj, level, prefix, suffix)
        )

    def repr_constructor(self, name: str, *args: object, **kwargs: object) -> str:
        """Represent a constructor in a text.

        The `max_width` and `max_n_lines` attributes are applied to each argument of a constructor.

        Parameters
        ----------
        name : str
            Class name.
        *args
            Positional arguments of constructor.
        **kwargs
            Keyword arguments of constructor.

        Returns
        -------
        str
            Text representation of a constructor.
        """
        prefix, suffix = f"{name}(", ")"

        # single line
        item_strs: list[str] = []
        width = len(prefix) + len(suffix)
        for key, value in itertools.chain(zip(itertools.repeat(None), args), kwargs.items()):
            lines = self._get_lines(value, 0, "" if key is None else f"{key}=", "")
            if len(lines) != 1:
                break
            item_str = lines[0]

            next_width = width + 2 + len(item_str) if item_strs else width + len(item_str)
            if self._max_width < next_width:
                break

            item_strs.append(item_str)
            width = next_width
        else:
            return prefix + ", ".join(item_strs) + suffix

        # multiple lines
        return "\n".join(
            [
                prefix,
                *(
                    f"{self.INDENT}{line}"
                    for arg in args
                    for line in self._get_lines(arg, 1, "", ",")
                ),
                *(
                    f"{self.INDENT}{line}"
                    for key, value in kwargs.items()
                    for line in self._get_lines(value, 1, f"{key}=", ",")
                ),
                suffix,
            ],
        )

    def _get_lines(self, obj: object, level: int, prefix: str, suffix: str) -> list[str]:  # noqa: PLR0911
        """Get lines of a text representation.

        Parameters
        ----------
        obj : object
            Object to be represented.
        level : int
            Indentation level.
        prefix : str
            Prefix of a text.
        suffix : str
            Suffix of a text.

        Returns
        -------
        list of str
            Lines of a text. Lines do not include indentation.
        """
        match obj:
            case float():
                return self._get_float_lines(obj, prefix, suffix)
            case list():
                return self._get_sequence_lines(obj, level, f"{prefix}[", f"]{suffix}")
            case tuple():
                return self._get_tuple_lines(obj, level, prefix, suffix)
            case set():
                return self._get_set_lines(obj, level, prefix, suffix)
            case dict():
                return self._get_sequence_lines(
                    [_KeyValuePair(key, ": ", value) for key, value in obj.items()],
                    level,
                    f"{prefix}{{",
                    f"}}{suffix}",
                )
            case _KeyValuePair():
                return self._get_key_value_pair_lines(obj, level, prefix, suffix)
            case _:
                return self._get_object_lines(obj, prefix, suffix)

    def _get_float_lines(self, obj: float, prefix: str, suffix: str) -> list[str]:
        return [f"{prefix}{obj:g}{suffix}"]

    def _get_tuple_lines(
        self,
        obj: tuple[object, ...],
        level: int,
        prefix: str,
        suffix: str,
    ) -> list[str]:
        if len(obj) != 1:
            return self._get_sequence_lines(obj, level, f"{prefix}(", f"){suffix}")

        lines = self._get_sequence_lines(obj, level, f"{prefix}(", f",){suffix}")
        if len(lines) != 1:
            lines[-1] = f"){suffix}"
        return lines

    def _get_set_lines(self, obj: set[object], level: int, prefix: str, suffix: str) -> list[str]:
        if obj:
            lines = self._get_sequence_lines(list(obj), level, f"{prefix}{{", f"}}{suffix}")
            if lines == [f"{prefix}{{{self.OMISSION}}}{suffix}"]:
                return [f"{prefix}set({self.OMISSION}){suffix}"]
            return lines
        return [f"{prefix}set(){suffix}"]

    def _get_key_value_pair_lines(
        self,
        obj: _KeyValuePair,
        level: int,
        prefix: str,
        suffix: str,
    ) -> list[str]:
        key_lines = self._get_lines(obj.key, level, prefix, obj.separator)
        lines = self._get_lines(obj.value, level, key_lines[-1], suffix)
        if self._max_width < level*len(self.INDENT)+len(lines[0]):
            value_front = lines[0][len(key_lines[-1]):]
            key_lines = self._get_lines(obj.key, level, prefix, f"{obj.separator}{value_front}")
            lines = self._get_lines(obj.value, level, key_lines[-1][:-len(value_front)], suffix)
        return [*key_lines[:-1], *lines]

    def _get_sequence_lines(  # noqa: C901, PLR0912, PLR0915
        self,
        obj: Sequence[object],
        level: int,
        prefix: str,
        suffix: str,
    ) -> list[str]:
        if not obj:
            return [f"{prefix}{suffix}"]

        indent_width = level * len(self.INDENT)

        # single line without omission
        item_strs: list[str] = []
        width = indent_width + len(prefix) + len(suffix)
        for item in obj:
            lines = self._get_lines(item, level, "", "")
            if len(lines) != 1:
                break
            item_str = lines[0]

            next_width = width + 2 + len(item_str) if item_strs else width + len(item_str)
            if self._max_width < next_width:
                break

            item_strs.append(item_str)
            width = next_width
        else:
            return [prefix+", ".join(item_strs)+suffix]

        # single line with omission
        while item_strs and self._max_width < width+2+len(self.OMISSION):
            item_str = item_strs.pop()
            width -= 2 + len(item_str)
        item_strs.append(self.OMISSION)
        n_items_single = len(item_strs) - 1
        single_line = prefix + ", ".join(item_strs) + suffix

        if self._max_n_lines < 3:
            return [single_line]

        # multiple lines without omission
        item_lines: list[list[str] | tuple[str, ...]] = []
        n_lines = 2
        width = 0
        for item in obj:
            lines = self._get_lines(item, level+1, "", ",")  # include trailing comma
            if len(lines) == 1:
                item_str = lines[0]
                if (
                    item_lines
                    and isinstance(item_lines[-1], list)  # multiple items in the last line
                    and width+1+len(item_str) <= self._max_width
                ):
                    # append an item to the last line
                    item_lines[-1].append(item_str)
                    width += 1 + len(item_str)
                elif n_lines+1 <= self._max_n_lines:
                    # append an item to a new line
                    item_lines.append([item_str])
                    n_lines += 1
                    width = indent_width + len(self.INDENT) + len(item_str)
                else:
                    break
            elif n_lines+len(lines) <= self._max_n_lines:
                # append lines of an item
                item_lines.append(tuple(lines))
                n_lines += len(lines)
            else:
                break
        else:
            out = [prefix]
            for seq in item_lines:
                if isinstance(seq, list):  # multiple items in a line
                    out.append(self.INDENT+" ".join(seq))
                else:  # an item across multiple lines
                    out.extend(f"{self.INDENT}{line}" for line in seq)
            out.append(suffix)
            return out

        # multiple lines with omission
        if self._max_n_lines < n_lines+1:
            # remove items to make room for the omission mark
            if isinstance(item_lines[-1], list):  # multiple items in the last line
                while item_lines[-1] and self._max_width < width+1+len(self.OMISSION):
                    item_str = item_lines[-1].pop()
                    width -= 1 + len(item_str)
                if not item_lines[-1]:
                    item_lines.pop()
            else:  # an item across multiple lines
                item_lines.pop()
        if (
            item_lines
            and isinstance(item_lines[-1], list)  # multiple items in the last line
            and (
                indent_width
                + len(self.INDENT)
                + sum(len(item_str) for item_str in item_lines[-1])
                + len(self.OMISSION)
                + len(item_lines[-1])
                <= self._max_width
            )
        ):
            # append the omission mark to the last line
            item_lines[-1].append(self.OMISSION)
        else:
            # append the omission mark to a new line
            item_lines.append([self.OMISSION])
        n_items_multi = sum(len(seq) if isinstance(seq, list) else 1 for seq in item_lines) - 1

        if n_items_multi <= n_items_single:
            return [single_line]

        out = [prefix]
        for seq in item_lines:
            if isinstance(seq, list):  # multiple items in a line
                out.append(self.INDENT+" ".join(seq))
            else:  # an item across multiple lines
                out.extend(f"{self.INDENT}{line}" for line in seq)
        out.append(suffix)
        return out

    def _get_object_lines(self, obj: object, prefix: str, suffix: str) -> list[str]:
        lines = repr(obj).splitlines()
        if len(lines) == 1:
            return [f"{prefix}{lines[0]}{suffix}"]
        return [f"{prefix}{lines[0]}", *lines[1:-1], f"{lines[-1]}{suffix}"]


class _KeyValuePair:

    key: object
    separator: str
    value: object

    def __init__(self, key: object, separator: str, value: object) -> None:
        self.key = key
        self.separator = separator
        self.value = value
