; Inno Setup script for HD Adjustment Processor (Windows)
; Produces a single-file installer: HDProcessor-Setup.exe

#define AppName "HD Adjustment Processor"
#define AppVersion "1.0.7"
#define AppPublisher "Klear Concepts"
#define AppExeName "HDProcessor.exe"

[Setup]
AppId={{A3F2B1C4-8E6D-4A5F-9B2C-1D3E7F0A4B5C}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
SourceDir=..
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
OutputDir=installer\Output
OutputBaseFilename=HDProcessor-Setup
SetupIconFile=assets\app_icon.ico
UninstallDisplayIcon={app}\{#AppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
; Allow install without admin if user prefers their own directory
PrivilegesRequiredOverridesAllowed=commandline dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Main executable (PyInstaller one-file or one-folder output)
Source: "dist\HDProcessor.exe"; DestDir: "{app}"; Flags: ignoreversion
; NOTE: service_account.json is NOT bundled. Klear Concepts provides it separately.
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName,'&','&&')}}"; \
  Flags: nowait postinstall skipifsilent

[Code]
procedure InitializeWizard();
begin
  WizardForm.WelcomeLabel2.Caption :=
    'This will install HD Adjustment Processor on your computer.'#13#10#13#10 +
    'After installation, launch the app and open Settings. For Google Sheets, paste the Sheet ID ' +
    'and browse to the Klear-provided service_account.json file. For Excel, choose an .xlsx file path.';
end;
