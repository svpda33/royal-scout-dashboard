"""Plotly chart helpers for synthetic public-demo data."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


def colors() -> dict[str, str]:
    return {"bg": "#FFFFFF", "grid": "#E7DCE6", "text": "#14264A",
            "pressure": "#E65391", "reference": "#14264A", "interval": "#A9225A"}


def finish(fig: go.Figure, *, height: int = 420, ytitle: str = "") -> go.Figure:
    c = colors()
    fig.update_layout(template="plotly_white",
        paper_bgcolor=c["bg"], plot_bgcolor=c["bg"],
        font=dict(color=c["text"], family="Arial", size=13),
        title_font=dict(color=c["text"], size=18),
        margin=dict(l=60, r=30, t=76, b=85),
        height=height, showlegend=len(fig.data) > 1,
        legend=dict(orientation="h", y=-0.24, x=0, font=dict(color=c["text"])),
        yaxis=dict(gridcolor=c["grid"], title=ytitle, zerolinecolor=c["grid"]),
        xaxis=dict(gridcolor=c["grid"], zerolinecolor=c["grid"]))
    return fig


def competition_coverage(frame: pd.DataFrame) -> go.Figure:
    c = colors()
    fig = go.Figure(go.Bar(
        x=frame.competition_type, y=frame.delivery_events,
        marker_color=[c["reference"] if i == "Demo League A" else c["pressure"] for i in frame.competition_type],
        text=[f"{m:,} synthetic matches" for m in frame.matches],
        textposition="inside",
    ))
    fig.update_layout(title="Synthetic eligible events by demonstration league")
    return finish(fig, height=500, ytitle="Synthetic delivery events")


def pressure_by_role(batting_pressure: int, bowling_pressure: int, total: int) -> go.Figure:
    c = colors()
    fig = go.Figure()
    fig.add_bar(name="Synthetic pressure", x=["Batting", "Bowling"],
                y=[batting_pressure, bowling_pressure], marker_color=c["pressure"])
    fig.add_bar(name="Synthetic reference", x=["Batting", "Bowling"],
                y=[total-batting_pressure, total-bowling_pressure], marker_color=c["reference"])
    fig.update_layout(barmode="stack", title="Synthetic role classifications")
    return finish(fig, ytitle="Synthetic events")


def metric_comparison(metrics: pd.DataFrame) -> go.Figure:
    c = colors()
    names = metrics["label"].tolist()
    fig = go.Figure()
    fig.add_bar(name="Synthetic pressure", x=names, y=metrics.pressure, marker_color=c["pressure"])
    fig.add_bar(name="Synthetic reference", x=names, y=metrics.reference, marker_color=c["reference"])
    fig.update_layout(barmode="group", title="Synthetic within-player values")
    return finish(fig, height=450, ytitle="Synthetic metric value")


def difference_intervals(metrics: pd.DataFrame) -> go.Figure:
    c = colors()
    fig = go.Figure()
    for row in metrics.itertuples():
        label = row.label
        fig.add_trace(go.Scatter(x=[row.interval_low, row.interval_high], y=[label, label],
                                 mode="lines", line=dict(color=c["interval"], width=4), showlegend=False))
        fig.add_trace(go.Scatter(x=[row.difference], y=[label], mode="markers",
                                 marker=dict(color=c["pressure"], size=12), showlegend=False))
    fig.add_vline(x=0, line_dash="dash", line_color="#52627C")
    fig.update_layout(title="Synthetic differences with illustrative intervals")
    return finish(fig, height=450)


def context_bars(context: pd.DataFrame, metric: str) -> go.Figure:
    c = colors()
    fig = go.Figure()
    for label, color in (("pressure", c["pressure"]), ("reference", c["reference"])):
        part = context[context.pressure_label.eq(label)]
        value_column = f"{metric}_value"
        if value_column not in part.columns:
            numeric_columns = [
                column for column in part.columns
                if column.endswith("_value") and pd.api.types.is_numeric_dtype(part[column])
            ]
            value_column = numeric_columns[0] if numeric_columns else part.select_dtypes("number").columns[-1]
        fig.add_bar(name=label.title(), x=part.competition_type,
                    y=part[value_column],
                    marker_color=color)
    fig.update_layout(barmode="group", title="Synthetic competition context")
    return finish(fig, ytitle="Synthetic value")


def season_events(history: pd.DataFrame) -> go.Figure:
    c = colors()
    part = history[history.context_type.eq("season")].sort_values("context_value")
    fig = go.Figure()
    fig.add_bar(name="Synthetic pressure", x=part.context_value.astype(str),
                y=part.events_pressure, marker_color=c["pressure"])
    fig.add_bar(name="Synthetic reference", x=part.context_value.astype(str),
                y=part.events_reference, marker_color=c["reference"])
    fig.update_layout(barmode="group", title="Synthetic opportunities by season")
    return finish(fig, ytitle="Synthetic events")


def sensitivity_retention(frame: pd.DataFrame) -> go.Figure:
    c = colors()
    fig = go.Figure(go.Bar(
        x=frame.primary_top10_retained, y=frame.variant,
        orientation="h", marker_color=c["pressure"], text=frame.primary_top10_retained,
        textposition="outside"))
    fig.update_xaxes(range=[0, 10.7], title="Synthetic Top 10 retained")
    fig.update_layout(title="Synthetic alternative-definition retention")
    fig = finish(fig, height=max(430, 70 * len(frame)))
    fig.update_layout(margin=dict(l=220, r=40, t=76, b=85))
    return fig


def alternative_intervals(frame: pd.DataFrame) -> go.Figure:
    c = colors()
    fig = go.Figure()
    for row in frame.itertuples():
        fig.add_trace(go.Scatter(x=[row.interval_low, row.interval_high], y=[row.variant, row.variant],
                                 mode="lines", line=dict(color=c["interval"], width=4), showlegend=False))
        fig.add_trace(go.Scatter(x=[row.point_difference_pressure_minus_reference], y=[row.variant],
                                 mode="markers", marker=dict(color=c["pressure"], size=11), showlegend=False))
    fig.add_vline(x=0, line_dash="dash", line_color="#52627C")
    fig.update_layout(title="Synthetic alternative differences")
    return finish(fig, height=max(430, 58 * len(frame)))
