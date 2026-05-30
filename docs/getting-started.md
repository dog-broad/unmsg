# Getting started

There are three ways to install UnMsg. Pick the one that matches how you'll
use it.

## Install — pick one

=== "Windows installer (most users)"

    Download the latest installer from the
    [releases page](https://github.com/dog-broad/unmsg/releases) and run it.
    You get:

    - **UnMsg** in the Start menu
    - A "Convert with UnMsg" entry on the **right‑click menu of `.msg` files**
    - A **Send To → UnMsg** target
    - An optional desktop shortcut

    Releases are currently **unsigned**, so SmartScreen shows a warning the
    first time. Click **More info → Run anyway**. (Code signing is planned.)

=== "Python package (CLI + API)"

    ```bash
    pip install unmsg
    ```

    That installs the conversion core and the `unmsg` command line. The
    desktop GUI is an optional extra — see below.

=== "With the desktop app"

    ```bash
    pip install "unmsg[gui]"
    unmsg-gui
    ```

=== "With PDF output"

    ```bash
    pip install "unmsg[pdf]"
    ```

    Or `unmsg[gui,pdf]` for both. PDF rendering is pure‑Python and
    deterministic.

## Your first conversion

### Desktop

1. Open **UnMsg**.
2. **Drop** one or more `.msg` files (or a folder) on the window.
3. Click **Convert**.

The default output folder is your `Documents/UnMsg` — change it from the
options bar.

### Command line

```bash
unmsg convert mail.msg -o ./out --format md,html,pdf
```

Convert a folder, recursively:

```bash
unmsg convert ./inbox -o ./out --format md
```

See the [CLI reference](cli.md) for every option.

### Python

```python
from pathlib import Path
from unmsg import convert_file, ConvertOptions

result = convert_file(
    Path("mail.msg"),
    Path("./out"),
    ConvertOptions(formats=["md", "html"]),
)
print(result.status, result.output_paths)
```

More in the [API reference](api.md).
