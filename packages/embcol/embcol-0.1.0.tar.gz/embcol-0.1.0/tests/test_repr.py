from __future__ import annotations

import pytest

from embcol._repr import Representor


class TestRepresentor:

    class TestRepr:

        @pytest.mark.parametrize(
            ("obj", "max_width", "max_n_lines", "expected"),
            [
                pytest.param(1.0, 1, 3, "1", id="integer_float"),
                pytest.param(1.23456, 1, 3, "1.23456", id="float"),
                pytest.param(1.234567, 1, 3, "1.23457", id="float_rounded"),
                pytest.param(1e-4, 1, 3, "0.0001", id="small_float_f"),
                pytest.param(1e-5, 1, 3, "1e-05", id="small_float_e"),
                pytest.param(1e+5, 1, 3, "100000", id="large_float_f"),
                pytest.param(1e+6, 1, 3, "1e+06", id="large_float_e"),
                pytest.param([], 1, 3, "[]", id="empty_list"),
                pytest.param([0, 1, 2], 9, 1, "[0, 1, 2]", id="list_without_omission"),
                pytest.param([0, 1, 2], 8, 1, "[0, ...]", id="list_with_partial_omission"),
                pytest.param([0, 1, 2], 1, 3, "[...]", id="list_with_full_omission"),
                pytest.param([0, 1, 2], 12, 3, "[0, 1, 2]", id="list_single_line"),
                pytest.param(
                    [1000, 2000, 3000],
                    15,
                    4,
                    (
                        "[\n"
                        "    1000, 2000,\n"
                        "    3000,\n"
                        "]"
                    ),
                    id="list_multiple_lines",
                ),
                pytest.param(
                    [1000, 2000, 30000000000],
                    15,
                    4,
                    (
                        "[\n"
                        "    1000, 2000,\n"
                        "    30000000000,\n"
                        "]"
                    ),
                    id="list_multiple_lines_long",
                ),
                pytest.param(
                    [1000, 2000, 3000, 40000],
                    15,
                    4,
                    (
                        "[\n"
                        "    1000, 2000,\n"
                        "    3000, ...\n"
                        "]"
                    ),
                    id="list_multiple_lines_with_omission",
                ),
                pytest.param(
                    [[0, 1, 2], [3], [4]],
                    13,
                    7,
                    (
                        "[\n"
                        "    [\n"
                        "        0, 1,\n"
                        "        2,\n"
                        "    ],\n"
                        "    [3], [4],\n"
                        "]"
                    ),
                    id="nested_list",
                ),
                pytest.param((), 1, 3, "()", id="empty_tuple"),
                pytest.param((0,), 4, 3, "(0,)", id="size_1_tuple"),
                pytest.param((0, 1, 2), 1, 3, "(...)", id="tuple_with_full_omission"),
                pytest.param(set(), 1, 3, "set()", id="empty_set"),
                pytest.param({0, 1, 2}, 1, 3, "set(...)", id="set_with_full_omission"),
                pytest.param({}, 1, 3, "{}", id="empty_dict"),
                pytest.param({0: "a", 1: "b"}, 1, 3, "{...}", id="dict_with_full_omission"),
                pytest.param(
                    {(0, 1): [0, 1, 2]},
                    19,
                    3,
                    "{(0, 1): [0, 1, 2]}",
                    id="dict_single_line",
                ),
                pytest.param(
                    {(0, 1): [0, 1, 2]},
                    13,
                    6,
                    (
                        "{\n"
                        "    (0, 1): [\n"
                        "        0, 1,\n"
                        "        2,\n"
                        "    ],\n"
                        "}"
                    ),
                    id="dict_multiple_lines",
                ),
                pytest.param(
                    {(0, 10): [0]},
                    13,
                    6,
                    (
                        "{\n"
                        "    (\n"
                        "        0,\n"
                        "        10,\n"
                        "    ): [0],\n"
                        "}"
                    ),
                    id="dict_key_multiple_lines_value_single_line",
                ),
                pytest.param(
                    {(0, 10): [0, 1, 2]},
                    13,
                    9,
                    (
                        "{\n"
                        "    (\n"
                        "        0,\n"
                        "        10,\n"
                        "    ): [\n"
                        "        0, 1,\n"
                        "        2,\n"
                        "    ],\n"
                        "}"
                    ),
                    id="dict_key_multiple_lines_value_multiple_lines",
                ),
            ],
        )
        def test_obj(self, obj: object, max_width: int, max_n_lines: int, expected: str) -> None:
            r = Representor(max_width=max_width, max_n_lines=max_n_lines)
            actual = r.repr(obj)
            assert actual == expected

        def test_level(self) -> None:
            r = Representor()
            actual = r.repr(0, level=1)
            expected = "    0"
            assert actual == expected

        def test_prefix(self) -> None:
            r = Representor()
            actual = r.repr(0, prefix="prefix")
            expected = "prefix0"
            assert actual == expected

        def test_suffix(self) -> None:
            r = Representor()
            actual = r.repr(0, suffix="suffix")
            expected = "0suffix"
            assert actual == expected
