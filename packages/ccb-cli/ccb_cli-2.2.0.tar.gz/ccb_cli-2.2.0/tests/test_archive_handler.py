"""
Archive handler 单元测试
"""

import pytest
from pathlib import Path
import tempfile

from ccb.archive_handler import (
    ZipHandler,
    TarHandler,
    RarHandler,
    get_handler,
)
from ccb.exceptions import ArchiveError


class TestArchiveHandler:
    def test_get_handler_mapping_and_unsupported(self):
        """测试 get_handler 的映射与不支持类型"""
        assert isinstance(get_handler("zip"), ZipHandler)
        assert isinstance(get_handler("cbz"), ZipHandler)
        assert isinstance(get_handler("tar"), TarHandler)
        assert isinstance(get_handler("cbt"), TarHandler)
        with pytest.raises(ArchiveError):
            get_handler("unknown-type")

    def test_zip_compress_extract_and_is_valid(self, tmp_path):
        """测试 ZipHandler 的 compress/extract/is_valid 基本流程"""
        src = tmp_path / "src"
        src.mkdir()
        (src / "a.txt").write_text("hello world")
        sub = src / "sub"
        sub.mkdir()
        (sub / "b.txt").write_text("subfile")

        archive = tmp_path / "out.cbz"
        handler = ZipHandler()
        handler.compress(src, archive)

        assert archive.exists()
        assert handler.is_valid(archive)

        extracted = tmp_path / "extracted"
        handler.extract(archive, extracted)
        assert (extracted / "a.txt").read_text() == "hello world"
        assert (extracted / "sub" / "b.txt").read_text() == "subfile"

    def test_zip_compress_single_file(self, tmp_path):
        """测试将单个文件压缩为 ZIP"""
        f = tmp_path / "single.txt"
        f.write_text("solo")
        archive = tmp_path / "single.cbz"

        handler = ZipHandler()
        handler.compress(f, archive)

        assert archive.exists()
        # 解压确认文件名在根目录
        out = tmp_path / "out"
        handler.extract(archive, out)
        assert (out / "single.txt").read_text() == "solo"

    def test_tar_compress_extract_and_is_valid(self, tmp_path):
        """测试 TarHandler 的 compress/extract/is_valid 基本流程"""
        src = tmp_path / "src_tar"
        src.mkdir()
        (src / "x.txt").write_text("tar test")

        archive = tmp_path / "out.tar"
        handler = TarHandler()
        handler.compress(src, archive)

        assert archive.exists()
        assert handler.is_valid(archive)

        extracted = tmp_path / "extracted_tar"
        handler.extract(archive, extracted)
        assert (extracted / "src_tar" / "x.txt").read_text() == "tar test"

    def test_rar_handler_no_support(self, tmp_path):
        """当系统既无外部工具又未安装 rarfile 时，RarHandler 的行为"""
        handler = RarHandler()
        # 如果系统可用 rar 支持，则跳过此测试以避免误报
        if handler._external_tool or handler._has_rarfile:
            pytest.skip("System provides RAR support; skipping absence test")

        with pytest.raises(ArchiveError):
            handler.extract(Path("nonexistent.cbr"), tmp_path / "out")

        assert handler.is_valid(Path("nonexistent.cbr")) is False
