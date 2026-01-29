try:
    from kivy.utils import platform as _kivy_platform  # ty: ignore[unresolved-import]
except Exception:
    _kivy_platform = None


def current_platform() -> str:
    """Return one of: "android", "ios", "desktop".

    Falls back to "desktop" if Kivy isn't importable.
    """
    if _kivy_platform in ("android", "ios"):
        return str(_kivy_platform)
    return "desktop"
