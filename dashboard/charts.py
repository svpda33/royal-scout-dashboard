"""Plotly figures for display; no analytical values are recalculated here."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

BG = "#FFFFFF"
GRID = "#E7DCE6"
TEXT = "#14264A"
PINK = "#E65391"
NAVY = "#14264A"
INTERVAL = "#A9225A"


def colors() -> dict[str, str]:
    return {"bg": BG, "grid": GRID, "text": TEXT,
            "pressure": PINK, "reference": NAVY, "interval": INTERVAL}


def finish(fig: go.Figure, *, height: int = 420, ytitle: str = "") -> go.Figure:
    c = colors()
    fig.update_layout(template="plotly_white",
        paper_bgcolor=c["bg"], plot_bgcolor=c["bg"],
        font=dict(color=c["text"], family="Arial", size=13),
        title_font=dict(color=c["text"], size=18),
        margin=dict(l=60, r=30, t=76, b=85),
        height=height, showlegend=len(fig.data)>1,
        legend=dict(orientation="h", y=-0.24, x=0, font=dict(color=c["text"])),
        yaxis=dict(gridcolor=c["grid"], title=ytitle, zerolinecolor=c["grid"]),
        xaxis=dict(gridcolor=c["grid"], zerolinecolor=c["grid"]))
    return fig


def opportunity_bars(pressure: int, reference: int, *, title: str) -> go.Figure:
    c = colors()
    fig = go.Figure(go.Bar(x=["Pressure", "Reference"], y=[pressure, reference],
        marker_color=[c["pressure"], c["reference"]], text=[f"{pressure:,}", f"{reference:,}"], textposition="outside"))
    fig.update_layout(title=title)
    return finish(fig, ytitle="Observed events")


def competition_coverage(frame: pd.DataFrame) -> go.Figure:
    c = colors()
    fig = go.Figure(go.Bar(x=frame.competition_type, y=frame.delivery_events,
        marker_color=[c["reference"] if item == "IPL" else c["pressure"] for item in frame.competition_type],
        text=[f"{m:,} matches" for m in frame.matches], textposition="inside",
        textfont=dict(color=["#FFFFFF" if item == "IPL" else TEXT for item in frame.competition_type], size=14),
        hovertemplate="%{x}<br>%{y:,} delivery events<br>%{text}<extra></extra>"))
    fig.update_layout(title="Eligible delivery events by competition", showlegend=False)
    return finish(fig, height=500, ytitle="Delivery events")


def pressure_by_role(batting_pressure: int, bowling_pressure: int, total: int) -> go.Figure:
    c = colors()
    fig = go.Figure()
    fig.add_bar(name="Pressure", x=["Batting", "Bowling"],
        y=[batting_pressure, bowling_pressure], marker_color=c["pressure"])
    fig.add_bar(name="Reference", x=["Batting", "Bowling"],
        y=[total-batting_pressure, total-bowling_pressure], marker_color=c["reference"])
    fig.update_layout(barmode="stack", title="Two separate pre-delivery classifications")
    return finish(fig, height=420, ytitle="Observed events")


def metric_comparison(metrics: pd.DataFrame) -> go.Figure:
    c = colors()
    fig = go.Figure()
    names = metrics["label"].str.split(" / ").str[0].tolist()
    fig.add_bar(name="Pressure", x=names, y=metrics.pressure, marker_color=c["pressure"])
    fig.add_bar(name="Reference", x=names, y=metrics.reference, marker_color=c["reference"])
    fig.update_layout(barmode="group", title="Within-player event-based rates")
    return finish(fig, height=450, ytitle="Source metric value")


def difference_intervals(metrics: pd.DataFrame) -> go.Figure:
    c = colors()
    fig = go.Figure()
    for row in metrics.itertuples():
        if pd.isna(row.difference):
            continue
        label = row.label.split(" / ")[0]
        if (row.interval_status == "exploratory_match_cluster_interval" and
                pd.notna(row.interval_low) and pd.notna(row.interval_high)):
            fig.add_trace(go.Scatter(x=[row.interval_low, row.interval_high], y=[label, label],
                mode="lines", line=dict(color=c["interval"], width=4), showlegend=False,
                hovertemplate="Interval endpoint: %{x:.4f}<extra></extra>"))
        fig.add_trace(go.Scatter(x=[row.difference], y=[label], mode="markers",
            marker=dict(color=c["pressure"], size=12), showlegend=False,
            hovertemplate="Difference: %{x:.4f}<extra></extra>"))
    fig.add_vline(x=0, line_dash="dash", line_color="#52627C")
    fig.update_layout(title="Pressure minus reference · exploratory match-cluster intervals")
    return finish(fig, height=450, ytitle="")


def context_bars(context: pd.DataFrame, metric: str) -> go.Figure:
    c = colors()
    fig = go.Figure()
    for label, color in (("pressure", c["pressure"]), ("reference", c["reference"])):
        part = context[context.pressure_label.eq(label)]
        fig.add_bar(name=label.title(), x=part.competition_type, y=part[f"{metric}_value"], marker_color=color)
    fig.update_layout(barmode="group", title="Competition context · cohort description")
    return finish(fig, ytitle="Event-based metric value")


def season_events(history: pd.DataFrame) -> go.Figure:
    c = colors()
    part = history[history.context_type.eq("season")].sort_values("context_value")
    fig = go.Figure()
    fig.add_bar(name="Pressure", x=part.context_value.astype(str), y=part.events_pressure, marker_color=c["pressure"])
    fig.add_bar(name="Reference", x=part.context_value.astype(str), y=part.events_reference, marker_color=c["reference"])
    fig.update_layout(barmode="group", title="Observed opportunities by season")
    return finish(fig, ytitle="Observed events")


def sensitivity_retention(frame: pd.DataFrame) -> go.Figure:
    c = colors()
    fig = go.Figure(go.Bar(x=frame.primary_top10_retained, y=frame.variant,
        orientation="h", marker_color=c["pressure"], text=frame.primary_top10_retained, textposition="outside"))
    fig.update_xaxes(range=[0, 10.7], title="Primary Top 10 players retained")
    fig.update_layout(title="Top 10 retention under alternative definitions")
    fig = finish(fig, height=max(430, 70 * len(frame)))
    fig.update_layout(margin=dict(l=220, r=40, t=76, b=85))
    return fig


def alternative_intervals(frame: pd.DataFrame) -> go.Figure:
    c = colors()
    fig = go.Figure()
    for row in frame.itertuples():
        if pd.isna(row.point_difference_pressure_minus_reference):
            continue
        if (row.interval_status == "exploratory_match_cluster_interval" and
                pd.notna(row.interval_low) and pd.notna(row.interval_high)):
            fig.add_trace(go.Scatter(x=[row.interval_low, row.interval_high], y=[row.variant, row.variant],
                mode="lines", line=dict(color=c["interval"], width=4), showlegend=False,
                hovertemplate="Interval endpoint: %{x:.4f}<extra></extra>"))
        fig.add_trace(go.Scatter(x=[row.point_difference_pressure_minus_reference], y=[row.variant],
            mode="markers", showlegend=False, marker=dict(color=c["pressure"], size=11),
            hovertemplate="Difference: %{x:.4f}<extra></extra>"))
    fig.add_vline(x=0, line_dash="dash", line_color="#52627C")
    fig.update_layout(title="Alternative pressure-minus-reference differences")
    return finish(fig, height=max(430, 58*len(frame)))
