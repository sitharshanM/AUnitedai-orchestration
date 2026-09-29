#define MyAppName "AUnitedAI"
#define MyAppVersion "2.0.0"
#define MyAppExeName "AUnitedAI.exe"

[Setup]
AppId={{BD4BDB3A-22F9-477B-92A7-829E4764DA2A}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\AUnitedAI
DefaultGroupName=AUnitedAI
OutputDir=..\release
OutputBaseFilename=AUnitedAI-Setup-2.0.0
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}

[Files]
Source: "..\release\AUnitedAI\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\AUnitedAI"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\AUnitedAI"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch AUnitedAI"; Flags: nowait postinstall skipifsilent
