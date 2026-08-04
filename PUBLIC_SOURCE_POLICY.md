# Public Source Scope

The public repository contains the application source and reproducible build configuration required to review, build, and validate Exiles Game Manager.

Public scope:

- Backend application source under `app/`
- Frontend source under `web/src/` and `web/public/`
- Nexus Mods integration, including metadata retrieval, authentication/session handling, mod browsing, preview images, download handoff, installation, and update handling
- Runtime and installer entry points
- Dependency lock files and build configuration
- Public documentation, licensing, security policy, support tooling, and GitHub Actions validation
- `scripts/check_app_version.py` as the only public build-validation script

Excluded scope:

- `.claude/`
- `tickets/`
- `tests/`
- internal documentation and development notes
- local release and GitHub publishing scripts
- logs, diagnostics, backups, saves, installed mods, caches, virtual environments, build output, and runtime data
- credentials, API keys, OAuth secrets, tokens, passwords, and user-specific configuration

Release binaries are distributed exclusively through GitHub Releases as installer, portable archive, and SHA-256 checksum assets. They are not committed to the source tree.

## Media, wiki and publishing

- Public screenshots use `EGM-*` filenames with hyphens and no spaces or special characters.
- `images/branding/` is retained as the canonical branding directory.
- Legacy AutoPalExpress wiki content is excluded.
- GitHub publishing must verify that local `HEAD` equals remote `origin/main`.

## GitHub mirror synchronization

- The local GitHub directory is a disposable publication mirror, not a development source.
- Before each publication it is reset to `origin/main` and cleaned.
- Stale rebases and merges are aborted automatically.
- `images/EGM-Thumbnail.png` is explicitly excluded as obsolete.

## Generated release output

- `C:\EGM\EGM-Releases` is generated output and never a development source.
- Previous Setup executables, portable ZIPs, source ZIPs and checksum files are removed before each One-Click build.
- `C:\EGM\EGM-Releases\GitHub-Source` is deleted completely and rebuilt from the current public allowlist.
## Nexus OAuth secrets

- The public client ID and callback URI are part of the source code.
- EGM uses OAuth 2.0 Authorization Code with PKCE and does not embed a reusable client secret.
- Access and refresh tokens are encrypted locally with Windows DPAPI.
- OAuth token files, runtime configuration and diagnostic data are excluded from the public source export.

