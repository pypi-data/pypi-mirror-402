from __future__ import annotations

import base64
import os
import tempfile
from collections.abc import Callable
from typing import Self

from kivy.clock import Clock  # ty: ignore[unresolved-import]
from pyobjus import autoclass, objc_str, protocol  # ty: ignore[unresolved-import]

from ._base import _BaseFileHandler

# Keep delegates alive while presented (UIKit delegates are weak)
_KEEPALIVE: list[tuple[object, object]] = []

NSURL = autoclass("NSURL")
NSData = autoclass("NSData")
NSArray = autoclass("NSArray")
UIApplication = autoclass("UIApplication")
UIDocumentPickerViewController = autoclass("UIDocumentPickerViewController")
UIDocumentPickerModeOpen = 1
UIDocumentPickerModeExportToService = 2  # legacy initializer fallback


# --- scene-safe presenting VC helper ---
def _presenting_controller():  # noqa: PLR0912
    app = UIApplication.sharedApplication()
    window = None

    scenes = getattr(app, "connectedScenes", None)
    if scenes:
        arr = scenes.allObjects() if hasattr(scenes, "allObjects") else scenes
        if arr:
            for i in range(arr.count()):
                scene = arr.objectAtIndex_(i)
                if hasattr(scene, "activationState") and scene.activationState() == 0:
                    ws = getattr(scene, "windows", None)
                    ws = ws() if callable(ws) else ws
                    if ws and ws.count() > 0:
                        for j in range(ws.count()):
                            w = ws.objectAtIndex_(j)
                            if hasattr(w, "isKeyWindow") and w.isKeyWindow():
                                window = w
                                break
                if window:
                    break

    if not window:
        kw = getattr(app, "keyWindow", None)
        window = kw() if callable(kw) else kw

    if not window:
        ws = getattr(app, "windows", None)
        ws = ws() if callable(ws) else ws
        if ws and ws.count() > 0:
            window = ws.objectAtIndex_(0)

    if not window:
        raise RuntimeError("Unable to find a UIWindow to present from.")

    vc = window.rootViewController()
    while vc.presentedViewController():
        vc = vc.presentedViewController()
    return vc


def _export_async(urls_array, *, completion=None):
    """Present native Save As sheet (export flow)."""
    vc = _presenting_controller()

    picker = UIDocumentPickerViewController.alloc()
    if picker.respondsToSelector_("initForExportingURLs:asCopy_"):
        picker = picker.initForExportingURLs_asCopy_(urls_array, True)
    elif urls_array and urls_array.count() > 0:
        single_url = urls_array.objectAtIndex_(0)
        picker = picker.initWithURL_inMode_(
            single_url, UIDocumentPickerModeExportToService
        )
    else:
        raise RuntimeError("Need at least one URL to export")

    delegate = _DocPickerDelegate(picker, completion)
    picker.setDelegate_(delegate)
    _KEEPALIVE.append((picker, delegate))
    vc.presentViewController_animated_completion_(picker, True, None)


class _DocPickerDelegate:
    def __init__(self, picker, completion):
        self.picker = picker
        self.completion = completion

    @protocol("UIDocumentPickerDelegate")
    def documentPicker_didPickDocumentsAtURLs_(self, picker, urls):  # noqa: N802
        self._finish(urls)

    @protocol("UIDocumentPickerDelegate")
    def documentPickerWasCancelled_(self, picker):  # noqa: N802
        self._finish(None)

    def _finish(self, urls):
        try:
            if self.picker:
                self.picker.dismissViewControllerAnimated_completion_(True, None)
        finally:
            try:
                _KEEPALIVE.remove((self.picker, self))
            except ValueError:
                pass
        if self.completion:
            Clock.schedule_once(lambda *_: self.completion(urls), 0)


def _pick_async(types, *, start_at=None, multiple=False, completion=None):
    vc = _presenting_controller()
    picker = UIDocumentPickerViewController.alloc().initWithDocumentTypes_inMode_(
        types, UIDocumentPickerModeOpen
    )

    try:
        if picker.respondsToSelector_("setAllowsMultipleSelection:"):
            picker.setAllowsMultipleSelection_(bool(multiple))
    except Exception:
        pass

    try:
        if start_at and picker.respondsToSelector_("setDirectoryURL:"):
            start_url = NSURL.fileURLWithPath_(objc_str(start_at))
            if start_url:
                picker.setDirectoryURL_(start_url)
    except Exception:
        pass

    delegate = _DocPickerDelegate(picker, completion)
    picker.setDelegate_(delegate)
    _KEEPALIVE.append((picker, delegate))
    vc.presentViewController_animated_completion_(picker, True, None)


class FileHandler(_BaseFileHandler):
    def __init__(self) -> None:
        self._bookmark_b64: str | None = None
        self._url = None
        self._path: str | None = None
        self._accessing = False

    # ---- constructors ----
    @classmethod
    def from_uri_string(cls, uri_string: str, require_write: bool = False) -> Self:
        inst = cls()
        inst._restore(uri_string)
        if not inst.has_access(require_write=require_write):
            raise RuntimeError("Bookmark invalid or not accessible.")
        return inst

    @classmethod
    def create_via_picker(
        cls, on_ready: Callable[[Self], None], *, start_at=None
    ) -> None:
        def _done(urls):
            if urls and urls.count() > 0:
                url = urls.objectAtIndex_(0)
                inst = cls()
                inst._set_from_url(url)
                on_ready(inst)

        _pick_async(
            [objc_str("public.data")],
            start_at=start_at,
            multiple=False,
            completion=_done,
        )

    @classmethod
    def create_via_multi_picker(
        cls, on_ready_many: Callable[[list[Self]], None], *, start_at=None
    ) -> None:
        def _done(urls):
            handlers: list[Self] = []
            if urls and urls.count() > 0:
                for i in range(urls.count()):
                    inst = cls()
                    inst._set_from_url(urls.objectAtIndex_(i))
                    handlers.append(inst)
            if handlers:
                on_ready_many(handlers)

        _pick_async(
            [objc_str("public.data")],
            start_at=start_at,
            multiple=True,
            completion=_done,
        )

    @classmethod
    def create_via_save_dialog(
        cls,
        on_ready: Callable[[Self], None],
        default_name: str = "untitled.bin",
        *,
        start_at: str | None = None,
    ) -> None:
        fd, tmp_path = tempfile.mkstemp(prefix="saveas_", suffix="")
        os.close(fd)
        dir_ = os.path.dirname(tmp_path)
        desired = os.path.join(dir_, default_name)
        os.replace(tmp_path, desired)
        tmp_path = desired
        open(tmp_path, "wb").close()

        tmp_url = NSURL.fileURLWithPath_(objc_str(tmp_path))
        urls_array = NSArray.arrayWithObject_(tmp_url)

        def _done(urls):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
            if not urls or urls.count() == 0:
                return
            dest_url = urls.objectAtIndex_(0)
            inst = cls()
            inst._set_from_url(dest_url)
            on_ready(inst)

        _export_async(urls_array, completion=_done)

    # ---- public API ----
    def to_uri_string(self) -> str | None:
        return self._bookmark_b64

    def has_access(self, require_write: bool = False) -> bool:
        if not self._path or not os.path.isfile(self._path):
            return False
        if not os.access(self._path, os.R_OK):
            return False
        if require_write and not os.access(self._path, os.W_OK):
            return False
        return True

    # BYTES API
    def read_bytes(self, callback):
        self._begin()
        try:
            with open(self._path, "rb") as f:
                callback(f.read())
        finally:
            self._end()

    def write_bytes(self, data: bytes) -> None:
        self._begin()
        try:
            with open(self._path, "wb") as f:
                f.write(data)
        finally:
            self._end()

    def append_bytes(self, data: bytes) -> None:
        self._begin()
        try:
            with open(self._path, "ab") as f:
                f.write(data)
        finally:
            self._end()

    # ---- internals ----
    def _set_from_url(self, url) -> None:
        opts_create_sec = 1 << 11  # NSURLBookmarkCreationWithSecurityScope
        bookmark = url.bookmarkDataWithOptions_includingResourceValuesForKeys_relativeToURL_error_(  # noqa: E501
            opts_create_sec, None, None, None
        )
        if not bookmark:
            raise RuntimeError("Bookmark creation failed.")
        py = bytes(bookmark.bytes().get_bytes(bookmark.length()))
        self._bookmark_b64 = base64.b64encode(py).decode("ascii")
        self._resolve(bookmark)

    def _restore(self, b64: str) -> None:
        raw = base64.b64decode(b64)
        nsd = NSData.dataWithBytes_length_(raw, len(raw))
        self._bookmark_b64 = b64
        self._resolve(nsd)

    def _resolve(self, nsdata) -> None:
        opts_resolve_sec = 1 << 10  # NSURLBookmarkResolutionWithSecurityScope
        url = NSURL.URLByResolvingBookmarkData_options_relativeToURL_bookmarkDataIsStale_error_(  # noqa: E501
            nsdata, opts_resolve_sec, None, None, None
        )
        if url is None:
            raise RuntimeError("Bookmark resolve failed.")
        self._url = url
        self._path = str(url.path())

    def _begin(self) -> None:
        if self._url and not self._accessing:
            self._accessing = bool(self._url.startAccessingSecurityScopedResource())

    def _end(self) -> None:
        if self._url and self._accessing:
            self._url.stopAccessingSecurityScopedResource()
            self._accessing = False
