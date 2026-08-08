import sys

import uvicorn

from app.services import runtime_logging


def configure_windows_event_loop() -> None:
    return None


def main() -> None:
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


if __name__ == "__main__":
    main()
