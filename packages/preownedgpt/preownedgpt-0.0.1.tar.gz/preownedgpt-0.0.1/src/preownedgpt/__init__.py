"""PreownedGPT placeholder package."""

from __future__ import annotations

import webbrowser


def _redirect_and_raise() -> None:
    url = "https://preownedgpt.com"
    try:
        webbrowser.open(url, new=2)
    except Exception:
        pass
    raise RuntimeError(
        "This package is a placeholder. Visit https://preownedgpt.com for details."
    )


_redirect_and_raise()
