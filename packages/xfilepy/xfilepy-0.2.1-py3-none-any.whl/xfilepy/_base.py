from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Self


class _BaseFileHandler(ABC):
    """Cross-platform, file handler using native pickers and security models.

    This class has overloads for creating file handlers via native file pickers
    and saving/loading persistent access grants. Supported platforms are
    Android, iOS, and Desktop (Windows, macOS, Linux). On all platforms you
    can choose files outside your app's sandbox using the native file picker
    without asking the user for broad filesystem permissions. Access to the
    chosen files is mediated by platform-specific security models (e.g., SAF on
    Android, security-scoped bookmarks on iOS). This allows your app to write
    to the files later without re-prompting the user, even across app restarts.

    Notes:
        - Methods that accept callbacks may be **asynchronous** depending on
          the platform. Do not assume the callback is invoked immediately.
        - The concrete class exported as ``xfile.FileHandler`` is selected at
          import time based on the runtime platform.
    """

    @classmethod
    @abstractmethod
    def from_uri_string(cls, uri_string: str, require_write: bool = False) -> Self:
        """Create an instance from a previously persisted URI/bookmark string.

        The string is the value returned by :meth:`to_uri_string` on a prior run.
        Implementations should validate that the underlying grant/bookmark is
        still valid and (optionally) writable.

        Args:
            uri_string: Opaque string that identifies and authorizes access to
                a previously chosen file (e.g. Android content URI, iOS
                security-scoped bookmark, or desktop file path).
            require_write: If ``True``, the instance must have write access; if
                not possible, an exception should be raised.

        Returns:
            A platform-specific :class:`_BaseFileHandler` instance.

        Raises:
            ValueError: If ``uri_string`` is empty or malformed.
            RuntimeError: If the persisted grant/bookmark does not exist or
                does not meet the requested access level.
        """

    @classmethod
    @abstractmethod
    def create_via_picker(
        cls,
        on_ready: Callable[[Self], None],
        start_at: str | None = None,
    ) -> Self | None:
        """Open a native “Open File” picker and return a handler for the choice.

        This presents the system file chooser. After the user selects a file,
        ``on_ready`` is called with a ready-to-use handler for that file.

        Args:
            on_ready: Callback receiving the created handler. The callback may be
                invoked asynchronously depending on platform. It is **not**
                called if the user cancels.
            start_at: Optional platform-specific starting location (directory
                path or URI). Implementations may ignore this if unsupported.

        Returns:
            The in-construction handler or ``None``. Do not rely on this being
            ready; use ``on_ready`` instead.
        """

    @classmethod
    @abstractmethod
    def create_via_multi_picker(
        cls,
        on_ready_many: Callable[[list[Self]], None],
        start_at: str | None = None,
    ) -> Self | None:
        """Open a native picker allowing multiple file selections.

        After selection, ``on_ready_many`` is called with one handler per file.
        If the user cancels or selects nothing, the callback is not invoked.

        Args:
            on_ready_many: Callback receiving a non-empty list of handlers.
            start_at: Optional hint for the initial directory/URI.

        Returns:
            The in-construction handler or ``None``. Do not rely on this being
            ready; use ``on_ready`` instead.
        """

    @classmethod
    @abstractmethod
    def create_via_save_dialog(
        cls,
        on_ready: Callable[[Self], None],
        default_name: str = "untitled.bin",
        start_at: str | None = None,
    ) -> Self | None:
        """Open a native “Save As” dialog and return a handler to the new file.

        The created file is empty unless the caller writes to it. Once the user
        confirms the destination, ``on_ready`` is invoked with a handler you can
        write bytes to immediately.

        Args:
            on_ready: Callback receiving the created handler. Not called if the
                user cancels.
            default_name: Suggested filename shown in the dialog.
            start_at: Optional hint for initial directory/URI.

        Returns:
            The in-construction handler or ``None``. Do not rely on this being
            ready; use ``on_ready`` instead.
        """

    @abstractmethod
    def to_uri_string(self) -> str | None:
        """Return a persistable identifier for this file, if available.

        The returned string can be stored (e.g., in app settings) and later
        passed to :meth:`from_uri_string` to rehydrate the handler with the same
        permissions.

        Returns:
            Opaque string suitable for persistence, or ``None`` if the handler
            cannot produce one (e.g., no file selected yet).
        """

    @abstractmethod
    def has_access(self, require_write: bool = False) -> bool:
        """Report whether the current handler has valid access to the file.

        Args:
            require_write: If ``True``, also require write permission.

        Returns:
            ``True`` if access (and optionally write) is currently available,
            ``False`` otherwise.
        """

    @abstractmethod
    def write_bytes(self, data: bytes) -> None:
        """Overwrite the file with the given bytes.

        This replaces the entire file contents with ``data``.

        Args:
            data: Bytes to write.

        Raises:
            RuntimeError: If the write fails on the underlying platform or if
                write access is not granted.
        """

    @abstractmethod
    def append_bytes(self, data: bytes) -> None:
        """Append bytes to the end of the file.

        Implementations may fall back to read-modify-write if true append mode
        is not supported by the platform.

        Args:
            data: Bytes to append.

        Raises:
            RuntimeError: If the append fails or write access is not granted.
        """

    @abstractmethod
    def read_bytes(self, callback: Callable[[bytes], None]) -> None:
        """Read the entire file into memory and pass it to ``callback``.

        The callback may be invoked asynchronously depending on platform. The
        method itself does not return the bytes to avoid blocking or copying
        twice in some implementations.

        Args:
            callback: Function that receives the file contents as ``bytes``.

        Raises:
            RuntimeError: If reading fails or access is not granted.
        """

    def __init_subclass__(cls, **kwargs):
        """Ensure subclasses inherit a docstring if they don't define one.

        Copies the first available base-class docstring into ``cls.__doc__``
        if the subclass does not set its own, keeping documentation consistent
        across platform-specific implementations.
        """
        super().__init_subclass__(**kwargs)
        if cls.__doc__ in (None, ""):
            for b in cls.__mro__[1:]:
                if getattr(b, "__doc__", None):
                    cls.__doc__ = b.__doc__
                    break
