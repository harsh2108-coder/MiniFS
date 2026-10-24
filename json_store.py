"""Saving and loading the file system as a JSON file (no database needed)."""
import json
import os

from models.vfs import VirtualFileSystem, FSError


class JsonStore:
    def __init__(self, path):
        self.path = path

    def save(self, fs, path=None):
        target = path or self.path
        tmp = target + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(fs.to_dict(), f, indent=2)
            os.replace(tmp, target)            # safe save: never leaves a half-written file
        except OSError as err:
            raise FSError(f"Could not save file: {err}")

    def load(self, path=None):
        """Return a VirtualFileSystem, or None if there is no (valid) save file."""
        target = path or self.path
        if not os.path.exists(target):
            return None
        try:
            with open(target, "r", encoding="utf-8") as f:
                return VirtualFileSystem.from_dict(json.load(f))
        except (OSError, ValueError, FSError):
            try:                               # keep a backup of the broken file
                os.replace(target, target + ".corrupt.bak")
            except OSError:
                pass
            return None

    def import_from(self, path):
        """Like load(), but raises a clear error for the user."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return VirtualFileSystem.from_dict(json.load(f))
        except (OSError, ValueError) as err:
            raise FSError(f"Import failed: {err}")
