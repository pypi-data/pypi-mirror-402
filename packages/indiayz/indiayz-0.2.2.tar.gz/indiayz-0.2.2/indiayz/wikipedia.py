from typing import Dict
from .client import client


def search(query: str) -> Dict:
    """
    Search Wikipedia articles via Indiayz API.

    Parameters
    ----------
    query : str
        Search query (e.g. "India")

    Returns
    -------
    dict
        Dictionary containing Wikipedia article data.
    """
    if not query or not isinstance(query, str):
        raise ValueError("query must be a non-empty string")

    return client.get(
        "/wiki",
        params={"q": query}
    )
