; =============================================================================
;  Inno Setup script  ->  builds a one-click "TrafficMonitor-Setup.exe"
; =============================================================================
;  This wraps the standalone dist\TrafficMonitor.exe into a friendly installer
;  with Start-menu shortcut, optional desktop icon, optional start-with-Windows,
;  and a proper uninstaller.
;
;  HOW TO COMPILE:
;    * Easiest: let GitHub Actions do it (see .github/workflows/build.yml).
;    * Locally: install Inno Setup (free, NO Python needed) from
;        https://jrsoftware.org/isdl.php
;      then run:   ISCC installer.iss
;      (or just right-click this file -> Compile)
;
;  NOTE: build the exe first (PyInstaller) so dist\TrafficMonitor.exe exists.
; =============================================================================

#define MyAppName "TrafficMonitor"
#define MyAppVersion "1.0.0"
#define MyAppExe "TrafficMonitor.exe"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=OR_Mahim
AppComments=Instructed & created with AI by OR_Mahim
; Install per-user so it works even WITHOUT admin rights (locked-down PCs):
PrivilegesRequired=lowest
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExe}
OutputDir=installer
OutputBaseFilename=TrafficMonitor-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"
Name: "startupicon"; Description: "Start {#MyAppName} when Windows starts"; GroupDescription: "Startup:"

[Files]
Source: "dist\{#MyAppExe}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}";            Filename: "{app}\{#MyAppExe}"
Name: "{group}\Uninstall {#MyAppName}";  Filename: "{uninstallexe}"
Name: "{userdesktop}\{#MyAppName}";      Filename: "{app}\{#MyAppExe}"; Tasks: desktopicon
Name: "{userstartup}\{#MyAppName}";      Filename: "{app}\{#MyAppExe}"; Tasks: startupicon

[Run]
Filename: "{app}\{#MyAppExe}"; Description: "Launch {#MyAppName} now"; Flags: nowait postinstall skipifsilent
