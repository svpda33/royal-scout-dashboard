"""ROYAL SCOUT · read-only Streamlit research dashboard.

Launch from the repository root: streamlit run app.py
"""
from __future__ import annotations

import streamlit as st

from dashboard.brand import logo_html
from dashboard.data import ROOT, DashboardDataError, load_bundle
from dashboard.views import (render_analysis, render_batters, render_bowlers,
    render_methodology, render_overview, render_profile, render_quality, render_sensitivity)


st.set_page_config(page_title="ROYAL SCOUT | Pressure Intelligence", page_icon="♛",
    layout="wide", initial_sidebar_state="auto")

st.markdown("""
<style>
:root { --blush:#F3EAF1; --white:#FFFFFF; --navy:#14264A; --pink:#E65391;
        --deep-pink:#A9225A; --muted:#52627C; --line:#E7DCE6; }
.stApp, [data-testid="stAppViewContainer"] {
  background:radial-gradient(circle at 88% 0%, #FCE5EF 0, var(--blush) 36%, #F8F5F8 100%);
  color:var(--navy);
}
[data-testid="stHeader"] { background:rgba(243,234,241,.94); }
[data-testid="stSidebar"] { background:var(--navy); border-right:3px solid var(--pink); }
.block-container { padding:4.7rem 2rem 2.5rem; max-width:1480px; }
h1,h2,h3 { font-family:Arial, sans-serif; color:var(--navy); letter-spacing:-.025em; }
h1 { font-size:clamp(2.1rem,3.2vw,3.5rem)!important; font-weight:780!important; margin:.12rem 0 .45rem!important; }
h2 { margin-top:1.8rem!important; }
.hero { background:linear-gradient(110deg,#FFFFFF 42%,#FCE9F1 100%);
  border:1px solid var(--line); border-left:5px solid var(--pink); border-radius:18px;
  padding:1.45rem 1.8rem 1.3rem; margin:0 0 1.75rem;
  box-shadow:0 10px 30px rgba(20,38,74,.07); }
.eyebrow { display:block; color:var(--deep-pink); font-size:.74rem; font-weight:800;
  line-height:1.5; letter-spacing:.18em; margin:0 0 .42rem; }
.lead { color:var(--muted); font-size:1.04rem; line-height:1.65; max-width:980px; margin:0!important; }
.brand { display:flex; align-items:center; gap:12px; padding:12px 0 25px;
  border-bottom:1px solid rgba(255,255,255,.2); margin-bottom:20px; }
.rr-monogram { display:block; flex:none; object-fit:contain; }
.rr-monogram--sidebar { width:45px; height:45px; }
.rr-monogram--header { width:27px; height:27px; }
.rr-monogram--overview { width:63px; height:63px; opacity:.9; }
.rr-monogram--footer { width:19px; height:19px; opacity:.72; }
.topbar { display:flex; align-items:center; gap:9px; margin:0 0 1.1rem;
  color:var(--navy); font-size:.78rem; font-weight:850; letter-spacing:.12em; }
.topbar span { font-size:.68rem; font-weight:600; letter-spacing:.06em; color:var(--muted); }
.hero-content { display:flex; align-items:center; justify-content:space-between; gap:1.2rem; }
.hero-copy { min-width:0; }
.brand-name { font-size:1.18rem; letter-spacing:.07em; font-weight:900;
  color:var(--white); white-space:nowrap; }
.brand-name span { color:#FF9BC3; }
.brand-sub { color:#C9D6EA; font-size:.61rem; letter-spacing:.1em;
  line-height:1.55; margin-top:5px; }
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] *,
[data-testid="stSidebar"] [role="radiogroup"] label,
[data-testid="stSidebar"] [role="radiogroup"] p { color:#EAF0FA; }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
  background:var(--pink); border-radius:9px; }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p { color:var(--navy); font-weight:750; }
[data-testid="stVerticalBlockBorderWrapper"] {
  background:var(--white); border-color:var(--line)!important; border-radius:16px!important;
  box-shadow:0 7px 22px rgba(20,38,74,.06); }
[data-testid="stMetric"] { background:#FBF4F8; border-radius:12px; padding:1rem 1.1rem; }
[data-testid="stMetricLabel"] *, [data-testid="stMetricValue"] { color:var(--navy); }
[data-testid="stMetricValue"] { font-weight:800; }
[data-testid="stPlotlyChart"] { background:var(--white); border:1px solid var(--line);
  border-radius:16px; box-shadow:0 7px 22px rgba(20,38,74,.05);
  padding:.35rem; overflow:hidden; }
[data-testid="stDataFrame"] { background:var(--white); border:1px solid var(--line);
  border-radius:12px; overflow:hidden; }
.research-note { background:#FFFFFF; border:1px solid var(--line); border-left:4px solid var(--pink);
  color:var(--navy); padding:16px 19px; border-radius:12px; margin:19px 0 25px;
  line-height:1.6; box-shadow:0 6px 20px rgba(20,38,74,.045); }
.scope-pill { color:var(--navy); background:#F8C9DD; border-radius:100px;
  padding:4px 12px; font-size:.72rem; vertical-align:middle; letter-spacing:.06em; }
.player-heading { display:flex; align-items:center; flex-wrap:wrap; gap:12px;
  background:var(--white); border:1px solid var(--line); border-left:4px solid var(--pink);
  border-radius:12px; padding:.5rem 1.1rem; margin:1rem 0 1.2rem; }
.player-heading h2 { margin:.3rem 0!important; }
div.stButton > button { background:var(--pink); color:var(--navy); border:1px solid var(--pink);
  font-weight:800; border-radius:9px; box-shadow:0 4px 12px rgba(230,83,145,.16); }
div.stButton > button:hover { background:#F37BAA; color:var(--navy); border-color:#F37BAA; }
div.stButton > button:focus-visible { outline:3px solid var(--navy); outline-offset:2px; }
.footer { border-top:1px solid var(--line); margin-top:3rem; padding:1.2rem 0;
  color:var(--muted); font-size:.73rem; letter-spacing:.04em; }
.footer-line { display:flex; align-items:center; gap:8px; }
[data-testid="stSidebar"] .footer { border-top-color:rgba(255,255,255,.2); color:#C9D6EA; }
@media (max-width: 900px) {
  .block-container { padding:4.3rem 1rem 1.5rem; }
  .hero { padding:1.2rem 1.25rem; }
  .rr-monogram--overview { width:48px; height:48px; }
  h1 { font-size:2rem!important; }
}
</style>
""", unsafe_allow_html=True)

@st.cache_data(show_spinner="Checking validated research outputs…", ttl=300)
def cached_bundle():
    return load_bundle(ROOT, verify_hashes=True)


try:
    bundle = cached_bundle()
except (DashboardDataError, OSError, ValueError) as exc:
    st.error(f"Dashboard data validation failed: {exc}")
    st.info("Run from the Momentra project root with the validated Phase 2B–5B outputs present. The dashboard does not regenerate missing data.")
    st.stop()

st.sidebar.markdown(f"""<div class="brand">{logo_html('sidebar')}<div>
<div class="brand-name">ROYAL <span>SCOUT</span></div>
<div class="brand-sub">IPL PRESSURE PERFORMANCE<br>INTELLIGENCE SYSTEM</div></div></div>""", unsafe_allow_html=True)
pages = {
    "Overview": render_overview,
    "Top 10 batters": render_batters,
    "Top 10 bowlers": render_bowlers,
    "Player profile": render_profile,
    "Performance analysis": render_analysis,
    "Sensitivity analysis": render_sensitivity,
    "Methodology": render_methodology,
    "Data quality": render_quality,
}
requested_page = st.session_state.pop("requested_page", None)
if requested_page in pages:
    # Resolve navigation before the radio widget is instantiated in this run.
    st.session_state["nav"] = requested_page
page = st.sidebar.radio("EXPLORE", list(pages), key="nav")
st.sidebar.markdown("<div class='footer'>INDEPENDENT RESEARCH DASHBOARD<br>RR-INSPIRED VISUAL IDENTITY</div>", unsafe_allow_html=True)
st.markdown(f"<div class='topbar'>{logo_html('header')}<strong>ROYAL SCOUT</strong>"
            "<span>PRESSURE PERFORMANCE INTELLIGENCE</span></div>", unsafe_allow_html=True)
pages[page](bundle)
st.markdown(f"<div class='footer footer-line'>{logo_html('footer')}<span>ROYAL SCOUT · "
            "SupeRR Selector Season 2 · Independent event-based research, not causal inference</span></div>",
            unsafe_allow_html=True)
