"""Windows subprocess helpers for packaged GUI builds.

Child console programs such as netsh, cmd.exe, PowerShell, and SteamCMD must
not create visible terminal windows when ExilesGameManager is built with the
Windows GUI bootloader. Interactive tools explicitly opened by the user keep
their own console and do not use these helpers.
"""

from __future__ import annotations

import os
import subprocess
from typing import Any


def hidden_process_kwargs() -> dict[str, Any]:
    if os.name != "nt":
        return {}

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE

    return {
        "creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0),
        "startupinfo": startupinfo,
    }
