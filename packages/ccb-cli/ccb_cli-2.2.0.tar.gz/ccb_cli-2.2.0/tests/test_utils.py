"""
工具函数模块的单元测试
"""

import pytest
from pathlib import Path
import tempfile
import os

from ccb.utils import (
    safe_remove,
    ensure_output_dir,
    get_output_path,
)


class TestUtils:
    """工具函数测试类"""

    def test_safe_remove_file(self):
        """测试安全删除文件"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            file_path = Path(f.name)
            file_path.write_text("test")

        assert file_path.exists()
        safe_remove(file_path)
        assert not file_path.exists()

    def test_safe_remove_directory(self):
        """测试安全删除文件夹"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "test_dir"
            test_dir.mkdir()
            (test_dir / "test.txt").write_text("test")

            assert test_dir.exists()
            safe_remove(test_dir)
            assert not test_dir.exists()

    def test_ensure_output_dir(self):
        """测试确保输出目录存在"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output" / "subdir"
            ensure_output_dir(output_dir)
            assert output_dir.exists()
            assert output_dir.is_dir()

    def test_get_output_path_folder(self):
        """测试生成文件夹输出路径"""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "test_folder"
            input_path.mkdir()

            output_path = get_output_path(input_path, "folder")
            assert output_path == input_path.parent / "test_folder"

    def test_get_output_path_cbz(self):
        """测试生成 CBZ 输出路径"""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "test_folder"
            input_path.mkdir()

            output_path = get_output_path(input_path, "cbz")
            assert output_path.suffix == ".cbz"
            assert output_path.stem == "test_folder"

    def test_get_output_path_with_output_dir(self):
        """测试指定输出目录的路径生成"""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input" / "test_folder"
            input_path.mkdir(parents=True)
            output_dir = Path(tmpdir) / "output"

            output_path = get_output_path(input_path, "cbz", output_dir)
            assert output_path.parent == output_dir
            assert output_path.suffix == ".cbz"
