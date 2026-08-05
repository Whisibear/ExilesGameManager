[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ProjectRoot,
    [Parameter(Mandatory = $true)][string]$OutputPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)
$OutputPath = [System.IO.Path]::GetFullPath($OutputPath)
$SourcePath = Join-Path $ProjectRoot 'update_worker\EGMUpdateWorker.cs'
$CompilerCandidates = @(
    (Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'),
    (Join-Path $env:WINDIR 'Microsoft.NET\Framework\v4.0.30319\csc.exe')
)
$Compiler = $CompilerCandidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1

if (-not (Test-Path -LiteralPath $SourcePath -PathType Leaf)) {
    throw "UpdateWorker source missing: $SourcePath"
}
if ([string]::IsNullOrWhiteSpace($Compiler)) {
    throw 'The Windows .NET Framework C# compiler (csc.exe) was not found.'
}

$outputDirectory = Split-Path -Parent $OutputPath
New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
Remove-Item -LiteralPath $OutputPath -Force -ErrorAction SilentlyContinue

$compilerArguments = @(
    '/nologo',
    '/target:winexe',
    '/platform:x64',
    '/optimize+',
    '/checked+',
    '/warnaserror+',
    "/out:$OutputPath",
    $SourcePath
)

& $Compiler @compilerArguments
$compilerExitCode = $LASTEXITCODE

if ($compilerExitCode -ne 0) {
    throw "UpdateWorker compilation failed with exit code $compilerExitCode."
}

if (-not (Test-Path -LiteralPath $OutputPath -PathType Leaf)) {
    throw "UpdateWorker output missing: $OutputPath"
}

$outputFile = Get-Item -LiteralPath $OutputPath
if ($outputFile.Length -lt 4096) {
    throw "UpdateWorker output is unexpectedly small: $($outputFile.Length) bytes."
}

$stream = [System.IO.File]::OpenRead($OutputPath)
try {
    $first = $stream.ReadByte()
    $second = $stream.ReadByte()
}
finally {
    $stream.Dispose()
}

if ($first -ne 0x4D -or $second -ne 0x5A) {
    throw "UpdateWorker output is not a valid Windows PE executable: $OutputPath"
}

$hash = (Get-FileHash -LiteralPath $OutputPath -Algorithm SHA256).Hash.ToLowerInvariant()
Write-Host "[OK] UpdateWorker: $OutputPath" -ForegroundColor Green
Write-Host "[OK] UpdateWorker SHA256: $hash" -ForegroundColor Green
