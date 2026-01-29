"""
文件类型检测模块

该模块提供了检测文件类型、判断图片格式和压缩包格式等功能。
"""

from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# 支持的图片格式
IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".webp",
    ".tiff",
    ".tif",
    ".ico",
    ".svg",
    ".avif",
    ".heic",
}

# 支持的压缩格式映射
ARCHIVE_EXTENSIONS = {
    ".cbz": "cbz",
    ".cbr": "cbr",
    ".cb7": "cb7",
    ".cbt": "cbt",
    ".zip": "zip",
    ".rar": "rar",
    ".7z": "7z",
    ".tar": "tar",
}

# 标准格式到漫画书格式的映射
STANDARD_TO_COMIC = {
    "zip": "cbz",
    "rar": "cbr",
    "7z": "cb7",
    "tar": "cbt",
}


def is_image_file(path: Path) -> bool:
    """
    判断文件是否为图片文件。

    Args:
        path: 文件路径

    Returns:
        如果是图片文件则返回True，否则返回False
    """
    if not path.is_file():
        return False
    return path.suffix.lower() in IMAGE_EXTENSIONS


def is_archive_file(path: Path) -> bool:
    """
    判断文件是否为压缩包文件。

    Args:
        path: 文件路径

    Returns:
        如果是压缩包文件则返回True，否则返回False
    """
    if not path.is_file():
        return False
    return path.suffix.lower() in ARCHIVE_EXTENSIONS


def detect_file_type(path: Path) -> Optional[str]:
    """
    检测文件或文件夹的类型。

    Args:
        path: 文件或文件夹路径

    Returns:
        类型字符串，可能的值:
        - "folder": 文件夹
        - "cbz", "cbr", "cb7", "cbt": 漫画书格式
        - "zip", "rar", "7z", "tar": 标准压缩格式
        - None: 无法识别
    """
    if not path.exists():
        logger.error(f"Path does not exist: {path}")
        return None

    if path.is_dir():
        return "folder"

    if path.is_file():
        extension = path.suffix.lower()
        if extension in ARCHIVE_EXTENSIONS:
            return ARCHIVE_EXTENSIONS[extension]

    logger.warning(f"Cannot detect file type for: {path}")
    return None


def get_comic_format(standard_format: str) -> str:
    """
    将标准压缩格式转换为对应的漫画书格式。

    Args:
        standard_format: 标准格式 ("zip", "rar", "7z", "tar")

    Returns:
        对应的漫画书格式 ("cbz", "cbr", "cb7", "cbt")
    """
    return STANDARD_TO_COMIC.get(standard_format, standard_format)


def is_valid_comic_format(format_type: str) -> bool:
    """
    检查格式是否为有效的漫画书格式。

    Args:
        format_type: 格式字符串

    Returns:
        如果是有效格式则返回True，否则返回False
    """
    valid_formats = {"folder", "cbz", "cbr", "cb7", "cbt"}
    return format_type in valid_formats
