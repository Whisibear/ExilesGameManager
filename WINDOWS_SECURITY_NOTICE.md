# Windows Security, SmartScreen and Antivirus Notice

## Why Windows may display a warning

Exiles Game Manager is distributed as a Windows desktop application and installer. A newly published or infrequently downloaded executable can trigger Microsoft Defender SmartScreen, Microsoft Defender Antivirus or another security product even when no malicious behavior is intended.

Typical reasons include:

- the executable is new and has little reputation data;
- the build is unsigned or is signed with a certificate that has not yet accumulated reputation;
- PyInstaller-packaged Python applications are sometimes classified heuristically;
- the installer starts services, manages processes, writes application files, configures Windows Firewall rules or downloads server tools;
- the automatic updater downloads and starts a replacement Setup executable.

A warning is not proof that a file is safe, and it is not proof that a file is malicious. Users should verify the exact release asset before running it.

## How to verify an official release

1. Download EGM only from the official GitHub repository and its Releases page.
2. Confirm that the release tag and filename match the version shown in EGM.
3. Compare the Setup SHA-256 hash with the published `.sha256.txt` file or `CHECKSUMS.sha256`.
4. Do not run a file whose checksum differs.
5. Inspect the public source and GitHub Actions workflow when independent verification is required.

PowerShell verification:

```powershell
Get-FileHash .\ExilesGameManager-Setup-v0.8.1-beta.7.exe -Algorithm SHA256
```

The resulting hash must exactly match the hash published with that release.

## What users should not do

- Do not disable Microsoft Defender or another antivirus product globally.
- Do not create broad permanent exclusions for Downloads, the entire system drive or the user profile.
- Do not ignore a warning when the file came from an unofficial mirror, message attachment or unknown website.
- Do not bypass a checksum mismatch.

## False-positive reports

When a verified official release is detected, users may submit the file to their security vendor as a possible false positive. Reports should include:

- the exact EGM version;
- the exact filename;
- the SHA-256 hash;
- the detection name;
- the antivirus product and engine version;
- the official GitHub release URL.

Do not publish private logs, OAuth tokens, passwords, server saves or complete user-data directories with a report.

## Application behavior relevant to security software

Depending on the selected features, EGM may:

- start and stop dedicated-server processes;
- download SteamCMD, server files, mods, UE4SS and verified EGM updates;
- create or inspect Windows Firewall rules;
- bind a local web interface to a configured address and port;
- create backups, logs, caches and configuration files;
- start a detached UpdateWorker and verified Setup executable during automatic updates.

These actions are documented because they can resemble administrative behavior used by both legitimate management tools and malware. EGM does not use a Whisibear-operated telemetry, advertising, analytics or remote-command service.

## Reporting a security issue

Security vulnerabilities should be reported according to `SECURITY.md`. Do not post exploitable details, credentials or private diagnostic archives in a public issue.
