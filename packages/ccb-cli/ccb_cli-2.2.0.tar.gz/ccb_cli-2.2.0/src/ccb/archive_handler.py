"""
压缩/解压处理模块

该模块提供了处理各种压缩格式的抽象基类和具体实现，支持漫画书格式如CBZ、CBR、CB7、CBT等。
"""

import zipfile
import tarfile
import shutil
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Optional
import logging
import tempfile
import subprocess

from .exceptions import ArchiveError

logger = logging.getLogger(__name__)


class ArchiveHandler(ABC):
    """压缩包处理器抽象基类。

    定义了压缩、解压和验证压缩包的接口，具体实现类需要继承此类并实现这些方法。
    """

    @abstractmethod
    def extract(self, archive_path: Path, output_path: Path) -> None:
        """
        解压压缩包到指定目录。

        Args:
            archive_path: 压缩包文件路径
            output_path: 输出目录路径

        Raises:
            ArchiveError: 解压失败时抛出
        """
        pass

    @abstractmethod
    def compress(self, source_path: Path, archive_path: Path) -> None:
        """
        将源文件或文件夹压缩为压缩包。

        Args:
            source_path: 源文件或文件夹路径
            archive_path: 输出压缩包路径

        Raises:
            ArchiveError: 压缩失败时抛出
        """
        pass

    @abstractmethod
    def is_valid(self, archive_path: Path) -> bool:
        """
        验证压缩包是否有效。

        Args:
            archive_path: 压缩包文件路径

        Returns:
            如果压缩包有效则返回True，否则返回False
        """
        pass


class ZipHandler(ArchiveHandler):
    """ZIP/CBZ 格式处理器。

    处理标准ZIP压缩格式和漫画书CBZ格式。
    """

    def extract(self, archive_path: Path, output_path: Path) -> None:
        """解压 ZIP/CBZ 文件到指定目录。

        Args:
            archive_path: ZIP/CBZ 压缩包路径
            output_path: 输出目录路径

        Raises:
            ArchiveError: 解压失败时抛出
        """
        try:
            output_path.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(archive_path, "r") as zipf:
                zipf.extractall(output_path)
            logger.debug(f"Extracted {archive_path} to {output_path}")
        except Exception as e:
            raise ArchiveError(f"Failed to extract ZIP archive {archive_path}: {e}")

    def compress(self, source_path: Path, archive_path: Path) -> None:
        """将源文件或文件夹压缩为 ZIP/CBZ 格式。

        Args:
            source_path: 源文件或文件夹路径
            archive_path: 输出 ZIP/CBZ 文件路径

        Raises:
            ArchiveError: 压缩失败时抛出
        """
        try:
            # 确保输出目录存在
            archive_path.parent.mkdir(parents=True, exist_ok=True)
            # 如果输出文件已存在，先删除（Windows 上可能需要）
            if archive_path.exists():
                archive_path.unlink()
            with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                if source_path.is_file():
                    zipf.write(source_path, source_path.name)
                elif source_path.is_dir():
                    for file_path in source_path.rglob("*"):
                        if file_path.is_file():
                            arcname = file_path.relative_to(source_path)
                            zipf.write(file_path, arcname)
            logger.debug(f"Compressed {source_path} to {archive_path}")
        except Exception as e:
            raise ArchiveError(f"Failed to create ZIP archive {archive_path}: {e}")

    def is_valid(self, archive_path: Path) -> bool:
        """验证 ZIP/CBZ 文件是否有效。

        Args:
            archive_path: ZIP/CBZ 压缩包路径

        Returns:
            如果文件有效返回True，否则返回False
        """
        try:
            with zipfile.ZipFile(archive_path, "r") as zipf:
                zipf.testzip()
            return True
        except Exception:
            return False


class TarHandler(ArchiveHandler):
    """TAR/CBT 格式处理器。

    处理标准TAR压缩格式和漫画书CBT格式。
    """

    def extract(self, archive_path: Path, output_path: Path) -> None:
        """解压 TAR/CBT 文件到指定目录。

        Args:
            archive_path: TAR/CBT 压缩包路径
            output_path: 输出目录路径

        Raises:
            ArchiveError: 解压失败时抛出
        """
        try:
            output_path.mkdir(parents=True, exist_ok=True)
            with tarfile.open(archive_path, "r:*") as tar:
                tar.extractall(output_path)
            logger.debug(f"Extracted {archive_path} to {output_path}")
        except Exception as e:
            raise ArchiveError(f"Failed to extract TAR archive {archive_path}: {e}")

    def compress(self, source_path: Path, archive_path: Path) -> None:
        """将源文件或文件夹压缩为 TAR/CBT 格式。

        Args:
            source_path: 源文件或文件夹路径
            archive_path: 输出 TAR/CBT 文件路径

        Raises:
            ArchiveError: 压缩失败时抛出
        """
        try:
            # 确保输出目录存在
            archive_path.parent.mkdir(parents=True, exist_ok=True)
            # 如果输出文件已存在，先删除（Windows 上可能需要）
            if archive_path.exists():
                archive_path.unlink()
            with tarfile.open(archive_path, "w") as tar:
                if source_path.is_file():
                    tar.add(source_path, arcname=source_path.name)
                elif source_path.is_dir():
                    tar.add(source_path, arcname=source_path.name, recursive=True)
            logger.debug(f"Compressed {source_path} to {archive_path}")
        except Exception as e:
            raise ArchiveError(f"Failed to create TAR archive {archive_path}: {e}")

    def is_valid(self, archive_path: Path) -> bool:
        """验证 TAR/CBT 文件是否有效。

        Args:
            archive_path: TAR/CBT 压缩包路径

        Returns:
            如果文件有效返回True，否则返回False
        """
        try:
            with tarfile.open(archive_path, "r:*") as tar:
                tar.getmembers()
            return True
        except Exception:
            return False


class RarHandler(ArchiveHandler):
    """RAR/CBR 格式处理器。

    处理标准RAR压缩格式和漫画书CBR格式。
    需要手动安装WinRAR软件，将其安装路径添加到环境变量Path，以调用rar命令。
    需要安装rarfile库，用于在没有外部命令rar时提供基础的解压缩功能。
    """

    def __init__(self):
        """初始化 RAR 处理器。

        检测外部命令rar，否则尝试导入rarfile库。
        """
        self._external_tool = shutil.which("rar")
        if self._external_tool:
            logger.debug(f"Found external rar command: {self._external_tool}")
        else:
            logger.warning("rar command not found, using rarfile library instead")
            self._has_rarfile = False
            try:
                import rarfile

                self.rarfile = rarfile
                self._has_rarfile = True
            except ImportError:
                logger.warning("rarfile not installed, RAR/CBR support unavailable")

    def extract(self, archive_path: Path, output_path: Path) -> None:
        """解压 RAR/CBR 文件到指定目录。

        优先使用外部命令 rar，如果没有则使用 rarfile 库。

        Args:
            archive_path: RAR/CBR 压缩包路径
            output_path: 输出目录路径

        Raises:
            ArchiveError: 解压失败时抛出
        """
        if self._external_tool:
            output_path.mkdir(parents=True, exist_ok=True)
            # build candidate commands to try (primary, alternatives, minimal)
            cmds = [
                [
                    self._external_tool,
                    "x",
                    "-y",
                    str(archive_path),
                    str(output_path),
                ],
                [
                    self._external_tool,
                    "x",
                    "/y",
                    str(archive_path),
                    str(output_path),
                ],
                [
                    self._external_tool,
                    "x",
                    str(archive_path),
                    str(output_path),
                ],
            ]

            # helper to run a single command and return (returncode, stdout, stderr, timeout_flag)
            def _run(cmd, timeout_sec=120):
                try:
                    completed = subprocess.run(
                        cmd,
                        check=False,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=timeout_sec,
                    )
                    out_s = (
                        completed.stdout.decode(errors="ignore")
                        if completed.stdout
                        else ""
                    )
                    err_s = (
                        completed.stderr.decode(errors="ignore")
                        if completed.stderr
                        else ""
                    )
                    return completed.returncode, out_s, err_s, False
                except subprocess.TimeoutExpired as e:
                    return -1, "", f"Timeout after {e.timeout}s", True
                except FileNotFoundError as e:
                    return -2, "", str(e), False

            last_err = None
            for cmd in cmds:
                rc, out, err, timed_out = _run(cmd)
                if rc == 0:
                    logger.debug(
                        f"Extracted {archive_path} to {output_path} using external tool {cmd}"
                    )
                    return
                # if timed out, raise immediately (avoid long waits)
                if timed_out:
                    raise ArchiveError(f"External extractor timeout for {archive_path}")
                # record last non-empty error
                last_err = err or out or last_err

            # all external attempts failed
            msg = (
                last_err
                or f"external tool exited with non-zero code using {self._external_tool}"
            ).strip()
            logger.debug(f"External extractor attempts failed: {msg}")

        # Fallback to rarfile library if present
        elif self._has_rarfile:
            try:
                output_path.mkdir(parents=True, exist_ok=True)
                with self.rarfile.RarFile(str(archive_path)) as rar:
                    rar.extractall(str(output_path))
                logger.debug(f"Extracted {archive_path} to {output_path} using rarfile")
            except Exception as e:
                raise ArchiveError(f"Failed to extract RAR archive {archive_path}: {e}")
        else:
            raise ArchiveError(
                "rar command or rarfile library is required for RAR/CBR support"
            )

    def compress(self, source_path: Path, archive_path: Path) -> None:
        """将源文件或文件夹压缩为 RAR/CBR 格式。

        Args:
            source_path: 源文件或文件夹路径
            archive_path: 输出 RAR/CBR 文件路径

        Raises:
            ArchiveError: 压缩失败时抛出
        """
        # RAR 压缩需要外部命令 rar
        if not self._external_tool:
            raise ArchiveError(
                "RAR compression requires rar command. Install WinRAR or use ZIP/CBZ instead."
            )

        cmds = [
            [
                self._external_tool,
                "a",
                "-r",
                str(archive_path),
                str(source_path),
            ],
            [
                self._external_tool,
                "a",
                "/r",
                str(archive_path),
                str(source_path),
            ],
        ]

        # helper to run a single command and return (returncode, stdout, stderr, timeout_flag)
        def _run(cmd, timeout_sec=300):
            try:
                completed = subprocess.run(
                    cmd,
                    check=False,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=timeout_sec,
                )
                out_s = completed.stdout.decode(errors="ignore") if completed.stdout else ""
                err_s = completed.stderr.decode(errors="ignore") if completed.stderr else ""
                return completed.returncode, out_s, err_s, False
            except subprocess.TimeoutExpired as e:
                return -1, "", f"Timeout after {e.timeout}s", True
            except FileNotFoundError as e:
                return -2, "", str(e), False

        last_err = None
        for cmd in cmds:
            rc, out, err, timed_out = _run(cmd)
            if rc == 0:
                logger.debug(f"Compressed {source_path} to {archive_path} using external tool {cmd}")
                return
            # if timed out, raise immediately
            if timed_out:
                raise ArchiveError(f"External compressor timeout for {source_path}")
            # record last non-empty error
            last_err = err or out or last_err

        # all external attempts failed
        msg = (last_err or f"external tool exited with non-zero code using {self._external_tool}").strip()
        raise ArchiveError(f"Failed to compress {source_path} to {archive_path}: {msg}")

    def is_valid(self, archive_path: Path) -> bool:
        """验证 RAR/CBR 文件是否有效。

        Args:
            archive_path: RAR/CBR 压缩包路径

        Returns:
            如果文件有效返回True，否则返回False
        """
        # If external tool available, use it to test the archive
        if self._external_tool:
            try:
                # try a few variants for the test command
                test_cmds = [[self._external_tool, "t", str(archive_path)]]
                for cmd in test_cmds:
                    try:
                        completed = subprocess.run(
                            cmd,
                            check=False,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            timeout=30,
                        )
                        if completed.returncode == 0:
                            return True
                    except subprocess.TimeoutExpired:
                        logger.warning(
                            f"External extractor timeout while testing archive: {archive_path}"
                        )
                        return False
                logger.debug("External tool test commands all returned non-zero")
                return False
            except subprocess.TimeoutExpired:
                logger.warning(
                    f"External extractor timeout while testing archive: {archive_path}"
                )
                return False
            except FileNotFoundError:
                return False
            except Exception as e:
                logger.debug(f"External extractor test error for {archive_path}: {e}")
                return False

        elif self._has_rarfile:
            try:
                with self.rarfile.RarFile(archive_path) as rar:
                    rar.testrar()
                return True
            except Exception:
                return False
        else:
            return False


class SevenZipHandler(ArchiveHandler):
    """7Z/CB7 格式处理器。

    处理标准7Z压缩格式和漫画书CB7格式。
    需要安装py7zr库。
    """

    def __init__(self):
        """初始化7Z处理器。

        尝试导入py7zr库，如果导入失败则禁用7Z支持。
        """
        self._has_py7zr = False
        try:
            import py7zr

            self.py7zr = py7zr
            self._has_py7zr = True
        except ImportError:
            logger.warning("py7zr not installed, 7Z/CB7 support unavailable")

    def extract(self, archive_path: Path, output_path: Path) -> None:
        """解压 7Z/CB7 文件到指定目录。

        Args:
            archive_path: 7Z/CB7 压缩包路径
            output_path: 输出目录路径

        Raises:
            ArchiveError: 解压失败时抛出
        """
        if not self._has_py7zr:
            raise ArchiveError("py7zr library is required for 7Z/CB7 support")
        try:
            output_path.mkdir(parents=True, exist_ok=True)
            with self.py7zr.SevenZipFile(archive_path, mode="r") as archive:
                archive.extractall(output_path)
            logger.debug(f"Extracted {archive_path} to {output_path}")
        except Exception as e:
            raise ArchiveError(f"Failed to extract 7Z archive {archive_path}: {e}")

    def compress(self, source_path: Path, archive_path: Path) -> None:
        """将源文件或文件夹压缩为 7Z/CB7 格式。

        Args:
            source_path: 源文件或文件夹路径
            archive_path: 输出 7Z/CB7 文件路径

        Raises:
            ArchiveError: 压缩失败时抛出
        """
        if not self._has_py7zr:
            raise ArchiveError("py7zr library is required for 7Z/CB7 support")
        try:
            # 确保输出目录存在
            archive_path.parent.mkdir(parents=True, exist_ok=True)
            # 如果输出文件已存在，先删除（Windows 上可能需要）
            if archive_path.exists():
                archive_path.unlink()
            with self.py7zr.SevenZipFile(archive_path, mode="w") as archive:
                if source_path.is_file():
                    archive.write(source_path, source_path.name)
                elif source_path.is_dir():
                    for file_path in source_path.rglob("*"):
                        if file_path.is_file():
                            arcname = file_path.relative_to(source_path)
                            archive.write(file_path, arcname)
            logger.debug(f"Compressed {source_path} to {archive_path}")
        except Exception as e:
            raise ArchiveError(f"Failed to create 7Z archive {archive_path}: {e}")

    def is_valid(self, archive_path: Path) -> bool:
        """验证 7Z/CB7 文件是否有效。

        Args:
            archive_path: 7Z/CB7 压缩包路径

        Returns:
            如果文件有效返回True，否则返回False
        """
        if not self._has_py7zr:
            return False
        try:
            with self.py7zr.SevenZipFile(archive_path, mode="r") as archive:
                archive.getnames()
            return True
        except Exception:
            return False


def get_handler(archive_type: str) -> ArchiveHandler:
    """
    根据压缩包类型获取对应的处理器实例。

    Args:
        archive_type: 压缩包类型 (cbz, cbr, cb7, cbt, zip, rar, 7z, tar)

    Returns:
        对应的ArchiveHandler子类实例

    Raises:
        ArchiveError: 如果压缩包类型不被支持
    """
    handler_map = {
        "zip": ZipHandler,
        "cbz": ZipHandler,
        "rar": RarHandler,
        "cbr": RarHandler,
        "7z": SevenZipHandler,
        "cb7": SevenZipHandler,
        "tar": TarHandler,
        "cbt": TarHandler,
    }

    handler_class = handler_map.get(archive_type.lower())
    if handler_class is None:
        raise ArchiveError(f"Unsupported archive type: {archive_type}")

    return handler_class()
