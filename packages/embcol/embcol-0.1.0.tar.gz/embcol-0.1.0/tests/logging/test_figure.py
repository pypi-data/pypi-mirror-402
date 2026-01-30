from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

import hypothesis
import hypothesis.strategies as st
import plotly.graph_objects as go
import pytest

from embcol.logging._figure import FigureHandler, _AggregatedFigure, _DataPoint
from embcol.logging._message import ProgressMessage

if TYPE_CHECKING:
    from plotly.basedatatypes import BaseTraceType


class TestFigureHandler:

    class TestEmit:

        def test_lt_interval(self) -> None:
            widget = go.FigureWidget()
            handler = FigureHandler(widget=widget, min_interval=3600.0)

            handler.emit(logging.makeLogRecord({"msg": ProgressMessage(1, 0.1, 0.01, {})}))
            handler.emit(logging.makeLogRecord({"msg": ProgressMessage(2, 0.2, 0.02, {})}))

            assert all(len(trace.x) == len(trace.y) == 1 for trace in widget.data)

        def test_gt_interval(self) -> None:
            widget = go.FigureWidget()
            handler = FigureHandler(widget=widget, min_interval=1e-9)

            handler.emit(logging.makeLogRecord({"msg": ProgressMessage(1, 0.1, 0.01, {})}))
            time.sleep(1e-6)
            handler.emit(logging.makeLogRecord({"msg": ProgressMessage(2, 0.2, 0.02, {})}))

            assert all(len(trace.x) == len(trace.y) == 2 for trace in widget.data)

    def test_flush(self) -> None:
        widget = go.FigureWidget()
        handler = FigureHandler(widget=widget, min_interval=3600.0)

        handler.emit(logging.makeLogRecord({"msg": ProgressMessage(1, 0.1, 0.01, {})}))
        handler.emit(logging.makeLogRecord({"msg": ProgressMessage(2, 0.2, 0.02, {})}))
        handler.flush()

        assert all(len(trace.x) == len(trace.y) == 2 for trace in widget.data)


class TestFigure:

    class TestAddData:

        def test_uniform_key(self) -> None:
            fig = _AggregatedFigure(go.FigureWidget(), 1.0, 1.0, 9)

            for i in range(2):
                fig.add_data({"a": _DataPoint("A", 0.1*(i+1))})
            fig.update_widget()

            assert len(fig.widget.data) == 1
            _check_trace(fig.widget.data[0], "A", (1.0, 2.0), (0.1, 0.2))

        def test_mixed_keys(self) -> None:
            fig = _AggregatedFigure(go.FigureWidget(), 1.0, 1.0, 9)

            fig.add_data({"a": _DataPoint("A", 0.1)})
            fig.add_data({"b": _DataPoint("B", 0.2)})
            fig.add_data({"a": _DataPoint("A", 0.3)})
            fig.update_widget()

            assert len(fig.widget.data) == 2
            _check_trace(fig.widget.data[0], "A", (1.0, 2.0, 3.0), (0.1, None, 0.3))
            _check_trace(fig.widget.data[1], "B", (1.0, 2.0), (None, 0.2))

    class TestUpdateWidget:

        def test_updated(self) -> None:
            fig = _AggregatedFigure(go.FigureWidget(), 1.0, 1.0, 9)

            fig.add_data({"a": _DataPoint("A", 0.1)})

            assert not fig.widget.data

            fig.update_widget()

            assert fig.widget.data

        @hypothesis.given(max_n_points=st.integers(min_value=3, max_value=9))
        def test_aggregation(self, max_n_points: int) -> None:
            fig = _AggregatedFigure(go.FigureWidget(), 1.0, 1.0, max_n_points)
            for i in range(max_n_points):
                fig.add_data({"a": _DataPoint("A", 0.1*(i+1))})

            for i in range(max_n_points, 2*max_n_points-2):
                fig.add_data({"a": _DataPoint("A", 0.1*(i+1))})
                fig.update_widget(aggregate=True)

                assert len(fig.widget.data) == 1
                _check_trace(
                    fig.widget.data[0],
                    "A",
                    (1, *range(2, i, 2), i+1),
                    (0.1, *(0.1*(ii+1)+0.05 for ii in range(1, i-1, 2)), 0.1*(i+1)),
                )

            for i in range(2*max_n_points-2, 3*max_n_points-4):
                fig.add_data({"a": _DataPoint("A", 0.1*(i+1))})
                fig.update_widget(aggregate=True)

                assert len(fig.widget.data) == 1
                _check_trace(
                    fig.widget.data[0],
                    "A",
                    (1, *range(3, i, 3), i+1),
                    (0.1, *(0.1*(ii+1) for ii in range(2, i-1, 3)), 0.1*(i+1)),
                )

        def test_no_aggregation(self) -> None:
            fig = _AggregatedFigure(go.FigureWidget(), 1.0, 1.0, 3)

            for i in range(4):
                fig.add_data({"a": _DataPoint("A", 0.1*(i+1))})
            fig.update_widget(aggregate=False)

            assert len(fig.widget.data) == 1
            _check_trace(fig.widget.data[0], "A", (1.0, 2.0, 3.0, 4.0), (0.1, 0.2, 0.3, 0.4))


def _check_trace(
    trace: BaseTraceType,
    name: str,
    x: tuple[float, ...],
    y: tuple[float | None, ...],
) -> None:
    assert isinstance(trace, go.Scatter)
    assert trace.name == name
    assert trace.x == pytest.approx(x, rel=1e-6, abs=1e-6)
    assert trace.y == pytest.approx(y, rel=1e-6, abs=1e-6)

    expected = "markers" if sum(value is not None for value in y) < 2 else "lines"
    assert trace.mode == expected
