# 安装

## 环境要求

- Python 3.10 或更高版本
- uv (推荐) 或 pip

## 使用 uv 安装（推荐）

### 最小安装

最小安装仅支持 ZIP 和 TAR 格式：

```bash
uv tool install ccb-cli
```

或

```bash
uv tool install ccb-cli[standard]
```

### 完整安装

完整安装包含所有格式支持（需要 RAR 和 7Z 支持）：

```bash
uv tool install ccb[full]
```

完整安装将安装以下可选依赖：
- `rarfile >= 4.0`: 用于 RAR/CBR 支持
- `py7zr >= 0.21.0`: 用于 7Z/CB7 支持

## 使用 pip 安装

```bash
# 最小安装
pip install ccb-cli

# 完整安装
pip install ccb-cli[full]
```

## 验证安装

安装完成后，可以通过以下命令验证：

```bash
ccb --version
```

应该显示版本信息，例如：
```
Convert to Comic Book v1.0.0
```

## 下一步

安装完成后，请查看[基本使用](usage.md)了解如何使用 CCB。

