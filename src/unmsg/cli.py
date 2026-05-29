"""Command-line interface for UnMsg.

Thin shell over :mod:`unmsg.core`: discover inputs, run the batch, report
clearly, and return a meaningful exit code. All the conversion logic lives in
the core; this module only does discovery, presentation, and process glue.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from unmsg._version import __version__
from unmsg.core import ConvertOptions, convert_batch
from unmsg.core.manifest import write_manifest
from unmsg.core.models import ConvertResult, FormatId, InlineMode, OnConflict

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Turn Outlook .msg files into clean, readable formats. Nothing leaves "
    "your machine.",
)
console = Console()
err_console = Console(stderr=True)

# Exit codes that mean something to scripts.
EXIT_OK = 0
EXIT_PARTIAL = 1
EXIT_FAILED = 2
EXIT_NO_INPUT = 3

_KNOWN_FORMATS: tuple[FormatId, ...] = (
    "md",
    "html",
    "html_single",
    "txt",
    "json",
    "eml",
    "pdf",
)


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"unmsg {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    _version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=_version_callback,
            is_eager=True,
            help="Show the version and exit.",
        ),
    ] = False,
) -> None:
    """UnMsg."""


@app.command()
def convert(
    paths: Annotated[
        list[Path],
        typer.Argument(help="The .msg files or folders to convert."),
    ],
    output: Annotated[
        Path,
        typer.Option("-o", "--output", help="Where to write the output."),
    ],
    formats: Annotated[
        str,
        typer.Option("-f", "--format", help="Comma-separated: md,html,html_single."),
    ] = "md,html",
    attachments: Annotated[
        bool,
        typer.Option(help="Save regular attachments."),
    ] = True,
    inline: Annotated[
        str,
        typer.Option(help="Inline images: extract, base64, or skip."),
    ] = "extract",
    naming: Annotated[
        str,
        typer.Option(help="Output naming template, e.g. {date}_{subject}."),
    ] = "{date}_{subject}",
    on_conflict: Annotated[
        str,
        typer.Option(
            "--on-conflict", help="When a name exists: rename, overwrite, skip."
        ),
    ] = "rename",
    manifest: Annotated[
        bool,
        typer.Option(help="Write manifest.json (with checksums) at the output root."),
    ] = True,
    jobs: Annotated[
        int,
        typer.Option(
            "-j", "--jobs", min=1, help="Convert with this many worker processes."
        ),
    ] = 1,
    timeout: Annotated[
        float,
        typer.Option(
            min=0.0, help="Give up on a single message after N seconds (0 = no limit)."
        ),
    ] = 0.0,
    resume: Annotated[
        bool,
        typer.Option(help="Skip messages already converted (per the manifest)."),
    ] = False,
) -> None:
    """Convert one or more .msg files."""
    sources = _discover(paths)
    if not sources:
        err_console.print("[yellow]No .msg files found in what you gave me.[/]")
        raise typer.Exit(EXIT_NO_INPUT)

    carried: list[dict[str, object]] = []
    if resume:
        from unmsg.resume import plan_resume

        sources, carried = plan_resume(sources, output)
        if carried:
            console.print(f"  resuming — skipping {len(carried)} already done")
        if not sources:
            console.print("[green]Nothing to do — everything is already converted.[/]")
            raise typer.Exit(EXIT_OK)

    try:
        opts = ConvertOptions(
            formats=_parse_formats(formats),
            attachments=attachments,
            inline_images=_parse_inline(inline),
            naming_template=naming.strip() or "{date}_{subject}",
            on_conflict=_parse_on_conflict(on_conflict),
        )
    except ValueError as exc:
        err_console.print(f"[red]{exc}[/]")
        raise typer.Exit(EXIT_FAILED) from None

    if jobs > 1 or timeout > 0:
        from unmsg.parallel import convert_batch_parallel

        results = convert_batch_parallel(
            sources, output, opts, jobs=jobs, timeout=timeout, progress=_progress
        )
    else:
        results = convert_batch(sources, output, opts, progress=_progress)
    if manifest and (results or carried):
        write_manifest(results, output, carried=carried)
    raise typer.Exit(_summarize(results))


def _discover(paths: list[Path]) -> list[Path]:
    found: set[Path] = set()
    for path in paths:
        if path.is_dir():
            found.update(p for p in path.rglob("*.msg") if p.is_file())
        elif path.suffix.lower() == ".msg" and path.is_file():
            found.add(path)
    return sorted(found, key=lambda p: str(p).lower())


def _parse_formats(raw: str) -> tuple[FormatId, ...]:
    ids = tuple(part.strip().lower() for part in raw.split(",") if part.strip())
    unknown = [i for i in ids if i not in _KNOWN_FORMATS]
    if unknown:
        raise ValueError(f"Unknown format(s): {', '.join(unknown)}.")
    if not ids:
        raise ValueError("Pick at least one output format.")
    return tuple(ids)  # type: ignore[return-value]


def _parse_inline(raw: str) -> InlineMode:
    value = raw.strip().lower()
    if value not in ("extract", "base64", "skip"):
        raise ValueError("Inline mode must be extract, base64, or skip.")
    return value  # type: ignore[return-value]


def _parse_on_conflict(raw: str) -> OnConflict:
    value = raw.strip().lower()
    if value not in ("rename", "overwrite", "skip"):
        raise ValueError("On-conflict must be rename, overwrite, or skip.")
    return value  # type: ignore[return-value]


def _progress(done: int, total: int, source: Path) -> None:
    console.print(f"  [{done}/{total}] {source.name}")


def _summarize(results: list[ConvertResult]) -> int:
    failed = [r for r in results if r.status == "failed"]
    warned = [r for r in results if r.status == "warning"]
    done = len(results) - len(failed)

    console.print()
    console.print(f"[green]Converted {done} of {len(results)} message(s).[/]")
    for result in warned:
        console.print(
            f"  [yellow]warning[/] {result.source.name}: {result.warnings[0]}"
        )
    for result in failed:
        console.print(f"  [red]failed[/] {result.source.name}: {result.error}")

    if failed and len(failed) == len(results):
        return EXIT_FAILED
    if failed or warned:
        return EXIT_PARTIAL
    return EXIT_OK
