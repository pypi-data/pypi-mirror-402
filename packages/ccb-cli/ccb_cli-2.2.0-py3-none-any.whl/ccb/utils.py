"""
工具函数模块

该模块提供了各种实用工具函数，包括文件操作、路径处理等功能。
"""

import shutil
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def safe_remove(path: Path) -> None:
    """
    安全删除文件或文件夹。

    Args:
        path: 要删除的路径

    Raises:
        Exception: 删除失败时抛出
    """
    try:
        if path.is_file():
            path.unlink()
            logger.debug(f"Removed file: {path}")
        elif path.is_dir():
            shutil.rmtree(path)
            logger.debug(f"Removed directory: {path}")
    except Exception as e:
        logger.error(f"Failed to remove {path}: {e}")
        raise


def ensure_output_dir(path: Path) -> None:
    """
    确保输出目录存在。

    Args:
        path: 输出目录路径（如果是文件路径，则使用其父目录）
    """
    if path.is_file():
        path = path.parent
    path.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Ensured output directory: {path}")


def is_empty_directory(path: Path) -> bool:
    """
    判断文件夹是否为空。

    Args:
        path: 要检查的文件夹路径

    Returns:
        如果文件夹为空返回True，否则返回False
    """
    if not path.is_dir():
        return False
    
    return not any(path.iterdir())


def get_output_path(
    input_path: Path,
    output_type: str,
    output_dir: Optional[Path] = None,
) -> Path:
    """
    生成输出文件路径。

    Args:
        input_path: 输入文件路径
        output_type: 输出类型 (folder, cbz, cbr, cb7, cbt)
        output_dir: 输出目录，如果为None则使用输入文件的目录

    Returns:
        输出文件路径
    """
    if output_dir is None:
        output_dir = input_path.parent

    ensure_output_dir(output_dir)

    if output_type == "folder":
        # 如果是文件夹，使用输入路径的名称
        if input_path.is_dir():
            return output_dir / input_path.name
        else:
            # 如果是文件，去掉扩展名作为文件夹名
            return output_dir / input_path.stem
    else:
        # 压缩包格式
        if input_path.is_dir():
            stem = input_path.name
        else:
            stem = input_path.stem

        extension_map = {
            "cbz": ".cbz",
            "cbr": ".cbr",
            "cb7": ".cb7",
            "cbt": ".cbt",
        }
        extension = extension_map.get(output_type, ".cbz")
        return output_dir / f"{stem}{extension}"
