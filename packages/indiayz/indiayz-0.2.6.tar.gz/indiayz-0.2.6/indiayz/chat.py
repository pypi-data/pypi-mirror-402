from typing import Dict, Optional
from .client import client
from .exceptions import IndiayzAPIError


class Chat:
    @staticmethod
    def ask(
        message: str,
        *,
        model: Optional[str] = None,
        timeout: Optional[int] = 60,
    ) -> Dict:
        if not isinstance(message, str) or not message.strip():
            raise ValueError("message must be a non-empty string")

        payload = {"message": message.strip()}
        if model:
            payload["model"] = model

        try:
            return client.post(
                "/chat",
                json=payload,
                timeout=timeout
            )
        except Exception as e:
            raise IndiayzAPIError("Chat request failed") from e
