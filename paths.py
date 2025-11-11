# paths.py
import sys
from pathlib import Path

def app_dir() -> Path:
    # Folder of the EXE when frozen, else folder of this file
    return Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent

def data_path(filename: str) -> Path:
    return app_dir() / filename
