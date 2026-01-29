# xfilepy

---

Cross-platform, file handler using native pickers and security models.

Provides overloads for creating file handlers via native file pickers and
saving/loading persistent access grants. Supported platforms are Android, iOS,
and Desktop (Windows, macOS, Linux). On all platforms you can choose files
outside your app's sandbox using the native file picker without asking the user
for broad filesystem permissions. Access to the chosen files is mediated by
platform-specific security models (e.g., SAF on Android, security-scoped
bookmarks on iOS). This allows your app to write to the files later without
re-prompting the user, even across app restarts.

Design goals:  
- zero side effects at import
- late binding to the active platform
- no runtime deps for platforms you don’t use.

## Usage

See [API Documentation](https://xfile-fb4acf.gitlab.io/) for full
details. Here is a brief example:

```python
from xfilepy import FileHandler

# Open via native picker
FileHandler.create_via_picker(lambda fh: fh.read_bytes(lambda b: print(len(b))))

# Save via native "Save as…"
fh = FileHandler.create_via_save_dialog(lambda fh: fh.write_bytes(b"hello"))

# Serialize back to store in your settings
persist = fh.to_uri_string()

# Rehydrate a previously granted URI/bookmark
fh = FileHandler.from_uri_string(persist, require_write=True)
fh.append_bytes(b"!\n")
```
