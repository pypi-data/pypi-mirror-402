"""Figure logging."""

from __future__ import annotations

import logging
import math
import statistics
import time
from typing import TYPE_CHECKING, NamedTuple

import IPython.display
import plotly.graph_objects as go

from .._checking import check_number, check_number_set, check_type
from .._exception import expr
from .._typing_imports import override
from ._message import ProgressMessage

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from logging import LogRecord

    from IPython.display import DisplayHandle
    from plotly.graph_objects import FigureWidget, Scatter

__all__ = ["FigureHandler"]


class FigureHandler(logging.Handler):
    """Handler sending optimization progress messages to a figure.

    Parameters
    ----------
    widget : plotly.graph_objects.FigureWidget, optional
        Figure widget where optimization progress is drawn. If nothing is given, a widget is created
        with default settings.
    max_n_points : int, optional
        Maximum number of points drawn on a figure.
    min_interval : float, optional
        Minimum time interval between figure updates. The value is in units of seconds.
    """

    _widget: FigureWidget
    _max_n_points: int
    _min_interval: float
    _figure: _AggregatedFigure | None
    _display_handle: DisplayHandle | None
    _last_updated_time: float | None

    def __init__(
        self,
        widget: FigureWidget | None = None,
        max_n_points: int = 1000,
        min_interval: float = 1e-9,
    ) -> None:
        check_type(widget, [go.FigureWidget, None], target=expr("widget"))
        if widget is None:
            widget = go.FigureWidget(
                layout={
                    "xaxis": {"title": {"text": "iteration"}, "rangemode": "tozero"},
                    "yaxis": {"type": "log", "exponentformat": "e"},
                    "legend": {"x": 1.02, "xanchor": "left", "xref": "paper"},
                    "hovermode": "x",
                    "height": 360,
                },
            )

        check_number_set(max_n_points, "integers", target=expr("max_n_points"))
        check_number(max_n_points, lower_bound=3, target=expr("max_n_points"))
        max_n_points = int(max_n_points)

        check_number_set(min_interval, "real_numbers", target=expr("min_interval"))
        check_number(
            min_interval,
            lower_bound=0,
            allow_lower_bound=False,
            allow_nan=False,
            target=expr("min_interval"),
        )
        min_interval = float(min_interval)

        super().__init__()
        self._widget = widget
        self._max_n_points = max_n_points
        self._min_interval = min_interval
        self._figure = None
        self._display_handle = None
        self._last_updated_time = None

    @property
    def widget(self) -> FigureWidget:
        """Figure widget where optimization progress is drawn.."""
        return self._lazy_figure.widget

    @property
    def max_n_points(self) -> int:
        """Maximum number of points drawn on a figure."""
        return self._max_n_points

    @property
    def min_interval(self) -> float:
        """Minimum time interval between figure updates."""
        return self._min_interval

    @override
    def emit(self, record: LogRecord) -> None:
        """Emit data to a figure.

        Parameters
        ----------
        record : logging.LogRecord
            Record storing emitted data.
        """
        if not isinstance(record.msg, ProgressMessage):
            return

        try:
            with self.lock:  # type: ignore[union-attr]
                self._lazy_figure.add_data(
                    {
                        "cost": _DataPoint("cost", record.msg.cost),
                        "max_constr_vio": _DataPoint(
                            "max. constraint violation",
                            record.msg.max_constr_vio,
                        ),
                        **{
                            f"state_{name}": _DataPoint(name, value)
                            for name, value in record.msg.state.items()
                        },
                    },
                )
            self._update_figure()
        except Exception:  # noqa: BLE001
            self.handleError(record)

    @override
    def flush(self) -> None:
        """Ensure that a figure is updated."""
        self._update_figure(force=True)

    @override
    def close(self) -> None:
        """Stop updating a figure.

        A figure widget is replaced by a non-widget figure where all data are drawn.
        """
        try:
            with self.lock:  # type: ignore[union-attr]
                self._update_figure(force=True, aggregate=False)
                if self._display_handle is not None:
                    fig = go.Figure(self._lazy_figure.widget)
                    self._display_handle.update(fig._repr_mimebundle_(), raw=True)
                    self._figure = None
                    self._display_handle = None
        finally:
            super().close()

    def display_figure(self) -> None:
        """Display a figure."""
        with self.lock:  # type: ignore[union-attr]
            if self._display_handle is None:
                self._display_handle = IPython.display.display(
                    self._lazy_figure.widget,
                    display_id=True,
                )

    @property
    def _lazy_figure(self) -> _AggregatedFigure:
        if self._figure is None:
            self._figure = _AggregatedFigure(self._widget, 1.0, 1.0, self._max_n_points)
        return self._figure

    def _update_figure(self, *, force: bool = False, aggregate: bool = True) -> bool:
        """Update a figure.

        Parameters
        ----------
        force : bool, optional
            If ``True`` is given, always update a figure regardless of an elapsed time from the last
            update.
        aggregate : bool, optional
            If ``True`` is given, only aggregated data points are drawn.

        Returns
        -------
        bool
            ``True`` if a figure is updated.
        """
        current_time = time.monotonic()

        if not (
            force
            or self._last_updated_time is None
            or self._last_updated_time+self._min_interval <= current_time
        ):
            return False

        with self.lock:  # type: ignore[union-attr]
            self._lazy_figure.update_widget(aggregate=aggregate)
            self._last_updated_time = current_time

        return True


class _AggregatedFigure:
    """Figure with aggregated data points.

    Parameters
    ----------
    widget : plotly.graph_objects.FigureWidget
        Figure widget where data points are drawn.
    x0 : float
        X coordinate of the first point.
    x_step : float
        Step size of the x coordinate.
    max_n_points : int
        Maximum number of points drawn on a figure.
    """

    _widget: FigureWidget
    _x0: float
    _x_step: float
    _max_n_points: int
    _n_x_steps: int
    _data: dict[str, _DataSeries]

    def __init__(
        self,
        widget: FigureWidget,
        x0: float,
        x_step: float,
        max_n_points: int,
    ) -> None:
        self._widget = widget
        self._x0 = x0
        self._x_step = x_step
        self._max_n_points = max(3, max_n_points)
        self._n_x_steps = 0
        self._data = {}

    @property
    def widget(self) -> FigureWidget:
        """Figure widget."""
        return self._widget

    def add_data(self, values: Mapping[str, _DataPoint]) -> None:
        """Add data points.

        Parameters
        ----------
        values : mapping of str to embcol.logging._figure._DataPoint
            Mapping of a data key to its name and value.
        """
        for key, point in values.items():
            if key not in self._data:
                self._data[key] = _DataSeries(point.name, [])
            if 0 < (dn := self._n_x_steps-len(self._data[key].values)):
                self._data[key].values.extend(None for _ in range(dn))
            self._data[key].values.append(point.value if math.isfinite(point.value) else None)

        self._n_x_steps += 1

    def update_widget(self, *, aggregate: bool = True) -> None:
        """Update a widget.

        Parameters
        ----------
        aggregate : bool, optional
            If ``True`` is given, data points are aggregated.
        """
        def agg(values: list[float | None]) -> float | None:
            values = [value for value in values if value is not None]
            if values:
                return statistics.median(values)
            return None

        with self._widget.batch_update():
            indices: Sequence[int]
            for i, series in enumerate(self._data.values()):
                if not aggregate or len(series.values) <= self._max_n_points:
                    indices = range(len(series.values))
                    y = series.values
                else:
                    step = max(1, math.ceil((len(series.values)-2)/(self._max_n_points-2)))
                    indices = [
                        0,
                        *range(1+(step-1)//2, len(series.values)-step+(step-1)//2, step),
                        len(series.values)-1,
                    ]
                    y = [
                        series.values[0],
                        *(
                            agg(series.values[i:i+step])
                            for i in range(1, len(series.values)-step, step)
                        ),
                        series.values[-1],
                    ]

                x = [self._x0+i*self._x_step for i in indices]

                if i < len(self._widget.data):
                    self._update_trace(self._widget.data[i], x, y)
                else:
                    self._widget.add_trace(self._make_trace(series.name, x, y))

    def _make_trace(self, name: str, x: list[float], y: list[float | None]) -> Scatter:
        trace = go.Scatter(name=name, showlegend=True)
        self._update_trace(trace, x, y)
        return trace

    def _update_trace(self, trace: Scatter, x: list[float], y: list[float | None]) -> None:
        trace.update(
            x=x,
            y=y,
            mode=("markers" if sum(value is not None for value in y) < 2 else "lines"),
        )


class _DataPoint(NamedTuple):

    name: str
    value: float


class _DataSeries(NamedTuple):

    name: str
    values: list[float | None]
