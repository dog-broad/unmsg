"""Opt-in update check — the only outbound network call in the whole app.

It runs only when the user has turned it on, reads a public version list, sends
nothing about the user, and never downloads or installs anything. Keeping it in
one small module makes that promise easy to audit.
"""

from __future__ import annotations

import json
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass

from unmsg._version import __version__

_OWNER_REPO = "dog-broad/unmsg"
RELEASES_API = f"https://api.github.com/repos/{_OWNER_REPO}/releases/latest"
RELEASES_PAGE = f"https://github.com/{_OWNER_REPO}/releases/latest"

Fetcher = Callable[[str, float], bytes]


@dataclass(slots=True, frozen=True)
class UpdateInfo:
    current: str
    latest: str
    url: str
    notes: str

    @property
    def is_newer(self) -> bool:
        return _version_tuple(self.latest) > _version_tuple(self.current)


def check_for_update(
    *, timeout: float = 5.0, fetch: Fetcher | None = None
) -> UpdateInfo | None:
    """Return update info, or ``None`` if the check fails or can't be parsed.

    ``fetch`` is injectable so this is unit-tested without touching the network.
    The caller decides what to do with a result; this function only reports.
    """
    fetcher = fetch or _default_fetch
    try:
        data = json.loads(fetcher(RELEASES_API, timeout))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    latest = str(data.get("tag_name", "")).lstrip("vV").strip()
    if not latest:
        return None
    return UpdateInfo(
        current=__version__,
        latest=latest,
        url=str(data.get("html_url") or RELEASES_PAGE),
        notes=str(data.get("body") or ""),
    )


def _default_fetch(url: str, timeout: float) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "unmsg"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def _version_tuple(version: str) -> tuple[int, ...]:
    """Compare versions by leading numeric components (prerelease suffix ignored)."""
    parts: list[int] = []
    for chunk in version.lstrip("vV").split("."):
        lead = ""
        for char in chunk:
            if char.isdigit():
                lead += char
            else:
                break
        parts.append(int(lead) if lead else 0)
    return tuple(parts)
