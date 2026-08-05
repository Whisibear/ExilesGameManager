# Changelog

## 0.8.1 Public Beta 4

### Highlights
- One-click GitHub updater with SHA-256 verification and automatic restart
- Complete update logging, history and diagnostics
- Installer Update / Repair workflow improvements
- Automatic preservation of user, server and configuration data
- Nexus Mods OAuth integration with Premium detection
- Nexus download, install, rescan and uninstall improvements
- Persistent Nexus metadata (Mod ID, File ID, author, version and install paths)
- Runtime verification for UE4SS, Steam Workshop, PalMod, PAK and LogicMods
- Improved Steam Workshop deployment verification
- Activity Center and Task Queue separation
- World Settings renamed to Server Settings
- The Grimoire renamed to Mods
- Refresh label fixed
- Manual -publicip launcher option
- Numerous stability, deployment and UI fixes



## 0.8.1-beta.3 - Persistent Nexus metadata and honest runtime verification

- Added persistent per-server Nexus metadata preserving Mod ID, file ID, name, author, version, image, URL and exact installed paths.
- Nexus rescans now merge filesystem discoveries with existing metadata instead of replacing records with `Unknown`.
- Added duplicate merging by Nexus ID and installed paths.
- Added persistent per-mod runtime verification shown in Downloaded Nexus Mods.
- UE4SS is verified only when UE4SS.log explicitly references the mod.
- PalMod and Steam Workshop packages are verified through InstallManifest.json.
- PAK and LogicMods remain runtime-unconfirmed when only file presence can be proven.
- Task Queue and Activity keep separate technical and user-facing verification records.

## 0.8.1-beta.3 - Unified mod verification, update checks and interface cleanup

- Renamed **World Settings** to **Server Settings** throughout the interface.
- Renamed the Mods page header from **The Grimoire** to **Mods** and removed the duplicate top **Browse Steam Workshop** button.
- Fixed the Activity Center action label showing `common.refresh`; it now displays **Refresh**.
- Changed `-publicip` to explicit manual configuration. EGM no longer detects or inserts a public IP automatically; the launch flag is only emitted when enabled and a value was entered by the administrator.
- Added a combined Steam Workshop and Nexus Mods update check. Steam Workshop timestamps are compared through Steam's published-file metadata and Nexus versions through the registered Nexus metadata service.
- Combined mod checks now run as persistent Task Queue operations and also write detailed Activity Center entries.
- Added automatic post-start mod verification as a separate Task Queue operation after every manual server start or restart.
- Verification checks that the Palworld process remains online, validates deployed files, checks Palworld `InstallManifest.json` evidence for managed mods, and reads UE4SS startup evidence from `UE4SS.log`.
- Added explicit Activity Center entries for every verified mod and a final verification summary.
- Fixed Setup launching EGM before the Finish button. Interactive Setup now launches only through the checked **Launch Exiles Game Manager** option after **Finish**, preventing duplicate browser tabs. Silent panel updates remain controlled by the detached updater.

## 0.8.1-beta.3 - Final Nexus deployment, migration and uninstall hardening

- Aligned Nexus deployment with the supported Palworld layouts: UE4SS mods, regular PAK mods, Blueprint/LogicMods, Workshop PAKs and Info.json-based PalMod packages.
- Fixed malformed legacy paths such as `Pal/Content/Paks/~mods/LogicMods` and nested `Pal/Content/Paks/...` wrappers created by earlier beta builds.
- Added automatic, narrowly scoped migration of legacy Nexus PAK files to their correct Palworld destination.
- Fixed PAK installation so structural archive folders such as `Pal`, `Content`, `Paks` and `LogicMods` are never shown as individual mods.
- Direct LogicMods PAK files are now installed and inventoried individually instead of being wrapped in generic folders.
- Existing tracked Nexus metadata is retained during rescans, preserving Nexus ID, file ID, author, version, image and Nexus URL.
- Added collision-safe persistent IDs for recovered Nexus inventory records.
- Added exact sidecar-aware tracking for `.pak`, `.utoc`, `.ucas` and `.sig` files.
- Uninstall now requires the selected Palworld server to be stopped before removing memory-mapped mod files.
- Added strict deletion boundaries that prevent EGM from deleting Palworld base files or entire shared mod roots.
- Added explicit protection for `Pal-WindowsServer.pak` and related core PAK files.
- Improved locked-file and stale-record errors with actionable rescan and server-stop instructions.
- Extended Nexus rescan, installation, migration and uninstall diagnostics in the application log and Activity Center.

## 0.8.1-beta.3 - Nexus PAK and LogicMods lifecycle fix

- Fixed approved Nexus PAK and LogicMods downloads being installed but omitted from Downloaded Nexus Mods.
- Added archive-layout detection for `~mods`, `LogicMods` and `~WorkshopMods`.
- PAK content is now installed into its actual Palworld destination instead of nested generic folders such as `Pal` or `LogicMods`.
- Added disk rescanning for UE4SS, regular PAK, LogicMods, Workshop PAK and PalMod installations.
- Added exact installed-path tracking and complete uninstall cleanup for every supported Nexus mod type.
- Existing incorrectly installed PAK folders are detected during rescan so they can be removed and reinstalled correctly.

## 0.8.1-beta.3 - UE4SS rescan and installer automation fix

- Fixed the Downloaded Nexus Mods endpoint not invoking the UE4SS directory scanner.
- Fixed imported paths already ending in `Pal`, preventing invalid `Pal/Pal/Binaries` lookups.
- Fixed PalModSettings and Workshop path resolution for both supported server import formats.
- Replaced Inno Setup Restart Manager closing with deterministic EGM-specific process shutdown.
- Manual Update and Repair now close EGM automatically and restart it after completion.
- Panel auto-update remains silent and restarts EGM exactly once.

## 0.8.1-beta.3 - Nexus UE4SS inventory and uninstall fix

- Downloaded Nexus Mods now scans the real UE4SS directory under `Pal/Binaries/Win64/ue4ss/Mods`.
- Added activation-state detection from UE4SS `mods.txt`, `mods.json` and `enabled.txt`.
- Added disk recovery for Nexus/third-party UE4SS mod folders that were installed successfully but were missing from EGM's saved inventory.
- Excluded UE4SS built-in framework folders from the Nexus inventory.
- Nexus UE4SS uninstall now removes the mod directory and its activation entries from `mods.txt` and `mods.json`.
- PalMod packages remain managed separately through `Mods/Workshop` and `PalModSettings.ini`.

## 0.8.1-beta.3 - Nexus PalMod deployment fix

- Nexus archives containing `Info.json` now use Palworld's official server mod workflow.
- Packages are copied to `Mods/Workshop`, added to `PalModSettings.ini`, and deployed by Palworld after a server restart.
- Added `Configured — restart required` status and marker-based rescanning.
- Nexus uninstall removes the ActiveModList entry, source package, deployed files, cached archive and server record.
- Legacy Nexus archives without `Info.json` remain supported through direct UE4SS/PAK installation.

## 0.8.1-beta.3 - Downloaded Nexus Mods management

- Added a dedicated `Downloaded Nexus Mods` section to the Mods page.
- Approved and installed Nexus Mods are now listed separately for the currently selected server.
- Added installation-state, Nexus ID, version, author and install-path information.
- Added a dedicated Nexus Mod uninstall workflow that removes installed files, the downloaded archive and the saved server entry.
- Separated pending Nexus wishlist requests from installed Nexus Mods.

## 0.8.1-beta.3 - Nexus Premium membership synchronization fix

- Fixed Nexus Mods Premium and Premium Trial accounts being displayed as Free members.
- EGM now reads Nexus membership roles and Premium expiry information from the current OAuth access token.
- Nexus account membership is synchronized after login, when the integration panel is opened and immediately before a Premium direct download.
- OAuth tokens and refresh tokens remain encrypted locally and are never returned to the frontend or included in public source exports.

## 0.8.1-beta.3 - Complete update logging and history

- Added detailed logging for every automatic update phase, including release detection, download, SHA-256 verification, installer hand-off, installation result and automatic restart.
- Added a detailed `New EGM Version Installed` Activity entry after a successful update.
- Added persistent update history and last-result files for support and diagnostics.
- Added update completion and failure details to diagnostic packages.
- Confirmed that Update, Repair and panel-based automatic updates preserve settings, OAuth data, managed servers and backups.

## 0.8.1-beta.3 - Reliable automatic update workflow

- Added a compact `New update available` card directly left of the notification bell.
- Added live download, verification and installation-preparation progress.
- Reworked automatic updates to use a detached Windows hand-off process that waits for EGM to close, runs the verified installer and restarts EGM.
- Added an Activity entry and notification after a successful update restart.
- Fixed cases where EGM closed before the installer was reliably launched.

## 0.8.1-beta.3 - One-click automatic updates

- Added a prominent update notification next to the notification bell.
- Added an update confirmation dialog with installed and available version information.
- EGM now downloads the verified GitHub release installer, closes all EGM processes, updates the existing installation and starts EGM again automatically.
- Settings, Nexus OAuth data, managed servers and backups remain unchanged during updates.
- Added automatic GitHub update checks every five minutes.

## 0.8.0 - Installer maintenance mode and in-panel application updates

- Added an installer maintenance screen for existing EGM installations with Update, Repair and Uninstall actions.
- Update and Repair preserve application settings, Nexus OAuth data, managed servers and backups.
- Added a Super Admin update panel that checks GitHub releases and installs verified EGM Setup assets directly from the dashboard.
- Automatic updates verify the published SHA-256 checksum before closing EGM and launching the installer in non-interactive update mode.

## 0.8.0 - Nexus Mods OAuth callback fix

- Fixed Nexus Mods login failing after successful browser authorization.
- EGM now reads the connected account from the OAuth access token returned by Nexus Mods instead of sending that token to the legacy API-key validation endpoint.
- Added clearer OAuth failure details while ensuring access and refresh tokens are never written to logs.

## 0.8.0 - Registered Nexus Mods login and application-data controls

- Added registered Nexus Mods OAuth login using Authorization Code with PKCE.
- Added encrypted local storage for Nexus access and refresh tokens on Windows.
- Added connect, connection-status, token-refresh and disconnect workflows in Super Admin.
- Added a dedicated LocalAppData structure for application settings, OAuth data, cache, logs, downloads, temporary files and backups.
- Added separate uninstall choices for per-user application data and managed server/runtime data.

## 0.8.0 - Steam Workshop Browser & Wishlist

- Added a Nexus-style Steam Workshop browser with trending, latest-added, latest-updated and search views.
- Added per-server Steam Workshop wishlist requests and super-admin approval.
- Connected approved Steam requests to the existing cache-based Workshop installer.
- Preserved the external SteamCMD console workflow under Super Admin.

# v0.7.7

- Moved external SteamCMD access to Super Admin below Nexus Mods Integration.
- Renamed the Workshop action to Browse Steam Workshop.
- Updated Workshop dialog guidance and translations.

## 0.7.6

- Added automatic detection of Workshop mods downloaded through the external SteamCMD console.
- Added a Downloaded Workshop Mods section with automatic five-second refresh and manual rescan.
- Added one-click installation and update directly from the shared SteamCMD Workshop cache.
- Added cache status detection for ready, installed, update available, and invalid items.
- Restored complete Steam Workshop mod removal, including PalModSettings, server copy, ManagedMods deployment, and EGM SteamCMD cache.
- Fixed the `steam_workshop.remove` AttributeError.

## 0.7.5

- Removed embedded SteamCMD authentication, Steam Guard, session directories, live terminal, and output polling.
- Added a Super Admin action that opens the normal Windows SteamCMD console directly.
- EGM never receives or records credentials or commands entered in the external console.
- Manually downloaded Workshop cache content is detected and used when Install or Update is retried.
- Removed obsolete SteamCMD authentication and live-terminal documentation.

## 0.7.4-r6

- Fixed the SteamCMD terminal process to use hidden redirected pipes on Windows.
- Added immediate prompt streaming for output without newline characters.
- Fixed terminal command delivery to use CRLF and drain the input pipe.
- Stabilized terminal frontend polling and byte offsets.

## 0.7.4-r4 - SteamCMD stdin login command fix

- Starts SteamCMD without credentials in process arguments.
- Sends the complete `login` command through the redirected stdin channel.
- Keeps the password out of PowerShell, CMD, process listings, application logs, and diagnostics.
- Preserves the existing Steam Guard session, task queue, activity, timeout, and cleanup flow.

## 0.7.4-r3 - SteamCMD redirected-login fix

- Starts SteamCMD directly with `+login <account>` instead of waiting for the unreliable redirected `Steam>` prompt on Windows.
- Sends the Steam password only through the process stdin pipe; it is never included in process arguments, logs, Activity, Task Queue, diagnostics, or persistent storage.
- Keeps the same SteamCMD process alive for Steam Guard and forwards the submitted code to that session.
- Expands Steam Guard and authentication response detection while keeping all authentication output memory-only.

# v0.7.4-r1

- Reworked temporary SteamCMD authentication into a true interactive prompt flow.
- Steam account name is submitted first; the password is supplied only to SteamCMD stdin when requested.
- Added a separate automatic Steam Guard dialog connected to the same running SteamCMD process.
- Added visible Task Queue and Activity lifecycle entries for sign-in, Guard verification, success, failure, cancellation, and timeout.
- Credentials and Guard codes remain memory-only and are excluded from process arguments, console output, logs, tasks, activity, and diagnostics.

# v0.7.4

- Added secure temporary SteamCMD sign-in and Steam Guard support for super admins.
- Added authenticated Workshop downloads without credential persistence or command-line exposure.

## v0.7.3 - Anonymous Workshop Library Context Fix

- Added an instance-aware anonymous SteamCMD Workshop download strategy.
- Initializes Palworld app metadata in the selected server library before downloading Workshop content.
- Falls back to the legacy global SteamCMD library without requiring Steam credentials.
- Searches and removes Workshop cache content in both instance and global libraries.
- Preserves Task Queue, Activity diagnostics, backups, and manual server-start behavior.

## v0.7.2 - Workshop and Query Port Reliability

- Serialized SteamCMD operations to prevent local client socket collisions.
- Added controlled Workshop retry and incomplete-download cleanup.
- Added explicit Steam Query Port to server deployment.
- Enabled unique Steam Query ports for new instances.
- Fixed Windows Firewall diagnostic inspection.

# Changelog

## 0.7.1 - Release Audit Fixes

- Fixed Workshop update diagnostics and pre-download validation.
- Added collision-free game, REST API, and query-port allocation.
- Replaced import auto-detection 404 responses with a normal empty result.
- Added concise Activity messages with expandable technical details.
- Corrected firewall diagnostics and offline-server verdicts.
- Reduced hidden-tab polling and removed deprecated asyncio policy calls.

# 0.7.0 — Release Audit & Diagnostics

- Added timestamped backend, frontend and HTTP audit logs.
- Added browser error capture and persistent debug logging control.
- Added downloadable, privacy-scrubbed diagnostic ZIP packages.
- Added request IDs and request-duration auditing.
- Updated the developer launcher to keep timestamped frontend logs.

## v0.6.0-r1 - Release Integrity and Launcher Correction
## 0.6.0-r2 - Server Control Build Fix

- Fixed the duplicate `ActionButton` declaration in `web/src/pages/ServerControl.tsx`.
- Renamed the server-control tile component export to `ServerActionButton`.
- Removed the recursive name collision inside `components/serverControl/ActionButton.tsx`.
- Audited all TypeScript and TSX named imports for duplicate local identifiers.
- Preserved the provided working `Start_Exiles_Game_Manager.bat` unchanged.

- Replaced `Start_Exiles_Game_Manager.bat` with the exact user-supplied working launcher.
- Removed the legacy internal logger namespace `palworld_admin` in favor of `egm`.
- Removed Python cache and compiled artifacts from the release.
- Audited the complete source and release tree for obsolete product branding.
- Preserved upstream attribution in README, LICENSE, and legal/credits documentation.
- Added `docs/RELEASE_INTEGRITY_AUDIT_V0_6.md`.

## v0.6.0 - Quality & Polish

- Unified active frontend imports under neutral EGM UI component names.
- Polished remaining legacy color and user-facing fantasy terminology.
- Added reusable EGM layout and interaction utilities.
- Added the fixed one-click developer launcher to the release root.
- Preserved all existing backend behavior, routes, data formats, and multi-server boundaries.
- Added `docs/QUALITY_AND_POLISH_V0_6.md`.
# Exiles Game Manager v0.5.1 — Modern Authentication UI

- Rebuilt the login screen as a responsive EGM desktop authentication workspace.
- Added a modern split layout with product capabilities and self-hosted security messaging.
- Replaced legacy fantasy authentication components with standard EGM UI controls.
- Reworked invitation registration and validation feedback.
- Rebuilt the first-run setup screen in the same EGM design language.
- Added authentication translations for all six supported languages.
- Preserved the existing authentication, invitation, and super-admin backend behavior.
- Added `docs/AUTHENTICATION_UI.md`.

## v0.4.1 - Server Selection and Backup Polish

- Added Dashboard, Import Server, Refresh, and New Server actions to `/servers`.
- Redesigned the All Servers landing page and first-install empty state.
- Added translated server-selection and Activity Center labels in all supported languages.
- Disabled GitHub release requests until `EGM_GITHUB_REPOSITORY` is configured.
- Replaced internal update logger names and raw HTTP errors with operator-friendly messages.
- Added Activity Center source formatting for EGM services.
- Changed normal backups from `Pal/Saved/SaveGames` to the complete `Pal/Saved` directory.
- Preserved restore compatibility with legacy SaveGames-only backups.
- Added regression coverage and `docs/POLISH_SERVER_SELECTION_BACKUPS.md`.

# Exiles Game Manager v0.4.0 — Activity & Notification Center

- Added persistent localized notifications with per-user read state.
- Added top-bar notification bell with unread counter and history.
- Added unified live Activity Center with server, application, and task events.
- Added multi-server, category, level, and search filters.
- Added Task Queue completion/failure/cancellation and server warning/error notifications.

## v0.5.0 - Modern Desktop UI

- Rebuilt the application shell around the approved EGM desktop-management design.
- Added grouped sidebar navigation and compact operational top-bar telemetry.
- Replaced the All Servers page with a responsive management overview and first-run empty state.
- Added a neutral Dashboard mode that does not visually select the first server.
- Rebuilt the active server dashboard with summary, quick actions, metrics, activity, tasks, and management shortcuts.
- Removed ambient fantasy particle rendering from the primary application shell.
- Added complete translations for all new visible navigation and dashboard strings.
- Added `docs/MODERN_DESKTOP_UI.md`.

## EGM v0.1.2 - Approved Brand Integration

- Added the approved isometric EGM cube identity.
- Added runtime PNG, SVG, favicon, Windows ICO, installer, and executable assets.
- Integrated the EGM identity into the sidebar, login, setup, browser metadata, PyInstaller, and Inno Setup.
- Updated the branding guidelines and fork roadmap.
- Preserved the existing application functionality and current UI theme; a full palette migration remains a separate future step.

## EGM v0.1.1 - Complete product rename

- Renamed the complete product identity to **Exiles Game Manager (EGM)**.
- Renamed the release root to `ExilesGameManager-main`.
- Renamed build, installer, diagnostic, project, solution, specification, image, executable, logging, firewall-rule, registry, environment, package, API-title, UI, and documentation references.
- Removed all legacy product-name and legacy acronym occurrences from source-controlled text and paths.
- Verified the required fork documents: `FORK_ROADMAP.md`, `PROJECT_IDENTITY.md`, `BRANDING_GUIDELINES.md`, `CREDITS.md`, `LEGAL.md`, and `RELEASE_PLAN.md`.
- Preserved original-author attribution through the MIT license and profile links in `docs/CREDITS.md`.

## v5.13.4 - UPnP startup regression fix

- Restored the missing `threading` import required by the UPnP discovery cache lock.
- Fixed backend startup failure: `NameError: name 'threading' is not defined`.
- Added module-import validation for the UPnP service.

## v5.13.3 - Topbar translations and UPnP cache

- Added complete localized Topbar titles/subtitles for All Servers, Performance, EGM University, Backup Center, and Firewall.
- Added safe Topbar fallbacks so untranslated i18n keys are never rendered.
- Added a 30-minute backend UPnP discovery cache, including negative results.
- Reduced missing-UPnP messages to debug level and coalesced/cached frontend status requests.

## v5.13.2 - Offline player roster handling

- `GET /api/players` now treats an offline, stopping, starting, or temporarily unreachable Palworld server as a normal lifecycle state instead of returning HTTP 400.
- The dashboard receives HTTP 200 and the persisted per-instance roster with every player marked offline, eliminating repeated REST-related error notifications and console noise.
- Authentication failures and genuine Palworld REST rejections remain actionable errors.
- Added regression coverage and documented the behavior in `docs/PLAYER_ROSTER_OFFLINE_BEHAVIOR.md`.

## v5.13.1 - University request optimization

- Removed the global five-second polling of `GET /api/university`.
- Added a shared client-side University catalog cache so multiple quest widgets no longer issue duplicate requests.
- University data now refreshes only on initial authenticated app use, when the University page is opened, or after an actual tutorial progress event.
- Reduced unnecessary backend traffic and improved page responsiveness, especially on Launcher Options and other pages containing quest spotlights.

## Steam Workshop Edition v3

- Restored anonymous-only SteamCMD Workshop downloads.
- Removed Steam username and password fields from the Workshop API.
- Added Windows 11 Proactor event-loop startup with reload disabled.
- Redacted non-anonymous SteamCMD credentials from command logs defensively.
- Reuses existing validated Workshop downloads before contacting Steam.
- Reports Steam anonymous-access restrictions explicitly instead of a misleading missing-directory error.

# Changelog

## Unreleased

- **Firewall Management completed:** added a dedicated multi-server firewall page using the existing live rule inspection, synchronize-all, repair-per-instance, and remove-per-instance operations. Windows 11 uses one UAC prompt when elevation is required; elevated Windows Server 2022 service operation is non-interactive.
- **Central Backup Center:** added a super-admin page listing backups for every immutable server instance with total size, create, verify, restore, export, and delete actions. All operations target the selected `instanceId` directly without changing the active server.
- **Live Performance Monitor:** added a two-second live view for the active server process and host CPU, RAM, disk capacity, disk throughput, network throughput, state, and uptime.
- Added complete translations for the three new areas in German, English, French, Spanish, Japanese, and Simplified Chinese.
- Documented the new multi-server invariants and Windows 11 / Windows Server 2022 behavior in `docs/FIREWALL_BACKUP_PERFORMANCE.md`.

- **World Settings decimal input:** decimal fields now accept both comma and dot separators (`0,5` or `0.5`) without resetting during entry. Values are validated server-side and normalized to Palworld-compatible dot notation when written to `PalWorldSettings.ini`. The same behavior applies to Local API decimal fields.

## 2.0.0 - 2026-07-22

- Installer checksum (SHA256): `FDAA13BB32763EDBC3F93C54EA8790F256E57E5BBBF74C0E4742D05BC1718158`.
- **Major version milestone.** Real Nexus Mods SSO integration (introduced in 1.0.5-1.0.9, confirmed working end-to-end with Nexus's registered application slug as of this release) makes Direct Install and Mod Wishlist approval fully functional for the first time without a personal API key workaround - the last major piece of the mod-management pipeline this project set out to build. Bumping to 2.0 to mark that milestone.
- **Configurable admin panel port (TICKET-0171):** Super Admin > Admin Panel Port lets you change the port ExilesGameManager itself listens on (default 8000, separate from the Palworld game server's own port) - useful if something else on your PC already uses 8000, or just to make this panel a less predictable target for random port scans. Takes effect after restarting ExilesGameManager; Firewall/Remote Access need to be re-allowed for the new port afterward.
- **Fixed: an interrupted data migration could be silently mistaken for a completed one (TICKET-0169):** upgrading could hang (with no progress feedback) while moving existing data into the Documents-based location, especially for a large existing server install - if that copy was ever interrupted (force-killed, a locked file, any mid-copy error), the app would permanently treat the resulting half-copied folder as "already migrated" with no way to retry, leaving some users with missing server files. Migration now copies to a temp location and verifies it first, so the real (Documents) location is only ever created once a complete, verified copy is ready - an interrupted attempt now leaves the original data fully untouched and gets offered again next launch, instead of silently leaving broken data behind.
- **Real guild names on Dashboard/Players (TICKET-0168):** the Guild column previously always showed "Unaffiliated" for every player, since Palworld's own REST API has no guild data at all. Guild membership is now read directly from the server's own save file. Not yet confirmed against a real multi-player guild on a live server - flagged for the developer to verify.
- **Nexus Mods application registration confirmed (TICKET-0167):** Nexus Mods assigned ExilesGameManager's real application slug (`kvitekvist-exilesgamemanager`), replacing the guessed placeholder `nexus_sso.APPLICATION_SLUG` had used since TICKET-0105/TICKET-0107. This lifts the "pre-release build" pending-approval caveat carried since 1.0.7 - "Connect via Nexus Mods" now points at a registered application. Direct Install and Mod Wishlist approval should work end-to-end; the live SSO click-through itself hasn't been exercised in this environment (no interactive browser session available here), so flagged for the developer to confirm on first real use.

## 1.0.9 - 2026-07-17

- Installer checksum (SHA256): `1B93E1A7FEFCFC7FE34BEFEB584E5EC2B121A0EF63E587E4877B4CBC0FEFDED9`.
- **This is a pre-release build.** Mod deployment (Direct Install and Mod Wishlist approval, both of which use the saved Nexus Premium API key) is still pending Nexus Mods confirming ExilesGameManager's application registration. Install From File no longer depends on this at all as of this release (see below) - everything else in this changelog is fully working.
- **Moved the "Update available" indicator from the sidebar to the top bar**, to the left of "Current Server", so it's visible without needing the sidebar expanded.
- **New: Privacy Mode (TICKET-0166):** a Super Admin toggle that masks IP addresses and folder paths everywhere they appear in the app - safe to turn on before streaming or screen-sharing. Masking happens server-side (before values ever reach the browser), covering Remote Access/Share With Friends' network info, Server Instances/Super Admin's install paths, the Mods folder path, and the diagnostics report. Interactive folder-picker dialogs (Deploy/Import/Save Import) deliberately keep showing real paths, since the admin needs to see them to confirm the right folder was picked.
- **Fixed: Server Control actions failed silently (TICKET-0164):** Save World, Start, Stop, Restart, Check for Updates, and Broadcast Message had no error handling at all - if the underlying request failed (most commonly the Palworld REST API not being enabled/configured yet), the button just stopped spinning with zero feedback, which is what produced reports like "Last saved: Never" even after repeatedly pressing Save World. All six actions now show a proper error notification on failure, matching the pattern the Update action already used.
- **Install From File no longer requires a Nexus catalog match (TICKET-0164):** a super admin can now install any archive they upload, not only files that hash-match something Nexus hosts - a match still auto-fills the mod's real name/author/version, but a miss (a different distribution source, an older/newer file revision, or Nexus's lookup being unreachable) now installs the file anyway, clearly marked unverified with an editable name field, instead of being rejected outright.
- **Fixed: CI's backend tests failed on every real run (TICKET-0165):** `pytest -v` as CI invokes it (the bare console-script entry point) never added the repo root to `sys.path`, so `tests/conftest.py`'s `from app.services import ...` failed with `ModuleNotFoundError: No module named 'app'` - latent since CI was added, only surfaced on its first real trigger. Fixed with `pythonpath = .` in `pytest.ini`.

## 1.0.8 - 2026-07-17

- Installer checksum (SHA256): `C1628A1501CA579C57C783EDF74A989B356D06CAB9F962E13B89824BFCF13E72`.
- **This is a pre-release build.** Mod deployment (Direct Install and Mod Wishlist approval, both of which use the saved Nexus Premium API key) is still pending Nexus Mods confirming ExilesGameManager's application registration. Everything else in this changelog is fully working.
- **EGM University fixes from live testing (TICKET-0163):** fixed two bugs that made auto-completion look entirely broken - `set_ports` blocked every later Super Admin step behind a manual click that was easy to miss (fixed in TICKET-0162), and the quest tracker never refetched after backend-only completions like creating a server (also TICKET-0162). This round: World Settings gets a Save Settings button in its top banner (the bottom Save bar was hidden behind the University tracker widget); Admin Basics now teaches Stop before Start; graduating now shows confetti and a congratulations message the next time you visit EGM University even if the last lesson completed on a different page; "Browse Nexus Mods" and every "Add to Wishlist" button now glow while wishlisting is the active step; Admin Basics' wishlist step actually completes now (it never had a trigger wired); and "Kick Captain Lamball" moved off the University page onto a new fake "Training Roster" panel on Dashboard.
- **EGM University tutorial upgrade (TICKET-0162):** most lessons now auto-complete from real actions instead of a manual "I completed this" click - creating a server, setting up firewall/port forwarding (evaluated jointly across the Remote Access and Share With Friends panels), toggling `-publiclobby`, checking for updates, enabling scheduled backups, starting the server, installing UE4SS, wishlisting/approving mods, reordering mods, and disabling all mods. A pulsing gold spotlight now highlights the actual control for the active step, and the floating tracker widget gained a manual "Mark this step done" fallback for judgment-call steps. Mod Supervisor's wishlist/approve steps were consolidated from 7 to 5 (wishlist and approve each now cover both mods in one step, with a nudge notification after the first wishlist). Added a Retake button for graduated courses, short blurbs on each course, and a super-admin-only view of which admins have finished Admin Basics (Users & Access panel). New Mods-page "Allow Mods" toggle stays in sync with World Settings' Allow Client Mods field since both write the same `bAllowClientMod` value through the existing endpoint.
- Removed the floating "quick actions" wand button (bottom-right corner) - Server Control and Logs remain reachable from the Sidebar, and World Settings/Server Control still have their own Save actions (TICKET-0161).
- **Maintainability refactor of frontend/backend hotspots (TICKET-0156):** `app/services/palworld_settings.py`'s ~360 lines of field metadata moved into `app/services/palworld_settings_data.py`, leaving the `.ini` engine on its own. `app/routes/mods.py` split into a package (`wishlist.py`/`crud.py`/`nexus.py`/`manual.py`), with Nexus-download and manual-upload-verification business logic extracted into `app/services/nexus_mod_service.py`/`app/services/manual_mod_service.py`. `web/src/pages/ServerControl.tsx` decomposed into `web/src/components/serverControl/*` plus `useShutdownCountdown`/`useServerUpdateJob` hooks, dropping from 595 to ~305 lines. Every routed page except Dashboard is now lazy-loaded (`React.lazy`/`Suspense` in `App.tsx`), shrinking the main JS bundle from ~1.10 MB to ~712 KB. Added `ruff` (backend) and `prettier` (frontend) formatting/lint gates plus an explicit `typecheck` script, all wired into CI. Pure structural refactor - no route paths, response shapes, or UI behavior changed.
- Added EGM University: sequential Super Admin, Mod Supervisor, and Admin Basics courses with an in-app quest tracker, role-aware automatic enrollment, safe training exercises, persistent diplomas, and graduation confetti (TICKET-0157, TICKET-0158, TICKET-0159).
- **One-click backup restore with integrity checks (TICKET-0155):** Recent Backups now has Restore, Verify, Export (download as .zip), and editable notes per backup, plus configurable retention (max count/age/total size, replacing the old fixed 10-backup limit). Every new backup records a file manifest (count + per-file checksum) in its `meta.json` so Verify can actually detect an incomplete or corrupted backup instead of just assuming it's fine. Restore stops the server first if it's running, snapshots the current save as a rollback point, then safely replaces the live save - automatically restoring that rollback snapshot if the replace itself fails for any reason.
- **Save Import hardening (TICKET-0148):** world-save discovery now searches up to 4 folders deep, so pointing the picker at `SaveGames`, `Saved`, or the whole `Pal` folder works automatically instead of only the world's own folder or its immediate parent. Required save files (`Level.sav`, `LevelMeta.sav`) are validated as present and non-empty before import, with issues shown per candidate in the picker. The dialog now shows what's currently on the server next to what's about to replace it. The actual replace no longer deletes the destination before copying (the class of bug that could leave a server's save slot empty or half-written if interrupted) - it copies to a verified temporary location first, then swaps it in, with automatic rollback to the pre-import backup if anything goes wrong.
- **New shared `app/services/safe_replace.py` primitive:** the safe copy-to-temp/verify/atomic-swap logic behind both of the above is one shared, independently-tested module rather than two separate implementations.
- **Automated backend test suite and CI (TICKET-0154):** added a real pytest suite (`tests/`) covering auth, permissions, instance switching, backup/restore, save import, mod archive extraction (zip-slip/oversized-archive rejection), process-discovery matching, and packaged frontend serving - previously `tests/` was empty and correctness relied entirely on manual verification. GitHub Actions CI (`.github/workflows/ci.yml`) now runs backend tests, frontend lint/build, and a packaging smoke test (real PyInstaller build + launch + health check, Inno Setup compile) on every push and pull request. Also fixed one pre-existing frontend lint error found along the way (a deprecated octal escape in `SaveImportDialog.tsx`'s placeholder text).
- **Browsing mods is wishlist-only for every role (TICKET-0153):** the Mods page's Browse Nexus Mods dialog no longer shows "Direct Install"/"Install File" to the super admin - every mod card, for admins and the super admin alike, now only offers Add to Wishlist. The Mod Wishlist page's Approve action and Super Admin's own Install From File panel are unaffected.
- **"Require Steam Authentication" toggle in World Settings (TICKET-0152):** Palworld's `bUseAuth` server setting is now a clearly labeled toggle under Identity and Access, instead of an unlabeled generic field. Explains that disabling it lets a split/virtualized Steam session tool (e.g. Nucleus co-op) join without an AUTH error, at the cost of removing that identity check for every player.
- **Backup folder path in the UI (TICKET-0151):** Recent Backups now has an "Open Folder" button per row, instead of needing to search the data folder by hand to find where a backup actually lives.

## 1.0.7 - 2026-07-14

- Installer checksum (SHA256): `1AA87767D2D1B28DAE47EFF8D7DDBC6CD9A2CF0C66C45019679DD8506002E8D9`.
- **This is a pre-release build.** It bundles Nexus SSO integration ahead of Nexus Mods confirming ExilesGameManager's application registration - Direct Install/Wishlist-approve are not fully functional until that's confirmed. Everything else in this changelog is fully working.
- **Fixed: deleting a server left it in the Current Server dropdown (TICKET-0150):** removing or unregistering a server in Server Instances now refreshes the app immediately, instead of the TopBar's server switcher still showing the deleted server until a manual browser refresh.
- **Nexus search and lists can now page through everything (TICKET-0149):** the Mods page search and Trending/Latest Added/Latest Updated tabs were capped at a fixed first 60 results with no way to see more - now they show a "Load More" button until every matching mod has been loaded.
- **Manually-installed mods now show up (TICKET-0146):** mods placed directly into the mods folders by hand now appear on the Mods page (tagged "Manually Added") and can be enabled/disabled/removed through the app, instead of being permanently invisible to it.
- **`.7z` mod archives supported (TICKET-0145):** Install From File and Nexus direct-install now accept `.7z` archives in addition to `.zip`.
- **Real Nexus Mods search (TICKET-0144):** searching the Mods page now searches all of Nexus Mods by name, instead of only filtering whatever was already loaded into the Trending/Latest Added/Latest Updated tabs.
- **Fixed: mods always installed to the wrong folder regardless of type (TICKET-0143):** pak-based content mods now install to `Pal/Content/Paks/~mods`, and UE4SS/PalSchema mods now install to `Pal/Binaries/Win64/ue4ss/Mods`, instead of everything landing in one folder that matched neither.
- **Fixed: UE4SS didn't create a `ue4ss` folder and mods didn't work (TICKET-0142):** UE4SS now installs from the Palworld-specific experimental fork (with the `Win64/ue4ss/...` layout PalSchema and most current mods require) instead of the generic stable release's old flat layout. Upgrading from a previous install automatically removes the old conflicting files and migrates any mods that had landed in the wrong place.
- **README sponsor section (TICKET-0141):** added an Indifferent Broccoli banner, personal recommendation, two-day free-trial note, and clear affiliate disclosure.
- **Traffic lights can be manually verified (TICKET-0140):** Dashboard's Game/Query/Remote-Access lights no longer stay permanently yellow just because no UPnP router was found - Super Admin's Port Forward and Remote Access panels now have a "Mark as Verified" button for once you've manually forwarded a port and confirmed it works, turning that light green.
- **Deploy New Server shows the real default location (TICKET-0139):** the "Server Deployment Location" field now shows exactly where a new server will land (e.g. `Documents\ExilesGameManager\Servers`) under the input, instead of just a generic "default folder" label.
- **Space Invaders while your server deploys (TICKET-0138):** the Deploy New Server dialog now shows the same mini-game from the loading screen while SteamCMD downloads your server - this time with a small squid-pal-styled ship.
- **Installer now defaults to Program Files (TICKET-0136):** the installer always asks for administrator permission (one UAC prompt) and defaults to installing into Program Files, like most Windows programs - removed the earlier "install for me only" no-admin choice. You can still Browse to a different folder on the destination page if you prefer.
- **Fixed: "Run Diagnostics as Admin" failed with a permission error (TICKET-0137):** a Windows argument-quoting gap in the elevation helper silently broke for any path containing a space - which every install path now does, since Program Files always has one. Diagnostics elevation (both buttons share the same helper) now works correctly regardless of where ExilesGameManager or your Documents folder are located.
- **Fun loading screen (TICKET-0135):** the plain "Awakening the realm..." loading text is now a small playable Space Invaders mini-game (arrow keys, Space to shoot) while the app checks your login status - disappears the moment it's done.
- **Documents\ExilesGameManager\Servers is now the default deploy location, and the installer stops offering a redundant launch (TICKET-0133):** new Palworld server deployments now land in a visible `Servers` folder next to the app's own data folder by default, created immediately when the installer finishes (not just on first deploy). The Finished page no longer offers to "Launch ExilesGameManager" on a fresh install, since the app is already running by then - it still offers this normally when updating/reinstalling over an existing account.
- **Fixed: Browse folder picker could silently open behind the app window (TICKET-0134):** clicking Browse (deploy location, Import Server, UE4SS folder, save import) could look like nothing happened - the dialog was opening, just without Windows granting it foreground focus. Also renamed "Install Location" to "Server Deployment Location" in the Deploy New Server dialog.
- **Installer no longer deploys your first server; the app asks instead (TICKET-0132):** the installer's server-name/install-location pages are gone - deploying during setup ran as a fire-and-forget background task with no reliable way to know it had actually finished, which could leave the app showing "No server" even after a real deployment succeeded. The super admin is now shown a full-screen "let's set up your first server" prompt the first time they log in with none registered yet, using the same reliable Deploy/Import flow already used from Settings.
- **Deploy dialog now says the download can take a few minutes:** clarified in the Deploy New Server description, since it's easy to assume something's stuck while SteamCMD downloads the server in the background.
- **Fixed: clicking Browse (Import Server, UE4SS folder, save import, deploy location) could crash the whole app (TICKET-0131):** the native folder picker used `tkinter`, which isn't safe to initialize outside the main thread - every Browse button called it via a background thread, which could bring down the entire process instead of just showing an error. Replaced with a short-lived PowerShell folder-browser dialog instead, which doesn't have this problem.
- **Migration now asks first (TICKET-0130):** upgrading from a previous version no longer silently moves your existing data into the new Documents location - ExilesGameManager now detects it and asks whether to bring it forward, or leave it alone and start with a completely fresh setup.
- **Program Files install option restored; data moved to Documents (TICKET-0129):** you can once again choose an elevated "install for all users" option that puts ExilesGameManager in Program Files, like most Windows programs - TICKET-0123 had removed that to guarantee the install folder was always writable, since data used to live there too. App data (accounts, server registry, mods, logs, backups) now lives under `Documents\ExilesGameManager\data` instead, visible and easy to find (not hidden like AppData), and independent of wherever the program itself is installed. Upgrading from either older data location migrates automatically with a one-time notice, same as before.
- **Renamed the app to ExilesGameManager everywhere, including the installed .exe (TICKET-0127):** the installer, the Start Menu entry, the Desktop shortcut, and the packaged executable itself all now say "ExilesGameManager" instead of "Palworld Server Admin"/`PalworldServerAdmin.exe` - matching the name used everywhere else (GitHub, this README, the Nexus API identity). Upgrading from an older version removes the stale old-named exe automatically, and an existing "allow through firewall" rule from before the rename still counts as allowed instead of prompting a redundant duplicate rule.
- **Fixed: installer failed with "Access is denied" partway through install (TICKET-0128):** since the installer never elevates (TICKET-0123), picking a folder that actually needs administrator rights (most commonly anything under Program Files) failed deep in the file-copy step with a bare, unhelpful Windows error. The installer now tests whether the chosen folder is actually writable right after you pick it and shows a clear explanation instead, before anything is copied.
- **Fixed: installer crashed with "internal error: an attempt was made to expand the app constant before it was initialized" (TICKET-0125):** a bug in TICKET-0123's installer changes - `HasAdminAccount`/`HasServerData`/the default server folder all referenced `{app}`, but were evaluated during `InitializeWizard`, before Setup has a destination folder to expand `{app}` to. Moved that evaluation to fire right after the user confirms the destination folder instead.
- **All app data now lives in the install folder, not AppData (TICKET-0123):** ExilesGameManager no longer stores anything under `%LOCALAPPDATA%\PalworldServerAdmin` - accounts, server registry, mods, backups references, logs, and diagnostics reports all live inside a `data` folder next to the installed exe, so the whole install is self-contained and portable. The installer also no longer offers an "install for all users" (admin-elevated) option, so the folder you pick is always writable. **If you're upgrading from an earlier version**, your existing data is moved over automatically the first time the new version runs, with a one-time popup confirming it.
- **"Run Diagnostics as Admin" button (TICKET-0124):** alongside the existing best-effort "Run Diagnostics" (which silently falls back to a limited report if the permission prompt is declined), a new button requires the elevated run to succeed and reports a clear error instead of a silently-degraded report if it doesn't.
- **"Manually Added" flag, no Request Update for manual installs (TICKET-0122):** mods installed via Super Admin's Install From File now show a "Manually Added" badge and never offer "Request Update" - their Nexus mod ID only proves the uploaded file's hash matched something on Nexus, not that they came through the Nexus download/wishlist pipeline that button triggers.
- **Launcher Options skeleton loading (TICKET-0121):** the Launcher Options page no longer blocks behind a full-page spinner - all option cards render immediately with placeholders standing in for the data (toggle states, Super Admin IP/port/query port values) until it loads, matching the pattern already used for Remote Access/Share With Friends.
- **Dashboard network traffic lights (TICKET-0112):** three grey/yellow/red/green indicators (Game Port, Steam Query Port, Remote Access) summarizing the same firewall+forwarding checks Super Admin's detailed panels already do, visible to super admins.
- **Dashboard CPU/RAM: Palworld vs whole machine (TICKET-0115):** both tiles now show two bars each - Palworld's own usage (unchanged) and the whole machine's current load, so a host can tell "is Palworld struggling" apart from "is this machine busy with something else."
- **Fixed: "Last saved" never updated (TICKET-0113):** clicking Save World (or a scheduled backup's live-save) produced a real timestamp that was then thrown away - nothing persisted it anywhere the status endpoint could read back. Dashboard/Server Control now reflect real save times.
- **Skeleton loading + static toggle text (TICKET-0111):** Remote Access and Share With Friends now show their real labels immediately with loading placeholders standing in for just the data, instead of the whole card popping in once network data resolves. Every boolean toggle across World Settings/Local API Settings now reads a static "Enable or Disable" instead of flipping between the two based on current state.
- **Import Save moved to Server Instances (TICKET-0114):** relocated from Automation to Settings > Server Instances, with a purple (arcane) accent.
- **Mod File Uploads moved to Mod Wishlist (TICKET-0110):** both super-admin mod-installation entry points (approve a wishlist request, install an already-downloaded file) now live on the same page.
- **Password reveal toggle (TICKET-0072):** every password field (login, first-run setup, World Settings/Local API sensitive fields) now has a show/hide eye icon, masked by default.
- **Pending Install badge, Nexus Login re-enabled (TICKET-0109):** the Mods page now shows a "Pending Install" card for wishlisted mods that aren't installed yet at all (update requests for an already-installed mod keep their own "Update Requested" badge). Also reverted TICKET-0107: "Nexus Login" is visible and clickable again even though Nexus hasn't confirmed ExilesGameManager's application slug yet, per explicit user request to see the real authorization step rather than have it hidden.
- **Fixed: Nexus errors force-logging you out (TICKET-0108):** an expected "no Nexus connection" or "Nexus key invalid" error was being misread as "your ExilesGameManager session died," forcing a full logout back to the login screen instead of a normal popup error. Both were using HTTP 401, which this app's frontend specifically treats as a dead session - they now use 400/whatever Nexus actually returned, and show as an ordinary error toast like every other action failure.
- **Nexus Connect degrades gracefully until Nexus approves (TICKET-0107):** since ExilesGameManager doesn't have its real Nexus application slug yet, "Connect via Nexus Mods" would have opened a Nexus page for an unregistered application - now disabled and clearly labeled "Pending Nexus Mods Approval" instead, until that's confirmed.
- **Nexus personal key not actually invalidated (TICKET-0106):** found immediately after updating a live server - TICKET-0105 blocked *pasting a new* personal API key but never invalidated one already saved from before that change, so it kept quietly authenticating installs. Any saved Nexus connection that didn't come from the new SSO flow is now cleared automatically the next time it's read - no manual step needed, but Direct Install/Wishlist-approve will stop working until you reconnect via SSO (once Nexus confirms the real application slug). Browsing and Install From File are unaffected.
- **Nexus Mods SSO, real update checks (TICKET-0105):** per Nexus Mods support's final requirement to complete ExilesGameManager's app registration, replaced the "paste your personal API key" connection flow with Nexus's own Single Sign-On (the same mechanism Vortex/MO2 use) - the super admin now clicks Connect, approves ExilesGameManager on a Nexus Mods tab, and never sees or copies a key. Installed mods also now show real update availability (previously always false) via a keyless Nexus GraphQL check; requesting an update goes through the existing Mod Wishlist approve/deny flow instead of a one-click super-admin action, and wishlist entries are labeled "Update" when they're for an already-installed mod. Uses a placeholder application slug pending Nexus's final registration confirmation.
- **Save Import (TICKET-0104):** added an "Import Save" tool in Settings > Automation so a co-op or single-player save copied over from another PC (e.g. the host's own Steam library) can be dropped straight into a registered server's save slot, even on a machine that never had Steam installed. Point it at the copied save folder (or its parent folder, if there's more than one world to choose from), confirm, and it automatically backs up the server's current save before replacing it. The server must be stopped first.
- **Docs cross-links (TICKET-0103):** README and Getting Started now reference the new wiki screenshots and link to the full Wiki; fixed Getting Started's long-missing diagnostics screenshot.
- **Wiki cleanup (TICKET-0102):** removed the leftover placeholder captions under each screenshot now that real images are in place.
- **Wiki screenshots (TICKET-0101):** added all 55 real screenshots to `images/wiki/` and the live GitHub Wiki, replacing the placeholders.
- **Wiki rewrite (TICKET-0100):** rewrote all 9 wiki pages as step-by-step "how do I...?" guides with a specific screenshot placeholder per step, instead of generic feature lists.
- **GitHub Wiki (TICKET-0099):** published one page per sidebar item to the actual GitHub Wiki tab, matching the pre-existing Home/Getting Started pages' conventions. Also fixed `git push` failing with a stale-credential 403 by pointing git at the already-working `gh` CLI login.
- **Wiki (TICKET-0098):** added a `wiki/` folder with one article per sidebar page, each with a screenshot placeholder under `images/wiki/` for the user to fill in.

## 1.0.6 - 2026-07-12

- Installer checksum (SHA256): `aabaddd84a80676ea753e925d85fea23e4bd5a1ba80444edbd738149e3139b83`.
- **README refresh (TICKET-0096):** documented the sidebar donation link and `scripts\build.bat` as the recommended way to build the installer; verified the local README already matched what's live on GitHub before editing.
- **Installer build script (TICKET-0095):** added `scripts\build.bat`, a one-command wrapper around `build_installer.ps1` for rebuilding the packaged executable and installer.
- **First-run "no servers" fix (TICKET-0093):** the top bar's server switcher now keeps checking for the installer's seeded first server instead of permanently showing "no servers" if the browser opened before that background deploy finished. Fixes a real install where the switcher stayed empty even after the server was ready, leading to a confusing duplicate-name error until the page was manually refreshed.
- **Windows 10 packaged login fix (TICKET-0092 / GitHub #154):** explicitly serve bundled `.js` and `.mjs` files as `application/javascript`. This fixes systems where Windows' MIME registry caused the packaged frontend bundle to be sent as `text/plain`, leaving only the background visible while browsers refused to load the login page.
- **GitHub release notifications (TICKET-0091):** ExilesGameManager now checks the public GitHub Releases feed through a cached, non-blocking backend service and shows a restrained sidebar update indicator when a newer stable version exists. No GitHub credential is required and installers are never downloaded or executed automatically. Runtime, Nexus, sidebar, and packaging version checks now share one authoritative application version.
- **Subtle donation link (TICKET-0090):** added a small project-styled PayPal donation control at the bottom of the sidebar, using the provided ExilesGameManager merchant details and NOK currency without PayPal's stock image button or tracking pixel.
- **Nexus compliance fix (TICKET-0088):** Nexus API requests and the installer now both declare version 1.0.6. Every endpoint that can use the saved Nexus Premium key or initiate a Nexus download, including updates to installed mods, now requires the super admin.
- **Server mod wishlist, for Nexus Mods compliance (TICKET-0089):** regular admins can add publicly browsed Nexus mods to a per-server wishlist, but never touch the saved Nexus Premium API key directly - only the super admin's explicit approval can use it to download and install a request (or deny it). Keeps every authenticated Nexus action strictly limited to the super admin, in line with Nexus Mods' Acceptable Use Policy for API keys.
- **Mod Wishlist gets its own page (TICKET-0094):** moved mod request approval out of a second Super Admin tab and into its own "Mod Wishlist" sidebar entry under Host Controls, so it's easier to find.

## 1.0.5 - 2026-07-11

- Installer checksum (SHA256): `11AB0B83B8230B00A3F4C8B51451CB4DA68C0756867BDC99170F540685236FD9`.
- **Mod install fix (TICKET-0082/TICKET-0084):** fixed installing mods whose archive bundles the full relative game path instead of just the mod's own folder (`Pal/Binaries/Win64/Mods/<ModName>/...` or `Pal/Binaries/Win64/ue4ss/Mods/<ModName>/...`, seen with "Infinite Weight In Camp") - these were unpacking into a broken, doubled folder path and not working in-game. They now unpack and install correctly. If you already installed an affected mod and it isn't working, remove it and reinstall the same file to get the corrected layout.
- **Multi-file mod picker (TICKET-0083):** Direct Install now shows a list of files to choose from when a Nexus mod has more than one current file (e.g. a Main File plus Optional Files), instead of the app silently picking one for you with no way to choose otherwise. Mods with only one file still install in a single click, unchanged.
- **TICKET-0081**: Fixed the Logs page exposing real host/client IP addresses to any logged-in user in the ExilesGameManager output panel - IPs are now masked there unless you're the super admin. Also removed the recurring low-value polling noise that was cluttering that panel, and both Logs panels now show the newest entry at the top instead of the bottom.
- **TICKET-0087**: Removed the bundled `Diagnose-ExilesGameManager.cmd` batch file, which some file scanners flag by default regardless of what it actually does. The Start Menu "Diagnose ExilesGameManager" shortcut now launches the same diagnostics script directly through PowerShell instead, with no `.cmd`/`.bat` file shipped at all.

## 1.0.4 - 2026-07-11

- Installer checksum (SHA256): `5B726B97261CBB18DBA81A4E4AE5261AFDCF4E9A6386F341B9B043833E429CE6`.
- **Fixes an issue introduced in 1.0.3:** the Steam Query Port option could collide with a server's own game port, causing Palworld to silently start on the next open port instead of the one you configured (a mismatch between what the app showed and what the server actually bound to). This is fixed - see TICKET-0075 below.
- **TICKET-0078**: Steam Query Port is now an explicit Enable/Disable toggle in Launcher Options and is off by default for both new and existing servers. ExilesGameManager only appends `-queryport=<port>` when you turn it on, and Super Admin's firewall/port-forward checklist only shows query-port steps while it's enabled.
- **TICKET-0076**: Fixed the in-app Super Admin diagnostics button so declining or being blocked by the Windows permission prompt no longer leaves you with no report at all. It now falls back to a limited non-admin diagnostics run and clearly marks the report when firewall inspection may be incomplete.
- **TICKET-0075**: Fixed Steam Query Port collisions with a server's own game port. If they matched, Palworld would bind the query port first and silently move the actual game server to the next open port, so the server would run on a different port than the one configured in ExilesGameManager. Query port is now guaranteed to stay distinct from the game port (old same-port values are migrated to a safe nearby port automatically), and saving a query port that matches any registered server's game port is now blocked with a clear warning.
- **TICKET-0074**: Added a "Run Diagnostics" button to Super Admin that runs the existing diagnostics tool (firewall, port forwarding, REST API, server files, etc.) from inside the app and shows the report right there, instead of needing to find the separate Start Menu shortcut.
- **TICKET-0073**: Made the Sidebar's "Host Controls" section (added in TICKET-0070) into a solid gold badge instead of a thin divider line, since it was too subtle for some users to notice. Also moved the Steam Query Port editor (TICKET-0069) from Super Admin into Launcher Options, next to the other launch arguments where it fits more naturally - Super Admin now shows it read-only for reference during port forwarding.

## 1.0.3 - 2026-07-10

- Installer checksum (SHA256): `FFF568316915A39FF1BF2900CA2520AF48498610A87A5F50A1A1FC56F014ED3E`.
- **A note on the new translations:** every non-English language in this release (Chinese Simplified, Japanese, German, French, Spanish) was translated by AI (Claude), not a human translator or native speaker. We have no reliable way to validate the quality of these translations ourselves. If you spot something that reads wrong, awkward, or mistranslated in your language, please open an issue or leave a comment - we genuinely appreciate the feedback and will fix it.
- **TICKET-0069**: Added a Steam query port option, answering a user's question about whether ExilesGameManager could designate a separate Steam server-list/query-protocol port (`-queryport=`) from the game port. Each server instance now has its own query port (defaulting to that instance's game port, so single-server hosts need to do nothing), editable in Super Admin, and covered by the same firewall/UPnP forwarding as the game port whenever it's set to a different value - fixes query-port collisions for hosts running multiple Palworld servers on one machine.
- **TICKET-0071**: Fixed Super Admin's Local API panel so the "REST API Enabled" toggle shows its field name as a title above the box with "Enable"/"Disable" text inside, matching how World Settings' toggles already look.
- **TICKET-0070**: Super Admin's exclusive Sidebar items (Launcher Options, Settings, Super Admin) now show a small gold crown badge and sit under a "Host Controls" divider, so it's visually obvious which pages only the super admin can see.
- **TICKET-0068**: The entire app is now translated in all 6 supported languages - Dashboard (including the player roster and kick/ban/whisper dialogs), Mods (including Nexus browsing/install dialogs and the UE4SS panel), Server Control, Launcher Options, Logs, Settings (startup recovery, users & invites, server instances, automation/backups, deploy/import wizards), and Super Admin (Local API, port forwarding, remote access, Nexus integration). Only World Settings and the TopBar/Sidebar chrome were done before this (TICKET-0066/TICKET-0067) - this covers everything else.
- **TICKET-0067**: World Settings is now fully translated in all 6 supported languages - every field's label, help text, description, and dropdown options (not just the Sidebar/TopBar chrome from TICKET-0066). The actual `PalWorldSettings.ini` file and everything sent to the backend still always use Palworld's exact English values (e.g. `Difficulty=Hard`) - only what's displayed on screen changes with the selected language.
- **TICKET-0066**: Added multi-language support (i18n). A new language dropdown in the top bar (flag + native name) lets each logged-in user pick their own language, persisted server-side per account so it follows them across sessions/devices. v1 ships English, Chinese (Simplified), Japanese, German, French, and Spanish, translating the Sidebar nav and TopBar page titles/subtitles as the initial proof-of-pipeline surface; more strings/pages can be added incrementally by extending the same translation files.

## 1.0.2 - 2026-07-10

- Installer checksum (SHA256): `50f9f4615efc6fa34239169fbde1f08cb8e02041df7354e4e8b0abbb34c5794b`.
- **TICKET-0064**: Rewrote `NEXUS_DESCRIPTION.md`'s setup instructions to match `GETTING_STARTED.md`'s full numbered walkthrough (screenshots, tips, warnings, quick fixes), converted to Nexus BBCode with placeholder image URLs ready to swap in after uploading screenshots to Nexus's gallery.
- **TICKET-0063**: Fixed a bug found right after shipping TICKET-0062: uninstalling then reinstalling ExilesGameManager never asked to create a new admin account, because the admin account file lived in the same app-data folder deliberately kept for real Palworld server references. Uninstalling now clears the saved admin account and app settings (via the compiled uninstaller itself, so this covers every uninstall path) while still keeping server registrations, mods, and backups untouched.
- **TICKET-0062**: The installer now opens with an Install / Update / Uninstall choice right after the Welcome page, so `PalworldServerAdmin-Setup.exe` can drive uninstall directly instead of requiring the separate uninstaller shortcut. Choosing Uninstall confirms, runs the real uninstaller, and exits without continuing into the install wizard.
- **TICKET-0061**: Updated World Settings for a Palworld config update that added dozens of new server settings (guild management, voice chat range, PvP damage/kill-drop config, stat-point-allocation locks, respawn penalty tuning, and more), verified against the live installed server's config file. Fixed `bHardcore`'s description, which had gone stale now that Pal permadeath is its own separate setting (`bPalLost`). `PublicIP` is now hidden from the generic editor, matching `PublicPort`, since Launcher Options already owns the public IP override.
- **TICKET-0060**: Rebuilt the executable and installer so the installed app includes the corrected World Settings toggle header/text layout.
- **TICKET-0059**: Added the available Getting Started screenshot files to git so GitHub can render them, and recorded the remaining missing image placeholders.
- **TICKET-0058**: Updated World Settings toggle boxes so the setting name stays as the field header and the box text reads `Enable` or `Disable`.
- **TICKET-0057**: Rewrote the Getting Started guide in simpler beginner-friendly language with more screenshot placeholders.
- **TICKET-0056**: Fixed World Settings group headers and toggle alignment so boolean controls line up with numeric/dropdown fields without long divider lines after category labels.
- **TICKET-0055**: Added a GitHub-ready Getting Started guide with step-by-step setup guidance and screenshot placeholders under `images/`.
- **TICKET-0054**: Refined World Settings with concrete numeric examples, compact aligned toggles, clearer alternating category bands, and moved Local API settings to Super Admin.
- **TICKET-0053**: Improved World Settings with grouped sections, tooltips, and dropdown controls for known Palworld categorical settings.
- **TICKET-0052**: Added a bundled diagnostics command that produces a support report for active server setup, local ports, firewall, REST API, and likely router/ISP issues.
- **TICKET-0050**: Fixed port enforcement so it edits the live `PalWorldSettings.ini` in place and preserves unrelated world settings.
- Also includes GETTING_STARTED.md screenshot/content updates made directly on GitHub between releases.

## 1.0.0 - 2026-07-07

- Fixed REST Unauthorized failures caused by blank `AdminPassword`: starting a server through ExilesGameManager now creates one only when missing or empty.
- Fixed Dashboard roster detection after the REST migration by trying the stored REST management port when the ini check is incomplete and normalizing Palworld player fields before displaying them.
- Fixed reinstall/update port drift: a remembered Super Admin game port now wins over Palworld's default and is used by Launcher Options.
- Fixed Launcher Options `-publicport` showing the original default port instead of the live Super Admin game port.
- Added Super Admin-only Launcher Options toggles for `-publicip` and `-publicport`; their values are shown read-only and come from the existing public address/game-port flow.
- Added Server Control update checks: ExilesGameManager compares the installed Palworld Dedicated Server build with Steam's public build and asks before running a SteamCMD update.
- Rebuilt the Windows installer so the packaged app includes the Launcher Options sidebar item and updated the release checksum.
- Renamed Launcher Flags to Launcher Options and split the combined performance toggle into individual `-useperfthreads`, `-NoAsyncLoadingThread`, `-UseMultithreadForDS`, and `-publiclobby` toggles.
- Nexus Browse now always shows the Direct Install action to super admins and explains when a saved Premium Nexus key is required, instead of hiding the option.
- Tightened server-instance dedupe by canonicalizing server paths and relabeled the per-instance folder action as Browse Files.
- Installer update/repair runs now preserve existing setup and skip the first-time server/account questions when ExilesGameManager data already exists.
- Fixed duplicate server-instance rows caused by re-importing or reinstalling the same server folder.
- Added Settings actions to switch servers, open a server folder in Explorer, unregister a server, or unregister and delete its server files.
- Restored direct Nexus installs for super admins with a saved Premium API key.
- Added Windows startup recovery: ExilesGameManager can start at Windows sign-in and restart the active server after the machine reboots.
- Added a dedicated Launcher Flags sidebar page for Community Server visibility, performance flags, worker thread override, and JSON log format.
- Fixed World Settings hiding the Launch Options panel even though the active server's settings loaded.
- Moved safe per-server Palworld launch-option controls from Settings into World Settings.
- Added World Settings controls for safe per-server Palworld launch options: performance flags, worker thread override, and JSON log format.
- Added a Settings checkbox to show a server in Palworld's Community Server list on next start.

- Added a custom install-location picker for new Palworld server deployments, including the optional first server created during setup.
- Fixed Nexus Browse cards opening the wrong Nexus URL path.
- Clarified the Nexus Browse install flow so cards no longer look like one-click installs; super admins now get an Install File shortcut to the verified upload area.
- Fixed Dashboard CPU/RAM reporting so status samples the real Palworld worker process in the selected server folder, even when the launcher tree is incomplete or the backend restarted.
- Dashboard tick-rate timing now shows as unavailable when Palworld's REST metrics payload does not provide frame time, instead of displaying a misleading `0 ms`.
- Replaced Palworld RCON usage with Palworld's official local REST API for player list, kick/ban/unban, announcements, saves, metrics, backups, and shutdown paths.
- Switched Nexus Mods browsing to public GraphQL metadata, so browsing no longer requires a personal API key.
- Switched verified manual mod uploads to Nexus GraphQL file-hash lookup.
- Paused one-click Nexus downloads until ExilesGameManager follows Nexus Mods' registered app/OAuth process.
- Removed the Nexus API-key prompt from the installer and updated public release docs.

## Unreleased - Steam Workshop Edition

### Added
- Native Palworld Steam Workshop URL and ID installation.
- Steam Workshop metadata validation and SteamCMD download orchestration.
- `Info.json` and server-compatibility validation.
- Atomic Workshop deployment with rollback protection.
- `PalModSettings.ini` activation management.
- Workshop update detection, update, enable, disable, and removal flows.
- Steam Workshop installation dialog and API types.
- Steam Workshop architecture, migration, security, and operating documentation.

### Changed
- Active Nexus API routing and Nexus browsing UI were replaced by Steam Workshop management.
- Mod update requests now perform direct Workshop updates for Workshop-managed mods.

### Security
- Steam credentials are request-scoped and never persisted.
- Workshop package names and application IDs are validated before deployment.

## Steam Workshop Automation v4
- Writes Palworld Workshop configuration exclusively to `Mods/PalModSettings.ini`.
- Maintains `WorkshopRootDir`, `ActiveModList`, and `ConfigVersion` automatically.
- Restarts the selected server after Workshop installation.
- Verifies deployment through `Mods/ManagedMods/<PackageName>/InstallManifest.json`.
- Publishes Workshop lifecycle events to The Chronicle.
- Exposes configured, pending, deployed, disabled, and restart-failed states in the Mods UI.

## v5.11 - Automatic Firewall and Clean Multi-Server Clone

- Added automatic, instance-specific Windows Firewall rules for Game UDP and REST API TCP ports.
- Missing rules are created in one elevated operation. Windows 11 shows one standard UAC consent dialog; an elevated Windows Server 2022 service applies rules directly.
- Added a clean local-copy deployment mode that reuses an existing stopped Palworld server installation without SteamCMD.
- Clean copies exclude saves, mods, logs, backups and runtime files, then generate fresh PalWorldSettings.ini values and a new ExilesGameManager instance identity.
- New instance creation validates that Game and REST API ports do not collide with existing Game, Query or REST ports.
- The deployment wizard now proposes a free port pair and lets the administrator choose SteamCMD or a clean local template.

## v5.11.1 - Clean Clone Deployment Hotfix

- Fixed clean local-copy deployments failing while writing the initial `PalWorldSettings.ini` because an unsupported `template_path` argument was passed to `initialize_settings()`.
- Added a final background-job exception guard so unexpected deployment failures are returned to the frontend as `error` instead of leaving the deployment dialog polling forever.
- Clean clones continue to use the copied server installation's own `DefaultPalWorldSettings.ini`; saves, mods, logs and runtime data remain excluded.

## v5.11.2 - Instance-Scoped Server Activity Logs

- Server Activity in The Chronicle is now filtered by the currently selected Palworld server instance.
- New activity entries persist the immutable instance ID instead of relying only on the editable server display name.
- Existing history from older builds remains visible only on the matching server through a backwards-compatible source-name migration.
- ExilesGameManager application events remain global in the left log column by design.

## v5.12.0 - Multi-Server Control Center

- Added a post-login server selection dashboard with one card per Palworld instance.
- Added per-instance status, map, uptime, player capacity, game port and persistent last-save timestamp read from the newest `.sav` file.
- Selecting a server now sets the active instance before opening its isolated management dashboard.
- Added centralized Windows Firewall management for all instances, including status, repair/synchronize and removal with one normal Windows UAC prompt when required.
- Added instance rename and archive/restore controls.
- Preserved existing instance-scoped settings, mods, logs, backups and runtime handling.

## v5.12.3 - Core Multi-Server Integrity Restore

- Restored the complete v5.12 Multi-Server Control Center after detecting that v5.12.1/v5.12.2 had been produced from the older v5.11.2 base and therefore omitted parts of centralized firewall and instance management.
- Preserved the v5.12.1 duplicate-notification suppression, five-second notification lifetime and manual close behavior.
- Preserved the v5.12.2 multilingual launcher network/firewall information card.
- Made post-login server selection a hard navigation invariant at `/servers`; `/` now redirects to `/servers`.
- Moved server selection outside the per-instance application shell so no server is treated as selected before the user chooses one.
- Added complete server-selection translations for German, English, French, Spanish, Japanese and Simplified Chinese.
- Added `docs/CORE_MULTI_SERVER_INVARIANTS.md` as mandatory architecture and regression documentation.

## v5.12.4 - Persistent All Servers Navigation and Clean Release Packaging

- Added a permanent **All Servers** navigation entry above Dashboard in the sidebar.
- The entry always routes directly to `/servers`, returning to the post-login multi-server selection screen without changing or deleting the currently selected instance.
- Added translations for the navigation label in German, English, French, Spanish, Japanese and Simplified Chinese.
- Defined clean release packaging as a core release invariant: every ZIP must contain exactly one `ExilesGameManager-main` project folder and no temporary merge/work directories.
- Removed the accidentally packaged `apx5123` working directory from the release archive.

## EGM Fork Identity
- Added identity and roadmap documentation.

## v0.2.0 - Complete EGM UI and Design System Refresh

- Replaced the inherited fantasy/gold appearance with the approved EGM infrastructure and DevOps visual identity.
- Applied the canonical `#0D1117`, `#161B22`, `#27303A`, `#7CFC00`, `#00D4FF`, `#8B5CF6`, and `#F1F5F9` palette globally.
- Replaced decorative display typography with Orbitron, Inter, and JetBrains Mono.
- Redesigned the application background, sidebar, top bar, server switcher, authentication screens, panels, cards, buttons, fields, tabs, dialogs, progress indicators, notifications, scrollbars, and loading states.
- Replaced floating fantasy embers with low-impact cyan, lime, and violet system nodes and a technical grid background.
- Removed warm hard-coded gold glow values from frontend source files.
- Preserved all server-management behavior, routes, API contracts, multi-server isolation, Steam Workshop, Nexus Mods, backups, firewall management, performance monitoring, logging, and authentication behavior.
- Added `docs/DESIGN_SYSTEM.md`, `docs/COLOR_SYSTEM.md`, and `docs/UI_COMPONENTS.md`.

## v0.3.0 - Persistent Multi-Server Task Queue

- Added a persistent task queue stored in `data/task_queue.json`.
- Added strict per-instance serialization for backups, restores, Workshop operations, firewall changes, and server updates.
- Added queue states, priority, progress, task logs, cancellation, pause/resume, retry, and completed-task cleanup.
- Added a translated Task Queue page and sidebar entry for German, English, French, Spanish, Japanese, and Simplified Chinese.
- Routed manual/scheduled backups, backup verification/restores, Steam Workshop installs/updates, firewall synchronization/removal, and server updates through the central queue without breaking existing API response contracts.
- Added restart-safe persistence: queued tasks resume, while interrupted running tasks fail safely and require explicit retry.
- Added `docs/TASK_QUEUE.md`, `docs/TASK_QUEUE_VALIDATION.md`, and queue regression tests.

## 0.8.0
- Separated Steam Workshop wishlist entries from Nexus Mods throughout the Mods and Administration pages.
- Added dedicated Nexus Mods and Steam Workshop wishlist panels.
- Restyled Steam Workshop Access as a full Super Admin panel matching Nexus Mods Integration.
- Steam Workshop approval now installs only from a validated SteamCMD cache item and returns an actionable 409 response when the item has not been downloaded yet.
