from typing import Dict
from .client import _get


def search(query: str) -> Dict:
    """
    Search Wikipedia articles.

    Parameters
    ----------
    query : str
        Search query.

    Returns
    -------
    dict
        API response containing search results.
    """
    if not query or not isinstance(query, str):
        raise ValueError("query must be a non-empty string")

    return _get("/wiki", params={"q": query})
