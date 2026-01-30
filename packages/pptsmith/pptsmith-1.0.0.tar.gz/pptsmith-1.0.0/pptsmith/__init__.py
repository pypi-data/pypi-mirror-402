"""pptsmith - Markdown to PowerPoint converter"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("pptsmith")
except PackageNotFoundError:
    __version__ = "0.0.0"  # fallback for development
