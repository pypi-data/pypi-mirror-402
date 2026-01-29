from typing import Generator, Optional
from .client import client
from .exceptions import IndiayzAPIError


def chat_stream(
    message: str,
    *,
    model: Optional[str] = None,
    timeout: Optional[int] = None,
) -> Generator[str, None, None]:

    if not isinstance(message, str) or not message.strip():
        raise ValueError("message must be a non-empty string")

    payload = {"message": message.strip()}
    if model:
        payload["model"] = model

    try:
        response = client.post(
            "/chat/stream",
            json=payload,
            stream=True,
            timeout=timeout
        )

        for chunk in response.iter_content(decode_unicode=True):
            if chunk:
                yield chunk

    except Exception as e:
        raise IndiayzAPIError(str(e))


class Chat:
    @staticmethod
    def stream(message: str, **kwargs):
        return chat_stream(message, **kwargs)
