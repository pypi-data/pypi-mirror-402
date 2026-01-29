"""
urlpath-filereader - библиотека для чтения файлов из локальной файловой системы и URL-адресов.

Основные возможности:
    - Чтение файлов как из локальных путей, так и из URL
    - Автоматическое определение кодировки файлов
    - Поддержка всех стандартных режимов открытия файлов
    - Создание локальных копий файлов из URL

Версия: 1.2.0
"""

import requests, chardet, os
from pathlib import Path
from typing import Literal, Optional
from urllib.parse import urlparse
from pathlike_typing import PathLike

__version__ = "1.2.0"
__all__ = ['__version__', 'detect_encoding', 'is_url', 'read_file', 'FileOpenMode', 'create_file_from_url', 'open_plus']

FileOpenMode = Literal[
    "r+", "+r", "rt+", "r+t", "+rt", "tr+", "t+r", "+tr", "w+", "+w", "wt+", "w+t", "+wt",
    "tw+", "t+w", "+tw", "a+", "+a", "at+", "a+t", "+at", "ta+", "t+a", "+ta", "x+", "+x",
    "xt+", "x+t", "+xt", "tx+", "t+x", "+tx", "w", "wt", "tw", "a", "at", "ta", "x", "xt",
    "tx", "r", "rt", "tr", "U", "rU", "Ur", "rtU", "rUt", "Urt", "trU", "tUr", "Utr"]


def detect_encoding(file_path: PathLike) -> str:
    """
    Определяет кодировку файла с помощью библиотеки chardet.

    Args:
        file_path (PathLike): Путь к файлу для определения кодировки.

    Returns:
        str: Предполагаемая кодировка файла (например, 'utf-8', 'windows-1251').

    Raises:
        FileNotFoundError: Если файл не существует.
        IOError: Если произошла ошибка при чтении файла.

    Example:
        >>> encoding = detect_encoding('example.txt')
        >>> print(f"Кодировка файла: {encoding}")
        Кодировка файла: utf-8
    """
    with open(file_path, 'rb') as file:
        raw_data = file.read()
        result = chardet.detect(raw_data)
        return result['encoding']


def is_url(source: PathLike) -> bool:
    """
    Проверяет, является ли переданная строка валидным URL-адресом.

    Args:
        source (PathLike): Строка для проверки (может быть путь или URL).

    Returns:
        bool: True если source является валидным URL, иначе False.

    Note:
        URL должен содержать схему (scheme) и домен (netloc).

    Example:
        >>> is_url('https://example.com/file.txt')
        True
        >>> is_url('/home/user/file.txt')
        False
        >>> is_url('file.txt')
        False
    """
    parsed = urlparse(str(source))
    return bool(parsed.scheme and parsed.netloc)


def read_file(source: PathLike) -> str:
    """
    Читает содержимое файла или URL-адреса.

    Для URL-адресов выполняет HTTP GET-запрос для получения содержимого.
    Для локальных файлов автоматически определяет кодировку.

    Args:
        source (PathLike): Путь к локальному файлу или URL-адрес.

    Returns:
        str: Содержимое файла или веб-страницы в виде строки.

    Raises:
        FileNotFoundError: Если локальный файл не существует.
        requests.exceptions.RequestException: При ошибке HTTP-запроса.
        UnicodeDecodeError: При проблемах с декодированием содержимого.

    Example:
        >>> # Чтение локального файла
        >>> content = read_file('example.txt')
        >>> 
        >>> # Чтение из URL
        >>> web_content = read_file('https://example.com/data.txt')
    """
    if is_url(source):
        response = requests.get(source)
        response.raise_for_status()
        return response.text
    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {source}")
    return path.read_text(detect_encoding(path))


def create_file_from_url(source: PathLike, encoding: str) -> str:
    """
    Создает локальную копию файла из URL-адреса.

    Args:
        source (PathLike): URL-адрес для загрузки файла.
        encoding (str): Кодировка для сохранения файла (например, 'utf-8').

    Returns:
        str: Путь к созданному локальному файлу.

    Note:
        Имя файла формируется из URL путем замены '//' и '/' на '_'.

    Example:
        >>> local_file = create_file_from_url('https://example.com/data.json', 'utf-8')
        >>> print(f"Файл сохранен как: {local_file}")
        Файл сохранен как: https:__example.com_data.json
    """
    if is_url(source):
        source = source.replace('//', '_').replace('/', '_')
        with open(source, 'w', encoding=encoding) as file:
            file.write(requests.get(source).text)
    return source


def open_plus(
    source: PathLike,
    mode: FileOpenMode = 'r',
    buffering: int = -1,
    encoding: Optional[str] = None,
    errors: Optional[str] = None,
    newline: Optional[str] = None,
    closefd: bool = True,
    auto_detect_encoding: bool = False
):
    """
    Универсальная функция для открытия файлов, поддерживающая как локальные пути, так и URL.

    Args:
        source (PathLike): Путь к файлу или URL-адрес.
        mode (FileOpenMode): Режим открытия файла. По умолчанию 'r'.
        buffering (int): Режим буферизации. По умолчанию -1 (системный).
        encoding (Optional[str]): Кодировка файла. Если не указана и auto_detect_encoding=False,
                                  используется DEFAULT_ENCODING из переменных окружения.
        errors (Optional[str]): Обработка ошибок кодировки (см. документацию open()).
        newline (Optional[str]): Контроль перевода строк (см. документацию open()).
        closefd (bool): Закрывать ли файловый дескриптор. По умолчанию True.
        auto_detect_encoding (bool): Автоматически определять кодировку файла. 
                                     По умолчанию False.

    Returns:
        _io.TextIOWrapper: Файловый объект.

    Raises:
        FileNotFoundError: Если локальный файл не существует.
        requests.exceptions.RequestException: При ошибке загрузки файла из URL.
        ValueError: При неверном режиме открытия файла.

    Note:
        При указании URL автоматически создается локальная копия файла.

    Example:
        >>> # Открытие локального файла с автоопределением кодировки
        >>> with open_plus('example.txt', auto_detect_encoding=True) as f:
        >>>     content = f.read()
        >>> 
        >>> # Открытие файла из URL
        >>> with open_plus('https://example.com/data.txt', 'r', encoding='utf-8') as f:
        >>>     data = f.readlines()
    """
    source = create_file_from_url(source.replace('\\', '/'), encoding)
    auto_encoding = detect_encoding(source) if auto_detect_encoding else None
    encoding = encoding or auto_encoding or os.environ['DEFAULT_ENCODING']
    return open(source, mode, buffering, encoding, errors, newline, closefd)