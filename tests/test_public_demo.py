"""Smoke and integrity checks for the public real-results dashboard."""
from __future__ import annotations

from pathlib import Path
import sys

import pytest

pytest.importorskip("streamlit")
pytest.importorskip("plotly")
from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dashboard.data import load_bundle, overview  # noqa: E402


def test_authoritative_outputs_load_with_hashes():
    bundle = load_bundle(ROOT, verify_hashes=True)
    assert len(bundle.frames) == 15
    assert len(bundle["batting_rankings"]) == 10
    assert len(bundle["bowling_rankings"]) == 10
    assert bundle["batting_rankings"].iloc[0].player_name == "Gareth Delany"
    assert bundle["bowling_rankings"].iloc[0].player_name == "Adam Zampa"
    assert set(bundle["batting_rankings"].competition_scope) == {"IPL", "T20I"}
    assert set(bundle["bowling_rankings"].competition_scope) == {"IPL", "T20I"}
    assert overview(bundle)["matches"] == 803


def test_all_eight_pages_run():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=90).run()
    assert not app.exception and not app.error
    for page in (
        "Top 10 batters", "Top 10 bowlers", "Player profile", "Performance analysis",
        "Sensitivity analysis", "Methodology", "Data quality",
    ):
        app.sidebar.radio[0].set_value(page).run()
        assert not app.exception, (page, [e.message for e in app.exception])
        assert not app.error


def test_real_player_profile_and_competition_filter():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=90).run()
    app.sidebar.radio[0].set_value("Top 10 batters").run()
    app.selectbox[0].set_value("IPL").run()
    assert not app.exception
    app.sidebar.radio[0].set_value("Player profile").run()
    app.radio[0].set_value("bowling").run()
    assert not app.exception
    assert not app.error


def test_published_source_and_output_files_present():
    source = sorted((ROOT / "6af3166e7b922_data_pack").glob("*.csv"))
    assert len(source) == 6
    for phase, manifest in (
        ("phase4_v4", "phase4_output_manifest.json"),
        ("phase5", "phase5_output_manifest.json"),
        ("phase5b", "phase5b_output_manifest.json"),
    ):
        assert (ROOT / "data" / "processed" / phase / manifest).is_file()
