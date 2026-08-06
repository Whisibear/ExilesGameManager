# Exiles Game Manager — Terms of Service and Local Privacy Notice

**Effective date:** 6 August 2026  
**Applies to:** Exiles Game Manager (EGM), including its Windows application, local web interface, installer, updater and public source code.

## 1. Scope and acceptance

By installing, running, copying, modifying or distributing EGM, you agree to these terms. If you do not agree, do not use EGM.

EGM is a self-hosted administration tool. It is not a hosted cloud service operated by the project maintainer. The software normally runs on the user's own Windows computer or Windows server and serves its interface from the local EGM backend.

These terms supplement the project license, third-party notices and the separate terms of any external service used through EGM. Mandatory consumer rights and other rights that cannot legally be excluded remain unaffected.

## 2. Project operator and no hosted EGM account service

The public project is maintained under the name **Whisibear** through the Exiles Game Manager GitHub repository.

The project maintainer does **not** operate a central EGM backend, user-account database, telemetry collector, advertising network or analytics service. EGM usernames, password hashes, server configurations, saves, backups, logs, uploaded mod archives, OAuth credentials and session records are not automatically transmitted to the project maintainer.

If a user voluntarily sends a diagnostic package, log, screenshot, issue report or other file to the maintainer or another support recipient, that disclosure is initiated and controlled by the user. Diagnostic redaction is a best-effort safeguard and must not be treated as a guarantee that every user-specific value has been removed. Users should inspect files before sharing them.

## 3. Local host operator responsibilities

The person or organization that installs and operates an EGM instance is the **host operator**. Where other people receive accounts or otherwise use that instance, the host operator controls that local processing and is responsible for:

- deciding who may access EGM and which role they receive;
- protecting the Windows host, EGM port, reverse proxy, firewall and administrator credentials;
- providing any legally required privacy information to invited users;
- choosing lawful retention periods and deleting data when it is no longer needed;
- obtaining authorization before managing a server, user account, file, mod or network configuration;
- complying with applicable employment, hosting, consumer, privacy and communications laws.

The project maintainer does not become the controller or processor of data stored only on a user's or host operator's computer merely because EGM software is used.

## 4. Data stored locally

Depending on the features used, EGM may store or process the following data on the host computer:

- local EGM usernames, roles, language preferences, invitation records and password-verification data;
- salted PBKDF2 password hashes; plaintext EGM passwords are not stored;
- managed-server names, paths, ports, configuration, launcher options and operational state;
- Palworld server files, saves, backups, mod files, uploaded archives and installation manifests;
- task history, activity entries, notifications, performance samples and local application logs;
- update metadata, downloaded installers, checksums and updater logs;
- Nexus Mods account metadata and OAuth tokens when the user connects Nexus Mods;
- SteamCMD process output and locally generated Workshop metadata;
- cached public metadata from third-party services;
- diagnostic packages created locally at the host operator's request.

Installed EGM application data is primarily stored below `%LOCALAPPDATA%\ExilesGameManager`. Managed dedicated-server files may be stored in locations selected by the host operator and may also use `%ProgramData%\ExilesGameManager` or other configured paths. Development-mode storage may use the project's local `data` directory.

Nexus OAuth tokens are stored locally using Windows Data Protection API protection for the current Windows user. They are not included in public source exports, release metadata or normal diagnostic packages. On non-Windows development environments, the DPAPI protection mechanism is unavailable; production distribution is intended for Windows.

## 5. Sessions, cookies and browser storage

EGM uses only functional storage required to operate the local interface. EGM does not use advertising or cross-site tracking cookies.

### 5.1 Authentication cookie

After login, EGM sets a local HTTP-only authentication cookie. The cookie:

- identifies the current local EGM session;
- is unavailable to normal browser JavaScript because it is `HttpOnly`;
- uses `SameSite=Lax`;
- is scoped to the EGM application path;
- has a maximum age of 30 days;
- is marked `Secure` when EGM is accessed through HTTPS;
- corresponds to a random server-side token held only in application memory.

Server-side session tokens are not persisted to disk. Restarting the EGM backend invalidates them even if a browser still temporarily retains the now-useless cookie. Logout removes the cookie and server-side session. Removing an invited user invalidates that user's active sessions.

### 5.2 Local storage

The browser's local storage is used for functional preferences such as the selected interface language and local EGM University completion-display state. These values stay in that browser profile until removed by the user or browser.

### 5.3 Session storage

The browser's session storage is used for short-lived interface state, including explicit language selection during login/setup and temporary dashboard-navigation state. It is normally discarded when the browser tab or session ends.

### 5.4 Cache

The browser may cache EGM frontend assets. EGM also maintains local application cache, download, temporary and update directories. Cached files are used for operation, updates and third-party metadata and are not used for advertising or user profiling.

## 6. Network connections and third-party recipients

EGM does not send application data to a Whisibear-operated server. It does make direct connections from the host computer to third parties when required by enabled features. Those providers receive normal network information such as the requesting public IP address, time, TLS connection metadata and user agent, and may receive the specific request data described below.

### 6.1 GitHub

EGM contacts GitHub to check the configured Exiles Game Manager release repository, retrieve release metadata and download update installers and checksum files. The updater verifies the published SHA-256 checksum before installation. Opening release or repository links is a direct browser visit to GitHub.

### 6.2 Nexus Mods

When Nexus functionality is used, EGM may contact Nexus Mods to:

- browse public mod metadata;
- authenticate through OAuth 2.0 Authorization Code with PKCE;
- exchange or refresh OAuth tokens;
- read connected-account and Premium status information;
- retrieve mod and file metadata;
- obtain Premium-gated download links;
- download selected files;
- submit the MD5 hash of a manually selected mod archive for catalog matching.

The manually selected archive itself is staged locally; the hash-lookup feature sends the archive's MD5 digest, not the complete archive, for catalog matching. Nexus Mods' own terms, privacy policy, rate limits, Premium restrictions, age/content restrictions and API acceptable-use rules apply independently.

### 6.3 Steam and SteamCMD

EGM may contact Valve/Steam services to download SteamCMD, install or update the Palworld dedicated server, browse Steam Workshop metadata, download Workshop items and compare build identifiers. When the host operator chooses authenticated SteamCMD access, credentials and Steam Guard codes are passed to the local SteamCMD process through standard input for that live process and are not intentionally persisted by EGM.

Valve's and Steam's terms and privacy rules apply independently.

### 6.4 Public-IP lookup

When EGM's public-IP or remote-access feature is requested, EGM may query `api.ipify.org`, `ifconfig.me` or `icanhazip.com`. Those services necessarily receive the host's public IP address as part of the network request. The returned address is used to show the operator connection information.

### 6.5 Microsoft and prerequisite downloads

Installation or prerequisite scripts may download the Microsoft Visual C++ Redistributable from Microsoft and SteamCMD from Valve's official distribution endpoint.

### 6.6 External links

Links to GitHub, Nexus Mods, Steam Community or PayPal open those third-party sites only when the user activates the relevant link or feature. Their own cookies, terms and privacy policies apply after navigation.

## 7. No telemetry, analytics or advertising

The reviewed stable release contains no EGM-operated telemetry endpoint, analytics SDK, advertising SDK or automatic crash-report upload. Runtime logging and diagnostics are written locally. EGM does not sell user data and does not use local data for behavioral advertising.

The frontend does not load Google Fonts or another remote font service. It uses fonts already available on the host operating system, preventing an otherwise automatic font-provider request during every interface load.

## 8. Remote access and security

EGM is designed primarily for self-hosted administration. Exposing EGM beyond localhost can permit remote users to perform powerful actions, including starting processes, changing server files, installing mods, controlling firewall rules and managing accounts.

The host operator must not expose EGM directly to the public internet without appropriate protection. Recommended controls include:

- HTTPS through a correctly configured reverse proxy or a trusted VPN;
- strong unique passwords and restricted invitation codes;
- firewall restrictions and least-privilege network access;
- timely operating-system, EGM and dependency updates;
- backups before updates, restores, mod installations or destructive actions;
- review of logs and account access;
- disabling remote access when it is not required.

A plain HTTP connection does not provide transport encryption. The `Secure` cookie attribute can only protect HTTPS sessions. EGM cannot protect credentials from an already compromised host, browser, administrator account or reverse proxy.

## 9. Mods, servers and third-party content

EGM does not grant ownership of games, mods, server files or third-party content. Users must have all permissions and licenses required to download, install, modify, host or redistribute content.

Mod compatibility, safety, legality and quality are controlled by their respective authors and distribution platforms. EGM's archive validation, hash comparison and path-safety checks reduce certain technical risks but do not prove that a mod is safe, lawful, compatible or free of malicious behavior.

The project is not affiliated with, endorsed by or sponsored by Pocketpair, Valve, Steam, Nexus Mods, GitHub, Microsoft or PayPal unless expressly stated by the relevant party.

## 10. Updates and software changes

EGM may check GitHub for newer releases. An update is installed only after the user initiates or approves the update flow. EGM downloads the installer, verifies the available SHA-256 file, executes the local update worker and installer, and records the result locally.

Updates may change features, dependencies, file formats or these terms. The applicable terms are those distributed with the installed release. Material changes should be documented in the public changelog.

## 11. Deletion, retention and uninstall

Local data remains under the control of the host operator. Retention depends on local settings and operator actions.

- Logout invalidates the active local session.
- Disconnecting Nexus Mods deletes EGM's locally stored Nexus OAuth record.
- Cache, downloads, logs, diagnostics and backups can be removed locally, subject to filesystem permissions and operational requirements.
- The uninstaller offers a choice to preserve or remove EGM application data under LocalAppData.
- Dedicated-server folders, saves, backups or mods stored outside EGM's application-data directory may require separate manual deletion.
- Browser cookies, local storage, session storage and cached assets can be cleared through the browser.

Users should back up important saves and configurations before deleting application data.

## 12. Acceptable use

Users must not use EGM to:

- access or administer systems without authorization;
- violate intellectual-property, privacy, computer-misuse or communications laws;
- distribute malware or intentionally harmful content;
- bypass third-party access controls, subscriptions, rate limits or platform restrictions;
- expose another person's credentials, tokens, private server data or personal information;
- misrepresent EGM as an official product of a third-party platform.

## 13. Availability, warranties and liability

EGM is provided under its project license and on an "as is" and "as available" basis, to the extent permitted by law. Server administration, updates, firewall changes, backups, restores and mod installation can cause downtime or data loss. Users are responsible for testing, backups and recovery plans.

No provision excludes liability or rights that cannot legally be excluded. Subject to mandatory law, the project maintainers are not responsible for indirect or consequential loss, third-party service outages, mod behavior, game updates, server incompatibilities, user configuration errors or unauthorized exposure caused by the host operator's deployment.

## 14. Third-party terms

Use of external services is governed by their current terms and policies, including where applicable:

- GitHub Terms and Privacy Statement;
- Nexus Mods Terms of Service, Privacy Policy and API Acceptable Use Policy;
- Steam Subscriber Agreement, Steam Privacy Policy and applicable Steam/Steamworks rules;
- Microsoft terms for downloaded runtime components;
- PayPal terms and privacy policy when the support link is used.

EGM cannot modify or waive third-party terms. If an EGM feature conflicts with a third-party rule, the host operator must stop using that feature until compliance is restored.

## 15. Changes and severability

These terms may be updated with future releases. If one provision is invalid or unenforceable, the remaining provisions continue to apply to the extent permitted by law.

## 16. Contact and issue reporting

Technical issues, security reports and questions about the public project should be submitted through the Exiles Game Manager GitHub repository. Do not include passwords, OAuth tokens, Steam Guard codes, private saves or unredacted personal data in public issues.

## 17. Reference framework

This document is designed to describe EGM's actual local processing and third-party connections. It is not individualized legal advice. Host operators with employees, customers, public users or internet-facing deployments should obtain advice appropriate to their jurisdiction and use case.

Relevant official reference material includes Regulation (EU) 2016/679 (GDPR), Directive 2002/58/EC as amended, and the current policies published by the third-party services listed above.
