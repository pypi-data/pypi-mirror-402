from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("urn_citation") # 'name' of package from pyproject.toml
except PackageNotFoundError:
    # Package is not installed (e.g., running from a local script)
    __version__ = "unknown"

from .urn import Urn
from .ctsurn import CtsUrn
from .cite2urn import Cite2Urn

__all__ = ["Urn", "CtsUrn", "Cite2Urn"]