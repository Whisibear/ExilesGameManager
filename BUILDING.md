# Building Exiles Game Manager

This repository contains the reviewable source code for Exiles Game Manager.

## Requirements

- Windows 10 or Windows 11 (64-bit)
- Python 3.12 or newer
- Node.js with npm
- Inno Setup 6 for the Windows Setup executable
- Git

## Backend development setup

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Run the development backend:

```powershell
.\.venv\Scripts\python.exe EGM_Server.py
```

## Frontend development setup

```powershell
cd web
npm ci
npm run build
```

The production frontend is generated in `web/dist` and embedded into the packaged application during the release build.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest
```

## Windows executable and Setup

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\build_installer.ps1
```

The build process uses `ExilesGameManager.spec` for PyInstaller and `installer.iss` for Inno Setup.

## Runtime data

Runtime data, user accounts, logs, SteamCMD files, server instances, saves, API credentials and generated build outputs are intentionally excluded from source control.

## Phase E.11 tray packaging contract

The frozen Windows build depends on `pystray` and Pillow. `ExilesGameManager.spec` must bundle the application icon and the Windows pystray backend. Release smoke tests set `EGM_SUPPRESS_BROWSER=1` and `EGM_SUPPRESS_TRAY=1` so automated packaging validation has no interactive side effects. The packaged process exposes the per-session named event `Local\ExilesGameManager.Quit`; Setup uses it for graceful Update/Repair/Uninstall shutdown before an EGM-only fallback.
