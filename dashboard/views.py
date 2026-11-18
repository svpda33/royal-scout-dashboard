"""Synthetic public-demo pages for ROYAL SCOUT."""
from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from . import charts
from .brand import logo_html
from .data import (
    METRICS,
    filter_rankings,
    profile_metrics,
    select_player,
    top10_retention,
)


def heading(kicker: str, title: str, description: str, *, overview_brand: bool = False) -> None:
    mark = logo_html("overview") if overview_brand else ""
    st.markdown(
        f'<div class="hero"><div class="hero-content"><div class="hero-copy">'
        f'<div class="eyebrow">SYNTHETIC DEMO · {kicker}</div><h1>{title}</h1>'
        f'<p class="lead">{description}</p></div>{mark}</div></div>',
        unsafe_allow_html=True,
    )


def demo_note(message: str) -> None:
    st.markdown(
        f'<div class="research-note"><strong>Demonstration notice:</strong> {message}</div>',
        unsafe_allow_html=True,
    )


def render_overview(bundle) -> None:
    heading(
        "PUBLIC DEMONSTRATION",
        "Synthetic evidence, before reputation.",
        "ROYAL SCOUT demonstrates its dashboard experience with fictional players and generated values.",
        overview_brand=True,
    )
    matches = bundle["matches"]
    cols = st.columns(4)
    counts = [
        ("Synthetic matches", int(matches.match_id.nunique())),
        ("Synthetic delivery events", int(matches.primary_eligible_events.sum())),
        ("Synthetic batters", int(bundle["batting_evaluation"].player_id.nunique())),
        ("Synthetic bowlers", int(bundle["bowling_evaluation"].player_id.nunique())),
    ]
    for col, (label, value) in zip(cols, counts):
        with col.container(border=True):
            st.metric(label, f"{value:,}")
    coverage = matches.groupby("competition_type", as_index=False).agg(
        matches=("match_id", "nunique"),
        delivery_events=("primary_eligible_events", "sum"),
    )
    st.subheader("Synthetic coverage")
    st.plotly_chart(
        charts.competition_coverage(coverage),
        width="stretch",
        theme=None,
        config={"displayModeBar": False},
    )
    st.plotly_chart(
        charts.pressure_by_role(
            int(matches.batting_pressure_events.sum()),
            int(matches.bowling_pressure_events.sum()),
            int(matches.primary_eligible_events.sum()),
        ),
        width="stretch",
        theme=None,
        config={"displayModeBar": False},
    )
    demo_note(
        "Every player, match, event count, score, interval, and ranking on this page is synthetic "
        "and must not be interpreted as a cricket, competition, or research finding."
    )


def _ranking_view(bundle, role: str) -> None:
    noun = "batters" if role == "batting" else "bowlers"
    heading("SYNTHETIC PRIMARY RANKING", f"Top 10 {noun}",
            "Fictional demonstration rankings. Filters change the displayed view only.")
    frame = bundle[f"{role}_rankings"]
    c1, c2, c3 = st.columns([1, 2, 1])
    competition = c1.selectbox("Competition", ["All", "Demo League A", "Demo League B"], key=f"{role}_competition")
    choices = {f"{row.player_name} · {row.competition_scope}": int(row.player_id) for row in frame.itertuples()}
    names = c2.multiselect("Synthetic player", list(choices), key=f"{role}_players")
    ranks = c3.slider("Ranking position", 1, 10, (1, 10), key=f"{role}_rank_range")
    selected = filter_rankings(
        frame,
        competition,
        [choices[name] for name in names] if names else None,
        ranks,
    )
    st.caption(f"Showing {len(selected)} synthetic ranking rows.")
    metric_deltas = [f"{metric}_difference_pressure_minus_reference" for metric, *_ in METRICS[role]]
    cols = [
        "rank", "player_name", "competition_scope", "composite_score",
        "pressure_events", "reference_events", "pressure_matches", "reference_matches",
        *metric_deltas,
    ]
    shown = selected[cols].copy()
    shown.columns = [
        "Synthetic Rank", "Player", "League", "Synthetic Score",
        "Pressure events", "Reference events", "Pressure matches", "Reference matches",
        *[f"{label.split(' / ')[0]} Δ" for _, label, *_ in METRICS[role]],
    ]
    st.dataframe(shown, width="stretch", hide_index=True)
    if len(selected):
        keys = {
            f"#{int(row['rank'])} · {row['player_name']} ({row['competition_scope']})": row
            for _, row in selected.iterrows()
        }
        chosen = st.selectbox("Open synthetic player profile", list(keys), key=f"{role}_profile_pick")
        if st.button("View synthetic profile", key=f"{role}_open"):
            row = keys[chosen]
            st.session_state["profile_role"] = role
            st.session_state["profile_player"] = int(row.player_id)
            st.session_state["profile_scope"] = row.competition_scope
            st.session_state["requested_page"] = "Player profile"
            st.rerun()
    demo_note("These fictional rankings demonstrate filtering and navigation; they are not published research rankings.")


def render_batters(bundle) -> None:
    _ranking_view(bundle, "batting")


def render_bowlers(bundle) -> None:
    _ranking_view(bundle, "bowling")


def render_profile(bundle) -> None:
    heading("SYNTHETIC PLAYER DOSSIER", "Pressure versus reference",
            "A demonstration of one-player comparison and illustrative uncertainty.")
    role = st.radio(
        "Role",
        ["batting", "bowling"],
        horizontal=True,
        index=0 if st.session_state.get("profile_role", "batting") == "batting" else 1,
    )
    st.session_state["profile_role"] = role
    evaluation = bundle[f"{role}_evaluation"]
    scopes = ["Demo League A", "Demo League B"]
    scope = st.selectbox(
        "Competition scope",
        scopes,
        index=scopes.index(st.session_state.get("profile_scope"))
        if st.session_state.get("profile_scope") in scopes else 0,
    )
    st.session_state["profile_scope"] = scope
    pool = evaluation[evaluation.competition_scope.eq(scope)].sort_values("player_name")
    choices = {f"{row.player_name} · ID {int(row.player_id)}": int(row.player_id) for row in pool.itertuples()}
    labels = list(choices)
    desired = st.session_state.get("profile_player")
    default = next((i for i, label in enumerate(labels) if choices[label] == desired), 0)
    label = st.selectbox("Synthetic player", labels, index=default)
    player_id = choices[label]
    st.session_state["profile_player"] = player_id
    row = select_player(pool, player_id, scope)
    st.markdown(
        f"<div class='player-heading'><h2>{escape(str(row.player_name))}</h2>"
        f"<span class='scope-pill'>{escape(scope)} · SYNTHETIC</span></div>",
        unsafe_allow_html=True,
    )
    cols = st.columns(4)
    for col, name, value in zip(
        cols,
        ["Pressure events", "Reference events", "Pressure matches", "Reference matches"],
        [row.pressure_events, row.reference_events, row.pressure_matches, row.reference_matches],
    ):
        col.metric(name, f"{int(value):,}")
    metrics = profile_metrics(row, bundle["intervals"], role)
    a, b = st.columns(2)
    with a:
        st.plotly_chart(charts.metric_comparison(metrics), width="stretch", theme=None)
    with b:
        st.plotly_chart(charts.difference_intervals(metrics), width="stretch", theme=None)
    detail = metrics[
        ["label", "pressure", "reference", "difference", "interval_low", "interval_high", "interval_status"]
    ].copy()
    detail.columns = ["Metric", "Synthetic pressure", "Synthetic reference", "Synthetic Δ",
                      "Low", "High", "Interval status"]
    st.dataframe(detail, width="stretch", hide_index=True)
    history = bundle["history"]
    history = history[
        history.role.eq(role) &
        history.player_id.eq(player_id) &
        history.competition_scope.eq(scope)
    ]
    if not history.empty:
        st.plotly_chart(charts.season_events(history), width="stretch", theme=None)
    demo_note("The interval endpoints are synthetic visual placeholders, not statistical uncertainty estimates.")


def render_analysis(bundle) -> None:
    heading("SYNTHETIC PERFORMANCE LENS", "Event-based comparison",
            "Explore generated metric values, illustrating filters and chart behavior.")
    role = st.radio("Analysis role", ["batting", "bowling"], horizontal=True)
    metric_names = {label: metric for metric, label, *_ in METRICS[role]}
    choice = st.selectbox("Metric", list(metric_names))
    metric = metric_names[choice]
    scope = st.selectbox("Competition", ["Demo League A", "Demo League B"])
    data = bundle[f"{role}_evaluation"]
    data = data[data.competition_scope.eq(scope)].copy()
    import plotly.express as px
    palette = charts.colors()
    fig = px.scatter(
        data,
        x=f"{metric}_value_reference",
        y=f"{metric}_value_pressure",
        size="pressure_matches",
        hover_name="player_name",
        color="competition_scope",
        color_discrete_map={"Demo League A": palette["reference"], "Demo League B": palette["pressure"]},
    )
    fig.update_layout(title="Synthetic player comparison")
    st.plotly_chart(charts.finish(fig, height=520), width="stretch", theme=None)
    context = bundle["competition_context"]
    context = context[context.role.eq(role) & context.competition_type.eq(scope)]
    if not context.empty:
        st.plotly_chart(charts.context_bars(context, metric), width="stretch", theme=None)
    table = data[
        ["player_id", "player_name", "pressure_events", "reference_events",
         "pressure_matches", "reference_matches", f"{metric}_difference_pressure_minus_reference"]
    ].copy()
    table.columns = ["Synthetic ID", "Player", "Pressure events", "Reference events",
                     "Pressure matches", "Reference matches", "Synthetic Δ"]
    st.dataframe(table, width="stretch", hide_index=True)
    demo_note("These values were generated for interface demonstration only.")


def render_sensitivity(bundle) -> None:
    heading("SYNTHETIC ROBUSTNESS CHECK", "Alternative pressure definitions",
            "Illustrates how the dashboard can present alternative-rule sensitivity.")
    role = st.radio("Sensitivity role", ["batting", "bowling"], horizontal=True)
    retention = top10_retention(bundle)
    retention = retention[retention.role.eq(role)]
    st.plotly_chart(charts.sensitivity_retention(retention), width="stretch", theme=None)
    st.dataframe(
        retention[
            ["variant", "definition", "changed_event_labels",
             "primary_top10_retained", "players_analyzed"]
        ],
        width="stretch",
        hide_index=True,
    )
    stability = bundle["stability"]
    stability = stability[stability.role.eq(role)]
    counts = stability.overall_stability.value_counts().rename_axis("Classification").reset_index(
        name="Synthetic player/league cases"
    )
    st.subheader("Synthetic evidence classifications")
    st.dataframe(counts, width="stretch", hide_index=True)
    top = stability[stability.primary_top10]
    names = {
        f"{row.player_name} · {row.competition_scope}": (int(row.player_id), row.competition_scope)
        for row in top.itertuples()
    }
    selected = st.selectbox("Inspect synthetic player's alternatives", list(names))
    pid, scope = names[selected]
    details = bundle["alternative_comparison"]
    person = details[
        details.role.eq(role) &
        details.player_id.eq(pid) &
        details.competition_scope.eq(scope)
    ]
    metric_names = {label: metric for metric, label, *_ in METRICS[role]}
    selected_metric = st.selectbox("Synthetic metric", list(metric_names))
    part = person[person.metric_name.eq(metric_names[selected_metric])]
    if not part.empty:
        st.plotly_chart(charts.alternative_intervals(part), width="stretch", theme=None)
        shown = part[
            ["variant", "point_difference_pressure_minus_reference", "interval_low",
             "interval_high", "metric_variant_stability"]
        ].copy()
        shown.columns = ["Alternative", "Synthetic Δ", "Low", "High", "Synthetic stability"]
        st.dataframe(shown, width="stretch", hide_index=True)
    demo_note("Sensitivity classifications are fictional demonstrations, not robustness findings.")


def render_methodology(bundle) -> None:
    heading("DEMONSTRATION DESIGN", "How to read the public demo",
            "This page explains interface concepts; it does not describe a real research study.")
    with st.expander("01 · Synthetic sources", expanded=True):
        st.markdown(
            "All records are generated deterministically inside the application. "
            "There are two fictional leagues, fictional players, and fictional seasons."
        )
    with st.expander("02 · Demonstrated pressure rules", expanded=True):
        st.markdown(
            "The demo illustrates innings-phase-style filters and pressure/reference comparisons. "
            "It does not publish or reproduce a real competition methodology."
        )
    with st.expander("03 · Synthetic metrics", expanded=True):
        rows = []
        for role, metrics in METRICS.items():
            for _, label, favorable, unit in metrics:
                rows.append({"Role": role.title(), "Metric": label,
                             "Favorable direction": favorable, "Unit": unit})
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    with st.expander("04 · Synthetic uncertainty", expanded=True):
        st.markdown(
            "Interval endpoints are visual placeholders generated by the demo data module. "
            "They are not confidence intervals or findings."
        )
    demo_note("Do not cite this demonstration as evidence of cricket performance.")


def render_quality(bundle) -> None:
    heading("PUBLIC DEMO GOVERNANCE", "Synthetic data and privacy",
            "A transparent record of what is included in this public version.")
    c1, c2 = st.columns(2)
    c1.metric("Synthetic matches", int(bundle["matches"].match_id.nunique()))
    c2.metric("Synthetic rankings", len(bundle["batting_rankings"]) + len(bundle["bowling_rankings"]))
    st.subheader("Synthetic quality flags")
    st.dataframe(bundle["metric_quality"], width="stretch", hide_index=True)
    st.subheader("Public-demo safeguards")
    st.markdown(
        "- No original datasets or processed outputs are read.\n"
        "- No derived competition rankings or reports are read.\n"
        "- All fictional names use the `Demo` prefix.\n"
        "- Generated values are not represented as real results.\n"
        "- The demo has no credentials or external network dependencies."
    )
    demo_note("This page confirms the public interface is entirely synthetic.")
