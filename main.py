"""
main.py
-------
ThermoConvert Pro – application entry point.

Run:
    python main.py

Author  : Yoga Prabu
Project : PRODIGY_SD_01 – ThermoConvert Pro
"""

import sys
import os

# ── Dependency check ─────────────────────────────────────────────────
def check_dependencies() -> None:
    """Warn if optional packages are missing; never crash on import."""
    try:
        import customtkinter  # noqa: F401
    except ImportError:
        print(
            "[INFO] customtkinter not found – running in standard tkinter mode.\n"
            "       Install it for an enhanced look:  pip install customtkinter"
        )

# ── Bootstrap ────────────────────────────────────────────────────────
def main() -> None:
    check_dependencies()

    from ui import ThermoConvertApp

    app = ThermoConvertApp()

    # Centre window on screen
    app.update_idletasks()
    w = app.winfo_width()
    h = app.winfo_height()
    sw = app.winfo_screenwidth()
    sh = app.winfo_screenheight()
    app.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    app.mainloop()


if __name__ == "__main__":
    main()
