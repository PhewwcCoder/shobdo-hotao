; Inno Setup script for ShobdoHotao (শব্দ-হটাও).
;
; Wraps the PyInstaller one-dir output (dist\ShobdoHotao\) into a single
; Setup.exe that installs per-user (no admin prompt) and creates Start-Menu +
; optional Desktop shortcuts. Version is injected from CI:
;     ISCC.exe /DAppVersion=0.1.0 installer\shobdohotao.iss
; A custom icon is used automatically if assets\app.ico exists.

#define AppName "ShobdoHotao"
#define AppPublisher "ShobdoHotao contributors"
#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

[Setup]
; Stable AppId so upgrades replace the previous install (do not change it).
AppId={{B3F1C2A4-9D7E-4F8B-A1C6-2E5D7A9C4B10}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
UninstallDisplayName={#AppName}
UninstallDisplayIcon={app}\ShobdoHotao.exe
OutputDir=Output
OutputBaseFilename=ShobdoHotao-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; Per-user install -> no UAC prompt, fewer clicks for non-technical users.
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
#if FileExists(AddBackslash(SourcePath) + "..\assets\app.ico")
SetupIconFile=..\assets\app.ico
#endif

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; \
    GroupDescription: "{cm:AdditionalIcons}"

[Files]
; The entire PyInstaller one-dir bundle.
Source: "..\dist\ShobdoHotao\*"; DestDir: "{app}"; \
    Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\ShobdoHotao.exe"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\ShobdoHotao.exe"; \
    Tasks: desktopicon

[Run]
Filename: "{app}\ShobdoHotao.exe"; \
    Description: "{cm:LaunchProgram,{#AppName}}"; \
    Flags: nowait postinstall skipifsilent
