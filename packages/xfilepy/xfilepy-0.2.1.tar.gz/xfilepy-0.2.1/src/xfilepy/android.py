from collections.abc import Callable
from typing import Self

# -------------------- ANDROID (Kivy + pyjnius, SAF) --------------------
from android import activity  # type: ignore[import]
from jnius import autoclass  # type: ignore[import]

from ._base import _BaseFileHandler

INITIAL_URI_MIN_SDK = 26  # Android 8.0 (O)

PythonActivity = autoclass("org.kivy.android.PythonActivity")
Intent = autoclass("android.content.Intent")
Activity = autoclass("android.app.Activity")
UriCls = autoclass("android.net.Uri")
DocumentsContract = autoclass("android.provider.DocumentsContract")
BuildVERSION = autoclass("android.os.Build$VERSION")
BufferedInputStream = autoclass("java.io.BufferedInputStream")
ByteArrayOutputStream = autoclass("java.io.ByteArrayOutputStream")
BufferedOutputStream = autoclass("java.io.BufferedOutputStream")


class FileHandler(_BaseFileHandler):
    _router_bound = False
    _next_req = 14000
    _instances: dict[int, "FileHandler"] = {}

    @classmethod
    def _bind_router_once(cls) -> None:
        if not cls._router_bound:
            activity.bind(on_activity_result=cls._router)
            cls._router_bound = True

    @classmethod
    def _router(cls, request_code, result_code, data):  # Android callback signature
        inst = cls._instances.get(int(request_code))
        if inst:
            inst._on_activity_result(request_code, result_code, data)

    def __init__(self) -> None:
        self._uri = None
        self._pending: list[Callable[[], None]] = []
        self._picking = False
        self._req = FileHandler._next_req
        FileHandler._next_req += 1
        FileHandler._instances[self._req] = self
        FileHandler._bind_router_once()
        self._multi_ready_cb: Callable[[list[Self]], None] | None = None

    # ---- constructors ----
    @classmethod
    def from_uri_string(cls, uri_string: str, require_write: bool = False) -> Self:
        inst = cls()
        ok, msg = inst._set_existing_persisted_uri(
            uri_string, require_write=require_write
        )
        if not ok:
            raise RuntimeError(f"URI not usable: {msg}")
        return inst

    @classmethod
    def create_via_picker(
        cls, on_ready: Callable[[Self], None], start_at: str | None = None
    ) -> Self:
        inst = cls()
        inst._pending.append(lambda: on_ready(inst))
        inst._start_picker_open(start_at=start_at, multiple=False)
        return inst

    @classmethod
    def create_via_multi_picker(
        cls,
        on_ready_many: Callable[[list[Self]], None],
        start_at: str | None = None,
    ) -> Self:
        inst = cls()
        inst._multi_ready_cb = on_ready_many
        inst._start_picker_open(start_at=start_at, multiple=True)
        return inst

    @classmethod
    def create_via_save_dialog(
        cls,
        on_ready: Callable[[Self], None],
        default_name: str = "untitled.bin",
        start_at: str | None = None,
    ) -> Self:
        inst = cls()
        inst._pending.append(lambda: on_ready(inst))
        inst._start_picker_create(default_name, "application/octet-stream", start_at)
        return inst

    # ---- public API ----
    def to_uri_string(self) -> str | None:
        return self._uri.toString() if self._uri else None

    def has_access(self, require_write: bool = False) -> bool:
        if not self._uri:
            return False
        has, _can_r, can_w = self._has_persisted_grant(self._uri)
        return has and (not require_write or can_w)

    # BYTES API
    def write_bytes(self, data: bytes) -> None:
        self._ensure_then(lambda: self._write_bytes(data))

    def append_bytes(self, data: bytes) -> None:
        self._ensure_then(lambda: self._append_bytes(data))

    def read_bytes(self, callback: Callable[[bytes], None]) -> None:
        self._ensure_then(lambda: callback(self._read_bytes()))

    # ---- flow helpers ----
    def _ensure_then(self, fn: Callable[[], None]) -> None:
        if self.has_access():
            try:
                fn()
            except Exception as e:  # pragma: no cover - android only
                print("action failed:", e)
            return
        self._pending.append(fn)
        if not self._picking and self._uri is None and self._multi_ready_cb is None:
            self._start_picker_open()

    def _maybe_set_initial_uri(self, intent, start_at: str | None) -> None:
        try:
            if start_at and BuildVERSION.SDK_INT >= INITIAL_URI_MIN_SDK:
                uri = UriCls.parse(start_at)
                if uri is not None and "content" == uri.getScheme():
                    intent.putExtra(DocumentsContract.EXTRA_INITIAL_URI, uri)
        except Exception as e:  # pragma: no cover
            print("Ignored start_at:", e)

    def _start_picker_open(
        self, start_at: str | None = None, *, multiple: bool = False
    ) -> None:
        if self._picking:
            return
        self._picking = True
        intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
        intent.addCategory(Intent.CATEGORY_OPENABLE)
        intent.setType("*/*")
        intent.addFlags(
            Intent.FLAG_GRANT_READ_URI_PERMISSION
            | Intent.FLAG_GRANT_WRITE_URI_PERMISSION
            | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION
        )
        if multiple:
            intent.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, True)
        self._maybe_set_initial_uri(intent, start_at)
        PythonActivity.mActivity.startActivityForResult(intent, self._req)

    def _start_picker_create(
        self, default_name: str, mime_type: str, start_at: str | None = None
    ) -> None:
        if self._picking:
            return
        self._picking = True
        intent = Intent(Intent.ACTION_CREATE_DOCUMENT)
        intent.addCategory(Intent.CATEGORY_OPENABLE)
        intent.setType(mime_type)
        intent.putExtra(Intent.EXTRA_TITLE, default_name)
        intent.addFlags(
            Intent.FLAG_GRANT_READ_URI_PERMISSION
            | Intent.FLAG_GRANT_WRITE_URI_PERMISSION
            | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION
        )
        self._maybe_set_initial_uri(intent, start_at)
        PythonActivity.mActivity.startActivityForResult(intent, self._req)

    def _on_activity_result(self, request_code, result_code, data) -> None:
        try:
            if result_code == Activity.RESULT_OK and data is not None:
                clip = data.getClipData()
                if self._multi_ready_cb and clip is not None:
                    uris = []
                    for i in range(clip.getItemCount()):
                        uri = clip.getItemAt(i).getUri()
                        self._take_persistable_grant(uri)
                        uris.append(uri)
                    handlers = []
                    for u in uris:
                        h = FileHandler()
                        h._uri = u
                        handlers.append(h)
                    cb = self._multi_ready_cb
                    self._multi_ready_cb = None
                    cb(handlers)
                else:
                    uri = data.getData()
                    self._take_persistable_grant(uri)
                    self._uri = uri
                    todo = list(self._pending)
                    self._pending.clear()
                    for fn in todo:
                        try:
                            fn()
                        except Exception as e:  # pragma: no cover
                            print("pending failed:", e)
            else:
                self._pending.clear()
        finally:
            self._picking = False

    # ---- I/O (bytes) ----
    def _read_bytes(self) -> bytes:
        cr = PythonActivity.mActivity.getContentResolver()
        inp = cr.openInputStream(self._uri)
        bis = BufferedInputStream(inp)
        baos = ByteArrayOutputStream()
        buf = bytearray(8192)
        while True:
            n = bis.read(buf)
            if n == -1:
                break
            baos.write(buf, 0, n)
        bis.close()
        inp.close()
        out = bytes(baos.toByteArray().tostring())
        baos.close()
        return out

    def _write_bytes(self, data: bytes) -> None:
        cr = PythonActivity.mActivity.getContentResolver()
        out = cr.openOutputStream(self._uri, "w")
        bos = BufferedOutputStream(out)
        bos.write(data)
        bos.flush()
        bos.close()
        out.close()

    def _append_bytes(self, data: bytes) -> None:
        cr = PythonActivity.mActivity.getContentResolver()
        try:
            out = cr.openOutputStream(self._uri, "wa")
            bos = BufferedOutputStream(out)
            bos.write(data)
            bos.flush()
            bos.close()
            out.close()
        except Exception:
            current = self._read_bytes()
            self._write_bytes(current + data)

    # ---- permission helpers ----
    def _take_persistable_grant(self, uri) -> None:
        cr = PythonActivity.mActivity.getContentResolver()
        flags = (
            Intent.FLAG_GRANT_READ_URI_PERMISSION
            | Intent.FLAG_GRANT_WRITE_URI_PERMISSION
        )
        cr.takePersistableUriPermission(uri, flags)

    def _has_persisted_grant(self, uri):
        cr = PythonActivity.mActivity.getContentResolver()
        perms = cr.getPersistedUriPermissions()
        for i in range(perms.size()):
            p = perms.get(i)
            if uri == p.getUri():
                return True, p.isReadPermission(), p.isWritePermission()
        return False, False, False

    def _set_existing_persisted_uri(self, uri_string: str, require_write: bool = False):
        try:
            uri = UriCls.parse(uri_string)
        except Exception as e:
            return False, f"Invalid URI: {e}"
        if uri is None or uri.getScheme() != "content":
            return False, "URI must be content://"
        has, _can_r, can_w = self._has_persisted_grant(uri)
        if not has:
            return False, "No persisted grant for this URI."
        if require_write and not can_w:
            return False, "Persisted grant is read-only."
        self._uri = uri
        return True, "OK"
