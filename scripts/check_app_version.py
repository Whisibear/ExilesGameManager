"""Fail when packaging and runtime application versions drift apart."""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.version import APP_VERSION  # noqa: E402

installer = (ROOT / "installer.iss").read_text(encoding="utf-8")
match = re.search(r'^#define MyAppVersion "([^"]+)"', installer, re.MULTILINE)
if not match:
    raise SystemExit("installer.iss does not declare MyAppVersion")
if match.group(1) != APP_VERSION:
    raise SystemExit(f"Version mismatch: runtime={APP_VERSION}, installer={match.group(1)}")
print(f"Version sources agree: {APP_VERSION}")


version_info = (ROOT / "version_info.txt").read_text(encoding="utf-8-sig")
revision_match = re.search(r"filevers=\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)", version_info)
if not revision_match:
    raise SystemExit("version_info.txt does not declare filevers")

semver_match = re.fullmatch(
    r"(\d+)\.(\d+)\.(\d+)(?:-(?:alpha|beta|rc)\.(\d+))?",
    APP_VERSION,
)
if not semver_match:
    raise SystemExit(f"Unsupported application version: {APP_VERSION}")

expected_windows = tuple(
    int(value or 0)
    for value in semver_match.groups()
)
actual_windows = tuple(int(value) for value in revision_match.groups())
if actual_windows != expected_windows:
    raise SystemExit(
        f"Windows version mismatch: expected={expected_windows}, actual={actual_windows}"
    )

manifest = (ROOT / "ExilesGameManager.manifest").read_text(encoding="utf-8")
if 'requestedExecutionLevel level="asInvoker"' not in manifest:
    raise SystemExit("ExilesGameManager.manifest must use asInvoker")
if "<longPathAware" not in manifest or ">true</longPathAware>" not in manifest:
    raise SystemExit("ExilesGameManager.manifest must enable longPathAware")

print(f"Windows metadata agrees: {actual_windows}")


def extract_version_string(text: str, key: str) -> str:
    pattern = rf"StringStruct\(u'{re.escape(key)}', u'([^']*)'\)"
    found = re.search(pattern, text)
    if not found:
        raise SystemExit(f"version_info.txt does not declare {key}")
    return found.group(1)


company_name = extract_version_string(version_info, "CompanyName")
product_name = extract_version_string(version_info, "ProductName")
product_version = extract_version_string(version_info, "ProductVersion")

if company_name != "Whisibear":
    raise SystemExit(
        f"CompanyName mismatch: expected=Whisibear, actual={company_name}"
    )
if product_name != "Exiles Game Manager":
    raise SystemExit(
        "ProductName mismatch: expected=Exiles Game Manager, "
        f"actual={product_name}"
    )
if product_version != APP_VERSION:
    raise SystemExit(
        f"ProductVersion mismatch: expected={APP_VERSION}, actual={product_version}"
    )

one_click_path = ROOT / "scripts" / "EGM_One_Click_Release.ps1"
if one_click_path.is_file():
    one_click = one_click_path.read_text(encoding="utf-8-sig")

    obsolete_company_template = (
        "StringStruct(u'CompanyName', u'Whisibear " + "EGM')"
    )
    obsolete_copyright_template = (
        "Copyright (c) 2026 Whisibear " + "EGM"
    )
    for forbidden in (
        obsolete_company_template,
        obsolete_copyright_template,
    ):
        if forbidden in one_click:
            raise SystemExit(
                "One-Click metadata template contains obsolete value: "
                f"{forbidden}"
            )

    required_template_values = (
        "StringStruct(u'CompanyName', u'Whisibear')",
        "StringStruct(u'ProductName', u'Exiles Game Manager')",
        "StringStruct(u'ProductVersion', u'$Version')",
    )
    for required in required_template_values:
        if required not in one_click:
            raise SystemExit(
                f"One-Click metadata template is missing: {required}"
            )

    print("Internal One-Click metadata template agrees.")
else:
    print(
        "Internal One-Click metadata template check skipped "
        "for minimal public source export."
    )

worker_source = (
    ROOT / "update_worker" / "EGMUpdateWorker.cs"
).read_text(encoding="utf-8-sig")

worker_checks = {
    'AssemblyCompany("Whisibear")': "UpdateWorker CompanyName",
    'AssemblyProduct("Exiles Game Manager")': "UpdateWorker ProductName",
    f'AssemblyInformationalVersion("{APP_VERSION}")': "UpdateWorker ProductVersion",
}
for expected, label in worker_checks.items():
    if expected not in worker_source:
        raise SystemExit(f"{label} is not synchronized: {expected}")

print(
    "Executable metadata agrees: "
    f"CompanyName={company_name}, ProductName={product_name}, "
    f"ProductVersion={product_version}"
)
