[CmdletBinding()]
param(
    [switch]$SkipFrontend,
    [switch]$RequireCodeSigning
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$root = [System.IO.Path]::GetFullPath($PSScriptRoot)

$versionSourcePath = Join-Path $root 'app\version.py'
if (-not (Test-Path -LiteralPath $versionSourcePath -PathType Leaf)) {
    throw "Application version source is missing: $versionSourcePath"
}
$versionSource = [System.IO.File]::ReadAllText(
    $versionSourcePath,
    [System.Text.Encoding]::UTF8
)
$versionMatch = [regex]::Match(
    $versionSource,
    'APP_VERSION\s*=\s*"(?<version>[^"]+)"'
)
if (-not $versionMatch.Success) {
    throw "APP_VERSION could not be read from: $versionSourcePath"
}
$expectedAppVersion = $versionMatch.Groups['version'].Value

function Write-Step([string]$Message) { Write-Host "`n==> $Message" -ForegroundColor Cyan }
function Invoke-NativeProcess([string]$FilePath, [string[]]$ArgumentList, [string]$WorkingDirectory) {
    Push-Location $WorkingDirectory
    try {
        & $FilePath @ArgumentList
        if ($LASTEXITCODE -ne 0) { throw "$FilePath failed with exit code $LASTEXITCODE" }
    } finally { Pop-Location }
}
function Find-InnoSetupCompiler {
    @(
        (Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe'),
        'C:\Program Files (x86)\Inno Setup 6\ISCC.exe',
        'C:\Program Files\Inno Setup 6\ISCC.exe'
    ) | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
}
function Find-SignTool {
    if ($env:EGM_SIGNTOOL_PATH -and (Test-Path -LiteralPath $env:EGM_SIGNTOOL_PATH -PathType Leaf)) { return $env:EGM_SIGNTOOL_PATH }
    $kitsRoot = Join-Path ${env:ProgramFiles(x86)} 'Windows Kits\10\bin'
    if (Test-Path -LiteralPath $kitsRoot -PathType Container) {
        return Get-ChildItem -LiteralPath $kitsRoot -Filter signtool.exe -Recurse -File -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -match '\\x64\\signtool\.exe$' } |
            Sort-Object FullName -Descending | Select-Object -ExpandProperty FullName -First 1
    }
    return $null
}
function Test-SigningConfigured {
    return (-not [string]::IsNullOrWhiteSpace($env:EGM_CODESIGN_PFX)) -or
           (-not [string]::IsNullOrWhiteSpace($env:EGM_CODESIGN_CERT_SHA1))
}
function Get-SignArguments([string]$Path) {
    $timestamp = if ($env:EGM_TIMESTAMP_URL) { $env:EGM_TIMESTAMP_URL } else { 'http://timestamp.digicert.com' }
    $args = @('sign','/fd','SHA256','/td','SHA256','/tr',$timestamp)
    if ($env:EGM_CODESIGN_PFX) {
        if (-not (Test-Path -LiteralPath $env:EGM_CODESIGN_PFX -PathType Leaf)) { throw "Signing certificate not found: $env:EGM_CODESIGN_PFX" }
        $args += @('/f',$env:EGM_CODESIGN_PFX)
        if ($env:EGM_CODESIGN_PASSWORD) { $args += @('/p',$env:EGM_CODESIGN_PASSWORD) }
    } elseif ($env:EGM_CODESIGN_CERT_SHA1) {
        $args += @('/sha1',$env:EGM_CODESIGN_CERT_SHA1)
    } else { throw 'No signing certificate configured.' }
    $args += $Path
    return $args
}
function Sign-And-Verify([string]$Path) {
    $signTool = Find-SignTool
    if (-not $signTool) { throw 'SignTool.exe was not found. Install the Windows SDK or set EGM_SIGNTOOL_PATH.' }
    & $signTool @(Get-SignArguments -Path $Path)
    if ($LASTEXITCODE -ne 0) { throw "Code signing failed: $Path" }
    & $signTool verify /pa /all /v $Path
    if ($LASTEXITCODE -ne 0) { throw "Signature verification failed: $Path" }
    Write-Host "[OK] Signed and verified: $Path" -ForegroundColor Green
}
function Assert-PE([string]$Path, [long]$MinimumSize = 4096) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Required executable missing: $Path" }
    $file = Get-Item -LiteralPath $Path
    if ($file.Length -lt $MinimumSize) { throw "Executable is unexpectedly small: $Path ($($file.Length) bytes)" }
    $stream = [IO.File]::OpenRead($Path)
    try { $a=$stream.ReadByte(); $b=$stream.ReadByte() } finally { $stream.Dispose() }
    if ($a -ne 0x4D -or $b -ne 0x5A) { throw "Not a valid Windows PE file: $Path" }
}
function Assert-VersionMetadata(
    [string]$Path,
    [string]$ExpectedCompany,
    [string]$ExpectedProduct,
    [string]$ExpectedVersion
) {
    $info = [System.Diagnostics.FileVersionInfo]::GetVersionInfo($Path)
    if ($info.CompanyName -ne $ExpectedCompany) {
        throw "Unexpected CompanyName in ${Path}: '$($info.CompanyName)'"
    }
    if ($info.ProductName -ne $ExpectedProduct) {
        throw "Unexpected ProductName in ${Path}: '$($info.ProductName)'"
    }
    if ($info.ProductVersion -ne $ExpectedVersion) {
        throw "Unexpected ProductVersion in ${Path}: '$($info.ProductVersion)'"
    }
}

function Assert-OnedirRuntime([string]$AppDirectory) {
    $appExe = Join-Path $AppDirectory 'ExilesGameManager.exe'
    $internal = Join-Path $AppDirectory '_internal'
    Assert-PE $appExe

    if (-not (Test-Path -LiteralPath $internal -PathType Container)) {
        throw "PyInstaller Onedir runtime directory is missing: $internal"
    }

    $pythonDll = Get-ChildItem -LiteralPath $internal -Filter 'python3*.dll' -File -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if (-not $pythonDll) {
        throw "Python runtime DLL is missing from: $internal"
    }

    if (-not (Test-Path -LiteralPath (Join-Path $internal 'base_library.zip') -PathType Leaf)) {
        throw "base_library.zip is missing from: $internal"
    }

    $forbiddenTempArtifacts = Get-ChildItem -LiteralPath $AppDirectory -Recurse -Force -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match '^_MEI\d+' }
    if ($forbiddenTempArtifacts) {
        throw 'Onefile _MEI artifacts were found in the Onedir build.'
    }
}

function Wait-Health([Diagnostics.Process]$Process, [int]$Seconds = 45) {
    for ($i=0; $i -lt $Seconds; $i++) {
        if ($Process.HasExited) { throw "Packaged EGM exited prematurely with code $($Process.ExitCode)." }
        try {
            $response=Invoke-WebRequest -Uri 'http://127.0.0.1:8000/api/health' -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -eq 200) { return }
        } catch {}
        Start-Sleep -Seconds 1
    }
    throw 'Packaged EGM did not answer /api/health.'
}

if (-not $SkipFrontend) {
    Write-Step 'Building frontend'
    Invoke-NativeProcess (Get-Command npm.cmd -ErrorAction Stop).Source @('run','build') (Join-Path $root 'web')
}

$python = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    Write-Step 'Creating Python build environment'
    Invoke-NativeProcess (Get-Command py.exe -ErrorAction Stop).Source @('-3.12','-m','venv',(Join-Path $root '.venv')) $root
}
Write-Step 'Installing build dependencies'
Invoke-NativeProcess $python @('-m','pip','install','--disable-pip-version-check','-r',(Join-Path $root 'requirements.txt'),'-r',(Join-Path $root 'requirements-build.txt')) $root

Remove-Item -LiteralPath (Join-Path $root 'build') -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath (Join-Path $root 'dist') -Recurse -Force -ErrorAction SilentlyContinue
Write-Step 'Building PyInstaller Onedir application'
Invoke-NativeProcess $python @('-m','PyInstaller','--noconfirm','--clean',(Join-Path $root 'ExilesGameManager.spec')) $root

$appDir=Join-Path $root 'dist\ExilesGameManager'
$appExe=Join-Path $appDir 'ExilesGameManager.exe'
$internalDir=Join-Path $appDir '_internal'
$pythonDll=Get-ChildItem -LiteralPath $internalDir -Filter 'python3*.dll' -File -ErrorAction SilentlyContinue | Select-Object -First 1
Assert-PE $appExe 1048576
if (-not (Test-Path -LiteralPath $internalDir -PathType Container)) { throw "PyInstaller _internal directory missing: $internalDir" }
if ($null -eq $pythonDll) { throw "Python runtime DLL missing from Onedir build: $internalDir" }
if (-not (Test-Path -LiteralPath (Join-Path $internalDir 'base_library.zip') -PathType Leaf)) { throw 'base_library.zip missing from Onedir build.' }

$workerBuild=Join-Path $root 'scripts\Build-EGMUpdateWorker.ps1'
$workerExe=Join-Path $appDir 'EGMUpdateWorker.exe'
Write-Step 'Building native EGM UpdateWorker'
& $workerBuild -ProjectRoot $root -OutputPath $workerExe
if (-not $?) { throw 'UpdateWorker build failed.' }
Assert-PE $workerExe

Assert-OnedirRuntime $appDir
$desktopEntry = [System.IO.File]::ReadAllText((Join-Path $root 'desktop_app.py'), [System.Text.Encoding]::UTF8)
$requirementsText = [System.IO.File]::ReadAllText((Join-Path $root 'requirements.txt'), [System.Text.Encoding]::UTF8)
if ($desktopEntry -notmatch 'ExilesGameManager\.Quit' -or $desktopEntry -notmatch 'pystray\.MenuItem' -or $desktopEntry -notmatch 'server\.should_exit') {
    throw 'E.11 system-tray/graceful-shutdown contract is missing from desktop_app.py.'
}
if ($requirementsText -notmatch '(?im)^pystray' -or $requirementsText -notmatch '(?im)^Pillow') {
    throw 'E.11 tray runtime dependencies are missing from requirements.txt.'
}
Assert-VersionMetadata $appExe 'Whisibear' 'Exiles Game Manager' $expectedAppVersion
Assert-VersionMetadata $workerExe 'Whisibear' 'Exiles Game Manager' $expectedAppVersion

$manifestPath = Join-Path $root 'ExilesGameManager.manifest'
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    throw "Windows application manifest is missing: $manifestPath"
}
$manifestText = [System.IO.File]::ReadAllText($manifestPath, [System.Text.Encoding]::UTF8)
if ($manifestText -notmatch 'requestedExecutionLevel level="asInvoker"') {
    throw 'Application manifest does not use asInvoker.'
}
if ($manifestText -notmatch '<longPathAware[^>]*>true</longPathAware>') {
    throw 'Application manifest is not long-path aware.'
}

$workerFallback=Join-Path $appDir 'update_worker_fallback.log'
Remove-Item $workerFallback -Force -ErrorAction SilentlyContinue
$workerSmoke=Start-Process -FilePath $workerExe -PassThru -Wait
if ($workerSmoke.ExitCode -ne 2 -or -not (Test-Path $workerFallback)) { throw 'Native worker smoke test failed.' }
Remove-Item $workerFallback -Force

$signingConfigured=Test-SigningConfigured
if ($RequireCodeSigning -and -not $signingConfigured) { throw 'Public release requires code signing, but no certificate is configured.' }
if ($signingConfigured) {
    Write-Step 'Signing application executables'
    Sign-And-Verify $appExe
    Sign-And-Verify $workerExe
} else { Write-Host '[INFO] Variante-4-Build ohne digitale Signatur. Onedir, Manifest, Metadaten und Defender-Prüfung bleiben aktiv.' -ForegroundColor Cyan }

Write-Step 'Smoke testing packaged Onedir application'
$previousSuppressBrowser = $env:EGM_SUPPRESS_BROWSER
$previousSuppressTray = $env:EGM_SUPPRESS_TRAY
$env:EGM_SUPPRESS_BROWSER = '1'
$env:EGM_SUPPRESS_TRAY = '1'
$proc = $null
try {
    $proc=Start-Process -FilePath $appExe -WorkingDirectory $appDir -PassThru
    Wait-Health $proc
}
finally {
    if ($proc) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue }
    $env:EGM_SUPPRESS_BROWSER = $previousSuppressBrowser
    $env:EGM_SUPPRESS_TRAY = $previousSuppressTray
}

$iscc=Find-InnoSetupCompiler
if (-not $iscc) {
    $winget=Get-Command winget.exe -ErrorAction SilentlyContinue
    if (-not $winget) { throw 'Inno Setup 6 is required.' }
    Invoke-NativeProcess $winget.Source @('install','--id','JRSoftware.InnoSetup','--exact','--silent','--accept-package-agreements','--accept-source-agreements') $root
    $iscc=Find-InnoSetupCompiler
}
if (-not $iscc) { throw 'ISCC.exe not found.' }

$output=Join-Path $root 'installer_output'
New-Item -ItemType Directory -Path $output -Force | Out-Null
Remove-Item -LiteralPath (Join-Path $output '*.exe') -Force -ErrorAction SilentlyContinue
Write-Step 'Compiling Inno Setup installer'
$innoArgs=@((Join-Path $root 'installer.iss'))
if ($signingConfigured) {
    $signTool=Find-SignTool
    $timestamp=if ($env:EGM_TIMESTAMP_URL) {$env:EGM_TIMESTAMP_URL} else {'http://timestamp.digicert.com'}
    if ($env:EGM_CODESIGN_PFX) {
        $cmd='"'+$signTool+'" sign /fd SHA256 /td SHA256 /tr "'+$timestamp+'" /f "'+$env:EGM_CODESIGN_PFX+'"'
        if ($env:EGM_CODESIGN_PASSWORD) { $cmd += ' /p "'+$env:EGM_CODESIGN_PASSWORD+'"' }
        $cmd += ' $f'
    } else { $cmd='"'+$signTool+'" sign /fd SHA256 /td SHA256 /tr "'+$timestamp+'" /sha1 '+$env:EGM_CODESIGN_CERT_SHA1+' $f' }
    $innoArgs=@('/DEGM_SIGNED_BUILD','/Segmsign='+$cmd,(Join-Path $root 'installer.iss'))
}
Invoke-NativeProcess $iscc $innoArgs $root
$setup=Get-ChildItem $output -Filter 'ExilesGameManager-Setup-*.exe' -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $setup) { throw 'Setup executable was not produced.' }
Assert-PE $setup.FullName 1048576
if ($signingConfigured) {
    $signTool=Find-SignTool
    & $signTool verify /pa /all /v $setup.FullName
    if ($LASTEXITCODE -ne 0) { throw "Setup signature verification failed: $($setup.FullName)" }
}

$defenderScript = Join-Path $root 'scripts\Test-EGMWindowsDefender.ps1'
if (-not (Test-Path -LiteralPath $defenderScript -PathType Leaf)) {
    throw "Defender validation script is missing: $defenderScript"
}

Write-Step 'Scanning final application and installer with Microsoft Defender'
& $defenderScript -Paths @($appDir, $setup.FullName)
if (-not $?) {
    throw 'Microsoft Defender validation failed.'
}

$hash=(Get-FileHash $setup.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
[IO.File]::WriteAllText($setup.FullName+'.sha256.txt',"$hash  $($setup.Name)`n",(New-Object Text.UTF8Encoding($false)))
Write-Host "`nInstaller: $($setup.FullName)" -ForegroundColor Green
Write-Host "SHA256:   $($setup.FullName).sha256.txt" -ForegroundColor Green
