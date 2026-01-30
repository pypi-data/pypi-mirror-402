from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING, cast

import plotly.graph_objects as go
import pytest

from embcol.logging._context import progress_figure, progress_text
from embcol.logging._figure import FigureHandler

if TYPE_CHECKING:
    from logging import StreamHandler

    from plotly.graph_objects import FigureWidget

    from embcol._typing_imports import Writer


@pytest.mark.parametrize("stream", [sys.stdout, None])
def test_progress_text(stream: Writer[str] | None) -> None:
    logger = logging.getLogger("embcol")
    orig_level = logger.level
    orig_handlers = tuple(logger.handlers)

    with progress_text(stream):
        assert logger.level == logging.INFO

        new_handlers = [handler for handler in logger.handlers if handler not in orig_handlers]
        assert len(new_handlers) == 2
        assert all(isinstance(handler, logging.StreamHandler) for handler in new_handlers)
        new_handlers = cast("list[StreamHandler[Writer[str]]]", new_handlers)

        expected = stream if stream is not None else sys.stderr
        assert any(handler.stream is expected for handler in new_handlers)

    assert logger.level == orig_level

    assert len(logger.handlers) == len(orig_handlers)
    assert all(handler in logger.handlers for handler in orig_handlers)


@pytest.mark.parametrize("widget", [go.FigureWidget(), None])
def test_progress_figure(widget: FigureWidget | None) -> None:
    logger = logging.getLogger("embcol")
    orig_level = logger.level
    orig_handlers = tuple(logger.handlers)

    with progress_figure(widget=widget):
        assert logger.level == logging.INFO

        new_handlers = [handler for handler in logger.handlers if handler not in orig_handlers]
        assert len(new_handlers) == 2
        assert any(isinstance(handler, logging.StreamHandler) for handler in new_handlers)
        assert any(isinstance(handler, FigureHandler) for handler in new_handlers)

        if widget is not None:
            figure_handler = next(
                handler for handler in new_handlers if isinstance(handler, FigureHandler)
            )
            assert figure_handler.widget is widget

    assert logger.level == orig_level

    assert len(logger.handlers) == len(orig_handlers)
    assert all(handler in logger.handlers for handler in orig_handlers)
