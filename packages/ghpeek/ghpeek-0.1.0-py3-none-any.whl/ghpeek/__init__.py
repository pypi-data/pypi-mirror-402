from importlib.metadata import PackageNotFoundError, version

__all__ = ["__version__"]

try:
    __version__ = version("ghpeek")
except PackageNotFoundError:  # pragma: no cover - fallback for editable runs
    __version__ = "0.0.0"
