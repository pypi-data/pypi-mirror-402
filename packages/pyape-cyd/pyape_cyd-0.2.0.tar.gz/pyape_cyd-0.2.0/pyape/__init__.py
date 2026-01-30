from importlib.metadata import version, PackageNotFoundError

from .client import (
    Ape,
    ApeException,
    ApeResponse,
    Md5,
    Sha256,
    get_ape_session,
    init_ape_session,
)

__all__ = ["Ape", "init_ape_session", "get_ape_session", "ApeException", "Md5", "Sha256", "ApeResponse"]

try:
    __version__ = version("pyape-cyd")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "Unknown"