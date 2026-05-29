# PyInstaller spec for the UnMsg desktop app (Windows, onedir, windowed).
#
# Build from the repository root:
#     pyinstaller installer/windows/pyinstaller.spec
#
# Produces dist/UnMsg/UnMsg.exe and its support files. onedir (not onefile) is
# deliberate: faster cold start and fewer antivirus false positives.

import os

from PyInstaller.utils.hooks import collect_submodules

# SPECPATH is this file's directory; the repo root is two levels up.
ROOT = os.path.abspath(os.path.join(SPECPATH, "..", ".."))
SRC = os.path.join(ROOT, "src")

hiddenimports = collect_submodules("unmsg")

ICONS = os.path.join(SRC, "unmsg", "ui", "resources", "icons")
a = Analysis(
    [os.path.join(SRC, "unmsg", "ui", "app.py")],
    pathex=[SRC],
    binaries=[],
    datas=[(ICONS, "unmsg/ui/resources/icons")],  # bundle the app icon assets
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "pandas", "numpy"],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="UnMsg",
    debug=False,
    strip=False,
    upx=False,
    console=False,  # windowed app — no console window
    icon=os.path.join(ICONS, "unmsg.ico"),
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="UnMsg",
)
