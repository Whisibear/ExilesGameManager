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
