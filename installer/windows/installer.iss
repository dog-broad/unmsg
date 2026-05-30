; Inno Setup script for the UnMsg Windows installer.
; Build the app first (see pyinstaller.spec), then compile from the repo root:
;     iscc installer/windows/installer.iss
; Keep MyAppVersion in step with src/unmsg/_version.py.

#define MyAppName "UnMsg"
#ifndef MyAppVersion
  #define MyAppVersion "0.0.0-local"
#endif
#define MyAppExe "UnMsg.exe"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=UnMsg
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=dist\installer
OutputBaseFilename=UnMsg-Setup-{#MyAppVersion}
SetupIconFile=src\unmsg\ui\resources\icons\unmsg.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked
Name: "sendto"; Description: "Add UnMsg to the Send To menu"
Name: "contextmenu"; Description: "Add 'Convert with UnMsg' to the .msg right-click menu"

[Files]
Source: "dist\UnMsg\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"; Tasks: desktopicon
Name: "{sendto}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"; Tasks: sendto

[Registry]
Root: HKCU; Subkey: "Software\Classes\.msg\shell\UnMsg"; ValueType: string; ValueData: "Convert with UnMsg"; Tasks: contextmenu; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\.msg\shell\UnMsg\command"; ValueType: string; ValueData: """{app}\{#MyAppExe}"" ""%1"""; Tasks: contextmenu

[Run]
Filename: "{app}\{#MyAppExe}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
