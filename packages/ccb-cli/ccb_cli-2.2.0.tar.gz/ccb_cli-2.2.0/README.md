# Convert to Comic Book 漫画转转转

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

一个强大的命令行工具，用于将图片文件夹或压缩包转换为漫画书格式（CBZ、CBR、CB7、CBT）。

## 特性

- 🔄 **多格式支持**: 支持文件夹、CBZ、CBR、CB7、CBT、ZIP、RAR、7Z、TAR 之间的相互转换
- 🚀 **高性能**: 使用异步处理，支持批量转换
- 📦 **灵活配置**: 支持自动识别资源类型、自定义输入输出流等
- 🛡️ **安全可靠**: 完善的错误处理和日志记录
- 🌍 **跨平台**: 支持 Windows、Linux、macOS

## 快速开始

### 安装

```bash
# 最小安装（仅支持 ZIP 和 TAR）
pip install ccb-cli

# 或使用标准安装
pip install ccb-cli[standard]

# 完整安装（扩展支持 RAR 和 7Z）
pip install ccb-cli[full]
```

### 基本使用

```bash
# 转换单个文件夹为 CBZ（-R 转换后删除源目录）
ccb /path/to/single_folder
ccb /path/to/single_folder -R

# 批量转换整个目录下的文件夹为 CBZ（-R 转换后删除叶目录）
ccb -c /path/to/root_folder
ccb -c /path/to/root_folder -R

# 指定多个 CBZ 转换为文件夹
ccb -f cbz -t folder comic_book1.cbz comic_book2.cbz

# 指定导出路径（-F 强制替换同名文件或目录）
ccb /path/to/source -o /dir/to/output
ccb /path/to/source -o /dir/to/output -F
```

## 支持的格式

### 输入格式
- 文件夹 (folder)
- 漫画书格式: CBZ, CBR, CB7, CBT
- 标准压缩格式: ZIP, RAR, 7Z, TAR

### 输出格式
- 文件夹 (folder)
- 漫画书格式: CBZ, CBR, CB7, CBT

### 转换关系

| 输入格式 | 可转换为 |
|---------|---------|
| `folder` | `cbz`, `cbr`, `cb7`, `cbt` |
| `cbz` | `folder`, `cbr`, `cb7`, `cbt` |
| `cbr` | `folder`, `cbz`, `cb7`, `cbt` |
| `cb7` | `folder`, `cbz`, `cbr`, `cbt` |
| `cbt` | `folder`, `cbz`, `cbr`, `cb7` |
| `zip` | `folder`, `cbz`, `cbr`, `cb7`, `cbt` |
| `rar` | `folder`, `cbz`, `cbr`, `cb7`, `cbt` |
| `7z` | `folder`, `cbz`, `cbr`, `cb7`, `cbt` |
| `tar` | `folder`, `cbz`, `cbr`, `cb7`, `cbt` |

## 命令行选项

```
ccb [可选参数] <源列表>

位置参数:
  源列表                目录或文件 (支持 cbz, cbr, cb7, cbt, zip, rar, 7z, tar)

选项:
  -h, --help            显示帮助信息.
  -f, --from-type {auto,folder,cbz,cbr,cb7,cbt,zip,rar,7z,tar}       
                        指定源类型，默认为`auto`
  -t, --to-type {folder,cbz,cbr,cb7,cbt}         
                        指定目标类型，默认为`cbz`（与`to-type`类型一致的源将不参与转换）
  -o, --output-dir OUTPUT_DIR
                        重定向导出目录（默认行为是导出到源所在目录）
  -c, --collect         搜集源列表中所有的叶文件或不含叶文件的叶目录，并作为新的源列表
  -q, --quiet           静默模式，仅显示错误和摘要信息
  -R, --remove          处理完成后删除源列表中所有被转换的源
  -F, --force           强制替换同名的文件或目录（默认行为是覆盖）
  -v, --version         显示版本信息
```

**特殊行为：如果源类型的`from-type`与`to-type`类型一致，则不会对该源进行任何转换或移除处理**

## 许可证

本项目使用 [MIT License](LICENSE) 开源协议。

## 文档

- [GitHub Pages](https://kongolou.github.io/convert-to-comic-book/)
- [Read the Docs](https://convert-to-comic-book.readthedocs.io/)
