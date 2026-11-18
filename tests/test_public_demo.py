"""Runtime and privacy tests for the public synthetic demo."""
from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("streamlit")
pytest.importorskip("plotly")
from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"


def test_all_demo_pages_execute():
    app = AppTest.from_file(str(APP), default_timeout=90).run()
    assert not app.exception and not app.error
    for page in (
        "Top 10 batters",
        "Top 10 bowlers",
        "Player profile",
        "Performance analysis",
        "Sensitivity analysis",
        "Methodology",
        "Data quality",
    ):
        app.sidebar.radio[0].set_value(page).run()
        assert not app.exception, (page, [error.message for error in app.exception])
        assert not app.error


def test_demo_filters_and_profile_navigation():
    app = AppTest.from_file(str(APP), default_timeout=90).run()
    app.sidebar.radio[0].set_value("Top 10 batters").run()
    app.selectbox[0].set_value("Demo League A").run()
    assert not app.exception
    app.sidebar.radio[0].set_value("Player profile").run()
    app.radio[0].set_value("bowling").run()
    assert not app.exception


def test_demo_bundle_is_synthetic_and_offline():
    import sys
    for name in list(sys.modules):
        if name == "dashboard" or name.startswith("dashboard."):
            del sys.modules[name]
    sys.path.insert(0, str(ROOT))
    from dashboard.data import load_synthetic_bundle

    bundle = load_synthetic_bundle()
    batting = bundle["batting_rankings"]
    bowling = bundle["bowling_rankings"]
    assert len(batting) == 20
    assert len(bowling) == 20
    assert batting.player_name.str.startswith("Demo ").all()
    assert bowling.player_name.str.startswith("Demo ").all()
    assert set(batting.competition_scope) == {"Demo League A", "Demo League B"}
    assert set(bowling.competition_scope) == {"Demo League A", "Demo League B"}
