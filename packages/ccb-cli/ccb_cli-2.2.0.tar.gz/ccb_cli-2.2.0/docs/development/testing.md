# 测试

## 运行测试

### 运行所有测试

```bash
pytest tests/
```

### 运行特定测试文件

```bash
pytest tests/test_converter.py
```

### 运行特定测试

```bash
pytest tests/test_converter.py::TestComicBookConverter::test_convert_folder_to_archive
```

### 查看测试覆盖率

```bash
pytest --cov=ccb tests/
```

生成覆盖率报告：

```bash
pytest --cov=ccb --cov-report=html tests/
```

## 测试覆盖

所有核心模块都有对应的单元测试：
- 文件类型检测：100% 覆盖
- 压缩/解压处理：ZIP 和 TAR 格式完整测试
- 转换逻辑：主要转换路径都有测试
- 工具函数：所有函数都有测试
- CLI 接口：基本功能和参数组合测试

### 在 Windows 虚拟环境中运行测试

如果你在 Windows 上使用项目自带或推荐的虚拟环境（例如 `.venv`），可以按如下方式运行测试：

```powershell
# 激活虚拟环境（如果尚未激活）
& ./.venv/Scripts/Activate.ps1

# 运行全部测试
pytest -q

# 仅运行 CLI 测试
pytest -q tests/test_cli.py
```

测试中包含对 CLI 行为的验证，例如对带空格的路径（在 PowerShell/命令行中常用引号包裹）处理的用例，确保在不同 shell 下路径解析正确。

## 编写新测试

### 测试文件命名

测试文件应以 `test_` 开头，例如 `test_new_feature.py`。

### 测试类命名

测试类应以 `Test` 开头，例如 `TestNewFeature`。

### 测试函数命名

测试函数应以 `test_` 开头，例如 `test_new_functionality`。

### 示例

```python
import pytest
from pathlib import Path
from ccb.converter import ComicBookConverter

class TestNewFeature:
    """新功能测试类"""
    
    def test_new_functionality(self):
        """测试新功能"""
        converter = ComicBookConverter()
        # 测试代码
        assert True
```

## 持续集成

项目使用 GitHub Actions 进行持续集成，自动运行测试。

