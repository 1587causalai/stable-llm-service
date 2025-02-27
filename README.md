# 稳定大模型调用中间层

![Python Package](https://github.com/1587causalai/stable-llm-service/workflows/Python%20Package/badge.svg)
[![PyPI version](https://badge.fury.io/py/stable-llm-service.svg)](https://badge.fury.io/py/stable-llm-service)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

这是一个完全独立的大模型调用中间层实现，专注于提供高稳定性和可靠性。它集成了多个LLM服务提供商(OpenAI、Anthropic和Google Gemini)，并通过多种策略确保API调用在高并发和限流场景下的可靠性。

本项目是一个轻量级、自包含的解决方案，不依赖于任何其他特定项目，可以直接集成到您的应用程序中。

## 核心特性

1. **多服务提供商策略**
   - 同时支持OpenAI、Anthropic和Google Gemini
   - 服务优先级排序和智能切换
   - 限流时立即切换，不等待重试间隔

2. **快速限流检测机制**
   - 毫秒级识别API限流情况
   - 基于错误代码和消息模式的智能判断

3. **多级故障转移系统**
   - 主要服务 → 其他提供商 → 备用服务的转移路径
   - 高性能模型与轻量级模型的组合策略

4. **智能超时控制**
   - 使用线程池实现超时控制
   - 可配置的超时参数，避免单个请求阻塞系统

5. **服务健康监控**
   - 断路器模式，暂时禁用频繁失败的服务
   - 自动冷却期后恢复服务
   - 全面的服务状态监控

## 安装指南

### 前提条件

- Python 3.8+
- 至少一个大模型服务的API密钥(OpenAI、Anthropic或Google Gemini)

### 从PyPI安装

```bash
pip install stable-llm-service
```

### 从源码安装

```bash
git clone https://github.com/yourusername/stable-llm-service.git
cd stable-llm-service
pip install -e .
```

### 设置API密钥

设置环境变量(或在代码中直接提供)
```bash
# Linux/Mac
export OPENAI_API_KEY=your-openai-key
export ANTHROPIC_API_KEY=your-anthropic-key
export GEMINI_API_KEY=your-gemini-key

# Windows
set OPENAI_API_KEY=your-openai-key
set ANTHROPIC_API_KEY=your-anthropic-key
set GEMINI_API_KEY=your-gemini-key
```

## 使用方法

### 命令行工具

安装后，您可以使用以下命令行工具:

#### 聊天

```bash
stable-llm-chat
```

交互式聊天，或传递单个提示词:

```bash
stable-llm-chat --prompt "用简短的一句话解释什么是量子计算"
```

#### 图像分析

```bash
stable-llm-analyze image.jpg
```

自定义提示词:

```bash
stable-llm-analyze image.jpg --prompt "这张图片中有什么不寻常的东西？"
```

### 作为Python库使用

#### 基本用法

```python
from stable_llm_service import StableLLMService

# 初始化服务
service = StableLLMService(
    # 可以直接提供API密钥或通过环境变量设置
    openai_api_key="your-openai-key",
    anthropic_api_key="your-anthropic-key",
    gemini_api_key="your-gemini-key",
    service_timeout=10.0,  # 服务超时时间(秒)
    failure_threshold=3,   # 触发断路器的失败阈值
    cool_down_period=60.0  # 服务禁用冷却期(秒)
)

# 发送聊天请求
response = service.chat("Hello, how are you?")
print(response["raw_content"])

# 图像分析(如果支持)
from PIL import Image
image = Image.open("example.jpg")
response = service.analyze("Describe this image", image)
print(response["raw_content"])

# 查看服务状态
status = service.get_service_status()
print(status)
```

#### 配置优先级顺序

您可以自定义LLM服务的调用顺序：

```python
service = StableLLMService(
    service_order=["anthropic", "openai", "gemini"]  # 先尝试Anthropic，然后OpenAI，最后Gemini
)
```

### 示例程序

项目包含了一些示例程序，您可以查看`examples`目录:

```bash
# 简单聊天示例
python -m stable_llm_service.examples.simple_chat

# 图像分析示例
python -m stable_llm_service.examples.image_analysis --image path/to/your/image.jpg
```

## 集成到现有项目

只需将`stable_llm_service`包导入到您的项目中，并根据需要进行使用。包是完全独立的，不需要任何外部依赖（除了标准库和指定的第三方库）。

## 可定制化

该服务设计为高度可定制：

- 可以调整每个模型的配置（超时、温度等）
- 可以修改断路器参数（失败阈值、冷却期）
- 可以扩展支持其他LLM提供商

## 适用场景

- 需要高可靠性的生产环境
- 处理高并发LLM请求的应用
- 对API限流敏感的系统
- 需要快速响应的交互式应用
- 希望平衡成本和性能的混合模型策略

## 贡献

欢迎贡献！请查看[贡献指南](CONTRIBUTING.md)获取更多信息。

## 许可证

MIT 