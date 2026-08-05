[CmdletBinding()]
param(
    [switch]$SkipFrontend
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$root = [System.IO.Path]::GetFullPath($PSScriptRoot)

function Write-Step {
    param([Parameter(Mandatory = $true)][string]$Message)
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Invoke-NativeProcess {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,

        [Parameter()]
        [string[]]$ArgumentList = @(),

        [Parameter(Mandatory = $true)]
        [string]$WorkingDirectory
    )

    if (-not (Test-Path -LiteralPath $WorkingDirectory -PathType Container)) {
        throw "Working directory not found: $WorkingDirectory"
    }

    if ([System.IO.Path]::IsPathRooted($FilePath) -and -not (Test-Path -LiteralPath $FilePath -PathType Leaf)) {
        throw "Executable not found: $FilePath"
    }

    Push-Location $WorkingDirectory
    try {
        & $FilePath @ArgumentList
        $exitCode = $LASTEXITCODE
        if ($null -eq $exitCode) {
            $exitCode = 0
        }
        if ($exitCode -ne 0) {
            throw "$FilePath failed with exit code $exitCode"
        }
    }
    finally {
        Pop-Location
    }
}

function Find-InnoSetupCompiler {
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe'),
        'C:\Program Files (x86)\Inno Setup 6\ISCC.exe',
        'C:\Program Files\Inno Setup 6\ISCC.exe'
    )

    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return $candidate
        }
    }

    return $null
}


function Find-SignTool {
    if (-not [string]::IsNullOrWhiteSpace($env:EGM_SIGNTOOL_PATH) -and (Test-Path -LiteralPath $env:EGM_SIGNTOOL_PATH -PathType Leaf)) {
        return $env:EGM_SIGNTOOL_PATH
    }
    $kitsRoot = Join-Path ${env:ProgramFiles(x86)} 'Windows Kits\10\bin'
    if (Test-Path -LiteralPath $kitsRoot -PathType Container) {
        return Get-ChildItem -LiteralPath $kitsRoot -Filter signtool.exe -Recurse -File -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -match '\x64\signtool.exe$' } |
            Sort-Object FullName -Descending |
            Select-Object -ExpandProperty FullName -First 1
    }
    return $null
}

function Sign-BinaryIfConfigured {
    param([Parameter(Mandatory = $true)][string]$Path)
    $signTool = Find-SignTool
    if ([string]::IsNullOrWhiteSpace($signTool)) {
        Write-Host "[INFO] Code signing skipped (SignTool unavailable): $Path" -ForegroundColor Yellow
        return
    }
    if (-not [string]::IsNullOrWhiteSpace($env:EGM_CODESIGN_PFX)) {
        $args = @('sign','/fd','SHA256','/td','SHA256','/tr','http://timestamp.digicert.com','/f',$env:EGM_CODESIGN_PFX)
        if (-not [string]::IsNullOrWhiteSpace($env:EGM_CODESIGN_PASSWORD)) { $args += @('/p',$env:EGM_CODESIGN_PASSWORD) }
        $args += $Path
    }
    elseif (-not [string]::IsNullOrWhiteSpace($env:EGM_CODESIGN_CERT_SHA1)) {
        $args = @('sign','/fd','SHA256','/td','SHA256','/tr','http://timestamp.digicert.com','/sha1',$env:EGM_CODESIGN_CERT_SHA1,$Path)
    }
    else {
        Write-Host "[INFO] Code signing skipped (no certificate configured): $Path" -ForegroundColor Yellow
        return
    }
    & $signTool @args
    if ($LASTEXITCODE -ne 0) { throw "Code signing failed for $Path" }
    & $signTool verify /pa /all $Path
    if ($LASTEXITCODE -ne 0) { throw "Signature verification failed for $Path" }
    Write-Host "[OK] Signed: $Path" -ForegroundColor Green
}

if (-not $SkipFrontend) {
    Write-Step 'Building frontend'
    $npm = (Get-Command npm.cmd -ErrorAction Stop).Source
    Invoke-NativeProcess `
        -FilePath $npm `
        -ArgumentList @('run', 'build') `
        -WorkingDirectory (Join-Path $root 'web')
}

$python = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    $py = (Get-Command py.exe -ErrorAction Stop).Source
    Write-Step 'Creating Python build environment'
    Invoke-NativeProcess `
        -FilePath $py `
        -ArgumentList @('-3', '-m', 'venv', (Join-Path $root '.venv')) `
        -WorkingDirectory $root
}

if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw "Python build environment was not created: $python"
}

$requirements = Join-Path $root 'requirements.txt'
$buildRequirements = Join-Path $root 'requirements-build.txt'
$specFile = Join-Path $root 'ExilesGameManager.spec'
$installerScript = Join-Path $root 'installer.iss'
$versionInfo = Join-Path $root 'version_info.txt'
$prerequisitesScript = Join-Path $root 'Install_Prerequisites.ps1'
$outputDirectory = Join-Path $root 'installer_output'

foreach ($requiredFile in @($requirements, $buildRequirements, $specFile, $installerScript, $versionInfo, $prerequisitesScript)) {
    if (-not (Test-Path -LiteralPath $requiredFile -PathType Leaf)) {
        throw "Required build file not found: $requiredFile"
    }
}

Write-Step 'Installing build dependencies'
Invoke-NativeProcess `
    -FilePath $python `
    -ArgumentList @(
        '-m', 'pip', 'install',
        '--disable-pip-version-check',
        '-r', $requirements,
        '-r', $buildRequirements
    ) `
    -WorkingDirectory $root

Write-Step 'Building standalone EGM executable'
Invoke-NativeProcess `
    -FilePath $python `
    -ArgumentList @(
        '-m', 'PyInstaller',
        '--noconfirm',
        '--clean',
        $specFile
    ) `
    -WorkingDirectory $root

$workerBuildScript = Join-Path $root 'scripts\Build-EGMUpdateWorker.ps1'
$workerExe = Join-Path $root 'dist\EGMUpdateWorker.exe'
if (-not (Test-Path -LiteralPath $workerBuildScript -PathType Leaf)) { throw "UpdateWorker build script not found: $workerBuildScript" }
Write-Step 'Building native EGM UpdateWorker'
& $workerBuildScript -ProjectRoot $root -OutputPath $workerExe
if (-not $?) { throw 'UpdateWorker build failed.' }

$standaloneExe = Join-Path $root 'dist\ExilesGameManager.exe'
if (-not (Test-Path -LiteralPath $standaloneExe -PathType Leaf)) {
    throw "Standalone executable was not produced: $standaloneExe"
}
if (-not (Test-Path -LiteralPath $workerExe -PathType Leaf)) {
    throw "UpdateWorker executable was not produced: $workerExe"
}

$workerFile = Get-Item -LiteralPath $workerExe
if ($workerFile.Length -lt 4096) {
    throw "UpdateWorker executable is unexpectedly small: $($workerFile.Length) bytes"
}

$workerBytes = [System.IO.File]::ReadAllBytes($workerExe)
if ($workerBytes.Length -lt 2 -or $workerBytes[0] -ne 0x4D -or $workerBytes[1] -ne 0x5A) {
    throw "UpdateWorker executable is not a valid Windows PE file: $workerExe"
}

$workerFallbackLog = Join-Path (Split-Path -Parent $workerExe) 'update_worker_fallback.log'
Remove-Item -LiteralPath $workerFallbackLog -Force -ErrorAction SilentlyContinue
$workerSmoke = Start-Process -FilePath $workerExe -PassThru -Wait
if ($workerSmoke.ExitCode -ne 2) {
    throw "UpdateWorker smoke test returned exit code $($workerSmoke.ExitCode); expected 2 without EGM_UPDATE_JOB."
}
if (-not (Test-Path -LiteralPath $workerFallbackLog -PathType Leaf)) {
    throw 'UpdateWorker smoke test did not create update_worker_fallback.log.'
}
Remove-Item -LiteralPath $workerFallbackLog -Force

$installerSource = [System.IO.File]::ReadAllText($installerScript, [System.Text.Encoding]::UTF8)
if ($installerSource -notmatch 'Source:\s*"dist\\EGMUpdateWorker\.exe"') {
    throw 'installer.iss does not include dist\EGMUpdateWorker.exe.'
}

Sign-BinaryIfConfigured -Path $standaloneExe
Sign-BinaryIfConfigured -Path $workerExe

$iscc = Find-InnoSetupCompiler
if ([string]::IsNullOrWhiteSpace($iscc)) {
    $winget = Get-Command winget.exe -ErrorAction SilentlyContinue
    if ($null -eq $winget) {
        throw 'Inno Setup 6 is required and winget is unavailable.'
    }

    Write-Step 'Installing Inno Setup 6'
    Invoke-NativeProcess `
        -FilePath $winget.Source `
        -ArgumentList @(
            'install',
            '--id', 'JRSoftware.InnoSetup',
            '--exact',
            '--silent',
            '--accept-package-agreements',
            '--accept-source-agreements'
        ) `
        -WorkingDirectory $root

    $iscc = Find-InnoSetupCompiler
}

if ([string]::IsNullOrWhiteSpace($iscc) -or -not (Test-Path -LiteralPath $iscc -PathType Leaf)) {
    throw 'ISCC.exe was not found after installing Inno Setup.'
}

Write-Step 'Compiling Setup executable'
New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
Invoke-NativeProcess `
    -FilePath $iscc `
    -ArgumentList @($installerScript) `
    -WorkingDirectory $root

$setup = Get-ChildItem -LiteralPath $outputDirectory -Filter '*.exe' -File |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if ($null -eq $setup) {
    throw "Setup executable was not produced in: $outputDirectory"
}

if ($setup.Length -lt 1MB) {
    throw "Setup executable is unexpectedly small: $($setup.Length) bytes"
}

$setupBytes = [System.IO.File]::ReadAllBytes($setup.FullName)
if ($setupBytes.Length -lt 2 -or $setupBytes[0] -ne 0x4D -or $setupBytes[1] -ne 0x5A) {
    throw "Setup output is not a valid Windows PE executable: $($setup.FullName)"
}

Sign-BinaryIfConfigured -Path $setup.FullName

$hash = (Get-FileHash -LiteralPath $setup.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
$hashPath = $setup.FullName + '.sha256.txt'
[System.IO.File]::WriteAllText(
    $hashPath,
    "$hash  $($setup.Name)`n",
    (New-Object System.Text.UTF8Encoding($false))
)

Write-Host "`nInstaller: $($setup.FullName)" -ForegroundColor Green
Write-Host "SHA256:   $hashPath" -ForegroundColor Green
