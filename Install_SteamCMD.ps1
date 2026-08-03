
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$Destination)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
$Destination=[System.IO.Path]::GetFullPath($Destination)
New-Item -ItemType Directory -Path $Destination -Force | Out-Null
$exe=Join-Path $Destination 'steamcmd.exe'
if(Test-Path -LiteralPath $exe -PathType Leaf){ exit 0 }
$zip=Join-Path $env:TEMP ('steamcmd-'+[guid]::NewGuid().ToString('N')+'.zip')
try {
  Invoke-WebRequest -UseBasicParsing -Uri 'https://client-update.steamstatic.com/installer/steamcmd.zip' -OutFile $zip -TimeoutSec 120
  Expand-Archive -LiteralPath $zip -DestinationPath $Destination -Force
  if(-not(Test-Path -LiteralPath $exe -PathType Leaf)){ throw 'steamcmd.exe was not found after extraction.' }
  & $exe +quit | Out-Null
  if($LASTEXITCODE-ne 0){ throw "SteamCMD bootstrap failed with exit code $LASTEXITCODE." }
} finally { Remove-Item -LiteralPath $zip -Force -ErrorAction SilentlyContinue }
