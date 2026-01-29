# dceapi-py Development Guide

## 开发环境设置

### 安装依赖

```bash
# 克隆仓库
git clone https://github.com/pseudocodes/dceapi-py.git
cd dceapi-py

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
.\venv\Scripts\activate  # Windows

# 安装开发依赖
pip install -e ".[dev]"
```

## 项目结构

```
dceapi-py/
├── src/dceapi/          # 源代码
│   ├── __init__.py      # 包入口
│   ├── client.py        # 客户端
│   ├── config.py        # 配置
│   ├── errors.py        # 错误定义
│   ├── http.py          # HTTP 客户端
│   ├── models.py        # 数据模型
│   ├── token.py         # Token 管理
│   └── services/        # API 服务
│       ├── common.py
│       ├── news.py
│       ├── market.py
│       └── ...
├── tests/               # 测试
├── examples/            # 示例
├── pyproject.toml       # 项目配置
└── README.md            # 文档
```

## 开发工作流

### 1. 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_config.py

# 查看覆盖率
pytest --cov=dceapi --cov-report=html
```

### 2. 代码格式化

```bash
# 格式化代码
black src/ tests/ examples/

# 检查格式
black --check src/ tests/ examples/
```

### 3. 代码检查

```bash
# 运行 ruff
ruff check src/ tests/

# 自动修复
ruff check --fix src/ tests/
```

### 4. 类型检查

```bash
# 运行 mypy
mypy src/
```

## 添加新功能

### 1. 添加新的 API 服务

在 `src/dceapi/services/` 目录下创建新文件：

```python
# src/dceapi/services/new_service.py
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..http import BaseClient


class NewService:
    """新服务描述."""

    def __init__(self, client: "BaseClient") -> None:
        self.client = client

    def some_method(self):
        """方法描述."""
        pass
```

在 `src/dceapi/services/__init__.py` 中导出：

```python
from .new_service import NewService

__all__ = [..., "NewService"]
```

在 `src/dceapi/client.py` 中初始化：

```python
from .services import NewService

class Client:
    def __init__(self, config: Config):
        # ...
        self.new_service = NewService(self._base_client)
```

### 2. 添加新的数据模型

在 `src/dceapi/models.py` 中添加：

```python
@dataclass
class NewModel:
    """新模型描述."""
    field1: str
    field2: int
```

### 3. 编写测试

在 `tests/` 目录下创建对应的测试文件：

```python
# tests/test_new_service.py
import pytest
from dceapi import Client, Config


def test_new_service():
    """测试新服务."""
    config = Config(api_key="test", secret="test")
    client = Client(config)
    # 编写测试逻辑
```

## 发布流程

### 1. 更新版本号

编辑 `src/dceapi/__init__.py`：

```python
__version__ = "0.2.0"
```

编辑 `pyproject.toml`：

```toml
[project]
version = "0.2.0"
```

### 2. 构建分发包

```bash
# 清理旧的构建
rm -rf dist/ build/

# 构建
python -m build
```

### 3. 上传到 PyPI

```bash
# 上传到测试 PyPI
python -m twine upload --repository testpypi dist/*

# 上传到正式 PyPI
python -m twine upload dist/*
```

## 编码规范

- 遵循 PEP 8
- 使用类型提示
- 编写文档字符串（Google 风格）
- 保持函数简短且职责单一
- 编写测试覆盖新功能

## Git 工作流

1. 从 main 分支创建功能分支
2. 开发并测试新功能
3. 提交前运行所有检查
4. 创建 Pull Request
5. Code Review
6. 合并到 main

## 常见问题

### Q: 如何调试 API 请求？

可以启用 requests 库的调试日志：

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```

### Q: 如何添加新的错误类型？

在 `src/dceapi/errors.py` 中添加新的异常类：

```python
class NewError(DCEAPIException):
    """新错误类型."""
    pass
```

## 资源

- [项目主页](https://github.com/pseudocodes/dceapi-py)
- [DCE API 文档](http://www.dce.com.cn)
- [Python Packaging Guide](https://packaging.python.org/)
