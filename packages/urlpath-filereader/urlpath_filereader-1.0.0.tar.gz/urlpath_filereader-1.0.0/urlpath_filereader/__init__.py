import requests
from pathlib import Path
from urllib.parse import urlparse

__version__ = "1.0.0"


def is_url(source: str) -> bool:
    parsed = urlparse(source)
    return bool(parsed.scheme and parsed.netloc)


def read_file(source: str, encoding: str) -> str:
    if is_url(source):
        response = requests.get(source)
        response.raise_for_status()
        return response.text
    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {source}")
    return path.read_text(encoding)

