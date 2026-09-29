; Inno Setup Script for VidMuncher
; For details on Inno Setup Scripting see: https://jrsoftware.org/ishelp/

#define AppName "VidMuncher"
#define AppVersion "1.1.1"
#define AppPublisher "Aprix Labs"
#define AppURL "https://github.com/aprixlabs/VidMuncher"
#define AppExeName "VidMuncher.exe"

[Setup]
; Unique App ID (generated for VidMuncher)
AppId={{9F7B2C5D-6A4E-4C21-BD3A-1B8D9E3C5F8A}
AppName={#AppName}
AppVersion={#AppVersion}
VersionInfoVersion={#AppVersion}.0
UninstallDisplayName={#AppName}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={localappdata}\Programs\{#AppName}
DisableProgramGroupPage=yes
LicenseFile=..\..\..\LICENSE
PrivilegesRequired=lowest
; Output directory for installer
OutputDir=..\..\..\dist\windows
OutputBaseFilename=VidMuncher-{#AppVersion}-Windows-x64-Installer
SetupIconFile=..\..\..\src\app\assets\icons\icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\..\..\dist\windows\VidMuncher\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
