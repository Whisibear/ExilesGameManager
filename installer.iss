#define MyAppName "Exiles Game Manager"
#define MyAppVersion "0.8.1-beta.6"
#define MyWindowsVersion "0.8.1.6"
#define MyAppPublisher "Whisibear EGM"
#define MyAppURL "https://github.com/Whisibear/ExilesGameManager"
#define MyAppExeName "ExilesGameManager.exe"

[Setup]
AppId={{C9B75D37-C6F7-4487-A49C-FBE76815AF7F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
VersionInfoVersion={#MyWindowsVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} Setup
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyWindowsVersion}
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
CloseApplications=no
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
english.RemoveUserData=Remove all EGM application data stored under LocalAppData, including configuration, OAuth tokens, cache, logs and downloads?%n%nChoose No to preserve these settings for a later reinstall.
german.RemoveUserData=Alle EGM-Anwendungsdaten unter LocalAppData löschen, einschließlich Konfiguration, OAuth-Tokens, Cache, Logs und Downloads?%n%nWählen Sie Nein, um diese Einstellungen für eine spätere Neuinstallation zu behalten.
english.RemoveRuntimeData=Remove all EGM runtime data, server registrations, downloaded tools, logs and server files stored under ProgramData?%n%nChoose No to preserve servers and runtime data. Login accounts are removed in either case.
german.RemoveRuntimeData=Alle EGM-Laufzeitdaten, Serverregistrierungen, heruntergeladenen Werkzeuge, Logs und unter ProgramData gespeicherten Serverdateien löschen?%n%nWählen Sie Nein, um Server und Laufzeitdaten zu behalten. Benutzerkonten werden in jedem Fall entfernt.
english.MaintenanceTitle=Maintain Exiles Game Manager
german.MaintenanceTitle=Exiles Game Manager verwalten
english.MaintenanceDescription=An existing installation was detected. Choose the action to perform.
german.MaintenanceDescription=Eine vorhandene Installation wurde erkannt. Wählen Sie die gewünschte Aktion.
english.MaintenanceUpdate=Update EGM to version {#MyAppVersion} and preserve all settings, OAuth data, servers and backups.
german.MaintenanceUpdate=EGM auf Version {#MyAppVersion} aktualisieren und alle Einstellungen, OAuth-Daten, Server und Backups behalten.
english.MaintenanceRepair=Repair the existing installation by reinstalling all program files. User and server data remain unchanged.
german.MaintenanceRepair=Die vorhandene Installation reparieren, indem alle Programmdateien neu installiert werden. Benutzer- und Serverdaten bleiben unverändert.
english.MaintenanceUninstall=Uninstall Exiles Game Manager. The uninstaller will ask separately whether application and server data should also be removed.
german.MaintenanceUninstall=Exiles Game Manager deinstallieren. Der Uninstaller fragt getrennt, ob Anwendungs- und Serverdaten ebenfalls entfernt werden sollen.
english.MaintenanceInstalledVersion=Installed version
german.MaintenanceInstalledVersion=Installierte Version
english.MaintenanceNewVersion=Setup version
german.MaintenanceNewVersion=Setup-Version
english.MaintenanceUninstallFailed=The existing uninstaller could not be started.
german.MaintenanceUninstallFailed=Das vorhandene Deinstallationsprogramm konnte nicht gestartet werden.
english.MaintenanceUninstallMissing=The existing installation was detected, but its uninstaller could not be found.
german.MaintenanceUninstallMissing=Die vorhandene Installation wurde erkannt, aber das Deinstallationsprogramm wurde nicht gefunden.

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Dirs]
Name: "{localappdata}\ExilesGameManager"; Permissions: users-modify
Name: "{localappdata}\ExilesGameManager\config"; Permissions: users-modify
Name: "{localappdata}\ExilesGameManager\cache"; Permissions: users-modify
Name: "{localappdata}\ExilesGameManager\logs"; Permissions: users-modify
Name: "{localappdata}\ExilesGameManager\oauth"; Permissions: users-modify
Name: "{localappdata}\ExilesGameManager\downloads"; Permissions: users-modify
Name: "{localappdata}\ExilesGameManager\temp"; Permissions: users-modify
Name: "{localappdata}\ExilesGameManager\backups"; Permissions: users-modify
Name: "{commonappdata}\ExilesGameManager"; Permissions: users-modify
Name: "{commonappdata}\ExilesGameManager\data"; Permissions: users-modify
Name: "{commonappdata}\ExilesGameManager\Servers"; Permissions: users-modify
Name: "{commonappdata}\ExilesGameManager\data\steamcmd"; Permissions: users-modify

[Files]
Source: "dist\ExilesGameManager.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\EGMUpdateWorker.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "ExilesGameManager.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "Install_Prerequisites.ps1"; DestDir: "{tmp}"; Flags: deleteafterinstall
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "THIRD_PARTY_NOTICES.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-NoLogo -NoProfile -ExecutionPolicy Bypass -File ""{tmp}\Install_Prerequisites.ps1"" -DataRoot ""{commonappdata}\ExilesGameManager\data"" -LogRoot ""{localappdata}\ExilesGameManager\logs\installer"""; StatusMsg: "{cm:InstallingRuntime}"; Flags: runhidden waituntilterminated
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram}"; Flags: nowait postinstall skipifsilent

[Code]
const
  EGMUninstallKey = 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{C9B75D37-C6F7-4487-A49C-FBE76815AF7F}_is1';

var
  MaintenancePage: TInputOptionWizardPage;
  EGMRestartExecutable: String;
  EGMRestartLaunched: Boolean;
  ExistingInstallDetected: Boolean;
  ExistingVersion: String;
  ExistingUninstaller: String;

function GetCommandLineValue(const Name: String): String;
var
  I: Integer;
  Prefix: String;
  Value: String;
begin
  Result := '';
  Prefix := '/' + Uppercase(Name) + '=';
  for I := 1 to ParamCount do
  begin
    Value := ParamStr(I);
    if Pos(Prefix, Uppercase(Value)) = 1 then
    begin
      Result := Copy(Value, Length(Prefix) + 1, MaxInt);
      Exit;
    end;
  end;
end;

function HasCommandLineSwitch(const SwitchName: String): Boolean;
var
  I: Integer;
  Value: String;
begin
  Result := False;
  for I := 1 to ParamCount do
  begin
    Value := Uppercase(ParamStr(I));
    if (Value = '/' + Uppercase(SwitchName)) or
       (Value = '-' + Uppercase(SwitchName)) then
    begin
      Result := True;
      Exit;
    end;
  end;
end;

function ReadExistingInstallation(): Boolean;
begin
  ExistingVersion := '';
  ExistingUninstaller := '';

  Result :=
    RegQueryStringValue(HKLM64, EGMUninstallKey, 'DisplayVersion', ExistingVersion) or
    RegQueryStringValue(HKLM, EGMUninstallKey, 'DisplayVersion', ExistingVersion);

  if Result then
  begin
    if not RegQueryStringValue(HKLM64, EGMUninstallKey, 'UninstallString', ExistingUninstaller) then
      RegQueryStringValue(HKLM, EGMUninstallKey, 'UninstallString', ExistingUninstaller);
  end;
end;

procedure InitializeWizard();
var
  VersionSummary: String;
begin
  EGMRestartExecutable := GetCommandLineValue('EGMRESTART');
  EGMRestartLaunched := False;
  ExistingInstallDetected := ReadExistingInstallation();

  if ExistingInstallDetected and
     (not WizardSilent()) and
     (not HasCommandLineSwitch('UPDATE')) and
     (not HasCommandLineSwitch('REPAIR')) then
  begin
    VersionSummary :=
      ExpandConstant('{cm:MaintenanceInstalledVersion}') + ': ' + ExistingVersion + #13#10 +
      ExpandConstant('{cm:MaintenanceNewVersion}') + ': {#MyAppVersion}';

    MaintenancePage := CreateInputOptionPage(
      wpWelcome,
      ExpandConstant('{cm:MaintenanceTitle}'),
      ExpandConstant('{cm:MaintenanceDescription}'),
      VersionSummary,
      True,
      False
    );
    MaintenancePage.Add(ExpandConstant('{cm:MaintenanceUpdate}'));
    MaintenancePage.Add(ExpandConstant('{cm:MaintenanceRepair}'));
    MaintenancePage.Add(ExpandConstant('{cm:MaintenanceUninstall}'));
    MaintenancePage.SelectedValueIndex := 0;
  end;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  ResultCode: Integer;
  UninstallerPath: String;
begin
  Result := True;

  if ExistingInstallDetected and
     Assigned(MaintenancePage) and
     (CurPageID = MaintenancePage.ID) and
     (MaintenancePage.SelectedValueIndex = 2) then
  begin
    UninstallerPath := RemoveQuotes(ExistingUninstaller);

    if (UninstallerPath = '') or (not FileExists(UninstallerPath)) then
    begin
      MsgBox(ExpandConstant('{cm:MaintenanceUninstallMissing}'), mbError, MB_OK);
      Result := False;
      Exit;
    end;

    if not Exec(
      UninstallerPath,
      '',
      ExtractFileDir(UninstallerPath),
      SW_SHOW,
      ewNoWait,
      ResultCode
    ) then
    begin
      MsgBox(ExpandConstant('{cm:MaintenanceUninstallFailed}'), mbError, MB_OK);
      Result := False;
      Exit;
    end;

    WizardForm.Close;
    Result := False;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  RemoveUserData: Integer;
  RemoveEverything: Integer;
begin
  if CurUninstallStep = usUninstall then
  begin
    RemoveUserData := MsgBox(
      ExpandConstant('{cm:RemoveUserData}'),
      mbConfirmation,
      MB_YESNO or MB_DEFBUTTON2
    );
    if RemoveUserData = IDYES then
      DelTree(ExpandConstant('{localappdata}\ExilesGameManager'), True, True, True);

    RemoveEverything := MsgBox(
      ExpandConstant('{cm:RemoveRuntimeData}'),
      mbConfirmation,
      MB_YESNO or MB_DEFBUTTON2
    );
    if RemoveEverything = IDYES then
      DelTree(ExpandConstant('{commonappdata}\ExilesGameManager'), True, True, True);
  end;
end;

procedure StopEGMProcesses();
var
  ResultCode: Integer;
  PowerShellExe: String;
  CommandLine: String;
begin
  PowerShellExe := ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe');
  CommandLine :=
    '-NoProfile -NonInteractive -ExecutionPolicy Bypass -Command "' +
    '$ErrorActionPreference = ''SilentlyContinue''; ' +
    '$installDir = [IO.Path]::GetFullPath(''' + ExpandConstant('{app}') + ''').TrimEnd(''\''); ' +
    '$targets = Get-CimInstance Win32_Process | Where-Object { ' +
    '($_.Name -ieq ''ExilesGameManager.exe'') -or ' +
    '(($_.Name -in @(''python.exe'',''pythonw.exe'',''uvicorn.exe'')) -and ' +
    '(($_.ExecutablePath -and $_.ExecutablePath.StartsWith($installDir,[StringComparison]::OrdinalIgnoreCase)) -or ' +
    '($_.CommandLine -and $_.CommandLine.IndexOf($installDir,[StringComparison]::OrdinalIgnoreCase) -ge 0))) }; ' +
    '$targets | ForEach-Object { Stop-Process -Id $_.ProcessId -ErrorAction SilentlyContinue }; ' +
    'Start-Sleep -Seconds 3; ' +
    '$targets = Get-CimInstance Win32_Process | Where-Object { ' +
    '($_.Name -ieq ''ExilesGameManager.exe'') -or ' +
    '(($_.Name -in @(''python.exe'',''pythonw.exe'',''uvicorn.exe'')) -and ' +
    '(($_.ExecutablePath -and $_.ExecutablePath.StartsWith($installDir,[StringComparison]::OrdinalIgnoreCase)) -or ' +
    '($_.CommandLine -and $_.CommandLine.IndexOf($installDir,[StringComparison]::OrdinalIgnoreCase) -ge 0))) }; ' +
    '$targets | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }; ' +
    'Start-Sleep -Seconds 2; exit 0"';

  Log('Stopping EGM and EGM-owned backend processes before file replacement.');
  if not Exec(
    PowerShellExe,
    CommandLine,
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  ) then
    Log('EGM shutdown helper could not be started.')
  else
    Log(Format('EGM shutdown helper returned exit code %d.', [ResultCode]));

  { Last-resort fallback for the main launcher only. }
  Exec(
    ExpandConstant('{sys}\taskkill.exe'),
    '/F /T /IM ExilesGameManager.exe',
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  );
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  LogFile: String;
  OperationName: String;
  ResultCode: Integer;
begin
  if CurStep = ssInstall then
  begin
    WizardForm.StatusLabel.Caption := ExpandConstant('{cm:PreparingComponents}');
    if ExistingInstallDetected or
       HasCommandLineSwitch('UPDATE') or
       HasCommandLineSwitch('REPAIR') then
      StopEGMProcesses();
  end;

  if CurStep = ssPostInstall then
  begin
    if HasCommandLineSwitch('REPAIR') then
      OperationName := 'repair'
    else if ExistingInstallDetected or HasCommandLineSwitch('UPDATE') then
      OperationName := 'update'
    else
      OperationName := 'installation';

    LogFile := ExpandConstant('{localappdata}\ExilesGameManager\logs\installer\installation.log');
    ForceDirectories(ExtractFileDir(LogFile));
    SaveStringToFile(
      LogFile,
      GetDateTimeString('yyyy-mm-dd hh:nn:ss', '-', ':') +
      ' Exiles Game Manager ' + '{#MyAppVersion}' + ' ' + OperationName + ' completed.' + #13#10,
      True
    );

    { Interactive setup launches only from the checked Finish-page [Run] entry.
      Silent panel updates are restarted by the detached updater. }
  end;
end;
