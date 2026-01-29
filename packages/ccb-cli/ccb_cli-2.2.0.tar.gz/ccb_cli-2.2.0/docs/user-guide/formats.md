# 支持的格式

## 输入格式

### 文件夹 (folder)

包含图片文件的文件夹。程序会递归扫描文件夹中的所有图片文件。

**支持的图片格式**:
- `.jpg`, `.jpeg`
- `.png`
- `.gif`
- `.bmp`
- `.webp`
- `.tiff`, `.tif`
- `.ico`
- `.svg`
- `.avif`
- `.heic`

### 漫画书格式

- **CBZ** (`.cbz`): 基于 ZIP 格式的漫画书
- **CBR** (`.cbr`): 基于 RAR 格式的漫画书
- **CB7** (`.cb7`): 基于 7Z 格式的漫画书
- **CBT** (`.cbt`): 基于 TAR 格式的漫画书

### 标准压缩格式

- **ZIP** (`.zip`): ZIP 压缩格式
- **RAR** (`.rar`): RAR 压缩格式（需要 `rarfile` 库）
- **7Z** (`.7z`): 7-Zip 压缩格式（需要 `py7zr` 库）
- **TAR** (`.tar`): TAR 归档格式

## 输出格式

### 文件夹 (folder)

解压后的文件夹，包含所有图片文件。

### 漫画书格式

- **CBZ** (`.cbz`): 基于 ZIP 格式
- **CBR** (`.cbr`): 基于 RAR 格式（需要 `rarfile` 库）
- **CB7** (`.cb7`): 基于 7Z 格式（需要 `py7zr` 库）
- **CBT** (`.cbt`): 基于 TAR 格式

## 转换关系表

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

## 格式要求

### 图片文件夹

一个好的图片文件夹应该：
- 仅包含图片文件

### 压缩包

压缩包应该：
- 包含有效的图片文件
- 格式正确且未损坏
- 可以被相应的库正确读取

## 依赖要求

某些格式需要额外的依赖库：

| 格式 | 依赖库 | 安装方式 |
|-----|--------|---------|
| RAR/CBR | `rarfile >= 4.0` | `pip install rarfile` 或 `uv tool install ccb[full]` |
| 7Z/CB7 | `py7zr >= 0.21.0` | `pip install py7zr` 或 `uv tool install ccb[full]` |

其他格式（ZIP/CBZ, TAR/CBT）使用 Python 标准库，无需额外依赖。

