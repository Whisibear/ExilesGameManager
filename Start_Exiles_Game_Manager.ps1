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

try {
    $required = @('Palworld_Server.py', 'requirements.txt', 'web\dist\index.html')
    foreach ($relative in $required) {
        if (-not (Test-Path -LiteralPath (Join-Path $Root $relative) -PathType Leaf)) {
            Fail "Erforderliche Datei fehlt: $relative"
        }
    }

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
    Start-Process 'http://127.0.0.1:8000'
    exit 0
}
catch {
    Fail $_.Exception.Message
}
