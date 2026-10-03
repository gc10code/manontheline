"""Filesystem locations that work both from source and from a PyInstaller bundle."""

import os
import sys


def resource_path(*parts: str) -> str:
    """Path to a bundled resource (PyInstaller unpacks data into sys._MEIPASS)."""
    base = getattr(sys, "_MEIPASS", None) or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)


def data_dir() -> str:
    """Per-user folder for the save file and custom word lists."""
    override = os.environ.get("MOTL_HOME")
    if override:
        return override
    if os.name == "nt":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return os.path.join(base, "manontheline")


def save_path() -> str:
    return os.path.join(data_dir(), "save.json")


def custom_words_dir() -> str:
    return os.path.join(data_dir(), "words")
