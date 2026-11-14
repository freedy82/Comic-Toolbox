"""Initialize paths and streams before a frozen entry point imports the app."""

import os
import sys
from pathlib import Path


# Portable settings, bookmarks and relative downloads stay beside the EXE.
# Bundled resources resolve separately through their modules' __file__ paths
# inside _internal, including when a shortcut starts from another directory.
# Both launchers share _internal as their bundle directory, including the
# browser helper whose executable is itself located inside that directory.
os.chdir(Path(sys._MEIPASS).resolve().parent)

# Windowed executables have no Python console streams. Libraries may still
# print diagnostics; keep that safe without touching the browser's real pipes.
for name in ("stdout", "stderr"):
    if getattr(sys, name) is None:
        setattr(sys, name, open(os.devnull, "w", encoding="utf-8"))
