# Build UnMsg from source

UnMsg's Windows installer is currently **unsigned**, so SmartScreen warns the
first time you run it. The warning isn't a verdict on the file — it's just
"no signature to vouch for the publisher yet." Three legitimate options:

1. Click **More info → Run anyway** once. Subsequent launches don't warn.
2. **Install via `pip`** — no executable to vouch for, your Python stack
   already trusts PyPI.
3. **Build the installer yourself** from the source on GitHub. That's the
   instructions below.

If you'd rather not deal with any of these, watch the
[releases page](https://github.com/dog-broad/unmsg/releases) — a signed
installer is on the way.

## Reproducible build

You'll produce **bit‑for‑bit the same artifacts** the GitHub Actions
release workflow produces, because both run the same `pyinstaller.spec` and
`installer.iss`.

### Prerequisites

- **Python 3.11 or 3.12** — get it from
  [python.org](https://www.python.org/downloads/) (tick "Add Python to PATH"
  during install).
- **Git** — [git‑scm.com](https://git-scm.com/downloads).
- For the Windows installer only: **Inno Setup 6** —
  [jrsoftware.org/isdl.php](https://jrsoftware.org/isdl.php). The default
  install location is `C:\Program Files (x86)\Inno Setup 6\`.

### Clone and create a virtual environment

```powershell
git clone https://github.com/dog-broad/unmsg.git
cd unmsg
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On macOS/Linux replace the last two lines with:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install with the GUI + PDF extras

```bash
pip install -e ".[gui,pdf]"
```

This installs the conversion core, the CLI (`unmsg`), and the desktop app
(`unmsg-gui`). Run them right away to verify:

```bash
unmsg --version
unmsg-gui
```

That's already a working install. The remaining steps repackage everything
into a single‑file installer for Windows.

### Build the Windows installer

```powershell
# bundle the app and Qt runtime into dist\UnMsg\
pip install pyinstaller
pyinstaller installer\windows\pyinstaller.spec --noconfirm

# wrap that into a setup .exe
$ver = (python -c "from unmsg._version import __version__; print(__version__)").Trim()
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" `
    /DMyAppVersion=$ver installer\windows\installer.iss
```

The installer lands at `dist\installer\UnMsg-Setup-<version>.exe`. Source
paths in `installer.iss` are anchored to the repo root with `SourceDir=..\..`,
so you can run `iscc` from anywhere on disk and the build still resolves
correctly.

### Verify your installer matches the release

The shipped installer is reproducible — the same source tree on the same
Python version produces the same Inno Setup bytes (Inno's compression is
deterministic given the same inputs). To confirm:

```powershell
Get-FileHash dist\installer\UnMsg-Setup-*.exe -Algorithm SHA256
```

…and compare to the SHA‑256 published alongside the installer on the
[release page](https://github.com/dog-broad/unmsg/releases). They should
match exactly.

## Just the wheel

If you only want the Python package (no installer), build the wheel:

```bash
pip install build
python -m build
```

`dist/unmsg-<version>-py3-none-any.whl` and the sdist appear in `dist/`. The
wheel is the same one published on PyPI.

## Run the tests while you're here

```bash
pip install -e ".[gui,pdf,dev]"
pytest --cov=unmsg
```

The full suite should pass and report ≥90% coverage. The GUI tests run
headless (`QT_QPA_PLATFORM=offscreen` is set automatically by
`pytest‑qt`).
