from typing import Dict
from .client import _get


def info(url: str) -> Dict:
    """
    Fetch media metadata from a given URL.

    Parameters
    ----------
    url : str
        Media URL.

    Returns
    -------
    dict
        API response containing media information.
    """
    if not url or not isinstance(url, str):
        raise ValueError("url must be a valid string")

    return _get("/media/info", params={"url": url})
