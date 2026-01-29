"""
Convert to Comic Book - 将图片文件夹或压缩包转换为漫画书格式
"""

__author__ = "kongolou"

from .converter import ComicBookConverter
from .file_detector import detect_file_type
from .exceptions import (
    ComicBookError,
    UnsupportedFormatError,
    ArchiveError,
    ConversionError,
)
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("ccb-cli")
except PackageNotFoundError:
    __version__ = "0.1.0"

__all__ = [
    "ComicBookConverter",
    "detect_file_type",
    "ComicBookError",
    "UnsupportedFormatError",
    "ArchiveError",
    "ConversionError",
]
