# Getting Started with Exiles Game Manager

## Requirements

- Windows 10 or Windows 11, 64-bit
- Administrator permission for installation and Windows Firewall changes
- Internet access for SteamCMD, dedicated-server downloads, updates and optional integrations
- SteamCMD will be downloaded automatically when required.

Python, Node.js and npm are not required on tester systems when the Setup executable is used.

## Installation

1. Download `ExilesGameManager-Setup-vX.Y.Z.exe` and its SHA256 file from the latest GitHub release.
2. Run Setup and approve the Windows UAC prompt.
3. Select the installation directory and optional desktop shortcut.
4. Setup installs EGM, verifies prerequisites and downloads SteamCMD directly from Valve.
5. Keep **Launch Exiles Game Manager** selected and click **Finish**.
6. EGM opens in the default browser at `http://127.0.0.1:8000`.
7. Create the first Super Admin account.
8. Import an existing Palworld server or deploy a new instance from **Servers**.

The React frontend is already built into EGM and is served by the background backend. No separate frontend window is required. The packaged EGM process runs without a visible terminal window; operational output is written to the Logs directory.

UE4SS is not bundled. It is downloaded and installed only when requested from the EGM panel.

## Data locations

Program files are installed in the folder selected during Setup. Persistent machine data is stored under:

```text
%ProgramData%\ExilesGameManager
```

New managed server deployments default to:

```text
%ProgramData%\ExilesGameManager\Servers
```

Support logs are stored in the installation directory:

```text
Logs\
```

Use the in-panel diagnostic export when reporting a problem.

## Steam Workshop

EGM browses public Workshop metadata and attempts anonymous SteamCMD downloads first. If Steam rejects an anonymous download:

1. Open **Super Admin → Steam Workshop Access**.
2. Launch the external SteamCMD console.
3. Authenticate directly in SteamCMD when required.
4. Download the Workshop item.
5. Return to EGM and approve or install the detected cached mod.

Credentials entered in the external SteamCMD console are not collected by EGM.

## Nexus Mods

Public metadata browsing works without linking a Nexus account. Direct Nexus downloads require the Nexus authentication flow and are governed by Nexus Mods API, SSO, Premium-download and acceptable-use requirements.

## Automatic updates

EGM checks the configured GitHub Releases channel for a newer version. Super Admins receive an in-panel notification. The update workflow downloads the Setup asset, validates its published SHA256 checksum and launches the installer.

## Uninstall and reinstall

Use Windows **Installed apps** or the Start Menu uninstall shortcut.

- Local EGM login accounts are removed during uninstall so a later clean installation starts with first-account setup again.
- The uninstaller separately asks whether all remaining EGM runtime data, downloaded tools, logs and managed server files under ProgramData should be removed.
- Choose **No** to retain servers and runtime data for a later reinstall.
- Server folders stored outside EGM-managed ProgramData locations are never deleted by the uninstaller.

## Beta feedback

When reporting a problem, include:

- EGM version
- Windows version
- the exact action that failed
- the generated diagnostic ZIP
- screenshots with credentials, public IP addresses and private tokens removed
