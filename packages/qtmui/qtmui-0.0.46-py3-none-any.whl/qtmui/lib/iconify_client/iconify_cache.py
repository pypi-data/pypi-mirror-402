# iconify_cache.py
from __future__ import annotations

import os
from collections.abc import Iterator, MutableMapping
from contextlib import suppress
from pathlib import Path

_SVG_CACHE: MutableMapping[str, bytes] | None = None

PYCONIFY_CACHE: str = os.environ.get("PYCONIFY_CACHE", "")
CACHE_DISABLED: bool = PYCONIFY_CACHE.lower() in {"0", "false", "no"}


# =================================================================
# GET CACHE DIRECTORY
# =================================================================
def get_cache_directory(app_name: str = "pyconify") -> Path:
    """Return the pyconify svg cache directory."""
    if PYCONIFY_CACHE:
        return Path(PYCONIFY_CACHE).expanduser().resolve()

    if os.name == "posix":
        return Path.home() / ".cache" / app_name
    elif os.name == "nt":
        appdata = os.environ.get("LOCALAPPDATA", "~/AppData/Local")
        return Path(appdata).expanduser() / app_name

    return Path.home() / f".{app_name}"


# =================================================================
# CACHE KEY BUILDER
# =================================================================
DELIM = "_"

def cache_key(args: tuple, kwargs: dict, last_modified: int | str) -> str:
    """
    Build a Windows-safe cache key:
    prefix + name + color + width + height + flip + rotate + lastModified
    """
    parts = list(args)
    for k, v in sorted(kwargs.items()):
        if v is not None:
            parts.append(f"{k}={v}")
    parts.append(str(last_modified))

    safe = DELIM.join(map(str, parts))
    return safe.replace(":", "_").replace("/", "_").replace("\\", "_")


# =================================================================
# SVG DISK CACHE
# =================================================================
class _SVGCache(MutableMapping[str, bytes]):
    """A simple directory cache for SVG file blobs."""

    def __init__(self, directory: str | Path | None = None):
        super().__init__()
        if not directory:
            directory = get_cache_directory() / "svg_cache"
        self.path = Path(directory).expanduser().resolve()
        self.path.mkdir(parents=True, exist_ok=True)
        self._ext = ".svg"

    def path_for(self, key: str) -> Path:
        fname = f"{key}{self._ext}"
        return self.path / fname

    def __setitem__(self, key: str, value: bytes):
        self.path_for(key).write_bytes(value)

    def __getitem__(self, key: str) -> bytes:
        try:
            return self.path_for(key).read_bytes()
        except FileNotFoundError:
            raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        yield from (x.stem for x in self.path.glob(f"*{self._ext}"))

    def __delitem__(self, key: str):
        self.path_for(key).unlink(missing_ok=True)

    def __len__(self):
        return len(list(self.path.glob(f"*{self._ext}")))

    def __contains__(self, key: object) -> bool:
        return isinstance(key, str) and self.path_for(key).exists()


# =================================================================
# INIT CACHE
# =================================================================
def svg_cache() -> MutableMapping[str, bytes]:
    global _SVG_CACHE
    if _SVG_CACHE is None:
        if CACHE_DISABLED:
            _SVG_CACHE = {}
        else:
            try:
                _SVG_CACHE = _SVGCache()
            except Exception:
                _SVG_CACHE = {}

    return _SVG_CACHE


# =================================================================
# CLEAR CACHE
# =================================================================
def clear_cache() -> None:
    import shutil
    shutil.rmtree(get_cache_directory(), ignore_errors=True)
    global _SVG_CACHE
    _SVG_CACHE = None


# =================================================================
# DELETE STALE CACHE (for lastModified support)
# =================================================================
def delete_stale_svgs(prefix_last_mod: dict[str, int]):
    """
    Used externally when caller knows last_modified state.
    """
    cache = svg_cache()
    for key in list(cache):
        try:
            # key pattern: prefix_name_color..._lastModified
            parts = key.split(DELIM)
            last_mod = int(parts[-1])
            prefix = parts[0]
            if last_mod < prefix_last_mod.get(prefix, 0):
                del cache[key]
        except Exception:
            pass
