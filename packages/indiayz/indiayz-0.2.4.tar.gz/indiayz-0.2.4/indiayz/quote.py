from typing import Dict
from .client import client


def random() -> Dict:
    """
    Fetch a random inspirational quote via Indiayz API.

    Returns
    -------
    dict
        Dictionary containing quote text and author.
    """
    return client.get("/quote")
