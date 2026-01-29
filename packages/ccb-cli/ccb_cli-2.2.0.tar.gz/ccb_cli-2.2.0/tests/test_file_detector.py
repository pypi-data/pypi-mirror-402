"""
文件类型检测模块的单元测试
"""

import pytest
from pathlib import Path
import tempfile
import os

from ccb.file_detector import (
    detect_file_type,
    is_image_file,
    is_archive_file,
    get_comic_format,
    is_valid_comic_format,
)


class TestFileDetector:
    """文件类型检测测试类"""

    def test_detect_folder(self):
        """测试文件夹检测"""
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            assert detect_file_type(folder) == "folder"

    def test_detect_cbz(self):
        """测试 CBZ 文件检测"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.cbz"
            path.touch()
            assert detect_file_type(path) == "cbz"

    def test_detect_cbr(self):
        """测试 CBR 文件检测"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.cbr"
            path.touch()
            assert detect_file_type(path) == "cbr"

    def test_detect_zip(self):
        """测试 ZIP 文件检测"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.zip"
            path.touch()
            assert detect_file_type(path) == "zip"

    def test_is_image_file(self):
        """测试图片文件判断"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.jpg"
            path.touch()
            assert is_image_file(path) is True

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.png"
            path.touch()
            assert is_image_file(path) is True

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.txt"
            path.touch()
            assert is_image_file(path) is False

    def test_is_archive_file(self):
        """测试压缩包文件判断"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.zip"
            path.touch()
            assert is_archive_file(path) is True

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.cbz"
            path.touch()
            assert is_archive_file(path) is True

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.txt"
            path.touch()
            assert is_archive_file(path) is False

    def test_get_comic_format(self):
        """测试标准格式到漫画书格式的转换"""
        assert get_comic_format("zip") == "cbz"
        assert get_comic_format("rar") == "cbr"
        assert get_comic_format("7z") == "cb7"
        assert get_comic_format("tar") == "cbt"
        assert get_comic_format("unknown") == "unknown"

    def test_is_valid_comic_format(self):
        """测试漫画书格式验证"""
        assert is_valid_comic_format("folder") is True
        assert is_valid_comic_format("cbz") is True
        assert is_valid_comic_format("cbr") is True
        assert is_valid_comic_format("cb7") is True
        assert is_valid_comic_format("cbt") is True
        assert is_valid_comic_format("zip") is False
        assert is_valid_comic_format("unknown") is False
