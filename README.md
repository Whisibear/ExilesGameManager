
#
### Conan import diagnostics

When an existing Conan Exiles server is imported, EGM validates the server layout and reports missing `WindowsServer` configuration or world database files without deleting or rewriting the imported installation. All in-app toast notifications remain visible for 10 seconds to keep operational messages readable.

## Conan RCON reliability

EGM does not continuously authenticate against Conan RCON. The Live Console reads `ConanSandbox.log` independently and displays the configured loopback RCON endpoint. A real RCON connection is created only when an administrator explicitly sends a command or broadcast, preventing background connection storms while keeping credentials backend-only.

## Conan RCON reliability

Conan Exiles instances use backend-only RCON on `127.0.0.1`. The Live Console shows the authenticated RCON connection state, accepts raw Conan RCON commands such as `ShowPlayers`, and keeps the RCON password out of the browser and Activity Center.

# Exiles Game Manager

## Public Beta 8 release hardening

Public Beta 8 (`0.8.1-beta.8`) keeps the E.11 Windows system-tray and graceful shutdown lifecycle and fixes the One-Click Release post-build contract validation. Update, Repair and Uninstall can request a clean EGM shutdown without stopping external Palworld or Conan dedicated servers. The installer/release metadata is synchronized to Windows version `0.8.1.8`.

Exiles Game Manager (EGM) is a Windows platform for installing, importing and operating dedicated game servers through one modern control panel. The current public beta provides full Palworld workflows and is being prepared for additional games, beginning with Conan Exiles.

> **Beta notice:** Keep independent backups of important saves before using server updates, restore operations or mod installation.

## What EGM helps with

- Importing existing dedicated-server installations
- Deploying and managing multiple server instances
- Starting, stopping and restarting servers
- Editing server and launcher settings
- Creating and restoring scoped backups
- Managing Windows Firewall rules and diagnostics
- Monitoring performance, activity, logs and background tasks
- Browsing and installing Steam Workshop content
- Browsing Nexus Mods metadata and using registered OAuth login for authorized downloads
- Receiving verified application-update notifications from GitHub Releases

## Supported games

| Game | Status |
|---|---|
| Palworld | Public beta |
| Conan Exiles | Beta integration: Enhanced + Legacy deployment, runtime control, RCON and Live Console |
| Additional dedicated servers | Planned through the multi-game module architecture |

## Screenshots

### Dashboard
![Dashboard](images/EGM-Dashboard.png)

### Server Control
![Server Control](images/EGM-Server-Control.png)

### Steam Workshop and Nexus Mods
![Steam Workshop and Nexus Mods](images/EGM-Steam-Workshop-and-Nexus-Mod.png)

### Task Queue
![Task Queue](images/EGM-Task-Queue.png)

### Performance Monitor
![Performance Monitor](images/EGM-Performance-Monitor.png)

### Activity Center
![Activity Center](images/EGM-Activity-Center.png)

### Firewall Management
![Firewall Management](images/EGM-Firewall-Management.png)

### Launcher Options
![Launcher Options](images/EGM-Launcher-Options.png)

### Mod Wishlist
![Mod Wishlist](images/EGM-Mod-Wishlist.png)

### Settings
![Settings](images/EGM-Settings.png)

### Super Admin
![Super Admin](images/EGM-Super-Admin.png)

## Installation

1. Download the current `ExilesGameManager-Setup-vX.Y.Z.exe` from GitHub Releases.
2. Run the installer and approve the Windows UAC prompt.
3. Launch EGM and create the first Super Admin account.
4. Import an existing server or deploy a new supported server instance.

The packaged application serves its own frontend. End users do not need to install Node.js. SteamCMD prerequisites are managed by the installer and EGM workflows.

## Windows system tray and shutdown

Installed EGM runs as a background Windows application with a notification-area icon. The tray menu can reopen EGM or the dashboard and provides **Quit / Beenden** for a clean application shutdown. Quitting EGM stops the EGM web/backend process only; managed Palworld and Conan dedicated servers continue running until they are stopped explicitly from EGM or by the server operator. Setup Update, Repair and Uninstall use the same graceful-shutdown signal before replacing application files.

## Where data is stored

Application binaries are installed under the directory selected in Setup. Per-user application state is stored under:

```text
%LOCALAPPDATA%\ExilesGameManager
├── config
├── cache
├── logs
├── oauth
├── downloads
├── temp
├── backups
└── data
```

Managed dedicated-server installations remain separate under:

```text
%ProgramData%\ExilesGameManager\Servers
```

During uninstall, EGM asks separately whether LocalAppData application data and machine-wide managed server data should be removed. Choosing **No** preserves the selected data for a later reinstall.


## Palworld Workshop runtime dependencies

Steam Workshop installation and runtime dependencies are intentionally separate. Installing a Workshop item does not automatically install UE4SS or PalSchema. Workshop mods that require UE4SS need the current **UE4SS Experimental (Palworld)** installed from the Palworld Steam Workshop. Mods that list **PalSchema** as a dependency also require **PalSchema** to be installed from the Palworld Steam Workshop. The EGM UE4SS panel is used to uninstall an older UE4SS installation before switching to the current Workshop version.

Before switching from an older UE4SS installation to the current Experimental Palworld build, uninstall the old UE4SS from the EGM panel first. Legacy UE4SS files can conflict with the current Palworld-specific layout and prevent PalSchema or dependent mods from loading correctly.

## Nexus Mods integration

EGM is registered as a public Nexus Mods application. Login uses OAuth 2.0 Authorization Code flow with PKCE and the local callback:

```text
http://127.0.0.1:8000/api/nexus/oauth/callback
```

Public metadata browsing does not require login. OAuth tokens are encrypted for the current Windows user with Windows DPAPI and are never written to the public source export, logs or diagnostic archives. EGM does not embed a reusable client secret. Direct automatic downloads remain subject to Nexus Mods account permissions, Premium requirements and API policy.

## Security and privacy

- Local EGM passwords are salted and hashed.
- Nexus OAuth tokens are stored encrypted under the current Windows user profile.
- Secrets and runtime data are excluded from the public GitHub source export.
- Steam credentials entered in the SteamCMD console are not stored by EGM.
- Administrative API ports should remain private unless protected by an appropriate network-security design.

Report security issues privately and never attach credentials, OAuth tokens, saves or complete private logs to a public issue.

## Development and support

- Build instructions: [`BUILDING.md`](BUILDING.md)
- Getting started: [`GETTING_STARTED.md`](GETTING_STARTED.md)
- Public changes: [`CHANGELOG.md`](CHANGELOG.md)
- Security policy: [`SECURITY.md`](SECURITY.md)
- Windows Defender and SmartScreen notice: [`WINDOWS_SECURITY_NOTICE.md`](WINDOWS_SECURITY_NOTICE.md)
- Issue tracker: use the repository issue templates

## Privacy and terms

EGM is self-hosted and does not use a Whisibear-operated telemetry, analytics or account server. Application data remains on the host machine unless the operator explicitly uses a third-party feature or voluntarily shares a diagnostic package. External connections for GitHub updates, Nexus Mods, Steam/SteamCMD and optional public-IP lookup are documented in [TERMS_OF_SERVICE.md](TERMS_OF_SERVICE.md).

The terms document also explains local accounts, the functional session cookie, browser local/session storage, caches, OAuth token storage, diagnostics, deletion and host-operator responsibilities.

Windows executable reputation, SmartScreen, antivirus detections, checksum verification and false-positive reporting are documented in [`WINDOWS_SECURITY_NOTICE.md`](WINDOWS_SECURITY_NOTICE.md).

## License and attribution

EGM is distributed under the MIT License. The current project is maintained by Whisibear while the original MIT attribution is preserved. See [`LICENSE`](LICENSE), [`COPYRIGHT_AND_ATTRIBUTION.md`](COPYRIGHT_AND_ATTRIBUTION.md), [`CREDITS.md`](CREDITS.md) and [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).


### RCON transport

Conan Exiles uses EGM's backend-only, mcrcon-compatible Source/Minecraft RCON transport. No external `mcrcon.exe` installation is required. The transport is intentionally game-neutral so future ARK: Survival Evolved and ARK: Survival Ascended providers can use the same protocol layer with game-specific commands and configuration.
