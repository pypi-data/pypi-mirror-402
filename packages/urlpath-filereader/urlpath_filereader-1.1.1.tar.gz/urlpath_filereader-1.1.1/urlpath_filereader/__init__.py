import requests, chardet
from pathlib import Path
from urllib.parse import urlparse

__version__ = "1.1.1"
__all__ = ['__version__', 'detect_encoding', 'is_url', 'read_file']


def detect_encoding(file_path):
    with open(file_path, 'rb') as file:
        raw_data = file.read()
        result = chardet.detect(raw_data)
        return result['encoding']


def is_url(source: str) -> bool:
    parsed = urlparse(source)
    return bool(parsed.scheme and parsed.netloc)


def read_file(source: str) -> str:
    if is_url(source):
        response = requests.get(source)
        response.raise_for_status()
        return response.text
    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {source}")
    return path.read_text(detect_encoding(path))

