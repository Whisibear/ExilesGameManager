# Exiles Game Manager v0.8.1 Public Beta 6

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

## Native UpdateWorker path hotfix

### Native UpdateWorker path hotfix

- Fixed the Windows error `The file '\\' was not found` during panel updates.
- Replaced all path-bearing UpdateWorker command-line arguments with a validated Base64 job file.
- The native worker now starts without path arguments and receives only the job-file location through `EGM_UPDATE_JOB`.
- Installer, restart, marker and log paths are validated both before EGM closes and inside the native worker.
- Setup and EGM restart use direct process creation without Windows shell execution.
- Added fallback diagnostics for errors that occur before the normal worker log can be opened.
- Version remains `0.8.1-beta.6`, allowing replacement of the current release assets.


## Complete UpdateWorker packaging fix

### Complete UpdateWorker packaging fix

- Fixed the GitHub Actions packaging job failing because `dist/EGMUpdateWorker.exe` was not built before Inno Setup.
- GitHub Actions now builds and validates the native UpdateWorker before compiling the installer.
- Added a real UpdateWorker startup smoke test to the Windows packaging job.
- Added PE-file and minimum-size checks for EGM, UpdateWorker and Setup outputs.
- Added CI packaging artifacts for inspection after every packaging smoke run.
- Local One-Click Release now validates the same worker-before-installer contract.
- GitHub source export and publish are blocked when the public CI workflow cannot reproduce the native worker build.
- Version remains `0.8.1-beta.6`; existing GitHub release assets can be replaced after rebuilding.


## Global language selection

## 0.8.1 Public Beta 6

### Global language selection

- Added a language selector to the top-right corner of the login and first-run setup pages.
- Language selection works before authentication, applies immediately and is remembered in the browser.
- The authenticated Topbar selector remains synchronized with the saved user preference.
- Login, setup, loading screen, Sidebar, Topbar, notifications and core navigation labels are validated for all six supported languages.
- Added translated branding and loading text.
- Added automated translation-completeness tests for English, German, French, Spanish, Japanese and Simplified Chinese.
- Updated backend, frontend and installer metadata to `0.8.1-beta.6`.


## Windows Variant 4 hardening

### Windows Variant 4 hardening

- Finalized the free local Windows hardening approach without Azure or a paid certificate.
- Kept the One-Click Release workflow unchanged for the user.
- Standardized PyInstaller on the Onedir layout with `_internal`, the Python runtime DLL and `base_library.zip`.
- Disabled UPX and embedded a modern Windows application manifest.
- EGM now runs as the current user (`asInvoker`) and declares Per-Monitor V2 DPI support, long-path awareness and Segment Heap.
- Standardized Windows metadata to publisher label `Whisibear`, product `Exiles Game Manager` and version `0.8.1-beta.6`.
- Added strict metadata, PE-file, Onedir-runtime and startup validation.
- Added local Microsoft Defender scans for the final application directory, Setup executable and portable ZIP.
- Defender validation never disables protection and never adds exclusions.
- Code signing remains optional for a future trusted certificate but is not required for local Variant-4 releases.


## Complete release metadata flow fix

### Complete release metadata flow fix

- Fixed the One-Click Release source template that restored the obsolete company value during every build.
- Standardized application, UpdateWorker, installer and CI metadata on publisher label `Whisibear`.
- Added semantic ProductVersion metadata to the native UpdateWorker.
- Removed hard-coded Beta 6 version checks from the local installer build and GitHub Actions.
- Future versions are now read dynamically from `app/version.py`.
- Added release-blocking validation for stale or conflicting metadata before packaging.


## Public source manifest export fix

### Public source manifest export fix

- Added `ExilesGameManager.manifest` to the minimal GitHub source export.
- Added the manifest to public-source completeness validation.
- Added the manifest to GitHub publish preflight checks.
- Fixed the final One-Click Release failure during exported-source version validation.


## Public export internal-validation fix

### Public export internal-validation fix

- Fixed exported-source validation when the internal One-Click Release script is intentionally excluded from the public repository.
- `check_app_version.py` now validates the One-Click metadata template only when the internal script exists.
- The minimal GitHub source export remains clean and does not expose internal release automation.
- Full development builds continue to validate the internal One-Click metadata template.

