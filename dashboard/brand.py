"""ROYAL SCOUT branding helpers for the public demo."""
from __future__ import annotations

from base64 import b64encode
from functools import lru_cache
from pathlib import Path


LOGO_PATH = Path(__file__).resolve().parent / "assets" / "rr_monogram.svg"


@lru_cache(maxsize=1)
def logo_src() -> str:
    return "data:image/svg+xml;base64," + b64encode(LOGO_PATH.read_bytes()).decode("ascii")


def logo_html(placement: str) -> str:
    if placement not in {"sidebar", "header", "overview", "footer"}:
        raise ValueError("Unknown monogram placement")
    return f'<img class="rr-monogram rr-monogram--{placement}" src="{logo_src()}" alt="" aria-hidden="true">'
