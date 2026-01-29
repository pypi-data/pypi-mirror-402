# CHANGELOG
## [2.2.0] - 2026-01-20
### Added
- 解决了[issues#2 Can't convert to cbr](https://github.com/26350/convert-to-comic-book/issues/2)

## [2.1.0] - 2026-01-18
### Added
- 解决了[issues#1 空文件夹被识别为有效的源](https://github.com/26350/convert-to-comic-book/issues/1)
- 修复项目文件

## [2.0.11] - 2026-01-11
### Updated
- 解决安装后`ccb`命令无法找到模块的问题

## [2.0.10] - 2026-01-11
### Updated
- 更改项目名称为`ccb-cli`

## [2.0.9] - 2026-01-11
### Updated
- 去除`cli.py`中指令帮助信息的句号
- 更新了 Google 风格的代码注释

## [2.0.8] - 2026-01-10
### Updated
- 更新`README.md`和`cli.py`中指令的帮助信息

## [2.0.7] - 2026-01-10
### Updated
- 新增`package-dir = {"" = "src"}`配置，支持src布局
- 修复Hatchling构建配置，将`packages = ["src/ccb"]`改为`sources = ["src"]`

## [2.0.0] - 2026-01-08

### Deleted
- 删除`-r`或`--recursive`参数
- 删除`--output`参数

### Added
- 新增`-R`参数，对应`--remove`参数
- 新增`-F`或`--force`参数，强制替换存在同名文件
- `-f`或`--from-type`参数新增`auto`选项，且默认值改为`auto`
- 新增`--output-dir`参数
- 更新文档与测试

### Updated
- 更改`-c`或`--collect`参数执行逻辑
- 修复使用`--remove`参数不能删除文件夹的问题
- 调整项目结构，将`ccb`目录迁移至`src`目录下，采用src布局

## [1.0.0] - 2026-01-02

### Added
- 初始版本发布
