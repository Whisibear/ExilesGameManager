# Exiles Game Manager v0.8.1 Public Beta 8

Public Beta 8 hardens the E.11 Windows release pipeline. The system-tray and graceful shutdown implementation from E.11 is retained, while the One-Click Release contract validation now recognizes the real installer contract reliably. Inno Setup warning cleanup and explicit timezone-data packaging are included.

## Beta 8 validation focus

1. Build with `EGM_One_Click_Release.bat`.
2. Confirm the release completes without the E.11 installer-contract blocker.
3. Install `ExilesGameManager-Setup-v0.8.1-beta.8.exe`.
4. Confirm EGM reports `0.8.1-beta.8`.
5. Confirm the system-tray icon is available and **Quit / Beenden** closes EGM cleanly without stopping running Palworld or Conan servers.
6. Confirm Update/Repair can close EGM cleanly and preserve all external game-server folders and persistent configuration.

## Phase E.11 — Installer / Release / System Tray Hardening

The packaged Windows application now remains accessible from the notification-area tray and can be closed cleanly with **Quit / Beenden**. Closing EGM does not stop managed Palworld or Conan dedicated servers. Setup Update/Repair/Uninstall requests the same graceful application shutdown before using an EGM-only fallback. Release and GitHub publishing pipelines now validate this lifecycle together with the current Conan RCON/import source contracts.
## Phase E.10 — Conan Integration Completion

Conan existing-server imports now report missing config/save data clearly, all EGM toast notifications remain visible for 10 seconds, and Performance Monitor is game-provider aware for Conan and Palworld.

## Phase E.9.4.2 — Generic mcrcon-compatible RCON transport

- Replaced Conan-specific packet parsing with a reusable in-tree Source/Minecraft RCON transport for future Conan/ARK adapters.
- Matched mcrcon wire behavior by using a stable request ID for authentication and commands and treating any non--1 authentication response ID as successful.
- Kept RCON credentials backend-only and loopback-only for Conan.
- Kept Live Console free of background RCON authentication polling.
- Added explicit mcrcon protocol attribution without adding a GPL Python dependency or requiring an external executable.

## Phase E.9.4.1 — Conan RCON stabilization

Conan Live Console no longer creates repeated background RCON authentication connections. The RCON endpoint is displayed from validated configuration, while actual authentication only occurs when an administrator explicitly sends a command or broadcast. This prevents localhost RCON connect/disconnect spam and preserves the existing ShowPlayers/Broadcast command path.

## Phase E.9.4 — Conan RCON reliability

- Improved Conan RCON compatibility and removed false command timeouts after successful authentication.
- Added an authenticated RCON connection indicator to Live Console.
- Conan player queries now use `ShowPlayers`, broadcasts use `Broadcast`, and multi-packet responses are collected safely.
- Added clear RCON port/configuration mismatch diagnostics without exposing credentials.

## Phase E.9.3 — Runtime window and Palworld dependency guidance

- Palworld dedicated-server worker now runs without a visible console window.
- Conan root launcher no longer receives `-log`, retaining the compact shutdown window instead of the scrolling log console.
- Restored missing English deployment-wizard translations.
- Added fully translated UE4SS / PalSchema dependency guidance for Palworld Steam Workshop mods, explicitly directing current UE4SS Experimental (Palworld) and PalSchema installation through Steam Workshop and reserving the EGM UE4SS panel for removal of legacy UE4SS installations.

## Phase E.8.1 path cleanup

- Conan Exiles Workshop content is resolved exclusively from each server instance at `<serverPath>/steamapps/workshop/content/440900/<WorkshopID>`.
- Removed the Conan legacy/global EGM `data/steamcmd/steamapps/workshop` cache migration and fallback dependency.
- `ConanSandbox/Mods/modlist.txt` keeps absolute `.pak` paths from the selected Conan server instance.
- Development launcher validation fails if Conan Workshop code reintroduces a global EGM Workshop cache dependency.

## Conan Phase E.8.1 server-local Workshop correction

- Conan Workshop downloads now use the selected server path as the SteamCMD library (`<ServerPath>/steamapps/workshop/content/440900/<WorkshopID>`), matching the per-server Palworld library model.
- `ConanSandbox/Mods/modlist.txt` references absolute `.pak` paths from that server-local Workshop library.
- Existing EGM-global Conan Workshop cache entries are migrated non-destructively into the selected server library when first used.
- SteamCMD itself remains centrally managed by EGM; only Workshop content is instance-local.
- Palworld behavior is unchanged.

## Conan Phase E.8.1 correction

Phase E.8.1 corrects Conan Workshop integration to use the native SteamCMD Workshop cache (`440900/<WorkshopID>`) as the `.pak` source referenced by `modlist.txt`, adds a Conan-specific Workshop browser and cache inventory, and extends the Backup Center to Conan `ConanSandbox/Saved` data while excluding `DedicatedServerLauncher.ini`. Palworld Workshop/Nexus/UE4SS behavior remains separated and unchanged.

## Conan Phase E.8

Phase E.8 adds Conan Exiles Steam Workshop mod management with anonymous SteamCMD downloads, `.pak` deployment, `modlist.txt` load-order management, Task Queue/Activity Center integration, a Conan-only Mods UI, Palworld runtime-verifier isolation, and hardened RCON command/result handling. Nexus Mods and UE4SS remain Palworld-only.

## Conan Phase E.7

Conan Exiles Enhanced and Legacy are now enabled for end-to-end dedicated-server deployment and runtime testing. Phase E.7 adds provider-correct port validation, persistent deployment/update Task Queue visibility, Activity Center lifecycle logging, Conan-safe scheduler monitoring, and updated development-launcher validation while keeping unsupported Palworld-only Conan capabilities disabled.

# Exiles Game Manager v0.8.1 Public Beta 7

This release is intended for the complete automatic update test from Public Beta 6 to Public Beta 7.

## Highlights

- Complete `0.8.1-beta.7` version synchronization.
- Persistent language selection across login, first-run setup, authenticated sessions, restarts and updates.
- Existing Onedir packaging, native UpdateWorker, SHA-256 verification and One-Click smoke test remain unchanged.

## Automatic update test

1. Start installed Public Beta 6.
2. Check GitHub for updates.
3. Download and verify Public Beta 7.
4. Start `EGMUpdateWorker.exe`.
5. Close Beta 6 and install Beta 7.
6. Restart EGM automatically.
7. Confirm `0.8.1-beta.7`.
8. Confirm settings, accounts, OAuth, servers, backups and language remain unchanged.

## Automatic Updater Fix

- Fixes Inno Setup exit code 5 during Beta 6 → Beta 7 updates.
- Runs future UpdateWorkers from the versioned cache.
- Reuses the current browser tab after restart.
- Keeps the update dialog visible and closable.

Phase E.8.1 follow-up hardens the Conan Exiles Workshop browser for Steam's current browse-page behavior and makes Conan/Palworld catalog selection explicit while preserving the validated Conan Workshop install/cache/modlist flow.

## Conan Phase E.9 - Server Settings

- Added real Conan `ConanSandbox/Saved/Config/WindowsServer/ServerSettings.ini` loading and editing through the existing World Settings UI.
- Added typed validation for core Conan combat, progression, harvesting, survival, day/night and server settings, including decimal comma normalization.
- Existing unknown/mod- or version-specific keys already present in `[ServerSettings]` are discovered dynamically, remain editable, and are preserved instead of being deleted.
- Writes are atomic and preserve unrelated INI sections/comments; unknown new keys cannot be injected through the API.
- Sensitive password/token-style fields are protected and are never written with their values to Activity Center logs.
- Saving Conan settings emits an instance-scoped Activity Center event and returns a visible restart-required state to the frontend.
- Corrected All Servers overview metadata so Conan instances no longer appear as Palworld/Palpagos; Conan uses its actual game label and Exiled Lands fallback.
- Palworld settings behavior remains unchanged.

## Conan Phase E.9.1 - Settings Help and Runtime Polish

- Improved Conan ServerSettings tooltips with setting-specific descriptions, including dynamically discovered Enhanced settings.
- Dedicated Conan and Palworld server processes now start hidden in the background on Windows.
- Palworld respawn cooldown and quick-death threshold now enforce a safe minimum/default of 1 second, including automatic repair of legacy zero values before server start.

## Conan Phase E.9.2 - Runtime and Decimal Input Polish

- Dedicated server processes now prefer their non-console/intended launch binaries on Windows.
- Conan multiplier and scale settings discovered from `ServerSettings.ini` accept decimal values correctly.
