# API reference

UnMsg's public Python API is intentionally small and **stable from `1.0`
onward**. The contract:

- The names listed here keep their identities and shapes across `1.x`.
- Data models (`Attachment`, `MsgRecord`, `ConvertResult`, `ConvertOptions`)
  gain new *optional* fields only — existing fields don't move or change
  meaning.
- `convert_file` and `convert_batch` keep their existing keyword arguments;
  new optional arguments may be added at the tail.

Anything not listed here — submodules of `unmsg.core`, writers, the UI, the
CLI module layout — is private and may change.

## Quick example

```python
from pathlib import Path
from unmsg import convert_file, ConvertOptions

result = convert_file(
    Path("mail.msg"),
    Path("./out"),
    ConvertOptions(formats=["md", "html", "pdf"]),
)

if result.status == "success":
    for path in result.output_paths:
        print("wrote", path)
elif result.status == "warning":
    print("converted with notes:", result.warnings)
else:
    print("couldn't convert:", result.error)
```

## Functions

::: unmsg.convert_file

::: unmsg.convert_batch

## Data models

::: unmsg.ConvertOptions

::: unmsg.ConvertResult

::: unmsg.MsgRecord

::: unmsg.Attachment

## Version

::: unmsg.__version__
