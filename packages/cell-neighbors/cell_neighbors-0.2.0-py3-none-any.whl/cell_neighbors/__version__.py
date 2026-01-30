# -- import packages: ---------------------------------------------------------
import importlib.metadata

try:
    __version__ = importlib.metadata.version("cell-neighbors")
except importlib.metadata.PackageNotFoundError:
    __version__ = "unknown"