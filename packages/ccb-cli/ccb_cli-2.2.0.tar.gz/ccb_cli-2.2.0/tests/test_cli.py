"""
命令行接口模块的单元测试
"""

import sys
import asyncio
import tempfile
import argparse
from unittest.mock import Mock
from pathlib import Path

from ccb.cli import (
    parse_args,
    collect_sources,
    convert_single,
    ComicBookConverter,
    process_paths,
)
import importlib


class TestCLI:
    """CLI 相关函数单元测试"""

    def test_parse_args(self, monkeypatch):
        monkeypatch.setattr(
            "sys.argv",
            [
                "ccb",
                "input_path",
                "-f",
                "folder",
                "-t",
                "cbz",
                "-o",
                "outdir",
                "-c",
                "-q",
                "-R",
                "-F",
            ],
        )
        args = parse_args()
        assert args.paths == ["input_path"]
        assert args.from_type == "folder"
        assert args.to_type == "cbz"
        assert args.output_dir == "outdir"
        assert args.collect is True
        assert args.quiet is True
        assert args.remove is True
        assert args.force is True

    def test_collect_sources_leaf_and_archive(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            # 叶子目录（无子目录且无归档文件）应该被视为源
            leaf = tmp / "leaf"
            leaf.mkdir()
            sources = collect_sources(leaf)
            assert leaf in sources

            # 当目录包含归档文件时，应包含该归档文件
            archive = tmp / "a.cbz"
            archive.touch()
            sources2 = collect_sources(tmp)
            assert archive in sources2

    def test_convert_single_with_dummy_converter(self):
        # 使用 Mock(spec=...) 作为替身，避免真实 I/O 并让类型检查器识别接口
        converter = Mock(spec=ComicBookConverter)
        converter.convert.return_value = Path("output.mock")

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input"
            input_path.mkdir()
            result = asyncio.run(
                convert_single(converter, input_path, None, "cbz", None, False, False)
            )
            assert isinstance(result, Path)
            assert result.name == "output.mock"

    def test_paths_with_spaces_quoted(self, monkeypatch):
        # 模拟带空格路径，并且在命令行中以引号包裹的情况
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            spaced = tmp / "My Folder With Spaces"
            spaced.mkdir()

            # 当通过 -c 收集模式返回的 paths 含带引号字符串时，process_paths 应正确处理
            args = argparse.Namespace()
            args.paths = [f'"{spaced}"']
            args.from_type = "auto"
            args.to_type = "cbz"
            args.output_dir = None
            args.collect = False
            args.quiet = True
            args.remove = False
            args.force = False

            # 使用 Mock(spec=...) 作为替身，避免真实 I/O
            mock_converter = Mock(spec=ComicBookConverter)
            mock_converter.convert.return_value = Path("output.mock")
            # 使用 monkeypatch 替换转换器构造函数以返回 mock 实例
            module = importlib.import_module("ccb.cli")
            monkeypatch.setattr(module, "ComicBookConverter", lambda: mock_converter)
            # 调用 process_paths 不应抛异常
            process_paths(args)
