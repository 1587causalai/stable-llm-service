# 贡献指南

感谢您考虑为Stable LLM Service项目做出贡献！这份指南将帮助您了解如何参与该项目的开发。

## 开发环境设置

1. 克隆仓库:
   ```bash
   git clone https://github.com/yourusername/stable-llm-service.git
   cd stable-llm-service
   ```

2. 创建虚拟环境:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或
   venv\Scripts\activate  # Windows
   ```

3. 安装开发依赖:
   ```bash
   pip install -e ".[dev]"  # 安装开发依赖
   ```

## 代码风格

我们使用以下工具确保代码质量和一致性:

- [Black](https://black.readthedocs.io/): 用于代码格式化
- [isort](https://pycqa.github.io/isort/): 用于导入排序
- [Flake8](https://flake8.pycqa.org/): 用于代码风格检查

在提交代码前，请运行:

```bash
black .
isort .
flake8 .
```

## 测试

确保添加或修改代码时也更新或添加相应的测试。我们使用`pytest`进行测试:

```bash
pytest
```

运行覆盖率报告:

```bash
pytest --cov=stable_llm_service tests/
```

## 提交Pull Request

1. 创建一个分支:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. 进行更改并遵循代码风格规范

3. 编写测试

4. 提交更改:
   ```bash
   git commit -m "Add feature X"
   ```

5. 推送到您的分支:
   ```bash
   git push origin feature/your-feature-name
   ```

6. 打开Pull Request

## 添加新的LLM服务提供商

如果您想添加新的LLM服务提供商，请遵循以下步骤:

1. 在`stable_llm_service.py`中创建一个新的服务类，继承自`BaseLLMService`
2. 实现所需的方法(`chat`和`analyze`)
3. 更新`ServiceFactory`以支持新的提供商
4. 添加相应的测试
5. 更新文档

## 问题和功能请求

如果您发现问题或有功能请求，请在GitHub的Issues页面上提交它们。

## 许可证

通过贡献代码，您同意将其许可证授予与项目相同的MIT许可证。 