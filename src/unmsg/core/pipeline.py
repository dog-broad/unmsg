"""Convert one ``.msg`` file end to end.

The public entry point is :func:`convert_file`. It reads the message, then hands
the parsed record to :func:`_convert_record`, which the recursion for embedded
messages reuses. Errors are caught here and humanised onto the result; raw
exception detail goes only to the DEBUG log, never to the user.
"""

from __future__ import annotations

import hashlib
import logging
import time
from pathlib import Path

from unmsg.core.attachments import plan_attachments
from unmsg.core.html_cleanup import clean_html, rewrite_cids
from unmsg.core.markdown import to_markdown
from unmsg.core.models import ConvertResult, MsgRecord, Status
from unmsg.core.naming import fit_within_budget, stem_for
from unmsg.core.options import ConvertOptions
from unmsg.core.reader import read_msg
from unmsg.core.writer import RenderContext, get_writer

logger = logging.getLogger("unmsg.core")

_MAX_NEST_DEPTH = 5


def convert_file(
    source: Path | str,
    out_root: Path | str,
    options: ConvertOptions | None = None,
) -> ConvertResult:
    """Convert a single ``.msg`` file into ``out_root``."""
    src = Path(source)
    root = Path(out_root)
    opts = options or ConvertOptions()
    started = time.perf_counter()

    try:
        record = read_msg(src)
    except FileNotFoundError:
        return _failed(src, "Couldn't find this file.", started)
    except Exception as exc:
        logger.debug("read failed for %s", src, exc_info=exc)
        return _failed(
            src,
            "Couldn't read this message — it may be corrupt or password-protected.",
            started,
        )

    try:
        result = _convert_record(record, root, opts, depth=0)
    except Exception as exc:
        logger.debug("convert failed for %s", src, exc_info=exc)
        return _failed(
            src, "Couldn't write the converted files for this message.", started
        )

    result.source = src
    result.duration_ms = int((time.perf_counter() - started) * 1000)
    return result


def _convert_record(
    record: MsgRecord, out_root: Path, opts: ConvertOptions, *, depth: int
) -> ConvertResult:
    warnings: list[str] = []
    plan = plan_attachments(record.attachments, opts)
    warnings.extend(plan.warnings)

    has_assets = bool(plan.files) or bool(record.nested)
    flat = not has_assets and len(opts.formats) == 1

    stem = stem_for(record, opts.naming_template)
    longest_ext = max((f".{f}" for f in opts.formats), key=len, default=".html")
    stem = fit_within_budget(len(str(out_root)), stem, longest_ext)

    bundle_dir = out_root if flat else out_root / stem
    bundle_dir.mkdir(parents=True, exist_ok=True)

    cleaned = clean_html(record.body_html)
    html_body = rewrite_cids(cleaned, plan.cid_map) if cleaned else ""
    if html_body:
        markdown_body = to_markdown(html_body, use_pandoc=opts.use_pandoc)
    else:
        markdown_body = (record.body_text.strip() + "\n") if record.body_text else ""

    assets = {rel: plan.files[rel] for rel in plan.inline_paths}
    ctx = RenderContext(
        record=record,
        markdown_body=markdown_body,
        html_body=html_body,
        assets=assets,
    )

    output_paths: list[Path] = []
    sha256: dict[Path, str] = {}

    # Attachment and inline-image files first, sorted for deterministic order.
    saved_inline: list[Path] = []
    saved_regular: list[Path] = []
    for relpath in sorted(plan.files):
        target = bundle_dir / Path(relpath)
        target.parent.mkdir(parents=True, exist_ok=True)
        _write(target, plan.files[relpath])
        sha256[target] = _sha256(plan.files[relpath])
        if relpath in plan.inline_paths:
            saved_inline.append(target)
        else:
            saved_regular.append(target)

    # Rendered formats.
    for fmt in opts.formats:
        writer = get_writer(fmt)
        if writer is None:
            warnings.append(f"The '{fmt}' format isn't available yet — skipped.")
            continue
        data = writer.render(ctx)
        dest = _resolve_conflict(bundle_dir / f"{stem}{writer.extension}", opts)
        if dest is None:
            warnings.append(f"Skipped existing {fmt} output.")
            continue
        _write(dest, data)
        sha256[dest] = _sha256(data)
        output_paths.append(dest)

    # Embedded messages, converted into the attachments folder.
    if record.nested and depth < _MAX_NEST_DEPTH:
        nested_root = bundle_dir / "attachments"
        for nested in record.nested:
            sub = _convert_record(
                nested, nested_root, _single_format(opts), depth=depth + 1
            )
            output_paths.extend(sub.output_paths)
            saved_regular.extend(sub.attachments_saved)
            sha256.update(sub.sha256)
            warnings.extend(sub.warnings)
    elif record.nested:
        warnings.append("Stopped unpacking deeply nested messages.")

    status: Status = "warning" if warnings else "success"
    return ConvertResult(
        source=record.raw_path,
        bundle_dir=None if flat else bundle_dir,
        output_paths=output_paths,
        attachments_saved=saved_regular,
        inline_images_saved=saved_inline,
        status=status,
        warnings=warnings,
        error=None,
        duration_ms=0,
        sha256=sha256,
    )


def _single_format(opts: ConvertOptions) -> ConvertOptions:
    """Nested messages render to Markdown only — enough to preserve content
    without exploding the output tree."""
    from dataclasses import replace

    fmt = "md" if "md" in opts.formats else opts.formats[0]
    return replace(opts, formats=(fmt,))


def _resolve_conflict(path: Path, opts: ConvertOptions) -> Path | None:
    if not path.exists():
        return path
    if opts.on_conflict == "overwrite":
        return path
    if opts.on_conflict == "skip":
        return None
    stem, suffix = path.stem, path.suffix
    n = 1
    candidate = path
    while candidate.exists():
        candidate = path.with_name(f"{stem}_{n}{suffix}")
        n += 1
    return candidate


def _write(path: Path, data: bytes) -> None:
    path.write_bytes(data)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _failed(source: Path, message: str, started: float) -> ConvertResult:
    return ConvertResult(
        source=source,
        bundle_dir=None,
        output_paths=[],
        attachments_saved=[],
        inline_images_saved=[],
        status="failed",
        warnings=[],
        error=message,
        duration_ms=int((time.perf_counter() - started) * 1000),
    )
