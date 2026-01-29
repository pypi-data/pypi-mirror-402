"""
indiayz.chat

High-level chat interface for AI conversations powered by indiayz backend.
"""

from typing import Dict, Optional
from .client import client
from .exceptions import IndiayzAPIError


def chat(
    message: str,
    *,
    model: Optional[str] = None,
    timeout: Optional[int] = None,
) -> Dict:
    """
    Send a message to the AI chat service.

    Parameters
    ----------
    message : str
        User message to send to the AI.
    model : str, optional
        Optional model identifier.
    timeout : int, optional
        Request timeout in seconds.

    Returns
    -------
    dict
        AI response payload.

    Example
    -------
    >>> import indiayz
    >>> response = indiayz.chat("Hello, explain AI simply")
    >>> print(response["data"]["response"])
    """

    if not isinstance(message, str) or not message.strip():
        raise ValueError("message must be a non-empty string")

    payload = {
        "message": message.strip()
    }

    if model:
        payload["model"] = model

    try:
        return client.post(
            "/chat",
            json=payload,
            timeout=timeout
        )
    except Exception as e:
        raise IndiayzAPIError(str(e))
