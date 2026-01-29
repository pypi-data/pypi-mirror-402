__all__ = ["__version__", "shiki", "decorations"]

from .version import __version__
from ._shiki_code import Code as shiki
from . import _decorations as decorations
