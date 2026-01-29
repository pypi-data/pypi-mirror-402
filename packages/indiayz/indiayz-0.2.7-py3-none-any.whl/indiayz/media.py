import requests
import os
from typing import Optional

from .client import client
from .exceptions import IndiayzAPIError


def download(
    url: str,
    format: str = "mp4",
    output: Optional[str] = None
):
    """
    Download media using Indiayz backend.

    Args:
        url (str): Media URL
        format (str): mp4 or mp3
        output (str, optional): Output filename

    Returns:
        str: Path to downloaded file
    """

    if format not in ("mp4", "mp3"):
        raise ValueError("format must be 'mp4' or 'mp3'")

    params = {
        "url": url,
        "format": format
    }

    download_url = f"{client.base_url}/media/download"

    try:
        with requests.get(
            download_url,
            params=params,
            stream=True,
            timeout=client.timeout
        ) as r:

            r.raise_for_status()

            # auto filename
            if not output:
                content_disposition = r.headers.get("content-disposition")
                if content_disposition and "filename=" in content_disposition:
                    output = content_disposition.split("filename=")[-1].strip('"')
                else:
                    output = f"indiayz_download.{format}"

            with open(output, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            return output

    except Exception as e:
        raise IndiayzAPIError(f"Download failed: {e}")
