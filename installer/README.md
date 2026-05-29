# Building the installers

## Windows

Prerequisites: Python 3.11+, the project installed with its GUI extra, and
[Inno Setup](https://jrsoftware.org/isinfo.php) on `PATH` (`iscc`).

```bat
pip install ".[gui]" pyinstaller
pyinstaller installer/windows/pyinstaller.spec
iscc installer/windows/installer.iss
```

- The first command bundles the app to `dist/UnMsg/`.
- The second produces `dist/installer/UnMsg-Setup-<version>.exe`.

The installer offers a Start-menu shortcut, an optional desktop shortcut, an
optional Send To entry, and an optional "Convert with UnMsg" entry on the `.msg`
right-click menu.

### Signing

Releases are unsigned for now: Windows SmartScreen shows a "Windows protected
your PC" notice — click **More info → Run anyway**. Code signing is planned for
the 1.0 release, after which the warning goes away.

## macOS / Linux

Best-effort `.dmg` and `.AppImage` builds arrive with the 1.0 release.
