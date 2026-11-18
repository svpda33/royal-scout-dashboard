"""Authoritative CSV loading, ownership checks, and presentation-only selectors."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TABLES = {
    "matches": "data/processed/phase3/pressure_match_coverage.csv",
    "excluded_matches": "data/processed/phase2b/excluded_matches.csv",
    "batting_rankings": "data/processed/phase5/batting_rankings.csv",
    "bowling_rankings": "data/processed/phase5/bowling_rankings.csv",
    "batting_evaluation": "data/processed/phase5/batting_player_evaluation.csv",
    "bowling_evaluation": "data/processed/phase5/bowling_player_evaluation.csv",
    "intervals": "data/processed/phase4_v4/player_interval_details.csv",
    "competition_context": "data/processed/phase4_v4/competition_context_metrics.csv",
    "metric_quality": "data/processed/phase4_v4/metric_quality_summary.csv",
    "history": "data/processed/phase5/historical_consistency.csv",
    "ranking_sensitivity": "data/processed/phase5/ranking_sensitivity.csv",
    "definitions": "data/processed/phase5b/alternative_pressure_definitions.csv",
    "stability": "data/processed/phase5b/player_overall_stability.csv",
    "metric_stability": "data/processed/phase5b/player_metric_stability.csv",
    "alternative_comparison": "data/processed/phase5b/primary_vs_alternative_comparison.csv",
}
REQUIRED = {
    "matches": {"match_id", "competition_type", "primary_eligible_events", "batting_pressure_events", "bowling_pressure_events"},
    "excluded_matches": {"match_id", "status", "reason"},
    "batting_rankings": {"rank", "player_id", "player_name", "competition_scope", "composite_score", "pressure_events", "reference_events"},
    "bowling_rankings": {"rank", "player_id", "player_name", "competition_scope", "composite_score", "pressure_events", "reference_events"},
    "batting_evaluation": {"player_id", "player_name", "competition_scope", "primary_eligible", "pressure_events", "reference_events"},
    "bowling_evaluation": {"player_id", "player_name", "competition_scope", "primary_eligible", "pressure_events", "reference_events"},
    "intervals": {"role", "player_id", "competition_scope", "metric_name", "interval_low", "interval_high", "interval_status"},
    "competition_context": {"role", "competition_type", "pressure_label", "observed_events"},
    "metric_quality": {"role", "competition_type", "pressure_label", "observed_events"},
    "history": {"role", "player_id", "competition_scope", "context_type", "context_value"},
    "ranking_sensitivity": {"role", "variant", "variant_type", "top10_overlap_count"},
    "definitions": {"role", "variant", "evaluation_status", "changed_labels_on_primary_events"},
    "stability": {"role", "player_id", "competition_scope", "overall_stability", "primary_top10"},
    "metric_stability": {"role", "player_id", "competition_scope", "metric_name", "metric_stability"},
    "alternative_comparison": {"role", "player_id", "competition_scope", "variant", "metric_name", "interval_status", "variant_rank"},
}
METRICS = {
    "batting": (
        ("recorded_batter_runs_per_event", "Recorded batter runs / observed striker event", "Higher", "runs/event"),
        ("boundary_event_rate", "Valid boundary-flag events / observed striker event", "Higher", "event share"),
        ("batter_dismissal_event_rate", "Striker-attributed dismissals / observed striker event", "Lower", "event share"),
    ),
    "bowling": (
        ("bowler_credit_wickets_per_event", "Bowler-credit wickets / observed bowler event", "Higher", "event share"),
        ("recorded_batter_runs_allowed_per_event", "Recorded batter runs allowed / observed bowler event", "Lower", "runs/event"),
    ),
}


class DashboardDataError(RuntimeError):
    """A required validated artifact is missing or structurally invalid."""


@dataclass(frozen=True)
class Bundle:
    frames: dict[str, pd.DataFrame]
    manifests: dict[str, dict]

    def __getitem__(self, name: str) -> pd.DataFrame:
        return self.frames[name]


def _manifest_map(root: Path) -> tuple[dict[str, str], dict[str, dict]]:
    paths = {
        "phase5": root / "data/processed/phase5/phase5_output_manifest.json",
        "phase5b": root / "data/processed/phase5b/phase5b_output_manifest.json",
        "phase4_v4": root / "data/processed/phase4_v4/phase4_output_manifest.json",
    }
    manifests = {}
    hashes = {}
    for phase, path in paths.items():
        if not path.is_file():
            raise DashboardDataError(f"Missing {phase} manifest: {path}")
        manifests[phase] = json.loads(path.read_text(encoding="utf-8"))
        for item in manifests[phase]["outputs"]:
            hashes[f"data/processed/{phase}/{item['filename']}"] = item["sha256"]
    hashes.update(manifests["phase5b"]["protected_hashes"])
    return hashes, manifests


def load_bundle(root: Path = ROOT, *, verify_hashes: bool = True) -> Bundle:
    """Read files only; never compute or rewrite any analytical output."""
    root = Path(root)
    hashes, manifests = _manifest_map(root)
    frames = {}
    for name, relative in TABLES.items():
        path = root / relative
        if not path.is_file():
            raise DashboardDataError(f"Missing required {name} output: {path}")
        if verify_hashes:
            expected = hashes.get(relative)
            if expected is None:
                raise DashboardDataError(f"No manifest SHA-256 for {relative}")
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual != expected:
                raise DashboardDataError(f"Validated output hash mismatch: {relative}")
        frame = pd.read_csv(path, low_memory=False)
        missing = REQUIRED[name] - set(frame.columns)
        if missing:
            raise DashboardDataError(f"{relative} lacks columns: {sorted(missing)}")
        frames[name] = frame
    for role in ("batting", "bowling"):
        ranked = frames[f"{role}_rankings"]
        if ranked.player_id.duplicated().any() or ranked["rank"].duplicated().any() or not ranked.competition_scope.isin(["IPL", "T20I"]).all():
            raise DashboardDataError(f"Invalid authoritative {role} rankings")
        if not ranked.primary_eligible.all():
            raise DashboardDataError(f"Ineligible player in authoritative {role} rankings")
    return Bundle(frames, manifests)


def filter_rankings(frame: pd.DataFrame, competition: str = "All", player_ids: list[int] | None = None,
                    rank_range: tuple[int, int] | None = None) -> pd.DataFrame:
    out = frame.copy()
    if competition != "All":
        if competition not in ("IPL", "T20I"):
            raise ValueError("competition must be All, IPL or T20I")
        out = out[out.competition_scope.eq(competition)]
    if player_ids is not None:
        out = out[out.player_id.isin(player_ids)]
    if rank_range is not None:
        out = out[out["rank"].between(*rank_range)]
    return out.sort_values("rank").reset_index(drop=True)


def select_player(frame: pd.DataFrame, player_id: int, scope: str) -> pd.Series | None:
    found = frame[frame.player_id.eq(player_id) & frame.competition_scope.eq(scope)]
    if len(found) > 1:
        raise DashboardDataError("Duplicate player and competition scope")
    return found.iloc[0] if len(found) else None


def interval_interpretation(status: str, low: object, high: object) -> str:
    if status != "exploratory_match_cluster_interval" or pd.isna(low) or pd.isna(high):
        return "Uncertainty interval unavailable; this is not a zero result."
    if float(low) <= 0 <= float(high):
        return "Exploratory interval includes zero; direction remains uncertain."
    return "Exploratory interval excludes zero; association is still non-causal."


def profile_metrics(row: pd.Series, interval_frame: pd.DataFrame, role: str) -> pd.DataFrame:
    """Present authoritative Phase 5 point values and Phase 4 v4 intervals only."""
    details = interval_frame[(interval_frame.role.eq(role)) & interval_frame.player_id.eq(row.player_id) &
                             interval_frame.competition_scope.eq(row.competition_scope)]
    if details.metric_name.duplicated().any():
        raise DashboardDataError("Duplicate interval metric key")
    indexed = details.set_index("metric_name")
    records = []
    for metric, label, favorable, unit in METRICS[role]:
        d = indexed.loc[metric] if metric in indexed.index else None
        p, r, diff = (row.get(f"{metric}_value_pressure"), row.get(f"{metric}_value_reference"),
                      row.get(f"{metric}_difference_pressure_minus_reference"))
        status = d.interval_status if d is not None else "unavailable"
        low = d.interval_low if d is not None else float("nan")
        high = d.interval_high if d is not None else float("nan")
        records.append({"metric": metric, "label": label, "favorable": favorable, "unit": unit,
                        "pressure": p, "reference": r, "difference": diff,
                        "interval_low": low, "interval_high": high, "interval_status": status,
                        "interpretation": interval_interpretation(status, low, high)})
    return pd.DataFrame(records)


def overview(bundle: Bundle) -> dict[str, object]:
    matches = bundle["matches"]
    eligible = matches[matches.primary_eligible_events.gt(0)]
    counts = {}
    for role in ("batting", "bowling"):
        players = bundle[f"{role}_evaluation"]
        selected = players[players.primary_eligible & players.competition_scope.isin(["IPL", "T20I"])]
        counts[f"{role}_scopes"] = len(selected)
        counts[f"{role}_players"] = selected.player_id.nunique()
    intervals = bundle["intervals"]
    valid = intervals[intervals.interval_status.eq("exploratory_match_cluster_interval") &
                      intervals.competition_scope.isin(["IPL", "T20I"])]
    counts.update(matches=eligible.match_id.nunique(), delivery_events=int(eligible.primary_eligible_events.sum()),
        ipl_matches=int(eligible[eligible.competition_type.eq("IPL")].match_id.nunique()),
        t20i_matches=int(eligible[eligible.competition_type.eq("T20I")].match_id.nunique()),
        batting_pressure_events=int(eligible.batting_pressure_events.sum()),
        bowling_pressure_events=int(eligible.bowling_pressure_events.sum()),
        interval_player_scopes=len(valid[["role", "player_id", "competition_scope"]].drop_duplicates()))
    return counts


def top10_retention(bundle: Bundle) -> pd.DataFrame:
    """Display only tested Phase 5B variants; no alternative ranking is created."""
    defs = bundle["definitions"]
    comparison = bundle["alternative_comparison"]
    rows = []
    for item in defs[defs.evaluation_status.eq("tested")].itertuples():
        primary = bundle[f"{item.role}_rankings"][["player_id", "competition_scope"]]
        subset = comparison[comparison.role.eq(item.role) & comparison.variant.eq(item.variant) & comparison.primary_top10]
        variant_rows = subset[["player_id", "competition_scope", "variant_rank"]].drop_duplicates()
        if variant_rows.duplicated(["player_id", "competition_scope"]).any():
            raise DashboardDataError(f"Conflicting variant ranks: {item.role}/{item.variant}")
        selected = primary.merge(variant_rows, on=["player_id", "competition_scope"],
                                 how="left", validate="one_to_one")
        rows.append({"role": item.role, "variant": item.variant, "definition": item.definition,
                     "changed_event_labels": item.changed_labels_on_primary_events,
                     "primary_top10_retained": int(selected.variant_rank.le(10).sum()),
                     "primary_top10_with_variant_rank": int(selected.variant_rank.notna().sum()),
                     "players_analyzed": int(comparison[comparison.role.eq(item.role) & comparison.variant.eq(item.variant)].player_id.nunique())})
    return pd.DataFrame(rows)
