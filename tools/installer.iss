; SimGhostInputs — Inno Setup 6
; Genera: dist\SimGhostInputs-v<version>-Setup.exe
; Requiere: bundle en dist\SimGhostInputs\ (generado por nicegui-pack --onedir)
;
; La version se pasa por linea de comandos: ISCC /DMyAppVersion=X.Y.Z installer.iss
; Si no se pasa, queda "0.0.0" como centinela (ver build_installer.py).

#define MyAppName "SimGhostInputs"
#ifndef MyAppVersion
#define MyAppVersion "0.0.0"
#endif
#define MyAppPublisher "Armando Medina"
#define MyAppURL "https://github.com/ArmandoMedina/SimGhostInputs"
#define MyAppExeName "SimGhostInputs.exe"
#define BundleDir "dist\SimGhostInputs"

[Setup]
; Las rutas relativas del script (LICENSE, dist\...) son respecto a la RAIZ
; del repo; ISCC resuelve respecto al .iss (tools\), asi que se corrige aqui.
SourceDir=..
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=dist
OutputBaseFilename=SimGhostInputs-v{#MyAppVersion}-Setup
SetupIconFile=docs\icon.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
DisableWelcomePage=no
LicenseFile=LICENSE
MinVersion=10.0.17763
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
Source: "{#BundleDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
