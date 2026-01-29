__all__ = ["__version__"]

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("k8s-agent")
except PackageNotFoundError:
    __version__ = "0.1.0"


