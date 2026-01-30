"""Logging context."""

from __future__ import annotations

import contextlib
import logging
from typing import TYPE_CHECKING

import plotly.graph_objects as go

from .._checking import check_number, check_number_set, check_type
from .._exception import expr
from .._typing_imports import Writer
from ._figure import FigureHandler
from ._message import ProgressMessage

if TYPE_CHECKING:
    from collections.abc import Collection, Iterator
    from logging import Handler

    from plotly.graph_objects import FigureWidget

__all__ = ["progress_figure", "progress_text"]


@contextlib.contextmanager
def progress_text(stream: Writer[str] | None = None) -> Iterator[None]:
    """Make a context manager for reporting optimization progress by text.

    The ``'embcol'`` logger is reconfigured on entering the context. The original settings are
    restored on exiting the context.

    Parameters
    ----------
    stream : file-like, optional
        Stream to which progress is written. If nothing is given, progress is written to
        the standard error.
    """
    check_type(stream, [Writer, None], target=expr("stream"))

    handler = logging.StreamHandler(stream)
    handler.addFilter(lambda record: isinstance(record.msg, ProgressMessage))
    handler.setFormatter(logging.Formatter("%(message)s"))

    with _progress_handling([handler]):
        yield


@contextlib.contextmanager
def progress_figure(
    widget: FigureWidget | None = None,
    min_interval: float = 1.0,
) -> Iterator[None]:
    """Make a context manager for reporting optimization progress by a figure.

    The ``'embcol'`` logger is reconfigured on entering the context. The original settings are
    restored on exiting the context.

    Parameters
    ----------
    widget : plotly.graph_objects.FigureWidget, optional
        Figure widget on which progress is drawn. If nothing is given, a widget is created with
        default settings.
    min_interval: float, optional
        Minimum time interval between figure updates. The value is in units of seconds.
    """
    check_type(widget, [go.FigureWidget, None], target=expr("widget"))

    check_number_set(min_interval, "real_numbers", target=expr("min_interval"))
    check_number(
        min_interval,
        lower_bound=0,
        allow_lower_bound=False,
        allow_nan=False,
        target=expr("min_interval"),
    )
    min_interval = float(min_interval)

    handler = FigureHandler(widget=widget, min_interval=min_interval)
    handler.addFilter(lambda record: isinstance(record.msg, ProgressMessage))

    handler.display_figure()
    with _progress_handling([handler]):
        yield


@contextlib.contextmanager
def _progress_handling(handlers: Collection[Handler]) -> Iterator[None]:
    handlers = list(handlers)

    logger = logging.getLogger(__name__.split(".")[0])  # logger of the package root

    # add a handler for records except for progress messages
    handler = logging.StreamHandler()
    handler.addFilter(lambda record: not isinstance(record.msg, ProgressMessage))
    handlers.append(handler)

    orig_level = logger.level

    logger.setLevel(logging.INFO)
    for handler in handlers:
        logger.addHandler(handler)
    try:
        yield
    finally:
        for handler in handlers:
            logger.removeHandler(handler)
            handler.close()
        logger.setLevel(orig_level)
