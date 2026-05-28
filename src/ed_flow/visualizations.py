"""Plotly visualization helpers."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


PLOT_TEMPLATE = "plotly_white"


def metric_bar(df: pd.DataFrame, x: str, y: str, color: str | None = None, title: str | None = None):
    if df.empty:
        return go.Figure()
    return px.bar(df, x=x, y=y, color=color, title=title, template=PLOT_TEMPLATE)


def line_chart(df: pd.DataFrame, x: str, y: str, color: str | None = None, title: str | None = None):
    if df.empty:
        return go.Figure()
    return px.line(df, x=x, y=y, color=color, title=title, template=PLOT_TEMPLATE)


def duration_distribution(df: pd.DataFrame, value_col: str, color: str | None = None, title: str | None = None):
    if df.empty or value_col not in df:
        return go.Figure()
    return px.histogram(df, x=value_col, color=color, nbins=40, marginal="box", title=title, template=PLOT_TEMPLATE)


def uncertainty_interval_chart(uncertainty: pd.DataFrame):
    """Render mean with p10-p90 intervals."""

    fig = go.Figure()
    if uncertainty.empty:
        return fig
    fig.add_trace(
        go.Bar(
            x=uncertainty["metric"],
            y=uncertainty["mean"],
            error_y=dict(
                type="data",
                symmetric=False,
                array=uncertainty["p90"] - uncertainty["mean"],
                arrayminus=uncertainty["mean"] - uncertainty["p10"],
            ),
            marker_color="#2F6F73",
        )
    )
    fig.update_layout(template=PLOT_TEMPLATE, title="Simulation mean with 80% interval", xaxis_title="", yaxis_title="Value")
    return fig

