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

New-Item -ItemType Directory -Path (Split-Path -Parent $OutputPath) -Force | Out-Null
& $Compiler /nologo /target:winexe /platform:x64 /optimize+ /checked+ /out:$OutputPath $SourcePath
if ($LASTEXITCODE -ne 0) {
    throw "UpdateWorker compilation failed with exit code $LASTEXITCODE."
}
if (-not (Test-Path -LiteralPath $OutputPath -PathType Leaf)) {
    throw "UpdateWorker output missing: $OutputPath"
}

Write-Host "[OK] UpdateWorker: $OutputPath" -ForegroundColor Green
