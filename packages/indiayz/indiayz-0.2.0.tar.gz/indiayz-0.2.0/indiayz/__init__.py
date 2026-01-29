"""
indiayz
A lightweight Python SDK providing utilities via hosted APIs.
"""

from .wikipedia import search as wikipedia_search
from .quote import random as random_quote
from .media import info as media_info

__all__ = [
    "wikipedia_search",
    "random_quote",
    "media_info",
]

__version__ = "0.2.0"
