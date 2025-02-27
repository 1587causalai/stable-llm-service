# 稳定大模型调用中间层 - 快速入门指南

这份快速入门指南将帮助您在几分钟内开始使用稳定大模型调用中间层。

## 📋 功能概览

- 同时支持 OpenAI、Anthropic 和 Google Gemini 的最新模型
- 自动故障转移和服务切换
- 快速限流检测和处理
- 文本对话和图像分析支持

## 🚀 快速安装

```bash
# 从 PyPI 安装
pip install stable-llm-service

# 或从源码安装
git clone https://github.com/yourusername/stable-llm-service.git
cd stable-llm-service
pip install -e .
```

## ⚙️ 配置 API 密钥

创建 `.env` 文件，填入您的 API 密钥（至少需要一个）：

```
# OpenAI API密钥
OPENAI_API_KEY=your-openai-api-key-here

# Anthropic API密钥
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Google Gemini API密钥
GEMINI_API_KEY=your-gemini-api-key-here

# 可选：配置服务调用顺序
SERVICE_ORDER=openai,anthropic,gemini
```

## 💬 基本用法

### Python 库方式

```python
from stable_llm_service import StableLLMService

# 初始化服务（会自动从.env加载密钥）
service = StableLLMService()

# 或手动指定参数
service = StableLLMService(
    openai_api_key="your-openai-key",  # 可选
    service_timeout=15.0,  # 超时时间(秒)
    service_order=["anthropic", "openai", "gemini"]  # 调用顺序
)

# 发送聊天请求
response = service.chat("Hello, how are you?")
print(response["raw_content"])

# 检查服务状态
print(service.get_service_status())
```

### 图像分析

```python
from PIL import Image
from stable_llm_service import StableLLMService

# 初始化服务
service = StableLLMService()

# 加载图像
image = Image.open("example.jpg")

# 发送图像分析请求
response = service.analyze("描述这张图片", image)
print(response["raw_content"])
```

## 🖥️ 命令行工具

### 聊天模式

```bash
# 交互式聊天
stable-llm-chat

# 单次提问
stable-llm-chat --prompt "用简短的一句话解释什么是量子计算"

# 指定服务顺序
stable-llm-chat --service-order anthropic,openai,gemini
```

### 图像分析

```bash
# 分析图像
stable-llm-analyze image.jpg

# 自定义提示词
stable-llm-analyze image.jpg --prompt "这张图片中有什么不寻常的东西？"
```

## ⚡ 最小可行示例

最快的体验方式:

1. 创建 `.env` 文件，添加至少一个 API 密钥
2. 运行以下任一命令:

```bash
# 聊天
stable-llm-chat

# 图像分析（用您自己的图像）
stable-llm-analyze path/to/your/image.jpg
```

## 🔄 自定义服务顺序

您可以通过以下方式自定义服务的调用顺序（按优先级从高到低）：

1. **初始化时设置**（最高优先级）:
   ```python
   service = StableLLMService(service_order=["anthropic", "openai", "gemini"])
   ```

2. **环境变量设置**（中优先级）:
   ```
   # 在.env文件中
   SERVICE_ORDER=gemini,openai,anthropic
   
   # 或直接在终端中
   export SERVICE_ORDER=gemini,openai,anthropic
   ```

3. **命令行参数**（命令行工具专用）:
   ```bash
   stable-llm-chat --service-order anthropic,openai,gemini
   ```

4. **默认顺序**（最低优先级）:
   如果没有指定服务顺序，将根据配置的 API 密钥自动确定默认顺序。

### 验证服务顺序

您可以运行测试脚本来验证服务顺序设置是否生效：

```bash
python -m stable_llm_service.examples.test_service_order
```

或查看日志输出中的服务调用顺序信息：

```
INFO - 服务调用顺序: openai, anthropic, gemini
```

## ❓ 常见问题

### Q: 为什么报错"未配置任何服务提供商"？
A: 您需要提供至少一个 API 密钥，可以通过环境变量、`.env` 文件或直接在代码中设置。

### Q: 如何查看服务状态？
A: 使用 `service.get_service_status()` 方法查看每个服务的当前状态，包括可用性和失败计数。

### Q: 如何处理服务限流？
A: 服务会自动检测限流并切换到下一个可用服务，您无需手动处理。

### Q: 如何处理超时？
A: 调整 `service_timeout` 参数，默认为10秒，图像分析可能需要更长时间。

### Q: 使用了哪些模型？
A: 系统使用了最新一代的大模型：
   - 主要模型: ChatGPT-4o latest, Claude 3.7 Sonnet, Gemini 2.0 Flash
   - 备用模型: GPT-4o Mini, Claude 3.5 Sonnet, Gemini 2.0 Pro
   - 额外备选: Gemini 2.0 Flash Lite (仅Gemini提供)

---

更详细的用法和配置选项，请参阅完整的 [README](README.md) 和 [API文档](API.md)。 