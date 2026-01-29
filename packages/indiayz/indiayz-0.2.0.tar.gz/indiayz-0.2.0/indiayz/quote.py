from typing import Dict
from .client import _get


def random() -> Dict:
    """
    Fetch a random quote.

    Returns
    -------
    dict
        API response containing a quote.
    """
    return _get("/quote")
