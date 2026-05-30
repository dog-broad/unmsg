# Command line

```text
unmsg convert <paths>… -o <out> [options]
```

`paths` may be `.msg` files or folders (folders are walked recursively for
`.msg` files). The output folder is created if it doesn't exist.

## Exit codes

UnMsg's CLI returns scriptable exit codes — no parsing of stderr needed.

| Code | Meaning                              |
|------|--------------------------------------|
| `0`  | All files converted successfully     |
| `1`  | Partial — at least one file failed   |
| `2`  | All files failed                     |
| `3`  | No input files matched               |

## Options

### Output formats

```bash
unmsg convert mail.msg -o out --format md,html,html_single,txt,json,eml,pdf
```

| Format        | Extension          |
|---------------|--------------------|
| `md`          | `.md`              |
| `html`        | `.html`            |
| `html_single` | `.single.html` (inline images) |
| `txt`         | `.txt`             |
| `json`        | `.metadata.json`   |
| `eml`         | `.eml`             |
| `pdf`         | `.pdf` (needs `unmsg[pdf]`) |

If a format's optional dependency is missing the other formats still convert
and that one is degraded to a warning for that message.

### Naming

`--naming` controls the output bundle name. Tokens you can use:

| Token         | Example         |
|---------------|-----------------|
| `{date}`      | `2024-03-15`    |
| `{time}`      | `093200`        |
| `{subject}`   | `Quarterly Report` |
| `{from_name}` | `Alice Example` |
| `{from_email}`| `alice@example.com` |
| `{hash}`      | 8‑char stable hash |

Defaults to `{date}_{subject}`. Unknown tokens degrade gracefully (the
literal name is used) — a typo won't fail your batch.

### Conflict handling

```bash
--on-conflict rename   # default — append a counter
--on-conflict skip     # leave existing outputs alone
--on-conflict overwrite
```

### Performance & resilience

```bash
--jobs N         # parallel conversion across worker processes
--timeout S      # per-file timeout; a single stuck file is terminated
--resume         # skip files whose outputs are already in the manifest
```

`--resume` verifies each existing output's SHA‑256 against the per‑batch
`manifest.json`; mismatched entries get reconverted.

### Manifests

A `manifest.json` is written at the output root by default — relative paths
and no timestamps, so identical runs produce identical manifests. Disable
with `--no-manifest`.

### Other flags

- `--theme`, `--log-level`, `--version`, `--help` — standard.
- Errors are friendly and concrete — no stack traces ever reach you. The full
  trace is in the local log file.
