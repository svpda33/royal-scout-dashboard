"""Deterministic synthetic data for the public ROYAL SCOUT demo."""
from __future__ import annotations

from dataclasses import dataclass
import random

import pandas as pd


SCOPES = ["Demo League A", "Demo League B"]
METRICS = {
    "batting": (
        ("synthetic_runs_per_event", "Synthetic runs / event", "Higher", "runs/event"),
        ("synthetic_boundary_rate", "Synthetic boundary rate", "Higher", "event share"),
        ("synthetic_dismissal_rate", "Synthetic dismissal rate", "Lower", "event share"),
    ),
    "bowling": (
        ("synthetic_wicket_rate", "Synthetic wicket rate", "Higher", "event share"),
        ("synthetic_runs_allowed", "Synthetic runs allowed", "Lower", "runs/event"),
    ),
}


@dataclass(frozen=True)
class Bundle:
    frames: dict[str, pd.DataFrame]

    def __getitem__(self, name: str) -> pd.DataFrame:
        return self.frames[name]


def _rankings(role: str) -> pd.DataFrame:
    noun = "Batter" if role == "batting" else "Bowler"
    rng = random.Random(100 + (1 if role == "bowling" else 0))
    rows = []
    for scope_index, scope in enumerate(SCOPES):
        for rank in range(1, 11):
            player_id = (scope_index + 1) * 1000 + rank
            player_name = f"Demo {noun} {rank:02d}"
            pressure_events = 420 + rng.randint(-90, 180)
            reference_events = 520 + rng.randint(-100, 200)
            row = {
                "rank": rank,
                "player_id": player_id,
                "player_name": player_name,
                "competition_scope": scope,
                "composite_score": round(0.92 - (rank - 1) * 0.035 - scope_index * 0.015 + rng.random() * 0.012, 4),
                "pressure_events": pressure_events,
                "reference_events": reference_events,
                "pressure_matches": 18 + rng.randint(-3, 5),
                "reference_matches": 24 + rng.randint(-4, 6),
                "primary_eligible": True,
            }
            if role == "batting":
                pressure = 1.18 + rng.random() * 0.42
                reference = 1.05 + rng.random() * 0.38
                boundary_pressure = 0.125 + rng.random() * 0.04
                boundary_reference = 0.115 + rng.random() * 0.035
                dismissal_pressure = 0.052 + rng.random() * 0.018
                dismissal_reference = 0.061 + rng.random() * 0.018
                row.update({
                    "synthetic_runs_per_event_value_pressure": round(pressure, 4),
                    "synthetic_runs_per_event_value_reference": round(reference, 4),
                    "synthetic_runs_per_event_difference_pressure_minus_reference": round(pressure-reference, 4),
                    "synthetic_boundary_rate_value_pressure": round(boundary_pressure, 4),
                    "synthetic_boundary_rate_value_reference": round(boundary_reference, 4),
                    "synthetic_boundary_rate_difference_pressure_minus_reference": round(boundary_pressure-boundary_reference, 4),
                    "synthetic_dismissal_rate_value_pressure": round(dismissal_pressure, 4),
                    "synthetic_dismissal_rate_value_reference": round(dismissal_reference, 4),
                    "synthetic_dismissal_rate_difference_pressure_minus_reference": round(dismissal_pressure-dismissal_reference, 4),
                })
            else:
                wicket_pressure = 0.105 + rng.random() * 0.035
                wicket_reference = 0.088 + rng.random() * 0.03
                allowed_pressure = 0.82 + rng.random() * 0.22
                allowed_reference = 0.88 + rng.random() * 0.23
                row.update({
                    "synthetic_wicket_rate_value_pressure": round(wicket_pressure, 4),
                    "synthetic_wicket_rate_value_reference": round(wicket_reference, 4),
                    "synthetic_wicket_rate_difference_pressure_minus_reference": round(wicket_pressure-wicket_reference, 4),
                    "synthetic_runs_allowed_value_pressure": round(allowed_pressure, 4),
                    "synthetic_runs_allowed_value_reference": round(allowed_reference, 4),
                    "synthetic_runs_allowed_difference_pressure_minus_reference": round(allowed_reference-allowed_pressure, 4),
                })
            rows.append(row)
    return pd.DataFrame(rows)


def load_synthetic_bundle() -> Bundle:
    """Generate stable synthetic records; no filesystem or private-data access."""
    rng = random.Random(2026)
    batting = _rankings("batting")
    bowling = _rankings("bowling")

    evaluation_rows = []
    interval_rows = []
    history_rows = []
    for role, frame in (("batting", batting), ("bowling", bowling)):
        for row in frame.itertuples(index=False):
            player_id = int(row.player_id)
            evaluation_rows.append({
                "role": role,
                "player_id": player_id,
                "player_name": row.player_name,
                "competition_scope": row.competition_scope,
                "primary_eligible": True,
                "pressure_events": row.pressure_events,
                "reference_events": row.reference_events,
                "pressure_matches": row.pressure_matches,
                "reference_matches": row.reference_matches,
                "seasons_represented": 3,
                "opponents_represented": 8,
                "comparison_status": "synthetic complete",
                "eligibility_reason": "synthetic demonstration",
                "metric_quality_caution": "Synthetic example only; no source-quality inference.",
                **{c: getattr(row, c) for c in row._fields if c not in {"role", "player_id", "player_name", "competition_scope", "primary_eligible", "pressure_events", "reference_events", "pressure_matches", "reference_matches", "rank", "composite_score"}},
            })
            for metric, label, _, _ in METRICS[role]:
                pressure_key = f"{metric}_value_pressure"
                reference_key = f"{metric}_value_reference"
                difference_key = f"{metric}_difference_pressure_minus_reference"
                point = getattr(row, pressure_key) - getattr(row, reference_key)
                interval_rows.append({
                    "role": role,
                    "player_id": player_id,
                    "competition_scope": row.competition_scope,
                    "metric_name": metric,
                    "interval_low": round(point - 0.018 - rng.random() * 0.01, 4),
                    "interval_high": round(point + 0.018 + rng.random() * 0.01, 4),
                    "interval_status": "synthetic_exploratory_interval",
                })
            for season in ("Demo Season 1", "Demo Season 2", "Demo Season 3"):
                history_rows.append({
                    "role": role,
                    "player_id": player_id,
                    "competition_scope": row.competition_scope,
                    "context_type": "season",
                    "context_value": season,
                    "events_pressure": 120 + rng.randint(-20, 50),
                    "events_reference": 150 + rng.randint(-25, 60),
                    "matches_pressure": 6 + rng.randint(-1, 2),
                    "matches_reference": 8 + rng.randint(-1, 3),
                })
            for opponent in range(1, 5):
                history_rows.append({
                    "role": role,
                    "player_id": player_id,
                    "competition_scope": row.competition_scope,
                    "context_type": "opponent",
                    "context_value": f"Demo Team {opponent:02d}",
                    "events_pressure": 30 + rng.randint(-8, 15),
                    "events_reference": 40 + rng.randint(-8, 18),
                    "matches_pressure": 3 + rng.randint(-1, 2),
                    "matches_reference": 5 + rng.randint(-1, 2),
                })

    matches = pd.DataFrame([
        {"match_id": i + 1, "competition_type": scope, "primary_eligible_events": 480 + rng.randint(-80, 120),
         "batting_pressure_events": 130 + rng.randint(-20, 35),
         "bowling_pressure_events": 140 + rng.randint(-20, 35)}
        for scope in SCOPES for i in range(12)
    ])

    excluded = pd.DataFrame([
        {"match_id": 101, "status": "synthetic excluded", "reason": "Demonstration placeholder"},
        {"match_id": 102, "status": "synthetic excluded", "reason": "Demonstration placeholder"},
    ])

    variants = []
    for role in ("batting", "bowling"):
        for i in range(1, 10):
            variants.append({
                "role": role,
                "variant": f"Synthetic definition {i}",
                "evaluation_status": "tested",
                "definition": f"Demonstration threshold variant {i}",
                "changed_labels_on_primary_events": round(0.02 * i, 3),
            })
    stability_rows = []
    alternative_rows = []
    for role, frame in (("batting", batting), ("bowling", bowling)):
        for row in frame.itertuples(index=False):
            stability_rows.append({
                "role": role,
                "player_id": row.player_id,
                "player_name": row.player_name,
                "competition_scope": row.competition_scope,
                "overall_stability": "synthetic stable" if row.rank <= 7 else "synthetic sensitive",
                "primary_top10": True,
                "primary_global_rank": row.rank,
                "sensitive_metrics": "1" if row.rank > 7 else "0",
                "insufficient_metrics": "0",
            })
            for variant_index in range(1, 10):
                for metric, _, _, _ in METRICS[role]:
                    alternative_rows.append({
                        "role": role,
                        "player_id": row.player_id,
                        "player_name": row.player_name,
                        "competition_scope": row.competition_scope,
                        "variant": f"Synthetic definition {variant_index}",
                        "metric_name": metric,
                        "primary_top10": True,
                        "interval_status": "synthetic_exploratory_interval",
                        "interval_low": -0.02,
                        "interval_high": 0.06,
                        "primary_point_difference_pressure_minus_reference": 0.04,
                        "point_difference_pressure_minus_reference": round(0.025 + variant_index * 0.002, 4),
                        "pressure_events": row.pressure_events,
                        "reference_events": row.reference_events,
                        "rank_shift_variant_minus_primary": (variant_index % 3) - 1,
                        "metric_variant_stability": "synthetic stable",
                        "variant_rank": max(1, row.rank + ((variant_index % 3) - 1)),
                    })

    frames = {
        "batting_rankings": batting,
        "bowling_rankings": bowling,
        "batting_evaluation": pd.DataFrame([r for r in evaluation_rows if r["role"] == "batting"]),
        "bowling_evaluation": pd.DataFrame([r for r in evaluation_rows if r["role"] == "bowling"]),
        "matches": matches,
        "excluded_matches": excluded,
        "intervals": pd.DataFrame(interval_rows),
        "history": pd.DataFrame(history_rows),
        "definitions": pd.DataFrame(variants),
        "stability": pd.DataFrame(stability_rows),
        "alternative_comparison": pd.DataFrame(alternative_rows),
        "metric_quality": pd.DataFrame([
            {"role": role, "competition_type": scope, "pressure_label": label,
             "observed_events": 40 + index * 13,
             "caution": "Synthetic placeholder"}
            for index, role in enumerate(("batting", "bowling"))
            for scope in SCOPES
            for label in ("pressure", "reference")
        ]),
        "competition_context": pd.DataFrame([
            {"role": role, "competition_type": scope, "pressure_label": label,
             "synthetic_runs_per_event_value": 1.1 + role_index * 0.1 + scope_index * 0.05,
             "synthetic_wicket_rate_value": 0.09 + role_index * 0.01 + scope_index * 0.008,
             "synthetic_runs_allowed_value": 0.9 - scope_index * 0.04,
             "observed_events": 100 + 25 * scope_index}
            for role_index, role in enumerate(("batting", "bowling"))
            for scope_index, scope in enumerate(SCOPES)
            for label in ("pressure", "reference")
        ]),
    }
    return Bundle(frames)


def filter_rankings(frame: pd.DataFrame, competition: str = "All", player_ids: list[int] | None = None,
                    rank_range: tuple[int, int] | None = None) -> pd.DataFrame:
    out = frame.copy()
    if competition != "All":
        out = out[out.competition_scope.eq(competition)]
    if player_ids:
        out = out[out.player_id.isin(player_ids)]
    if rank_range:
        out = out[out["rank"].between(*rank_range)]
    return out.sort_values(["competition_scope", "rank"]).reset_index(drop=True)


def select_player(frame: pd.DataFrame, player_id: int, scope: str) -> pd.Series | None:
    found = frame[(frame.player_id == player_id) & (frame.competition_scope == scope)]
    return found.iloc[0] if len(found) else None


def profile_metrics(row: pd.Series, intervals: pd.DataFrame, role: str) -> pd.DataFrame:
    records = []
    for metric, label, favorable, unit in METRICS[role]:
        pressure = row[f"{metric}_value_pressure"]
        reference = row[f"{metric}_value_reference"]
        difference = row[f"{metric}_difference_pressure_minus_reference"]
        interval = intervals[
            (intervals.role == role) &
            (intervals.player_id == row.player_id) &
            (intervals.competition_scope == row.competition_scope) &
            (intervals.metric_name == metric)
        ]
        records.append({
            "metric": metric,
            "label": label,
            "favorable": favorable,
            "unit": unit,
            "pressure": pressure,
            "reference": reference,
            "difference": difference,
            "interval_low": float(interval.iloc[0].interval_low) if len(interval) else float("nan"),
            "interval_high": float(interval.iloc[0].interval_high) if len(interval) else float("nan"),
            "interval_status": "synthetic_exploratory_interval" if len(interval) else "unavailable",
        })
    return pd.DataFrame(records)


def top10_retention(bundle: Bundle) -> pd.DataFrame:
    rows = []
    for role in ("batting", "bowling"):
        for variant in bundle["definitions"][bundle["definitions"].role == role]["variant"].unique():
            rows.append({
                "role": role,
                "variant": variant,
                "definition": "Synthetic threshold comparison",
                "changed_event_labels": 0.05,
                "primary_top10_retained": 8,
                "primary_top10_with_variant_rank": 9,
                "players_analyzed": 10,
            })
    return pd.DataFrame(rows)
