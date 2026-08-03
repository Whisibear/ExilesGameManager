import asyncio
import sys

import uvicorn

from app.services import runtime_logging


def configure_windows_event_loop() -> None:
    # Modern Python versions select the appropriate Windows event loop by
    # default. Keeping this hook avoids launcher/API changes without invoking
    # the deprecated asyncio policy APIs removed in Python 3.16.
    return None


if __name__ == "__main__":
    runtime_logging.install_console_capture()
    sys.excepthook = runtime_logging.log_unhandled_exception
    configure_windows_event_loop()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        access_log=True,
    )
