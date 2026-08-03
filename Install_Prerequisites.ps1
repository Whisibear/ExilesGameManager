[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$DataRoot,
    [Parameter(Mandatory = $true)][string]$LogRoot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$LogRoot = [System.IO.Path]::GetFullPath($LogRoot)
New-Item -ItemType Directory -Path $LogRoot -Force | Out-Null
$TranscriptPath = Join-Path $LogRoot ("prerequisites-{0}.log" -f (Get-Date -Format "yyyyMMdd-HHmmss"))
Start-Transcript -LiteralPath $TranscriptPath -Force | Out-Null

function Test-VcRuntime {
    $keys = @(
        'HKLM:\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64',
        'HKLM:\SOFTWARE\WOW6432Node\Microsoft\VisualStudio\14.0\VC\Runtimes\x64'
    )
    foreach ($key in $keys) {
        if (Test-Path $key) {
            $item = Get-ItemProperty $key -ErrorAction SilentlyContinue
            if ($item.Installed -eq 1) { return $true }
        }
    }
    return $false
}

function Install-VcRuntime {
    if (Test-VcRuntime) { return }
    $installer = Join-Path $env:TEMP ('vc_redist.x64-' + [guid]::NewGuid().ToString('N') + '.exe')
    try {
        Invoke-WebRequest -UseBasicParsing -Uri 'https://aka.ms/vs/17/release/vc_redist.x64.exe' -OutFile $installer -TimeoutSec 180
        $signature = Get-AuthenticodeSignature -FilePath $installer
        if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'Microsoft') {
            throw 'The Microsoft Visual C++ Runtime signature could not be verified.'
        }
        $process = Start-Process -FilePath $installer -ArgumentList '/install','/quiet','/norestart' -Wait -PassThru
        if ($process.ExitCode -notin @(0, 1638, 3010)) {
            throw "Visual C++ Runtime installation failed with exit code $($process.ExitCode)."
        }
    }
    finally {
        Remove-Item -LiteralPath $installer -Force -ErrorAction SilentlyContinue
    }
}

function Install-SteamCmd {
    $destination = Join-Path $DataRoot 'steamcmd'
    New-Item -ItemType Directory -Path $destination -Force | Out-Null
    $exe = Join-Path $destination 'steamcmd.exe'
    if (Test-Path -LiteralPath $exe -PathType Leaf) { return }

    $archive = Join-Path $env:TEMP ('steamcmd-' + [guid]::NewGuid().ToString('N') + '.zip')
    try {
        Invoke-WebRequest -UseBasicParsing -Uri 'https://client-update.steamstatic.com/installer/steamcmd.zip' -OutFile $archive -TimeoutSec 180
        Expand-Archive -LiteralPath $archive -DestinationPath $destination -Force
        if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) {
            throw 'steamcmd.exe was not found after extraction.'
        }
        $process = Start-Process -FilePath $exe -ArgumentList '+quit' -WorkingDirectory $destination -Wait -PassThru -WindowStyle Hidden
        if ($process.ExitCode -ne 0) {
            throw "SteamCMD initialization failed with exit code $($process.ExitCode)."
        }

        $rawSteamLogs = Join-Path $destination 'logs'
        $visibleSteamRoot = Join-Path (Split-Path -Path $LogRoot -Parent) 'steamcmd'
        $visibleSteamLogs = Join-Path $visibleSteamRoot 'raw'
        New-Item -ItemType Directory -Path $visibleSteamRoot -Force | Out-Null
        if ((Test-Path -LiteralPath $rawSteamLogs -PathType Container) -and -not (Test-Path -LiteralPath $visibleSteamLogs)) {
            New-Item -ItemType Junction -Path $visibleSteamLogs -Target $rawSteamLogs -Force | Out-Null
        }
    }
    finally {
        Remove-Item -LiteralPath $archive -Force -ErrorAction SilentlyContinue
    }
}

try {
    $DataRoot = [System.IO.Path]::GetFullPath($DataRoot)
    New-Item -ItemType Directory -Path $DataRoot -Force | Out-Null
    Install-VcRuntime
    Install-SteamCmd
}
finally {
    Stop-Transcript -ErrorAction SilentlyContinue | Out-Null
}
