#define MyAppName "Exiles Game Manager"
#define MyAppVersion "0.8.1-beta.8"
#define MyWindowsVersion "0.8.1.8"
#define MyAppPublisher "Whisibear"
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
VersionInfoCopyright=Copyright © 2026 Whisibear
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
UsedUserAreasWarning=no
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
#ifdef EGM_SIGNED_BUILD
SignTool=egmsign
SignedUninstaller=yes
#endif

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
english.TrayInfo=Exiles Game Manager keeps running in the Windows notification area. Use the tray icon and choose Quit to close EGM cleanly. Running dedicated game servers are not stopped.
german.TrayInfo=Exiles Game Manager läuft im Windows-Infobereich weiter. Verwenden Sie das Tray-Symbol und wählen Sie Beenden, um EGM sauber zu schließen. Laufende Dedicated-Server werden dabei nicht gestoppt.
english.RemoveUserData=Remove all EGM application data stored under LocalAppData, including configuration, OAuth tokens, cache, logs and downloads?%n%nChoose No to preserve these settings for a later reinstall.
german.RemoveUserData=Alle EGM-Anwendungsdaten unter LocalAppData löschen, einschließlich Konfiguration, OAuth-Tokens, Cache, Logs und Downloads?%n%nWählen Sie Nein, um diese Einstellungen für eine spätere Neuinstallation zu behalten.
english.RemoveRuntimeData=Remove EGM machine-wide runtime data stored under ProgramData, including server registrations, downloaded tools, logs and only server files that are physically stored inside the EGM ProgramData tree?%n%nExternal Palworld/Conan server folders are never deleted by this option. Choose No to preserve all ProgramData runtime state. Login accounts are removed in either case.
german.RemoveRuntimeData=Maschinenweite EGM-Laufzeitdaten unter ProgramData löschen, einschließlich Serverregistrierungen, heruntergeladenen Werkzeugen, Logs und nur solchen Serverdateien, die tatsächlich innerhalb des EGM-ProgramData-Verzeichnisses liegen?%n%nExterne Palworld-/Conan-Serverordner werden durch diese Option niemals gelöscht. Wählen Sie Nein, um alle ProgramData-Laufzeitdaten zu behalten. Benutzerkonten werden in jedem Fall entfernt.
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
Source: "dist\ExilesGameManager\*"; DestDir: "{app}"; Excludes: "EGMUpdateWorker.exe"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "dist\ExilesGameManager\EGMUpdateWorker.exe"; DestDir: "{app}"; Flags: ignoreversion; Check: ShouldInstallUpdateWorker
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

function ShouldInstallUpdateWorker(): Boolean;
begin
  Result := not HasCommandLineSwitch('UPDATE');
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

procedure StopEGMProcesses(); forward;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  RemoveUserData: Integer;
  RemoveEverything: Integer;
begin
  if CurUninstallStep = usUninstall then
  begin
    StopEGMProcesses();

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
  GracefulCommand: String;
  FallbackCommand: String;
begin
  PowerShellExe := ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe');

  { E.11: request a graceful application shutdown first. This allows Uvicorn
    shutdown hooks to finish and deliberately leaves managed game servers running. }
  GracefulCommand :=
    '-NoProfile -NonInteractive -ExecutionPolicy Bypass -Command "' +
    '$ErrorActionPreference = ''SilentlyContinue''; ' +
    'try { ' +
    '$event = [System.Threading.EventWaitHandle]::OpenExisting(''Local\ExilesGameManager.Quit''); ' +
    '$null = $event.Set(); $event.Dispose(); ' +
    '} catch {}; ' +
    '$deadline = (Get-Date).AddSeconds(15); ' +
    'do { ' +
    '$running = Get-Process -Name ''ExilesGameManager'' -ErrorAction SilentlyContinue; ' +
    'if (-not $running) { exit 0 }; Start-Sleep -Milliseconds 250 ' +
    '} while ((Get-Date) -lt $deadline); exit 1"';

  Log('Stopping EGM and EGM-owned backend processes before file replacement.');
  Log('Requesting graceful EGM shutdown through the E.11 tray quit event.');
  if Exec(
    PowerShellExe,
    GracefulCommand,
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  ) and (ResultCode = 0) then
  begin
    Log('EGM stopped gracefully.');
    Exit;
  end;

  { Last resort: stop only EGM application/backend processes. Palworld and
    Conan dedicated-server executables are never selected by this fallback. }
  FallbackCommand :=
    '-NoProfile -NonInteractive -ExecutionPolicy Bypass -Command "' +
    '$ErrorActionPreference = ''SilentlyContinue''; ' +
    '$installDir = [IO.Path]::GetFullPath(''' + ExpandConstant('{app}') + ''').TrimEnd(''\''); ' +
    '$targets = Get-CimInstance Win32_Process | Where-Object { ' +
    '($_.Name -ieq ''ExilesGameManager.exe'') -or ' +
    '(($_.Name -in @(''python.exe'',''pythonw.exe'',''uvicorn.exe'')) -and ' +
    '(($_.ExecutablePath -and $_.ExecutablePath.StartsWith($installDir,[StringComparison]::OrdinalIgnoreCase)) -or ' +
    '($_.CommandLine -and $_.CommandLine.IndexOf($installDir,[StringComparison]::OrdinalIgnoreCase) -ge 0))) }; ' +
    '$targets | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }; ' +
    'Start-Sleep -Seconds 2; exit 0"';

  Log('Graceful EGM shutdown timed out; using EGM-only fallback termination.');
  Exec(
    PowerShellExe,
    FallbackCommand,
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
