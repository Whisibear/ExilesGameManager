
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
