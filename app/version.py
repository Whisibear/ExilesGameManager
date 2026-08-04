
"""Authoritative runtime and release-channel configuration for EGM."""
from __future__ import annotations
import os
APP_VERSION = "0.8.1-beta.2"
APP_CHANNEL = os.getenv("EGM_UPDATE_CHANNEL", "beta").strip().lower() or "beta"
GITHUB_REPOSITORY = os.getenv("EGM_GITHUB_REPOSITORY", "Whisibear/ExilesGameManager").strip().strip("/")
GITHUB_API_VERSION = "2022-11-28"
UPDATE_CHECK_SECONDS = 5 * 60
