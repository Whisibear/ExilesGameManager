"""Compatibility entry point for pre-multi-game installations."""

from EGM_Server import configure_windows_event_loop, main

__all__ = ["configure_windows_event_loop", "main"]


if __name__ == "__main__":
    main()
