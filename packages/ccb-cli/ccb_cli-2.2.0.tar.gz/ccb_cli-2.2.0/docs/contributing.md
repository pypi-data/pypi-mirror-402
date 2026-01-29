# 贡献指南

感谢您对 Convert to Comic Book 项目的关注！我们欢迎所有形式的贡献。

## 如何贡献

### 报告问题

如果您发现了 bug 或有功能建议，请：

1. 检查 [Issues](https://github.com/yourusername/convert-to-comic-book/issues) 是否已有相关问题
2. 如果没有，请创建新的 Issue，包含：
   - 问题描述
   - 复现步骤
   - 预期行为
   - 实际行为
   - 环境信息（操作系统、Python 版本等）

### 提交代码

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 代码规范

- 遵循 PEP 8 代码风格
- 使用类型提示
- 添加适当的文档字符串
- 为新功能添加测试
- 确保所有测试通过

### 运行测试

在提交代码前，请确保所有测试通过：

```bash
pytest tests/
```

### 代码格式化

使用 `ruff` 进行代码格式化和检查：

```bash
# 检查代码
ruff check

# 格式化代码
ruff format
```

## 开发环境设置

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/convert-to-comic-book.git
cd convert-to-comic-book
```

2. 安装开发依赖：
```bash
uv sync --group dev
```

3. 运行测试：
```bash
pytest tests/
```

## 文档贡献

文档改进同样欢迎！请：

1. 检查文档的准确性和清晰度
2. 添加使用示例
3. 改进文档结构
4. 修复拼写和语法错误

## 行为准则

请遵守项目的行为准则，保持友好和尊重的交流环境。

## 许可证

通过贡献代码，您同意您的贡献将在 MIT 许可证下发布。

