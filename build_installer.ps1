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

$standaloneExe = Join-Path $root 'dist\ExilesGameManager.exe'
if (-not (Test-Path -LiteralPath $standaloneExe -PathType Leaf)) {
    throw "Standalone executable was not produced: $standaloneExe"
}

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

$hash = (Get-FileHash -LiteralPath $setup.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
$hashPath = $setup.FullName + '.sha256.txt'
[System.IO.File]::WriteAllText(
    $hashPath,
    "$hash  $($setup.Name)`n",
    (New-Object System.Text.UTF8Encoding($false))
)

Write-Host "`nInstaller: $($setup.FullName)" -ForegroundColor Green
Write-Host "SHA256:   $hashPath" -ForegroundColor Green
