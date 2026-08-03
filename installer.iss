#define MyAppName "Exiles Game Manager"
#define MyAppVersion "0.8.0"
#define MyAppPublisher "Whisibear EGM"
#define MyAppURL "https://github.com/Whisibear/ExilesGameManager"
#define MyAppExeName "ExilesGameManager.exe"

[Setup]
AppId={{C9B75D37-C6F7-4487-A49C-FBE76815AF7F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion} Beta
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
VersionInfoVersion={#MyAppVersion}.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} Setup
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion=0.8.0.0
VersionInfoCopyright=Copyright (c) 2026 Kvitekvist; Copyright (c) 2026 Whisibear EGM
DefaultDirName={autopf}\Exiles Game Manager
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=installer_output
OutputBaseFilename=ExilesGameManager-Setup-v{#MyAppVersion}
SetupIconFile=ExilesGameManager.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
CloseApplications=yes
RestartApplications=no
RestartIfNeededByRun=no
AlwaysRestart=no
MinVersion=10.0
ChangesEnvironment=no
UsePreviousAppDir=yes
UsePreviousTasks=yes
SetupLogging=yes
Uninstallable=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[CustomMessages]
english.PreparingComponents=Preparing required components...
german.PreparingComponents=Benötigte Komponenten werden vorbereitet...
english.InstallingRuntime=Installing Microsoft Visual C++ Runtime and SteamCMD...
german.InstallingRuntime=Microsoft Visual C++ Runtime und SteamCMD werden installiert...
english.LaunchProgram=Launch Exiles Game Manager
german.LaunchProgram=Exiles Game Manager starten
english.RemoveRuntimeData=Remove all EGM runtime data, server registrations, downloaded tools, logs and server files stored under ProgramData?%n%nChoose No to preserve servers and runtime data. Login accounts are removed in either case.
german.RemoveRuntimeData=Alle EGM-Laufzeitdaten, Serverregistrierungen, heruntergeladenen Werkzeuge, Logs und unter ProgramData gespeicherten Serverdateien löschen?%n%nWählen Sie Nein, um Server und Laufzeitdaten zu behalten. Benutzerkonten werden in jedem Fall entfernt.

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Dirs]
Name: "{commonappdata}\ExilesGameManager"; Permissions: users-modify
Name: "{commonappdata}\ExilesGameManager\data"; Permissions: users-modify
Name: "{commonappdata}\ExilesGameManager\Servers"; Permissions: users-modify
Name: "{commonappdata}\ExilesGameManager\data\steamcmd"; Permissions: users-modify
Name: "{app}\Logs"; Permissions: users-modify
Name: "{app}\Logs\backend"; Permissions: users-modify
Name: "{app}\Logs\frontend"; Permissions: users-modify
Name: "{app}\Logs\audit"; Permissions: users-modify
Name: "{app}\Logs\application"; Permissions: users-modify
Name: "{app}\Logs\activity"; Permissions: users-modify
Name: "{app}\Logs\taskqueue"; Permissions: users-modify
Name: "{app}\Logs\installer"; Permissions: users-modify
Name: "{app}\Logs\updater"; Permissions: users-modify
Name: "{app}\Logs\steamcmd"; Permissions: users-modify
Name: "{app}\Logs\diagnostics"; Permissions: users-modify

[Files]
Source: "dist\ExilesGameManager.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "ExilesGameManager.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "Install_Prerequisites.ps1"; DestDir: "{tmp}"; Flags: deleteafterinstall
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "THIRD_PARTY_NOTICES.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-NoLogo -NoProfile -ExecutionPolicy Bypass -File ""{tmp}\Install_Prerequisites.ps1"" -DataRoot ""{commonappdata}\ExilesGameManager\data"" -LogRoot ""{app}\Logs\installer"""; StatusMsg: "{cm:InstallingRuntime}"; Flags: runhidden waituntilterminated
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram}"; Flags: nowait postinstall skipifsilent

[Code]
procedure RemoveAuthenticationData();
var
  DataRoot: String;
begin
  DataRoot := ExpandConstant('{commonappdata}\ExilesGameManager\data');
  DeleteFile(DataRoot + '\users.json');
  DeleteFile(DataRoot + '\users.json.corrupt');
  DeleteFile(DataRoot + '\invites.json');
  DeleteFile(DataRoot + '\invites.json.corrupt');
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  RemoveEverything: Integer;
begin
  if CurUninstallStep = usUninstall then
  begin
    RemoveAuthenticationData();
    RemoveEverything := MsgBox(
      ExpandConstant('{cm:RemoveRuntimeData}'),
      mbConfirmation,
      MB_YESNO or MB_DEFBUTTON2
    );
    if RemoveEverything = IDYES then
      DelTree(ExpandConstant('{commonappdata}\ExilesGameManager'), True, True, True);
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  LogFile: String;
begin
  if CurStep = ssInstall then
    WizardForm.StatusLabel.Caption := ExpandConstant('{cm:PreparingComponents}');

  if CurStep = ssPostInstall then
  begin
    LogFile := ExpandConstant('{app}\Logs\installer\installation.log');
    SaveStringToFile(
      LogFile,
      GetDateTimeString('yyyy-mm-dd hh:nn:ss', '-', ':') +
      ' Exiles Game Manager ' + '{#MyAppVersion}' + ' installation completed.' + #13#10,
      True
    );
  end;
end;
