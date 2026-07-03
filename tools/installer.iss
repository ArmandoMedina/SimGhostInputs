; SimGhostInputs — Inno Setup 6
; Genera: dist\SimGhostInputs-v2.0-Setup.exe
; Requiere: bundle en dist\SimGhostInputs\ (generado por nicegui-pack --onedir)
;
; NOTA: SetupIconFile esta comentado porque docs\icon.ico aun no existe.
; Para agregar el icono: pon el .ico en docs\icon.ico y descomenta la linea.

#define MyAppName "SimGhostInputs"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "Armando Medina"
#define MyAppURL "https://github.com/ArmandoMedina/SimGhostInputs"
#define MyAppExeName "SimGhostInputs.exe"
#define BundleDir "dist\SimGhostInputs"

[Setup]
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
; SetupIconFile=docs\icon.ico  <- descomentar cuando exista docs\icon.ico
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
Name: "desktopicon"; Description: "Crear icono en el {cm:DesktopFolder}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

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
