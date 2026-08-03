"""Opens a native Windows folder picker. The admin backend and its web UI
always run on the same machine, so a server-side dialog is a legitimate
stand-in for a browser folder picker (browsers can't expose real filesystem
paths to a page).

Shown via a short-lived PowerShell subprocess (System.Windows.Forms's
FolderBrowserDialog), not tkinter in-process (TICKET-0131): every caller
invokes this through asyncio.to_thread, so it never runs on the process's
main thread - uvicorn's event loop already owns that. tkinter's Tcl/Tk
runtime isn't safe to initialize outside the main thread, and doing so was
observed to bring down the entire packaged process with a low-level native
crash rather than a normal Python exception. A subprocess has its own real
main thread, sidestepping the problem entirely, and matches this project's
existing pattern of shelling out to PowerShell for other native Windows
integration (firewall.py, diagnostics.py).
"""

import locale
import logging
import subprocess

from app.services.windows_subprocess import hidden_process_kwargs

logger = logging.getLogger("egm.native_dialog")


def _ps_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


_FORCE_FOREGROUND_HELPER = """
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public class ApexForceForeground {
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);
    [DllImport("user32.dll")] public static extern bool AttachThreadInput(uint idAttach, uint idAttachTo, bool fAttach);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("kernel32.dll")] public static extern uint GetCurrentThreadId();
    public static void Force(IntPtr hWnd) {
        uint fgThread = GetWindowThreadProcessId(GetForegroundWindow(), out _);
        uint curThread = GetCurrentThreadId();
        AttachThreadInput(curThread, fgThread, true);
        SetForegroundWindow(hWnd);
        AttachThreadInput(curThread, fgThread, false);
    }
}
'@
"""


def pick_folder(title: str, initial_dir: str | None = None) -> str | None:
    # A window TopMost/Activate() alone isn't enough - Windows deliberately
    # restricts which processes may steal foreground focus, so a dialog
    # raised from a spawned PowerShell process can otherwise open silently
    # behind the browser/app window, looking like clicking Browse did
    # nothing. AttachThreadInput here is the standard workaround: briefly
    # share input state with whatever currently has focus so
    # SetForegroundWindow is actually honored.
    script = (
        "Add-Type -AssemblyName System.Windows.Forms;"
        + _FORCE_FOREGROUND_HELPER
        + "$owner = New-Object System.Windows.Forms.Form;"
        "$owner.TopMost = $true;"
        "$owner.ShowInTaskbar = $false;"
        "$owner.StartPosition = 'CenterScreen';"
        "$owner.Size = New-Object System.Drawing.Size(0, 0);"
        "$owner.Show();"
        "[ApexForceForeground]::Force($owner.Handle);"
        "$d = New-Object System.Windows.Forms.FolderBrowserDialog;"
        f"$d.Description = {_ps_quote(title)};"
    )
    if initial_dir:
        script += f"$d.SelectedPath = {_ps_quote(initial_dir)};"
    script += (
        "if ($d.ShowDialog($owner) -eq [System.Windows.Forms.DialogResult]::OK) {"
        "Write-Output $d.SelectedPath"
        "}"
        "$owner.Close();"
    )

    try:
        # Keep stdout/stderr as bytes. Using text=True makes subprocess use
        # the Windows ANSI code page (commonly cp1252), while PowerShell may
        # emit bytes from a different encoding. On cancel this previously
        # crashed subprocess' background reader thread with UnicodeDecodeError.
        result = subprocess.run(
            ["powershell", "-NoProfile", "-STA", "-Command", script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=300,
            **hidden_process_kwargs(),
        )
    except (OSError, subprocess.TimeoutExpired):
        logger.warning("pick_folder: PowerShell folder picker didn't run")
        return None

    def _decode_output(value: bytes | None) -> str:
        if not value:
            return ""

        # Windows PowerShell commonly writes redirected output as UTF-8, the
        # active OEM/ANSI code page, or UTF-16 LE. Try the deterministic
        # encodings first and always finish with replacement instead of
        # allowing a UI cancellation to raise UnicodeDecodeError.
        encodings = ("utf-8-sig", "utf-16-le", locale.getpreferredencoding(False), "cp850")
        for encoding in encodings:
            if not encoding:
                continue
            try:
                return value.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                continue
        return value.decode("utf-8", errors="replace")

    stderr = _decode_output(result.stderr).strip()
    if result.returncode != 0:
        logger.warning("pick_folder: PowerShell folder picker failed: %s", stderr)
        return None

    # Empty stdout is the normal result when the user clicks Cancel.
    path = _decode_output(result.stdout).strip().strip("\ufeff\x00")
    return path or None
