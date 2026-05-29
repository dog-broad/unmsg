# PyInstaller spec for the UnMsg desktop app (Windows, onedir, windowed).
#
# Build from the repository root:
#     pyinstaller installer/windows/pyinstaller.spec
#
# Produces dist/UnMsg/UnMsg.exe and its support files. onedir (not onefile) is
# deliberate: faster cold start and fewer antivirus false positives.

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules("unmsg")

a = Analysis(
    ["src/unmsg/ui/app.py"],
    pathex=["src"],
    binaries=[],
    datas=[],
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
