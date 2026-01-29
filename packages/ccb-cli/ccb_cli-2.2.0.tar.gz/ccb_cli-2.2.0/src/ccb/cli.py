"""
命令行接口模块
"""

import argparse
import asyncio
import logging
from pathlib import Path
from typing import List, Optional
import time

from . import __version__
from .converter import ComicBookConverter
from .file_detector import detect_file_type, get_comic_format, is_archive_file
from .exceptions import ComicBookError

logger = logging.getLogger(__name__)

PROG_NAME = "Convert to Comic Book"


def parse_args() -> argparse.Namespace:
    """
    解析命令行参数

    Returns:
        解析后的参数对象
    """
    parser = argparse.ArgumentParser(
        prog="ccb",
        description="Convert to Comic Book - Convert image folders or archives to comic book formats.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ccb /path/to/source
  # Remove the whole source when done
  ccb /path/to/source -R

  ccb -c /path/to/root_folder
  # Remove leaf sources under the root folder when done
  ccb -c /path/to/root_folder -R

  ccb -f cbz -t folder comic1.cbz comic2.zip

  ccb /path/to/source -o /dir/to/output -F
        """,
    )

    parser.add_argument(
        "paths",
        nargs="*",
        help="Input files or directories (supports cbz, cbr, cb7, cbt, zip, rar, 7z, tar)",
    )

    parser.add_argument(
        "-f",
        "--from-type",
        choices=[
            "auto",
            "folder",
            "cbz",
            "cbr",
            "cb7",
            "cbt",
            "zip",
            "rar",
            "7z",
            "tar",
        ],
        default="auto",
        help="Source type (default: auto)",
    )

    parser.add_argument(
        "-t",
        "--to-type",
        choices=["folder", "cbz", "cbr", "cb7", "cbt"],
        default="cbz",
        help="Target type (default: cbz)",
    )

    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default=None,
        help="Output directory (default: source directory)",
    )

    parser.add_argument(
        "-c",
        "--collect",
        action="store_true",
        help="Collect leaf sources under given paths, and use them as new input",
    )

    parser.add_argument(
        "-q", "--quiet", action="store_true", help="Quiet mode: show only errors"
    )

    parser.add_argument(
        "-R",
        "--remove",
        action="store_true",
        help="Remove sources after processing (excluding already matching targets)",
    )

    parser.add_argument(
        "-F", "--force", action="store_true", help="Force replace existing targets"
    )

    parser.add_argument(
        "-v", "--version", action="version", version=f"{PROG_NAME} v{__version__}"
    )

    return parser.parse_args()


def collect_sources(path: Path, exclude_to_type: Optional[str] = None) -> List[Path]:
    """
    搜集路径下的所有叶子文件或不含叶子文件的叶子目录

    Args:
        path: 搜索路径

    Returns:
        叶子文件或目录列表
    """
    sources = []

    if not path.exists():
        logger.warning(f"Path does not exist: {path}")
        return sources

    if path.is_file():
        # 叶子文件，检查是否是支持的压缩格式
        if is_archive_file(path):
            detected = detect_file_type(path)
            # 如果提供了排除的 to-type，仅跳过那些已经是目标漫画书格式的文件（例如已为 cbz/cbr/cb7/cbt）
            if exclude_to_type and detected is not None and detected == exclude_to_type:
                return sources
            sources.append(path)
    elif path.is_dir():
        try:
            has_subdirs = False
            has_archive_files = False

            # 记录递归前的sources长度
            before_recursive = len(sources)

            for item in path.iterdir():
                if item.is_file():
                    # 检查是否是支持的压缩格式
                    if is_archive_file(item):
                        detected_item = detect_file_type(item)
                        # 如果提供了排除的 to-type，跳过已经是目标漫画书格式的文件
                        if (
                            exclude_to_type
                            and detected_item is not None
                            and detected_item == exclude_to_type
                        ):
                            continue
                        has_archive_files = True
                        sources.append(item)
                elif item.is_dir():
                    has_subdirs = True
                    # 递归搜集子目录中的源
                    sources.extend(
                        collect_sources(item, exclude_to_type=exclude_to_type)
                    )

            # 计算递归后新增的源数量
            added_sources = len(sources) - before_recursive

            # 如果目录不含子目录且不含压缩文件，或者含子目录但递归后没有新增源（说明子目录中也没有压缩文件）
            if (not has_subdirs and not has_archive_files) or (
                has_subdirs and added_sources == 0
            ):
                sources.append(path)
        except (PermissionError, OSError) as e:
            logger.warning(f"Error accessing directory {path}: {e}")
            return sources

    return sources


async def convert_single(
    converter: ComicBookConverter,
    input_path: Path,
    from_type: Optional[str],
    to_type: str,
    output_dir: Optional[Path],
    remove_source: bool,
    force: bool,
) -> Optional[Path]:
    """
    异步转换单个文件或文件夹

    Args:
        converter: 转换器实例
        input_path: 输入路径
        from_type: 输入类型（如果为None则自动检测）
        to_type: 输出类型
        output_dir: 输出目录
        remove_source: 是否删除源文件

    Returns:
        输出路径，如果失败返回None
    """
    try:
        # 如果指定了输入类型，需要验证
        if from_type:
            detected_type = detect_file_type(input_path)
            if detected_type != from_type:
                logger.warning(
                    f"Specified type '{from_type}' does not match detected type '{detected_type}' "
                    f"for {input_path}"
                )

        result = await asyncio.get_event_loop().run_in_executor(
            None,
            converter.convert,
            input_path,
            to_type,
            output_dir,
            remove_source,
            force,
        )
        return result
    except Exception as e:
        logger.error(f"Failed to convert {input_path}: {e}")
        return None


def process_paths(args: argparse.Namespace) -> None:
    """
    处理路径列表

    Args:
        args: 命令行参数
    """
    # 配置日志
    if args.quiet:
        logging.basicConfig(level=logging.ERROR, format="%(levelname)s %(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if not args.paths:
        logger.error("No input paths provided")
        return

    converter = ComicBookConverter()
    # 处理输出目录路径，移除可能的引号
    output_dir = Path(args.output_dir.strip("\"'")) if args.output_dir else None

    # 收集要处理的路径
    paths_to_process = []

    if args.collect:
        # 收集模式：查找叶子文件或不含叶子文件的叶子目录
        for path_str in args.paths:
            # 处理路径字符串，移除可能的引号（Windows PowerShell 可能会保留引号）
            path_str = path_str.strip("\"'")
            path = Path(path_str)

            # 检查路径是否存在
            if not path.exists():
                logger.warning(f"Path does not exist: {path}")
                continue

            collected = collect_sources(path)
            # 在收集模式下，排除已经是目标类型的文件（如 to-type=cbz 时跳过 cbz/zip 映射后的文件）
            collected = collect_sources(path, exclude_to_type=args.to_type)
            if collected:
                # 当通过 -c 参数生成源列表时，统一使用带引号的路径字符串表示（便于在 shell/PowerShell 中复用）
                quoted = [f'"{p}"' for p in collected]
                paths_to_process.extend(quoted)
                if not args.quiet:
                    logger.info(f"Collected {len(collected)} source(s) from: {path}")
            else:
                if not args.quiet:
                    logger.info(f"No sources collected from: {path}")
    else:
        # 普通模式：处理指定的路径
        for path_str in args.paths:
            # 处理路径字符串，移除可能的引号（Windows PowerShell 可能会保留引号）
            path_str = path_str.strip("\"'")
            path = Path(path_str)

            # 检查路径是否存在
            if not path.exists():
                logger.warning(f"Path does not exist: {path}")
                continue

            if path.is_dir():
                paths_to_process.append(path)
            elif path.is_file():
                paths_to_process.append(path)
            else:
                logger.warning(
                    f"Invalid path (exists but is neither file nor directory): {path}"
                )

    if not paths_to_process:
        logger.warning("No valid paths to process")
        return

    # 异步处理所有路径
    start_time = time.time()

    async def process_all():
        tasks = []
        for input_path in paths_to_process:
            # 支持 paths_to_process 中既有 Path 对象也有带引号的字符串（来自 -c 模式）
            if isinstance(input_path, str):
                path_str = input_path.strip("\"'")
                input_path = Path(path_str)

            # 确定输入类型
            from_type = args.from_type
            if from_type == "auto":
                detected = detect_file_type(input_path)
                from_type = detected

            # 确定输出类型
            to_type = args.to_type
            if args.collect and from_type in ["zip", "rar", "7z", "tar"]:
                # 收集模式下，标准格式自动映射到对应的漫画书格式
                # 但如果用户指定了输出类型，使用用户指定的类型
                if to_type == "cbz":  # 默认值，使用映射
                    to_type = get_comic_format(from_type)

            task = convert_single(
                converter,
                input_path,
                from_type,
                to_type,
                output_dir,
                args.remove,
                args.force,
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        return results

    try:
        results = asyncio.run(process_all())
        elapsed_time = time.time() - start_time

        successful = sum(1 for r in results if r is not None)
        total = len(results)

        if not args.quiet:
            print(f"\nDone in {elapsed_time:.2f}s")
            print(f"Processed {successful}/{total} files successfully")
        elif successful < total:
            print(f"Processed {successful}/{total} files successfully")
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error during processing: {e}")


def main() -> None:
    """主程序入口"""
    args = parse_args()
    try:
        process_paths(args)
    except ComicBookError as e:
        logger.error(f"ComicBook error: {e}")
        exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        exit(1)
