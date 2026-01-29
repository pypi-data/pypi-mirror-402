from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from typing import Self

import crossfiledialog

from ._base import _BaseFileHandler


def _norm_dir(s: str | None) -> str | None:
    if not s:
        return None
    abs_path = Path(s).absolute()
    abs_dir = abs_path if abs_path.is_dir() else abs_path.parent
    return str(abs_dir) if abs_dir.is_dir() else None


class FileHandler(_BaseFileHandler):
    def __init__(self, path: str | None = None):
        self._path = Path(path).absolute() if path else None

    # ---- constructors ----
    @classmethod
    def from_uri_string(cls, uri_string: str, require_write: bool = False) -> Self:
        if not uri_string:
            raise ValueError("uri_string is empty or None.")
        inst = cls(uri_string)
        if not inst.has_access(require_write=require_write):
            raise RuntimeError("Path not accessible with requested permissions.")
        return inst

    @classmethod
    def create_via_picker(
        cls, on_ready: Callable[[Self], None], *, start_at=None
    ) -> Self | None:
        try:
            path = crossfiledialog.open_file(start_dir=_norm_dir(start_at))
        except Exception as e:
            print("File open dialog failed:", e)
            path = None
        inst = cls(path if path else None)
        if inst._path:
            on_ready(inst)
        return inst

    @classmethod
    def create_via_multi_picker(
        cls, on_ready_many: Callable[[list[Self]], None], *, start_at=None
    ) -> None:
        paths = crossfiledialog.open_multiple(start_dir=_norm_dir(start_at))
        handlers = [cls(p) for p in paths] if paths else []
        if handlers:
            on_ready_many(handlers)

    @classmethod
    def create_via_save_dialog(
        cls,
        on_ready: Callable[[Self], None],
        default_name: str = "untitled.bin",
        *,
        start_at=None,
    ) -> Self | None:
        path = crossfiledialog.save_file(start_dir=_norm_dir(start_at))
        inst = cls(path if path else None)
        if inst._path:
            if not inst._path.exists():
                inst._path.open("wb").close()
            on_ready(inst)
        return inst

    # ---- public API ----
    def to_uri_string(self) -> str | None:
        return str(self._path) if self._path else None

    def has_access(self, require_write: bool = False) -> bool:
        if not self._path or not self._path.is_file():
            return False
        if not os.access(self._path, os.R_OK):
            return False
        if require_write and not os.access(self._path, os.W_OK):
            return False
        return True

    # BYTES API
    def read_bytes(self, callback: Callable[[bytes], None]) -> None:
        self._ensure_path_for_read()
        assert isinstance(self._path, Path)
        callback(self._path.read_bytes())

    def write_bytes(self, data: bytes) -> None:
        self._ensure_path_for_write()
        assert isinstance(self._path, Path)
        self._path.write_bytes(data)

    def append_bytes(self, data: bytes) -> None:
        self._ensure_path_for_write()
        assert isinstance(self._path, Path)
        with self._path.open("ab") as f:
            f.write(data)

    # ---- internals ----
    def _ensure_path_for_read(self) -> None:
        if self._path and self._path.is_file():
            return
        path = crossfiledialog.open_file()
        if not path:
            raise RuntimeError("No file selected.")
        self._path = Path(path).absolute()

    def _ensure_path_for_write(self) -> None:
        if self._path and self._path.exists():
            if not os.access(self._path, os.W_OK):
                raise PermissionError(f"File not writable: {self._path}")
            return
        path = crossfiledialog.save_file()
        if not path:
            raise RuntimeError("No file chosen for saving.")
        self._path = Path(path).absolute()
