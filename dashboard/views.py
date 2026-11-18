"""Streamlit pages over immutable research outputs."""
from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from . import charts
from .brand import logo_html
from .data import Bundle, METRICS, filter_rankings, interval_interpretation, overview, profile_metrics, select_player, top10_retention


def heading(kicker: str, title: str, description: str, *, overview_brand: bool = False) -> None:
    mark = logo_html("overview") if overview_brand else ""
    st.markdown(f'<div class="hero"><div class="hero-content"><div class="hero-copy">'
                f'<div class="eyebrow">{kicker}</div><h1>{title}</h1>'
                f'<p class="lead">{description}</p></div>{mark}</div></div>', unsafe_allow_html=True)


def note(message: str) -> None:
    st.markdown(f'<div class="research-note">{message}</div>', unsafe_allow_html=True)


def fmt(value: object, digits: int = 3) -> str:
    return "—" if pd.isna(value) else f"{float(value):,.{digits}f}"


def render_overview(bundle: Bundle) -> None:
    heading("RESEARCH OVERVIEW", "Evidence, before reputation.",
        "ROYAL SCOUT compares observed event performance in pre-delivery pressure contexts with each player's own same-competition reference.",
        overview_brand=True)
    k = overview(bundle)
    st.subheader("Primary analysis at a glance")
    cols = st.columns(4, gap="medium")
    for col, label, value in zip(cols, ["Eligible matches", "Delivery events", "Eligible batter scopes", "Eligible bowler scopes"],
                                  [k["matches"], k["delivery_events"], k["batting_scopes"], k["bowling_scopes"]]):
        with col.container(border=True):
            st.metric(label, f"{value:,}")
    st.caption("Primary Phase 3 population: ordinary innings 1–2 with revised-metadata matches excluded. Each delivery event supplies one observed striker event and one observed bowler event; neither is a certified ball.")
    coverage = bundle["matches"]
    coverage = coverage[coverage.primary_eligible_events.gt(0)].groupby("competition_type", as_index=False).agg(
        matches=("match_id","nunique"),delivery_events=("primary_eligible_events","sum"),
        batting_pressure_events=("batting_pressure_events","sum"),bowling_pressure_events=("bowling_pressure_events","sum"))
    st.subheader("Coverage and evidence")
    with st.container(border=True):
        st.plotly_chart(charts.competition_coverage(coverage), width="stretch", theme=None, config={"displayModeBar": False})
        st.caption(f"{k['ipl_matches']:,} IPL matches · {k['t20i_matches']:,} T20I matches")
    evidence_cols = st.columns(3, gap="medium")
    for col, label, value in zip(evidence_cols,
                                 ["Distinct batters", "Distinct bowlers", "Interval-covered scopes"],
                                 [k["batting_players"], k["bowling_players"], k["interval_player_scopes"]]):
        with col.container(border=True):
            st.metric(label, f"{value:,}")
    st.caption("One scope is a role × player ID × competition. A player can have both IPL and T20I scopes. The interval-covered count includes records with at least one published exploratory interval; it is broader than ranking eligibility.")
    with st.container(border=True):
        st.plotly_chart(charts.pressure_by_role(k["batting_pressure_events"],k["bowling_pressure_events"],k["delivery_events"]),
                        width="stretch", theme=None, config={"displayModeBar": False})
        st.caption(f"Batting pressure: {k['batting_pressure_events']:,} events · Bowling pressure: {k['bowling_pressure_events']:,} events. Each role has its own rule and reference set.")
    note("Pressure is an operational proxy based on innings phase and wickets already lost. It does not measure psychological pressure. Rankings are comparative point estimates, not causal proof of improvement.")


def _ranking_view(bundle: Bundle, role: str) -> None:
    noun = "Batters" if role == "batting" else "Bowlers"
    heading("PRIMARY PHASE 5 RANKING", f"Top 10 {noun}",
        "Authoritative primary order. Filters change the view, never the underlying rank or score.")
    frame = bundle[f"{role}_rankings"]
    c1,c2,c3 = st.columns([1,2,1])
    competition = c1.selectbox("Competition",["All","IPL","T20I"],key=f"{role}_competition")
    choices = {f"{r.player_name} · {r.competition_scope}": int(r.player_id) for r in frame.itertuples()}
    names = c2.multiselect("Player",list(choices),key=f"{role}_players")
    maximum = int(frame["rank"].max())
    ranks = c3.slider("Ranking position",1,maximum,(1,maximum),key=f"{role}_rank_range")
    selected = filter_rankings(frame,competition,[choices[n] for n in names] if names else None,ranks)
    st.caption(f"Showing {len(selected)} of {len(frame)} ranked players. Scores are within-competition midrank composites; global positions are descriptive across competition scopes.")
    metric_cols = [m[0]+"_difference_pressure_minus_reference" for m in METRICS[role]]
    cols = ["rank","player_name","competition_scope","composite_score","pressure_events","reference_events",
            "pressure_matches","reference_matches",*metric_cols,"interval_status"]
    shown = selected[cols].copy()
    shown.columns = ["Rank","Player","Competition","Score","Pressure events","Reference events",
        "Pressure matches","Reference matches",*[m[1].split(" / ")[0]+" Δ" for m in METRICS[role]],"Interval status"]
    highlighted = shown.style.apply(
        lambda row: ["background-color: #FCE5EF; color: #14264A; font-weight: 700" if row["Rank"] <= 3
                     else "" for _ in row], axis=1)
    st.dataframe(highlighted, width="stretch", hide_index=True)
    note("Δ is pressure minus the same player's reference value in the same competition. A high rank does not imply every Δ is favorable or that its exploratory interval excludes zero.")
    if len(selected):
        keys = {f"#{int(r['rank'])} · {r.player_name} ({r.competition_scope})": r for _,r in selected.iterrows()}
        chosen = st.selectbox("Open player profile",list(keys),key=f"{role}_profile_pick")
        if st.button("View full profile",key=f"{role}_open"):
            row = keys[chosen]
            st.session_state["profile_role"] = role
            st.session_state["profile_player"] = int(row.player_id)
            st.session_state["profile_scope"] = row.competition_scope
            st.session_state["requested_page"] = "Player profile"
            st.rerun()


def render_batters(bundle: Bundle) -> None:
    _ranking_view(bundle,"batting")


def render_bowlers(bundle: Bundle) -> None:
    _ranking_view(bundle,"bowling")


def render_profile(bundle: Bundle) -> None:
    heading("PLAYER DOSSIER", "Pressure versus reference", "Inspect observed opportunity, match coverage, metric direction and exploratory uncertainty in one competition.")
    role = st.radio("Role",["batting","bowling"], horizontal=True,
        index=0 if st.session_state.get("profile_role","batting")=="batting" else 1)
    st.session_state["profile_role"] = role
    evaluation = bundle[f"{role}_evaluation"]
    evaluation = evaluation[evaluation.competition_scope.isin(["IPL","T20I"])].copy()
    scope_options = ["IPL","T20I"]
    scope = st.selectbox("Competition scope",scope_options,
        index=scope_options.index(st.session_state.get("profile_scope","IPL")) if st.session_state.get("profile_scope") in scope_options else 0)
    st.session_state["profile_scope"] = scope
    pool = evaluation[evaluation.competition_scope.eq(scope)].sort_values("player_name")
    if pool.empty:
        st.info("No player evaluations in this competition.")
        return
    choices = {f"{r.player_name} · ID {int(r.player_id)}":int(r.player_id) for r in pool.itertuples()}
    labels = list(choices)
    desired = st.session_state.get("profile_player")
    default = next((i for i,label in enumerate(labels) if choices[label]==desired),0)
    label = st.selectbox("Player",labels,index=default)
    player_id = choices[label]
    st.session_state["profile_player"] = player_id
    row = select_player(pool,player_id,scope)
    if row is None:
        st.warning("This player has no evaluation in the selected competition.")
        return
    st.markdown(f"<div class='player-heading'><h2>{escape(str(row.player_name))}</h2>"
                f"<span class='scope-pill'>{escape(scope)}</span></div>",unsafe_allow_html=True)
    cols = st.columns(4)
    for col,name,value in zip(cols,["Pressure events","Reference events","Pressure matches","Reference matches"],
                              [row.pressure_events,row.reference_events,row.pressure_matches,row.reference_matches]):
        col.metric(name,f"{int(value):,}")
    st.caption(f"Seasons: {fmt(row.get('seasons_represented'),0)} · Opponents: {fmt(row.get('opponents_represented'),0)} · Baseline: {row.get('comparison_status','unavailable')} · Phase 5 eligibility: {'eligible' if row.primary_eligible else row.get('eligibility_reason','not eligible')}")
    metrics = profile_metrics(row,bundle["intervals"],role)
    a,b = st.columns(2)
    with a: st.plotly_chart(charts.metric_comparison(metrics),width="stretch",theme=None)
    with b: st.plotly_chart(charts.difference_intervals(metrics),width="stretch",theme=None)
    detail = metrics[["label","pressure","reference","difference","interval_low","interval_high","interval_status","interpretation"]].copy()
    detail.columns = ["Metric","Pressure","Reference","Δ P−R","2.5% endpoint","97.5% endpoint","Interval status","Interpretation"]
    st.dataframe(detail,width="stretch",hide_index=True)
    caution = row.get("metric_quality_caution")
    if pd.notna(caution) and str(caution).strip():
        st.warning(f"Recorded data-quality caution: {caution}")
    history = bundle["history"]
    history = history[history.role.eq(role)&history.player_id.eq(player_id)&history.competition_scope.eq(scope)]
    if not history.empty:
        st.plotly_chart(charts.season_events(history),width="stretch",theme=None)
        opp = history[history.context_type.eq("opponent")][["context_value","events_pressure","events_reference","matches_pressure","matches_reference"]]
        with st.expander("Opponent coverage"):
            st.dataframe(opp.rename(columns={"context_value":"Opponent ID"}),width="stretch",hide_index=True)
    note("An unavailable interval is missing evidence, not zero performance. Intervals are exploratory match-cluster intervals for pressure minus reference and do not establish causality or statistical significance.")


def render_analysis(bundle: Bundle) -> None:
    heading("PERFORMANCE LENS", "Event-based comparisons", "Explore each approved metric without converting observed events into certified balls or conventional cricket rates.")
    role = st.radio("Analysis role",["batting","bowling"],horizontal=True)
    metric_names = {m[1]:m[0] for m in METRICS[role]}
    choice = st.selectbox("Metric",list(metric_names))
    metric = metric_names[choice]
    scope = st.selectbox("Competition",["IPL","T20I"])
    data = bundle[f"{role}_evaluation"]
    data = data[data.competition_scope.eq(scope)&data.primary_eligible].copy()
    st.caption(f"{len(data)} eligible player scopes · metric direction: {next(m[2] for m in METRICS[role] if m[0]==metric)} is favorable. Values use observed events.")
    if data.empty:
        st.info("No eligible players for this selection.")
        return
    import plotly.express as px
    palette = charts.colors()
    fig = px.scatter(data,x=f"{metric}_value_reference",y=f"{metric}_value_pressure",
        size="pressure_matches",hover_name="player_name",color="competition_scope",
        color_discrete_map={"IPL":palette["reference"],"T20I":palette["pressure"]},
        hover_data=["pressure_events","reference_events","pressure_matches","reference_matches"],
        labels={f"{metric}_value_reference":"Personal reference",f"{metric}_value_pressure":"Pressure value"})
    low = min(data[f"{metric}_value_reference"].min(),data[f"{metric}_value_pressure"].min())
    high = max(data[f"{metric}_value_reference"].max(),data[f"{metric}_value_pressure"].max())
    fig.add_shape(type="line",x0=low,y0=low,x1=high,y1=high,line=dict(color="#52627C",dash="dash"))
    fig.update_layout(title="Each point is one eligible player in one competition")
    st.plotly_chart(charts.finish(fig,height=520),width="stretch",theme=None)
    context = bundle["competition_context"]
    context = context[context.role.eq(role)]
    st.plotly_chart(charts.context_bars(context,metric),width="stretch",theme=None)
    table = data[["player_id","player_name","pressure_events","reference_events","pressure_matches","reference_matches",f"{metric}_difference_pressure_minus_reference"]].copy()
    table.columns=["Player ID","Player","Pressure events","Reference events","Pressure matches","Reference matches","Δ P−R"]
    st.dataframe(table,width="stretch",hide_index=True)
    note("Competition context is descriptive cohort data. A player's pressure reference is always that player's own observations in the selected competition.")


def render_sensitivity(bundle: Bundle) -> None:
    heading("ROBUSTNESS CHECK", "Alternative pressure definitions", "The original Phase 5 order is fixed. Phase 5B tests whether its evidence changes under nine documented pre-delivery rule variations.")
    role = st.radio("Sensitivity role",["batting","bowling"],horizontal=True)
    retention = top10_retention(bundle)
    retention = retention[retention.role.eq(role)]
    st.plotly_chart(charts.sensitivity_retention(retention),width="stretch",theme=None)
    st.dataframe(retention[["variant","definition","changed_event_labels","primary_top10_retained","primary_top10_with_variant_rank","players_analyzed"]],width="stretch",hide_index=True)
    st.caption("Retention counts use published Phase 5B variant ranks for the original Top 10 IDs. A missing variant rank means the player did not receive a comparable variant rank; it is never counted as retained.")
    stability = bundle["stability"]
    stability = stability[stability.role.eq(role)]
    counts = stability.overall_stability.value_counts().rename_axis("Classification").reset_index(name="Player/competition cases")
    st.subheader("Evidence classifications")
    st.dataframe(counts,width="stretch",hide_index=True)
    top = stability[stability.primary_top10][["primary_global_rank","player_id","player_name","competition_scope","overall_stability","sensitive_metrics","insufficient_metrics"]].copy()
    authoritative = bundle[f"{role}_rankings"][["player_id","competition_scope","rank"]]
    top = top.merge(authoritative,on=["player_id","competition_scope"],how="left",validate="one_to_one")
    if top["rank"].isna().any():
        st.error("A Phase 5B Top 10 case has no matching authoritative Phase 5 rank.")
        return
    disputed = top[top.primary_global_rank.ne(top["rank"])]
    if not disputed.empty:
        st.warning("Phase 5B records a different primary rank for " +
                   ", ".join(disputed.player_name.tolist()) +
                   ". The table uses the authoritative Phase 5 rank; published variant rank shifts for these cases need review.")
    top = top.drop(columns="primary_global_rank").rename(columns={"rank":"Phase 5 rank"}).sort_values("Phase 5 rank")
    st.dataframe(top,width="stretch",hide_index=True)
    details = bundle["alternative_comparison"]
    details = details[details.role.eq(role)&details.primary_top10]
    names = {f"{row['player_name']} · {row['competition_scope']}":
             (int(row["player_id"]), row["competition_scope"]) for _, row in top.iterrows()}
    selected = st.selectbox("Inspect Top 10 player's alternatives",list(names))
    pid,scope = names[selected]
    person = details[details.player_id.eq(pid)&details.competition_scope.eq(scope)]
    metrics = {m[1]:m[0] for m in METRICS[role]}
    selected_metric = st.selectbox("Metric",list(metrics))
    part = person[person.metric_name.eq(metrics[selected_metric])]
    st.plotly_chart(charts.alternative_intervals(part),width="stretch",theme=None)
    shown = part[["variant","primary_point_difference_pressure_minus_reference","point_difference_pressure_minus_reference",
        "interval_low","interval_high","interval_status","pressure_events","reference_events","rank_shift_variant_minus_primary","metric_variant_stability"]].copy()
    shown.columns=["Alternative","Primary Δ","Alternative Δ","Low","High","Interval status","Pressure events","Reference events","Published same-scope rank shift","Metric stability"]
    st.dataframe(shown,width="stretch",hide_index=True)
    note("Definition-sensitive means the point direction or exploratory interval evidence changed under at least one alternative. It does not prove or disprove psychological resilience. Knockout inclusion was documented but not part of the Phase 5B stability verdict because cross-competition evidence was sparse.")


def render_methodology(bundle: Bundle) -> None:
    heading("RESEARCH DESIGN", "How to read the system", "The dashboard is a read-only view of approved pipeline artifacts. No ranking or interval is recalculated in the browser.")
    with st.expander("01 · Sources and eligible population",expanded=True):
        st.markdown("The supplied match, delivery, player and mapping files cover IPL and T20I from 2022 onward. The primary analysis uses ordinary innings 1–2, excluding matches with revised-overs or target metadata and extra innings. Phase 2B records event opportunities; Phase 3 supplies pre-delivery labels.")
    with st.expander("02 · Operational pressure rules",expanded=True):
        st.markdown("Pressure uses **innings phase plus prior recorded wickets**, both known before the delivery. Batting: opening ≥3 prior wickets, middle ≥5, or closing ≥6. Bowling: closing overs with ≤4 prior wickets. Other eligible events are reference. Competition, opponent, venue, match result and current delivery outcome do not assign pressure. These rules proxy resource and phase difficulty, not psychological pressure.")
    with st.expander("03 · Approved event-based metrics",expanded=True):
        rows=[]
        for role,metrics in METRICS.items():
            for _,label,favorable,unit in metrics:
                rows.append({"Role":role.title(),"Metric":label,"Favorable direction":favorable,"Unit":unit})
        st.dataframe(pd.DataFrame(rows),width="stretch",hide_index=True)
        st.markdown("Recorded batter runs have a documented leg-bye exception. Boundary flags and dismissal attribution carry source-quality caveats. Bowler-credit wickets use the approved dismissal whitelist. Observed events are not certified balls faced or legal deliveries.")
    with st.expander("04 · Baselines, uncertainty and eligibility",expanded=True):
        st.markdown("Pressure and reference values compare the **same player in the same competition**. Missing personal reference observations remain missing. Phase 4 v4 exploratory intervals resample match clusters 500 times and estimate the pressure-minus-reference rate difference; at least three pressure and three reference matches and 80% valid draws are needed to publish an interval. Phase 5 ranking eligibility is stricter: ≥50 events and ≥8 matches in each label, ≥2 seasons, ≥4 opponents, finite role contrasts, all role rate intervals, and no recorded-run semantic exception.")
    with st.expander("05 · Ranking and sensitivity",expanded=True):
        st.markdown("Favorable metric differences become within-role, within-competition empirical midrank percentiles. Batting score weights: runs 25%, boundary 25%, dismissal survival 50%. Bowling: bowler-credit wicket rate 50%, recorded-run control 50%. Global lists select one eligible competition scope per player based on opportunity evidence before sorting by score. Phase 5B tests nine alternative phase/wicket thresholds and publishes exploratory intervals; some positions and directions change materially.")
    note("Do not read these rankings as causal proof of improved pressure performance. Many exploratory intervals include zero. Exact strike rate, batting average, economy and bowler runs conceded cannot be derived reliably from the incomplete scoring and legal-ball information.")


def render_quality(bundle: Bundle) -> None:
    heading("DATA GOVERNANCE", "Quality and validation", "A clear audit trail from observed events to primary ranking and sensitivity outputs.")
    matches = bundle["matches"]
    eligible = matches[matches.primary_eligible_events.gt(0)]
    st.metric("Primary eligible matches",f"{eligible.match_id.nunique():,}")
    st.caption(f"Phase 3 match coverage: {len(matches):,} eligible Phase 2B matches; {len(matches)-eligible.match_id.nunique():,} had no primary events under Phase 3 exclusions.")
    excluded = bundle["excluded_matches"]
    st.subheader("Phase 2B match inventory and exclusions")
    st.dataframe(excluded.groupby(["status","reason"]).size().reset_index(name="matches"),width="stretch",hide_index=True)
    st.subheader("Phase 4 metric-quality flags by competition and label")
    st.dataframe(bundle["metric_quality"],width="stretch",hide_index=True)
    st.subheader("Verified pipeline status")
    st.markdown("- **Phase 5:** validation report records an 11-of-11 deterministic CSV rebuild and unchanged historical protected hashes.\n- **Phase 5B:** test-cleanup report records a six-CSV read-only rebuild, 66 passing tests, and unchanged pre-existing outputs/reports.\n- **Dashboard:** each required file is checked against its published manifest hash before display; missing or altered data raises a visible error.")
    note("Known source limits: incomplete numeric extras, undocumented ‘other’ extras, anomalous overs, a leg-bye run exception, boundary-flag mismatches and some dismissal-ID ambiguity. Team totals, required run rate, certified legal balls, conventional strike rate, batting average, economy and exact bowler runs conceded are not published.")
