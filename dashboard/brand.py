"""Original ROYAL SCOUT monogram for dashboard presentation only."""
from __future__ import annotations

from base64 import b64encode
from functools import lru_cache
from pathlib import Path


LOGO_PATH = Path(__file__).resolve().parent / "assets" / "rr_monogram.svg"


@lru_cache(maxsize=1)
def logo_src() -> str:
    """Embed the local transparent SVG without relying on a static-file server."""
    return "data:image/svg+xml;base64," + b64encode(LOGO_PATH.read_bytes()).decode("ascii")


def logo_html(placement: str) -> str:
    """Return a decorative image; surrounding brand text provides the name."""
    if placement not in {"sidebar", "header", "overview", "footer"}:
        raise ValueError(f"Unknown monogram placement: {placement}")
    return f'<img class="rr-monogram rr-monogram--{placement}" src="{logo_src()}" alt="" aria-hidden="true">'
