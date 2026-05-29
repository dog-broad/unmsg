"""CLI: discovery, exit codes, version, and a real conversion run."""

from __future__ import annotations

from typer.testing import CliRunner

import unmsg.core.pipeline as pipeline
from unmsg.cli import app

runner = CliRunner()


def _patch_reader(monkeypatch, record):
    monkeypatch.setattr(pipeline, "read_msg", lambda path: record)


def test_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "unmsg" in result.stdout


def test_no_input_returns_3(tmp_path):
    result = runner.invoke(app, ["convert", str(tmp_path), "-o", str(tmp_path / "out")])
    assert result.exit_code == 3


def test_unknown_format_returns_2(monkeypatch, tmp_path, make_record):
    _patch_reader(monkeypatch, make_record())
    src = tmp_path / "a.msg"
    src.write_bytes(b"x")
    result = runner.invoke(
        app, ["convert", str(src), "-o", str(tmp_path / "out"), "-f", "md,bogus"]
    )
    assert result.exit_code == 2


def test_successful_conversion_returns_0(monkeypatch, tmp_path, make_record):
    _patch_reader(monkeypatch, make_record())
    src = tmp_path / "a.msg"
    src.write_bytes(b"x")
    out = tmp_path / "out"
    result = runner.invoke(app, ["convert", str(src), "-o", str(out), "-f", "md"])
    assert result.exit_code == 0
    assert (out / "2024-03-15_Quarterly Report.md").exists()


def test_warning_conversion_returns_1(monkeypatch, tmp_path, make_record):
    _patch_reader(monkeypatch, make_record())
    src = tmp_path / "a.msg"
    src.write_bytes(b"x")
    result = runner.invoke(
        app, ["convert", str(src), "-o", str(tmp_path / "out"), "-f", "md,pdf"]
    )
    assert result.exit_code == 1


def test_folder_discovery_finds_msg(monkeypatch, tmp_path, make_record):
    _patch_reader(monkeypatch, make_record())
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "x.msg").write_bytes(b"x")
    out = tmp_path / "out"
    result = runner.invoke(app, ["convert", str(tmp_path), "-o", str(out), "-f", "md"])
    assert result.exit_code == 0


def test_manifest_written_by_default(monkeypatch, tmp_path, make_record):
    _patch_reader(monkeypatch, make_record())
    src = tmp_path / "a.msg"
    src.write_bytes(b"x")
    out = tmp_path / "out"
    result = runner.invoke(app, ["convert", str(src), "-o", str(out), "-f", "md"])
    assert result.exit_code == 0
    assert (out / "manifest.json").exists()


def test_no_manifest_flag_skips_it(monkeypatch, tmp_path, make_record):
    _patch_reader(monkeypatch, make_record())
    src = tmp_path / "a.msg"
    src.write_bytes(b"x")
    out = tmp_path / "out"
    result = runner.invoke(
        app, ["convert", str(src), "-o", str(out), "-f", "md", "--no-manifest"]
    )
    assert result.exit_code == 0
    assert not (out / "manifest.json").exists()


def test_eml_format_is_produced(monkeypatch, tmp_path, make_record):
    _patch_reader(monkeypatch, make_record())
    src = tmp_path / "a.msg"
    src.write_bytes(b"x")
    out = tmp_path / "out"
    result = runner.invoke(app, ["convert", str(src), "-o", str(out), "-f", "eml"])
    assert result.exit_code == 0
    assert list(out.rglob("*.eml"))


def test_invalid_on_conflict_returns_2(monkeypatch, tmp_path, make_record):
    _patch_reader(monkeypatch, make_record())
    src = tmp_path / "a.msg"
    src.write_bytes(b"x")
    result = runner.invoke(
        app,
        ["convert", str(src), "-o", str(tmp_path / "out"), "--on-conflict", "bogus"],
    )
    assert result.exit_code == 2


def test_naming_template_applied(monkeypatch, tmp_path, make_record):
    _patch_reader(monkeypatch, make_record())
    src = tmp_path / "a.msg"
    src.write_bytes(b"x")
    out = tmp_path / "out"
    result = runner.invoke(
        app, ["convert", str(src), "-o", str(out), "-f", "md", "--naming", "{subject}"]
    )
    assert result.exit_code == 0
    assert (out / "Quarterly Report.md").exists()
