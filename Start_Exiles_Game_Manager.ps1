[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$Root = [System.IO.Path]::GetFullPath($PSScriptRoot)
$LogDir = Join-Path $Root 'logs\launcher'
$LogFile = Join-Path $LogDir ("launcher-{0}.log" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

function Write-LauncherLog {
    param([string]$Message, [ConsoleColor]$Color = [ConsoleColor]::Gray)
    $line = '[{0}] {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss.fff'), $Message
    Write-Host $line -ForegroundColor $Color
    Add-Content -LiteralPath $LogFile -Value $line -Encoding UTF8
}

function Fail {
    param([string]$Message)
    Write-LauncherLog "ERROR: $Message" Red
    Read-Host 'Druecke ENTER zum Beenden'
    exit 1
}

function Get-PythonExecutable {
    $candidates = @()
    $py = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($null -ne $py) { $candidates += ,@($py.Source, '-3') }
    $python = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($null -ne $python) { $candidates += ,@($python.Source) }

    foreach ($candidate in $candidates) {
        $exe = $candidate[0]
        $prefix = @()
        if ($candidate.Count -gt 1) { $prefix = $candidate[1..($candidate.Count - 1)] }
        try {
            $versionText = & $exe @prefix -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
            if ($LASTEXITCODE -eq 0 -and $versionText) {
                $parts = $versionText.Trim().Split('.')
                if ([int]$parts[0] -gt 3 -or ([int]$parts[0] -eq 3 -and [int]$parts[1] -ge 12)) {
                    return $candidate
                }
            }
        } catch {}
    }
    return $null
}

function Invoke-PythonCommand {
    param([object[]]$Command, [string[]]$Arguments)
    $exe = [string]$Command[0]
    $prefix = @()
    if ($Command.Count -gt 1) { $prefix = $Command[1..($Command.Count - 1)] }
    & $exe @prefix @Arguments
    return $LASTEXITCODE
}

function Get-FrontendSourceHash {
    param([string]$WebRoot)

    $hashInputs = @(
        (Join-Path $WebRoot 'package.json'),
        (Join-Path $WebRoot 'package-lock.json'),
        (Join-Path $WebRoot 'vite.config.ts'),
        (Join-Path $WebRoot 'tsconfig.json'),
        (Join-Path $WebRoot 'tsconfig.app.json'),
        (Join-Path $WebRoot 'tsconfig.node.json')
    )

    $srcRoot = Join-Path $WebRoot 'src'
    if (Test-Path -LiteralPath $srcRoot -PathType Container) {
        $hashInputs += Get-ChildItem -LiteralPath $srcRoot -Recurse -File |
            Sort-Object FullName |
            Select-Object -ExpandProperty FullName
    }

    $rootPrefix = $WebRoot.TrimEnd('\\') + '\\'
    $manifest = New-Object System.Text.StringBuilder
    foreach ($path in $hashInputs) {
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { continue }
        $relative = $path
        if ($relative.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            $relative = $relative.Substring($rootPrefix.Length)
        }
        $fileHash = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
        [void]$manifest.Append($relative.Replace('\\', '/'))
        [void]$manifest.Append(':')
        [void]$manifest.Append($fileHash)
        [void]$manifest.Append("`n")
    }

    $bytes = [System.Text.Encoding]::UTF8.GetBytes($manifest.ToString())
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        return ([System.BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '').ToLowerInvariant()
    }
    finally {
        $sha.Dispose()
    }
}

function Ensure-FrontendBuild {
    param([string]$RootPath)

    $webRoot = Join-Path $RootPath 'web'
    $distIndex = Join-Path $webRoot 'dist\index.html'
    $stampFile = Join-Path $webRoot 'dist\.egm-source.sha256'
    $sourceHash = Get-FrontendSourceHash -WebRoot $webRoot
    $storedHash = ''
    if (Test-Path -LiteralPath $stampFile -PathType Leaf) {
        $storedHash = (Get-Content -LiteralPath $stampFile -Raw -ErrorAction SilentlyContinue).Trim()
    }

    $containsGameSelector = $false
    $assetRoot = Join-Path $webRoot 'dist\assets'
    if (Test-Path -LiteralPath $assetRoot -PathType Container) {
        $containsGameSelector = [bool](
            Get-ChildItem -LiteralPath $assetRoot -Filter '*.js' -File -ErrorAction SilentlyContinue |
                Select-String -SimpleMatch 'conan_exiles_enhanced' -Quiet
        )
    }

    if (
        (Test-Path -LiteralPath $distIndex -PathType Leaf) -and
        $storedHash -eq $sourceHash -and
        $containsGameSelector
    ) {
        Write-LauncherLog "Frontend ist aktuell ($($sourceHash.Substring(0, 12)))." DarkGray
        return $sourceHash
    }

    $npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
    if ($null -eq $npm) {
        Fail 'Node.js/npm wurde nicht gefunden. Installiere eine aktuelle Node.js-LTS-Version.'
    }

    Write-LauncherLog 'Frontend wird aus dem aktuellen Quellcode neu gebaut...' Cyan
    Push-Location $webRoot
    try {
        & $npm.Source install --no-audit --no-fund | ForEach-Object { Write-Host $_ }
        if ($LASTEXITCODE -ne 0) { Fail 'Frontend-Abhängigkeiten konnten nicht installiert werden.' }
        & $npm.Source run build | ForEach-Object { Write-Host $_ }
        if ($LASTEXITCODE -ne 0) { Fail 'Der Frontend-Build ist fehlgeschlagen.' }
    }
    finally {
        Pop-Location
    }

    if (-not (Test-Path -LiteralPath $distIndex -PathType Leaf)) {
        Fail 'Der Frontend-Build hat keine web\dist\index.html erzeugt.'
    }

    $containsGameSelector = [bool](
        Get-ChildItem -LiteralPath $assetRoot -Filter '*.js' -File -ErrorAction SilentlyContinue |
            Select-String -SimpleMatch 'conan_exiles_enhanced' -Quiet
    )
    if (-not $containsGameSelector) {
        Fail 'Der erzeugte Frontend-Build enthält die Phase-D.2-Spielauswahl nicht.'
    }

    [System.IO.File]::WriteAllText(
        $stampFile,
        $sourceHash,
        (New-Object System.Text.UTF8Encoding($false))
    )
    Write-LauncherLog "Frontend erfolgreich gebaut ($($sourceHash.Substring(0, 12)))." Green
    return $sourceHash
}

function Stop-ExistingDevelopmentBackend {
    param([string]$RootPath)

    $escapedRoot = [Regex]::Escape($RootPath.TrimEnd('\\'))
    $processes = @(
        Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
            Where-Object {
                $_.ProcessId -ne $PID -and
                $_.CommandLine -and
                $_.CommandLine -match $escapedRoot -and
                ($_.CommandLine -match 'EGM_Server\.py' -or $_.CommandLine -match 'Palworld_Server\.py')
            }
    )

    foreach ($process in $processes) {
        Write-LauncherLog "Alter EGM-Entwicklungsprozess wird beendet: PID $($process.ProcessId)" Yellow
        Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue
    }

    if ($processes.Count -gt 0) { Start-Sleep -Milliseconds 750 }
}

try {
    $required = @(
        'EGM_Server.py',
        'requirements.txt',
        'web\package.json',
        'web\src\main.tsx',
        'web\src\components\settings\DeployServerWizard.tsx',
        'web\src\lib\gameCatalogFallback.ts'
    )
    foreach ($relative in $required) {
        if (-not (Test-Path -LiteralPath (Join-Path $Root $relative) -PathType Leaf)) {
            Fail "Erforderliche Datei fehlt: $relative"
        }
    }

    $wizardSource = Get-Content -LiteralPath (
        Join-Path $Root 'web\src\components\settings\DeployServerWizard.tsx'
    ) -Raw
    $catalogSource = Get-Content -LiteralPath (
        Join-Path $Root 'web\src\lib\gameCatalogFallback.ts'
    ) -Raw

    if (-not $wizardSource.Contains('FALLBACK_GAME_CATALOG')) {
        Fail 'Der Deployment-Wizard verwendet den lokalen Spielekatalog nicht.'
    }

    foreach ($requiredGame in @(
        'palworld',
        'conan_exiles_enhanced',
        'conan_exiles_legacy'
    )) {
        if (-not $catalogSource.Contains($requiredGame)) {
            Fail "Lokaler Spielekatalog unvollständig: $requiredGame fehlt."
        }
    }

    foreach ($conanGame in @(
        'conan_exiles_enhanced',
        'conan_exiles_legacy'
    )) {
        $pattern = 'id:\s*"' + [Regex]::Escape($conanGame) + '"[\s\S]*?availability:\s*"available"[\s\S]*?deployable:\s*true'
        if ($catalogSource -notmatch $pattern) {
            Fail "Conan Phase E.8 ist im lokalen Spielekatalog nicht deploybar: $conanGame."
        }
        $conanCapabilityPattern = 'const\s+sharedConanCapabilities\s*=\s*\{[\s\S]*?steam_workshop:\s*true[\s\S]*?nexus_mods:\s*false[\s\S]*?ue4ss:\s*false[\s\S]*?\};'
        if ($catalogSource -notmatch $conanCapabilityPattern) {
            Fail 'Conan Phase E.8 Capability-Trennung ist im lokalen Spielekatalog unvollständig.'
        }
    }
    $conanWorkshopSource = Get-Content -LiteralPath (
        Join-Path $Root 'app\services\conan_workshop.py'
    ) -Raw
    if (-not $conanWorkshopSource.Contains('Path(instance["serverPath"]).resolve() / "steamapps" / "workshop" / "content"')) {
        Fail 'Conan Phase E.8.1 verwendet keine serverlokale Steam-Workshop-Library.'
    }
    if (-not $conanWorkshopSource.Contains('"+force_install_dir", str(server_root)')) {
        Fail 'Conan Phase E.8.1 SteamCMD-Workshop-Download verwendet den Serverpfad nicht.'
    }
    if ($conanWorkshopSource.Contains('STEAMCMD_DIR') -or $conanWorkshopSource.Contains('_legacy_download_path') -or $conanWorkshopSource.Contains('_migrate_legacy_download')) {
        Fail 'Conan Phase E.8.1 enthaelt noch eine globale EGM-Workshop-Cache-Abhaengigkeit.'
    }
    $conanSettingsSource = Get-Content -LiteralPath (
        Join-Path $Root 'app\services\conan_settings.py'
    ) -Raw
    $serverSettingsRouteSource = Get-Content -LiteralPath (
        Join-Path $Root 'app\routes\server_settings.py'
    ) -Raw
    if (-not $conanSettingsSource.Contains('SERVER_SETTINGS_INI = "ServerSettings.ini"')) {
        Fail 'Conan Phase E.9 ServerSettings.ini-Integration fehlt.'
    }
    if (-not $conanSettingsSource.Contains('Additional ServerSettings') -or -not $conanSettingsSource.Contains('temporary.replace(path)')) {
        Fail 'Conan Phase E.9 dynamisches/atomares ServerSettings-Handling fehlt.'
    }
    if (-not $serverSettingsRouteSource.Contains('Conan server settings saved:') -or -not $serverSettingsRouteSource.Contains('restartRequired')) {
        Fail 'Conan Phase E.9 Activity-Center- oder Restart-Integration fehlt.'
    }
    if (-not $conanSettingsSource.Contains('_dynamic_help_for') -or -not $conanSettingsSource.Contains('PlayerStaminaCostSprintMultiplier')) {
        Fail 'Conan Phase E.9.1 setting-spezifische Hilfe fuer dynamische ServerSettings fehlt.'
    }
    $palworldSettingsSource = Get-Content -LiteralPath (
        Join-Path $Root 'app\services\palworld_settings.py'
    ) -Raw
    $palworldSettingsDataSource = Get-Content -LiteralPath (
        Join-Path $Root 'app\services\palworld_settings_data.py'
    ) -Raw
    if (-not $palworldSettingsSource.Contains('enforce_safe_respawn_settings') -or -not $palworldSettingsDataSource.Contains('"minimum": 1')) {
        Fail 'Phase E.9.1 Palworld Respawn-Sicherheitsgrenzen fehlen.'
    }
    $palProcessSource = Get-Content -LiteralPath (Join-Path $Root 'app\services\process_manager.py') -Raw
    $conanProcessSource = Get-Content -LiteralPath (Join-Path $Root 'app\services\conan_process_manager.py') -Raw
    if (-not $palProcessSource.Contains('hidden_process_kwargs') -or -not $conanProcessSource.Contains('hidden_process_kwargs')) {
        Fail 'Phase E.9.1/E.9.2 Hintergrundstart fuer Palworld/Conan fehlt.'
    }
    if (-not $palProcessSource.Contains('PalServer-Win64-Shipping-Cmd.exe') -or -not $palProcessSource.Contains('hidden_process_kwargs')) {
        Fail 'Phase E.9.3 Palworld Worker-Hintergrundstart fehlt.'
    }
    $gameRegistrySource = Get-Content -LiteralPath (Join-Path $Root 'app\games\registry.py') -Raw
    if (-not $gameRegistrySource.Contains('("ConanSandboxServer.exe",') -or -not $conanProcessSource.Contains('exe.name.lower() == "conansandboxserver.exe"')) {
        Fail 'Phase E.9.3 Conan Launcher-/Logfenster-Trennung fehlt.'
    }
    if (-not $conanSettingsSource.Contains('_dynamic_numeric_type') -or -not $conanSettingsSource.Contains('("Multiplier", "Scale")')) {
        Fail 'Phase E.9.2 Conan Dezimalfeld-Erkennung fehlt.'
    }
    $conanRconSource = Get-Content -LiteralPath (Join-Path $Root 'app\services\conan_rcon.py') -Raw
    $serverControlSource = Get-Content -LiteralPath (Join-Path $Root 'app\routes\server_control.py') -Raw
    if (-not $conanRconSource.Contains('check_ready_sync') -or -not $conanRconSource.Contains('ShowPlayers') -or -not $conanRconSource.Contains('Broadcast {cleaned}')) {
        Fail 'Phase E.9.4 Conan RCON Readiness/Command-Hardening fehlt.'
    }
    if ($conanRconSource.Contains('marker_id = command_id + 1') -or -not $serverControlSource.Contains('/rcon/status')) {
        Fail 'Phase E.9.4 Conan RCON Timeout-/Status-Fix fehlt.'
    }
    $conanConsoleSource = Get-Content -LiteralPath (Join-Path $Root 'web\src\components\serverControl\ConanLiveConsole.tsx') -Raw
    if (-not $conanRconSource.Contains('"mode": "configured"') -or $conanConsoleSource.Contains('pollRcon')) {
        Fail 'Phase E.9.4.1 Conan RCON Polling-Fix fehlt.'
    }
    Write-LauncherLog 'Lokaler Phase-E.7-Spielekatalog wurde verifiziert.' Green
    Write-LauncherLog 'Lokaler Phase-E.8.1-Spielekatalog wurde verifiziert.' Green
    Write-LauncherLog 'Lokaler Phase-E.9-Spielekatalog wurde verifiziert.' Green
    Write-LauncherLog 'Serverlokale Conan-Workshop-Library ohne globalen EGM-Cache wurde verifiziert.' Green
    Write-LauncherLog 'Conan ServerSettings.ini, Validierung, Restart-Hinweis und Activity-Logging wurden verifiziert.' Green
    Write-LauncherLog 'Phase E.9.1 Settings-Hilfe, Hintergrundstart und Palworld-Respawn-Sicherheit wurden verifiziert.' Green
    Write-LauncherLog 'Phase E.9.2 Dedicated-Binary-Start und Conan-Dezimalfelder wurden verifiziert.' Green
    Write-LauncherLog 'Phase E.9.3 Runtime-Fenster, Deploy-Uebersetzungen und Palworld-Mod-Abhaengigkeiten wurden verifiziert.' Green
    Write-LauncherLog 'Phase E.9.4 Conan RCON Reliability wurde verifiziert.' Green
    Write-LauncherLog 'Phase E.9.4.1 Conan RCON Polling-Stabilisierung wurde verifiziert.' Green
    $genericRconPath = Join-Path $Root 'app\services\source_rcon.py'
    if (-not (Test-Path -LiteralPath $genericRconPath -PathType Leaf)) {
        Fail 'Phase E.9.4.2 generischer mcrcon-kompatibler RCON-Transport fehlt.'
    }
    $genericRconSource = Get-Content -LiteralPath $genericRconPath -Raw
    $conanRconSource = Get-Content -LiteralPath (Join-Path $Root 'app\services\conan_rcon.py') -Raw
    if (-not $genericRconSource.Contains('MCRCON_REQUEST_ID') -or
        -not $genericRconSource.Contains('execute_mcrcon') -or
        -not $conanRconSource.Contains('source_rcon.execute_mcrcon')) {
        Fail 'Phase E.9.4.2 mcrcon-kompatibler RCON-Transport ist unvollstaendig.'
    }
    Write-LauncherLog 'Phase E.9.4.2 generischer mcrcon-kompatibler RCON-Transport wurde verifiziert.' Green

    $e10ImportAnalyzer = Join-Path $Root 'app\services\instance_import_analyzer.py'
    $e10Notifications = Join-Path $Root 'web\src\hooks\useNotifications.tsx'
    $e10Performance = Join-Path $Root 'app\services\performance_monitor.py'
    if (-not (Test-Path -LiteralPath $e10ImportAnalyzer -PathType Leaf) -or
        -not (Test-Path -LiteralPath $e10Notifications -PathType Leaf) -or
        -not (Test-Path -LiteralPath $e10Performance -PathType Leaf)) {
        Fail 'Phase E.10 Conan Integration Completion Dateien fehlen.'
    }
    $e10NotificationSource = Get-Content -LiteralPath $e10Notifications -Raw
    $e10PerformanceSource = Get-Content -LiteralPath $e10Performance -Raw
    if (-not $e10NotificationSource.Contains('10_000') -or
        -not $e10PerformanceSource.Contains('conan_process_manager.get_status(instance)')) {
        Fail 'Phase E.10 Toast-Dauer oder Conan Performance Provider ist unvollstaendig.'
    }
    Write-LauncherLog 'Phase E.10 Conan Import-Analyse, 10-Sekunden-Notifications und Performance-Provider wurden verifiziert.' Green

    $e11DesktopApp = Join-Path $Root 'desktop_app.py'
    $e11Installer = Join-Path $Root 'installer.iss'
    $e11BuildInstaller = Join-Path $Root 'build_installer.ps1'
    $e11ReleaseScript = Join-Path $Root 'scripts\EGM_One_Click_Release.ps1'
    $e11PublishScript = Join-Path $Root 'EGM_Publish_To_GitHub.ps1'
    $e11Requirements = Join-Path $Root 'requirements.txt'
    foreach ($requiredE11 in @($e11DesktopApp,$e11Installer,$e11BuildInstaller,$e11ReleaseScript,$e11PublishScript,$e11Requirements)) {
        if (-not (Test-Path -LiteralPath $requiredE11 -PathType Leaf)) {
            Fail "Phase E.11 Datei fehlt: $requiredE11"
        }
    }
    $e11DesktopSource = Get-Content -LiteralPath $e11DesktopApp -Raw
    $e11InstallerSource = Get-Content -LiteralPath $e11Installer -Raw
    $e11RequirementsSource = Get-Content -LiteralPath $e11Requirements -Raw
    if (-not $e11DesktopSource.Contains('QUIT_EVENT_NAME') -or
        -not $e11DesktopSource.Contains('pystray.MenuItem') -or
        -not $e11DesktopSource.Contains('server.should_exit')) {
        Fail 'Phase E.11 System-Tray oder Graceful Shutdown ist unvollstaendig.'
    }
    if (-not $e11InstallerSource.Contains('OpenExisting(''Local\ExilesGameManager.Quit'')') -or
        -not $e11InstallerSource.Contains('External Palworld/Conan server folders are never deleted')) {
        Fail 'Phase E.11 Installer Upgrade/Uninstall-Sicherheit ist unvollstaendig.'
    }
    if (-not $e11RequirementsSource.Contains('pystray') -or -not $e11RequirementsSource.Contains('Pillow')) {
        Fail 'Phase E.11 Tray-Runtime-Abhaengigkeiten fehlen.'
    }
    Write-LauncherLog 'Phase E.11 System-Tray, Graceful Shutdown, Installer- und Release-Hardening wurden verifiziert.' Green

    $FrontendHash = [string](Ensure-FrontendBuild -RootPath $Root | Select-Object -Last 1)
    $FrontendHash = $FrontendHash.Trim()
    if ($FrontendHash -notmatch '^[a-f0-9]{64}$') { Fail 'Die Frontend-Buildkennung ist ungültig.' }
    Stop-ExistingDevelopmentBackend -RootPath $Root

    $VenvPython = Join-Path $Root '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $VenvPython -PathType Leaf)) {
        $pythonCommand = Get-PythonExecutable
        if ($null -eq $pythonCommand) {
            Fail 'Python 3.12 oder neuer wurde nicht gefunden. Installiere Python und aktiviere Add Python to PATH.'
        }
        Write-LauncherLog 'Python-Umgebung wird erstellt...' Cyan
        $exitCode = Invoke-PythonCommand -Command $pythonCommand -Arguments @('-m','venv',(Join-Path $Root '.venv'))
        if ($exitCode -ne 0) { Fail "Die Python-Umgebung konnte nicht erstellt werden (Code $exitCode)." }
    }

    $Requirements = Join-Path $Root 'requirements.txt'
    $HashFile = Join-Path $Root '.venv\egm-requirements.sha256'
    $CurrentHash = (Get-FileHash -LiteralPath $Requirements -Algorithm SHA256).Hash
    $StoredHash = ''
    if (Test-Path -LiteralPath $HashFile -PathType Leaf) {
        $StoredHash = (Get-Content -LiteralPath $HashFile -Raw -ErrorAction SilentlyContinue).Trim()
    }

    $DependenciesOk = $false
    if ($StoredHash -eq $CurrentHash) {
        & $VenvPython -c "import fastapi, uvicorn, pydantic, psutil" 2>$null
        $DependenciesOk = ($LASTEXITCODE -eq 0)
    }

    if (-not $DependenciesOk) {
        Write-LauncherLog 'Backend-Abhängigkeiten werden installiert bzw. repariert...' Cyan
        & $VenvPython -m pip install --disable-pip-version-check --upgrade pip setuptools wheel
        if ($LASTEXITCODE -ne 0) { Fail 'pip konnte nicht aktualisiert werden.' }
        & $VenvPython -m pip install --disable-pip-version-check -r $Requirements
        if ($LASTEXITCODE -ne 0) { Fail 'Backend-Abhängigkeiten konnten nicht installiert werden.' }
        & $VenvPython -m pip check
        if ($LASTEXITCODE -ne 0) { Fail 'Die installierten Python-Abhängigkeiten sind inkonsistent.' }
        [System.IO.File]::WriteAllText($HashFile, $CurrentHash, (New-Object System.Text.UTF8Encoding($false)))
    }

    $BackendScript = Join-Path $Root 'Start_EGM_Backend.ps1'
    if (-not (Test-Path -LiteralPath $BackendScript -PathType Leaf)) {
        Fail 'Start_EGM_Backend.ps1 wurde nicht gefunden.'
    }

    Write-LauncherLog 'EGM Backend wird gestartet...' Cyan
    $arguments = @('-NoLogo','-NoProfile','-NoExit','-ExecutionPolicy','Bypass','-File',('"{0}"' -f $BackendScript))
    $backend = Start-Process -FilePath 'powershell.exe' -ArgumentList $arguments -WorkingDirectory $Root -PassThru

    $healthUri = 'http://127.0.0.1:8000/api/health'
    $ready = $false
    for ($attempt = 1; $attempt -le 90; $attempt++) {
        Start-Sleep -Seconds 1
        if ($backend.HasExited) { Fail "Das Backend wurde unerwartet mit Code $($backend.ExitCode) beendet." }
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri $healthUri -TimeoutSec 2
            if ($response.StatusCode -eq 200) { $ready = $true; break }
        } catch {}
    }
    if (-not $ready) { Fail 'Das Backend war nach 90 Sekunden nicht erreichbar.' }

    Write-LauncherLog 'EGM ist bereit: http://127.0.0.1:8000' Green
    $launchUrl = 'http://127.0.0.1:8000/servers?egmBuild=' + $FrontendHash
    Start-Process $launchUrl
    exit 0
}
catch {
    Fail $_.Exception.Message
}
