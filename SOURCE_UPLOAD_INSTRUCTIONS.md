# Safe Source Additions

Extract the contents of this archive directly into:

`C:\EGM\GitHub\ExilesGameManager`

This package deliberately does not contain or overwrite:

- README.md
- CHANGELOG.md
- CREDITS.md
- GETTING_STARTED.md
- LICENSE
- SECURITY.md
- THIRD_PARTY_NOTICES.md
- the existing `.gitignore`
- the `images` directory
- `.github/ISSUE_TEMPLATE`

It adds only the reviewable application source, tests, dependency manifests, build configuration and CI workflow required for source review.

After extraction, append any missing entries from `SOURCE_GITIGNORE_ADDITIONS.txt` to the existing `.gitignore`, then run:

```bash
git status
git add .
git commit -m "Publish Exiles Game Manager source code"
git push
```
