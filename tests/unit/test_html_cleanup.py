"""HTML cleanup and cid rewriting."""

from __future__ import annotations

from unmsg.core.html_cleanup import clean_html, rewrite_cids


def test_clean_removes_script_and_style():
    out = clean_html(
        "<html><body><script>evil()</script><style>x{}</style><p>Hi</p></body></html>"
    )
    assert "evil" not in out
    assert "x{}" not in out
    assert "Hi" in out


def test_clean_removes_comments_and_mso():
    out = clean_html(
        "<body><!--[if mso]><p>bloat</p><![endif]--><o:p></o:p><p>Real</p></body>"
    )
    assert "bloat" not in out
    assert "Real" in out


def test_clean_strips_event_handlers():
    out = clean_html('<body><a href="#" onclick="steal()">link</a></body>')
    assert "onclick" not in out
    assert "steal" not in out
    assert "link" in out


def test_clean_empty_returns_empty():
    assert clean_html("") == ""
    assert clean_html("   ") == ""


def test_rewrite_cids_replaces_known_reference():
    html = '<img src="cid:image001">'
    out = rewrite_cids(html, {"image001": "assets/inline_image_1.png"})
    assert "assets/inline_image_1.png" in out
    assert "cid:" not in out


def test_rewrite_cids_handles_angle_brackets_and_case():
    html = '<img src="cid:ABC123">'
    out = rewrite_cids(html, {"<abc123>": "assets/x.png"})
    assert "assets/x.png" in out


def test_rewrite_cids_leaves_unknown_untouched():
    html = '<img src="cid:missing">'
    assert rewrite_cids(html, {"other": "x"}) == html


def test_rewrite_cids_empty_map_is_noop():
    html = '<img src="cid:x">'
    assert rewrite_cids(html, {}) == html
