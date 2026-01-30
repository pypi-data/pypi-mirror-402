from __future__ import annotations

from typing import TYPE_CHECKING

import hypothesis
import hypothesis.strategies as st
import pytest

from embcol.logging._message import ProgressMessage

if TYPE_CHECKING:
    from hypothesis.strategies import SearchStrategy


def _progress_messages(*, allow_nan: bool = True) -> SearchStrategy[ProgressMessage]:
    max_constr_vios = st.floats(min_value=0.0)
    if allow_nan:
        max_constr_vios |= st.just(float("nan"))

    return st.builds(
        ProgressMessage,
        st.integers(min_value=1),
        st.floats(allow_nan=allow_nan),
        max_constr_vios,
        st.dictionaries(st.text(), st.floats(allow_nan=allow_nan)),
    )


class TestProgressMessage:

    @pytest.mark.parametrize(
        ("progress_message", "expected"),
        [
            pytest.param(
                ProgressMessage(1, 2.0, 3.0, {}),
                "ProgressMessage(1, 2, 3, {})",
                id="empty_state",
            ),
            pytest.param(
                ProgressMessage(1, 2.0, 3.0, {"a": float("inf")}),
                "ProgressMessage(1, 2, 3, {'a': inf})",
                id="inf_state",
            ),
            pytest.param(
                ProgressMessage(1, 2.0, 3.0, {"a": float("inf"), "b": float("nan")}),
                "ProgressMessage(1, 2, 3, {'a': inf, 'b': nan})",
                id="inf_nan_state",
            ),
        ],
    )
    def test_repr(self, progress_message: ProgressMessage, expected: str) -> None:
        assert repr(progress_message) == expected

    @pytest.mark.parametrize(
        ("progress_message", "expected"),
        [
            pytest.param(
                ProgressMessage(1, 2.0, 3.0, {}),
                "iteration 1: cost=2.0, max. constraint violation=3.0",
                id="empty_state",
            ),
            pytest.param(
                ProgressMessage(1, 2.0, 3.0, {"a": float("inf")}),
                "iteration 1: cost=2.0, max. constraint violation=3.0, a=inf",
                id="inf_state",
            ),
            pytest.param(
                ProgressMessage(1, 2.0, 3.0, {"a": float("inf"), "b": float("nan")}),
                "iteration 1: cost=2.0, max. constraint violation=3.0, a=inf, b=nan",
                id="inf_nan_state",
            ),
        ],
    )
    def test_str(self, progress_message: ProgressMessage, expected: str) -> None:
        assert str(progress_message) == expected

    @hypothesis.given(progress_message=_progress_messages(allow_nan=False))
    def test_eq(self, progress_message: ProgressMessage) -> None:
        # recreate from attributes to prevent numerical error
        objs = [
            ProgressMessage(
                progress_message.iteration,
                progress_message.cost,
                progress_message.max_constr_vio,
                progress_message.state,
            )
            for _ in range(2)
        ]
        assert objs[0] == objs[1]

    @hypothesis.given(progress_message=_progress_messages())
    def test_hash(self, progress_message: ProgressMessage) -> None:
        hash(progress_message)
