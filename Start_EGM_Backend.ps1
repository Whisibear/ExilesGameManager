[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$Root = [System.IO.Path]::GetFullPath($PSScriptRoot)
$Python = Join-Path $Root '.venv\Scripts\python.exe'
$Server = Join-Path $Root 'EGM_Server.py'
$Host.UI.RawUI.WindowTitle = 'EGM Backend'
Set-Location -LiteralPath $Root
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) { throw 'Die EGM Python-Umgebung fehlt.' }
if (-not (Test-Path -LiteralPath $Server -PathType Leaf)) { throw 'EGM_Server.py fehlt.' }
& $Python $Server
$code = $LASTEXITCODE
if ($code -ne 0) {
    Write-Host "`n[ERROR] Das Backend wurde mit Fehlercode $code beendet." -ForegroundColor Red
}
exit $code
