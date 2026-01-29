"""Crisp package."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("roche.crisp")
except PackageNotFoundError:
    # If the package is not installed, don't add __version__
    pass
