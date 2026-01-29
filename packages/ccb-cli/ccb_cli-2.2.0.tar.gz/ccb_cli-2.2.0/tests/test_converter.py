"""
核心转换模块的单元测试
"""

import pytest
from pathlib import Path
import tempfile
import zipfile
import os

from ccb.converter import ComicBookConverter
from ccb.exceptions import ConversionError, UnsupportedFormatError


class TestComicBookConverter:
    """转换器测试类"""

    def test_convert_folder_to_cbz(self):
        """测试文件夹转 CBZ"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试文件夹
            test_folder = Path(tmpdir) / "test_folder"
            test_folder.mkdir()
            (test_folder / "test.txt").write_text("test content")

            # 转换 - 使用不同的输出目录避免路径冲突
            output_dir = Path(tmpdir) / "output"
            converter = ComicBookConverter()
            output_path = converter.convert(
                test_folder,
                "cbz",
                output_dir=output_dir,
                remove_source=False,
            )

            # 验证
            assert output_path.exists()
            assert output_path.suffix == ".cbz"
            assert zipfile.is_zipfile(output_path)
            assert test_folder.exists()  # 源文件未删除

    def test_convert_folder_to_cbz_remove_source(self):
        """测试文件夹转 CBZ 并删除源文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试文件夹
            test_folder = Path(tmpdir) / "test_folder"
            test_folder.mkdir()
            (test_folder / "test.txt").write_text("test content")

            # 转换 - 使用不同的输出目录避免路径冲突
            output_dir = Path(tmpdir) / "output"
            converter = ComicBookConverter()
            output_path = converter.convert(
                test_folder,
                "cbz",
                output_dir=output_dir,
                remove_source=True,
            )

            # 验证
            assert output_path.exists()
            assert not test_folder.exists()  # 源文件已删除

    def test_convert_cbz_to_folder(self):
        """测试 CBZ 转文件夹"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试 ZIP 文件
            zip_path = Path(tmpdir) / "test.cbz"
            with zipfile.ZipFile(zip_path, "w") as zipf:
                zipf.writestr("test.txt", "test content")

            # 转换
            converter = ComicBookConverter()
            output_path = converter.convert(
                zip_path,
                "folder",
                output_dir=Path(tmpdir),
                remove_source=False,
            )

            # 验证
            assert output_path.exists()
            assert output_path.is_dir()
            assert (output_path / "test.txt").exists()
            assert (output_path / "test.txt").read_text() == "test content"

    def test_convert_cbz_to_cbt(self):
        """测试 CBZ 转 CBT"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试 ZIP 文件
            zip_path = Path(tmpdir) / "test.cbz"
            with zipfile.ZipFile(zip_path, "w") as zipf:
                zipf.writestr("test.txt", "test content")

            # 转换 - 使用不同的输出目录避免路径冲突
            output_dir = Path(tmpdir) / "output"
            converter = ComicBookConverter()
            output_path = converter.convert(
                zip_path,
                "cbt",
                output_dir=output_dir,
                remove_source=False,
            )

            # 验证
            assert output_path.exists()
            assert output_path.suffix == ".cbt"
            import tarfile

            assert tarfile.is_tarfile(output_path)

    def test_convert_same_type(self):
        """测试相同类型的转换（应该跳过）"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_folder = Path(tmpdir) / "test_folder"
            test_folder.mkdir()

            converter = ComicBookConverter()
            output_path = converter.convert(
                test_folder,
                "folder",
                output_dir=Path(tmpdir),
                remove_source=False,
            )

            # 应该返回原路径
            assert output_path == test_folder

    def test_convert_invalid_input(self):
        """测试无效输入"""
        converter = ComicBookConverter()
        with pytest.raises(ConversionError):
            converter.convert(
                Path("/nonexistent/path"),
                "cbz",
                remove_source=False,
            )

    def test_convert_invalid_output_format(self):
        """测试无效输出格式"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_folder = Path(tmpdir) / "test_folder"
            test_folder.mkdir()

            converter = ComicBookConverter()
            with pytest.raises(UnsupportedFormatError):
                converter.convert(
                    test_folder,
                    "invalid_format",
                    remove_source=False,
                )
