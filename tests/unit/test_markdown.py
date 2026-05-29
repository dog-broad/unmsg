"""HTML to Markdown conversion."""

from __future__ import annotations

from unmsg.core.markdown import to_markdown


def test_basic_conversion():
    out = to_markdown("<h1>Title</h1><p>Hello <b>world</b></p>")
    assert "# Title" in out
    assert "**world**" in out
    assert out.endswith("\n")


def test_empty_html_returns_empty():
    assert to_markdown("") == ""
    assert to_markdown("   ") == ""


def test_links_preserved():
    out = to_markdown('<p>See <a href="https://example.com">site</a></p>')
    assert "https://example.com" in out


def test_collapses_excess_blank_lines():
    out = to_markdown("<p>a</p><p>b</p>")
    assert "\n\n\n" not in out


def test_pandoc_falls_back_when_absent():
    # use_pandoc requested but pandoc is not on PATH in CI -> markdownify used.
    out = to_markdown("<p>fallback</p>", use_pandoc=True)
    assert "fallback" in out


def test_pandoc_used_when_available(monkeypatch):
    import sys
    import types

    import unmsg.core.markdown as md

    fake = types.ModuleType("pypandoc")
    fake.convert_text = lambda text, to, format: "# Pandoc said so\n"  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "pypandoc", fake)
    monkeypatch.setattr(md.shutil, "which", lambda name: "/usr/bin/pandoc")

    out = to_markdown("<h1>x</h1>", use_pandoc=True)
    assert "Pandoc said so" in out


def test_pandoc_import_error_falls_back(monkeypatch):
    import builtins

    import unmsg.core.markdown as md

    monkeypatch.setattr(md.shutil, "which", lambda name: "/usr/bin/pandoc")
    real_import = builtins.__import__

    def no_pypandoc(name, *args, **kw):
        if name == "pypandoc":
            raise ImportError("nope")
        return real_import(name, *args, **kw)

    monkeypatch.setattr(builtins, "__import__", no_pypandoc)
    out = to_markdown("<p>still works</p>", use_pandoc=True)
    assert "still works" in out
