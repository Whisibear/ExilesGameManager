# Exiles Game Manager v0.8.1 Public Beta 5

Public Beta 5 replaces the PowerShell automatic-update handoff with a dedicated `EGMUpdateWorker.exe`. The worker starts the verified Setup, captures its exit code, writes update diagnostics and restarts EGM after a successful update.

## Automatic updater

- Native UpdateWorker instead of PowerShell or CMD handoff scripts
- Bounded wait for the existing EGM process
- Silent Setup execution and installer exit-code validation
- Automatic restart after success and fallback restart after failure
- Worker bootstrap, update and installer logs
- SHA-256 verification remains mandatory before the worker starts

## Defender hardening

- PyInstaller UPX compression disabled
- Optional Authenticode signing for EGM, UpdateWorker and Setup
- One-Click release fails when the UpdateWorker is missing
- Public source and GitHub publish validation include the worker source and build script


# GitHub Beta Release Checklist

1. Confirm the repository configured in `app/version.py`.
2. Run `EGM_One_Click_Release.bat`.
3. Upload the generated Setup executable and its `.sha256.txt` file from `EGM-Releases`.
4. Optionally upload the lean portable Beta ZIP and its SHA256 file.
5. Create a version tag such as `v0.8.0` and mark beta builds as **Pre-release**.
6. Add release notes, known limitations and migration notes.
7. Never upload `.venv`, `node_modules`, Steam credentials, server saves, Workshop caches or diagnostic logs.

The in-app updater selects the newest supported GitHub release and looks for the Setup `.exe` asset automatically.

- Verify all README screenshot previews.
- Verify `images/` contains only `EGM-*` assets and `images/branding/`.
- Verify no legacy AutoPalExpress wiki content remains.
- Verify the publisher reports identical local and remote commit hashes.

- Confirm that `images/EGM-Thumbnail.png` is absent.
- Confirm that the publisher resets the mirror to `origin/main` before synchronization.
- Confirm that no rebase or merge operation remains active after publishing.

- Confirm that all older Setup executables, portable ZIPs and checksum files are removed before the build.
- Confirm that `C:\EGM\EGM-Releases\GitHub-Source` is deleted and recreated.
- Confirm that only artifacts from the current One-Click build remain in `C:\EGM\EGM-Releases`.
