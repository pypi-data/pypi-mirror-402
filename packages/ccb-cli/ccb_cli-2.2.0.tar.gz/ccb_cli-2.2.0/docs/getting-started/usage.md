# 基本使用

## 最简单的用法

转换单个文件夹为 CBZ 格式：

```bash
ccb /path/to/your/folder
```

输出文件将保存在同一目录下：`/path/to/your/folder.cbz`

## 指定输出格式

使用 `-t` 参数指定输出格式：

```bash
# 转换为 CBR
ccb -t cbr /path/to/your/folder

# 转换为 CB7
ccb -t cb7 /path/to/your/folder

# 转换为 CBT
ccb -t cbt /path/to/your/folder
```

## 指定输出目录

使用 `-o` 参数指定输出目录：

```bash
ccb /path/to/source -o /dir/to/output
```

## 查看帮助

使用 `-h` 或 `--help` 查看完整的帮助信息：

```bash
ccb -h
```

## 下一步

查看[使用示例](examples.md)了解更多高级用法。

