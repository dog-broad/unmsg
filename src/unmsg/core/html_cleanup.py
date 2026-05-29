"""Clean message HTML and rewrite inline-image references.

Outlook HTML is noisy: scripts, styles, MSO conditional comments, and event
handlers. We strip what is unsafe or pointless and leave readable content. The
parser preserves source order, so cleanup is deterministic.
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup, Comment

_DROP_TAGS = ("script", "style", "meta", "link", "o:p")
_EVENT_ATTR = re.compile(r"^on", re.IGNORECASE)
_CID_REF = re.compile(r'(?i)\bcid:([^"\'>\s]+)')


def clean_html(html: str) -> str:
    """Strip scripts, styles, MSO bloat, comments, and event handlers."""
    if not html.strip():
        return ""
    soup = BeautifulSoup(html, "html.parser")

    for comment in soup.find_all(string=lambda s: isinstance(s, Comment)):
        comment.extract()

    for tag in soup.find_all(_DROP_TAGS):
        tag.decompose()

    for tag in soup.find_all(True):
        for attr in list(tag.attrs):
            if _EVENT_ATTR.match(attr):
                del tag[attr]

    body = soup.body
    fragment = body.decode_contents() if body else str(soup)
    return fragment.strip()


def to_text(html: str) -> str:
    """Extract readable plain text from HTML (for messages with no text body)."""
    if not html.strip():
        return ""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n")
    out: list[str] = []
    blanks = 0
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            blanks = 0
            out.append(stripped)
        else:
            blanks += 1
            if blanks <= 1:
                out.append("")
    return "\n".join(out).strip()


def rewrite_cids(html: str, cid_map: dict[str, str]) -> str:
    """Rewrite ``cid:`` references to the relative paths in ``cid_map``.

    Keys are content-ids without the ``cid:`` scheme or angle brackets. An
    unmatched reference is left untouched so nothing is silently broken.
    """
    if not cid_map:
        return html

    normalized = {k.strip().strip("<>").lower(): v for k, v in cid_map.items()}

    def repl(match: re.Match[str]) -> str:
        key = match.group(1).strip().strip("<>").lower()
        return normalized.get(key, match.group(0))

    return _CID_REF.sub(repl, html)
