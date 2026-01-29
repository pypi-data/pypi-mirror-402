# 常见问题

## 安装相关

### Q: 如何安装 CCB？

A: 推荐使用 `uv` 进行安装：

```bash
uv tool install ccb-cli
```

或使用 `pip`:

```bash
pip install ccb-cli
```

### Q: 如何安装完整版本（包含 RAR 和 7Z 支持）？

A: 使用 `[full]` 额外依赖：

```bash
uv tool install ccb-cli[full]
```

或

```bash
pip install ccb-cli[full]
```

### Q: 安装后无法使用 `ccb` 命令？

A: 确保 `uv` 的工具目录在 PATH 环境变量中。使用 `uv` 安装的工具通常位于 `~/.cargo/bin` 或类似位置。

## 使用相关

### Q: 如何处理包含空格的路径？

A: 在 Windows PowerShell 中，使用引号包裹路径：

```powershell
ccb "C:\path with spaces\folder"
```

在 Linux/macOS 中，也可以使用引号：

```bash
ccb "/path with spaces/folder"
```

### Q: 如何处理子文件夹？

A: 使用 `-c` 参数处理子文件夹：

```bash
ccb -c /path/to/folders
```

### Q: 收集模式如何工作？

A: `-c` 参数的作用是搜集源列表中所有的叶文件或不含叶文件的叶目录，并作为新的源列表

### Q: 如何查看详细日志？

A: 默认情况下会显示 INFO 级别的日志。使用 `-q` 参数可以启用静默模式，仅显示错误和摘要。

### Q: 如何指定输出目录？

A: 使用 `-o` 参数：

```bash
ccb /path/to/folder -o /path/to/output
```

### Q: 转换后如何删除源文件？

A: 使用 `--remove` 参数（请谨慎使用）：

```bash
ccb --remove /path/to/folder
```

注意这将删除源列表中的所有源。

如果不想删除整个文件夹，只需要定点清除，请阅读并使用 `-c` 参数。

## 格式相关

### Q: 支持哪些输入格式？

A: 支持文件夹、CBZ、CBR、CB7、CBT、ZIP、RAR、7Z、TAR。

### Q: 支持哪些输出格式？

A: 支持文件夹、CBZ、CBR、CB7、CBT。

### Q: 为什么无法处理 RAR 文件？

A: RAR 格式需要 `rarfile` 库。请安装完整版本：

```bash
uv tool install ccb-cli[full]
```

**注意：基于 `WinRAR` 的商业闭源策略，用户可能需要手动安装 `WinRAR` 专有软件提供外部命令支持。**

### Q: 为什么无法处理 7Z 文件？

A: 7Z 格式需要 `py7zr` 库。请安装完整版本：

```bash
uv tool install ccb-cli[full]
```

## 错误处理

### Q: 遇到 "Path does not exist" 错误？

A: 检查路径是否正确，确保路径存在且可访问。在 Windows 上，注意路径中的空格需要用引号包裹。

### Q: 遇到 "Permission denied" 错误？

A: 确保对输入和输出路径有读写权限。在 Windows 上，可能需要以管理员身份运行。

### Q: 遇到 "Unsupported format" 错误？

A: 检查输入文件格式是否支持。某些格式（如 RAR、7Z）需要安装额外的依赖库。

### Q: 转换失败怎么办？

A: 检查错误日志获取详细信息。确保：
- 输入文件格式正确且未损坏
- 有足够的磁盘空间
- 有读写权限

## 性能相关

### Q: 处理大文件很慢？

A: CCB 使用异步处理提高性能。对于非常大的文件，可能需要一些时间。可以：
- 使用 `-q` 参数减少日志输出
- 确保有足够的磁盘空间和内存
- 考虑分批处理

### Q: 如何批量处理多个文件？

A: 可以同时指定多个路径：

```bash
ccb /path/to/folder1 /path/to/folder2 /path/to/folder3
```

或使用 `-c` 参数：

```bash
ccb -c /path/to/parent/folder
```

## 其他问题

### Q: 如何查看版本信息？

A: 使用 `-v` 或 `--version` 参数：

```bash
ccb --version
```

### Q: 如何获取帮助？

A: 使用 `-h` 或 `--help` 参数：

```bash
ccb -h
```

### Q: 项目在哪里可以找到？

A: 项目托管在 GitHub 上。请查看项目主页获取最新信息。

