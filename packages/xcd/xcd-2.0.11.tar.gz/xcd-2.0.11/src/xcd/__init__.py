
from importlib.metadata import version as _pkg_version  # Py3.8+

__all__ = ["__version__", "XCD_VERSION"]

DEFAULT_VER = "dev"

try:
    __version__ = _pkg_version("xcd")
except Exception:
    __version__ = DEFAULT_VER

XCD_VERSION = __version__
