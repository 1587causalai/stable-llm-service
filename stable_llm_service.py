#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
稳定大模型调用中间层 (Stable LLM Service)
=========================================

这是一个最小可行的大模型调用中间层实现，专注于提供高稳定性和可靠性。
核心特性:
1. 多服务提供商策略：同时支持OpenAI、Anthropic和Google Gemini
2. 快速限流检测：毫秒级识别API限流情况
3. 多级故障转移：主服务→其他提供商→备用服务的自动转移
4. 智能超时控制：防止请求长时间阻塞
5. 服务健康监控：断路器模式，自动禁用频繁失败的服务

使用方法:
    from stable_llm_service import StableLLMService
    
    # 初始化服务
    llm_service = StableLLMService(
        openai_api_key="your-openai-key",
        anthropic_api_key="your-anthropic-key",
        gemini_api_key="your-gemini-key"
    )
    
    # 发送聊天请求
    response = llm_service.chat("Hello, how are you?")
    print(response)
    
    # 分析图像(如果模型支持)
    from PIL import Image
    image = Image.open("example.jpg")
    response = llm_service.analyze("Describe this image", image)
    print(response)
"""

import time
import json
import random
import logging
import functools
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Union, Tuple
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from dataclasses import dataclass
import base64
from io import BytesIO
import os
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("StableLLMService")

# 尝试导入大模型依赖，如果不存在则提供安装指南
try:
    import openai
except ImportError:
    logger.warning("未安装OpenAI SDK，请运行: pip install openai")

try:
    import anthropic
except ImportError:
    logger.warning("未安装Anthropic SDK，请运行: pip install anthropic")

try:
    import google.generativeai as genai
except ImportError:
    logger.warning("未安装Google Generative AI SDK，请运行: pip install google-generativeai")

try:
    from PIL import Image
except ImportError:
    logger.warning("未安装PIL库，请运行: pip install pillow")

# =======================
# 配置数据结构
# =======================

@dataclass
class LLMServiceConfig:
    """LLM服务配置"""
    provider: str
    model_name: str
    api_key: str
    max_tokens: int = 2000
    temperature: float = 0.5
    timeout: float = 15.0  # 超时时间(秒)
    is_primary: bool = True  # 是否为主要服务

# =======================
# 服务健康监控器
# =======================

class ServiceHealthMonitor:
    """服务健康监控，实现断路器模式"""
    
    def __init__(self, failure_threshold: int = 3, cool_down_period: float = 60.0):
        """
        初始化健康监控器
        
        Args:
            failure_threshold: 触发断路器的连续失败阈值
            cool_down_period: 冷却期(秒)，在此期间服务将被禁用
        """
        self.failure_counts = {}  # 服务失败计数
        self.disabled_until = {}  # 服务禁用时间
        self.failure_threshold = failure_threshold
        self.cool_down_period = cool_down_period
    
    def is_available(self, service_name: str) -> bool:
        """检查服务是否可用"""
        if service_name in self.disabled_until:
            if time.time() > self.disabled_until[service_name]:
                # 冷却期已过，重新启用服务
                del self.disabled_until[service_name]
                self.failure_counts[service_name] = 0
                logger.info(f"服务 {service_name} 已重新启用")
                return True
            return False
        return True
    
    def record_failure(self, service_name: str) -> None:
        """记录服务失败"""
        count = self.failure_counts.get(service_name, 0) + 1
        self.failure_counts[service_name] = count
        
        if count >= self.failure_threshold:
            # 触发断路器，禁用服务一段时间
            self.disabled_until[service_name] = time.time() + self.cool_down_period
            logger.warning(f"服务 {service_name} 暂时禁用 {self.cool_down_period} 秒")
    
    def record_success(self, service_name: str) -> None:
        """记录服务成功"""
        self.failure_counts[service_name] = 0

# =======================
# 基础LLM服务接口
# =======================

class BaseLLMService:
    """LLM服务的基础抽象类"""
    
    def __init__(self, config: LLMServiceConfig):
        self.config = config
        self.provider = config.provider
        self.model_name = config.model_name
        self.api_key = config.api_key
        self.max_tokens = config.max_tokens
        self.temperature = config.temperature
    
    def chat(self, prompt: str) -> Dict[str, Any]:
        """
        发送聊天请求
        
        Args:
            prompt: 用户提示词
            
        Returns:
            Dict: 包含响应内容的字典
        """
        raise NotImplementedError("Subclass must implement chat()")
    
    def analyze(self, prompt: str, image: 'Image.Image') -> Dict[str, Any]:
        """
        分析图像
        
        Args:
            prompt: 用户提示词
            image: PIL图像对象
            
        Returns:
            Dict: 包含响应内容的字典
        """
        raise NotImplementedError("Subclass must implement analyze()")
    
    @staticmethod
    def encode_image(image: 'Image.Image') -> str:
        """将PIL图像编码为base64字符串"""
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

# =======================
# OpenAI服务实现
# =======================

class OpenAIService(BaseLLMService):
    """OpenAI API服务实现"""
    
    def __init__(self, config: LLMServiceConfig):
        super().__init__(config)
        self.client = openai.OpenAI(api_key=self.api_key)
    
    def chat(self, prompt: str) -> Dict[str, Any]:
        """实现OpenAI聊天"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            return {
                "raw_content": response.choices[0].message.content,
                "provider": self.provider,
                "model": self.model_name,
                "finish_reason": response.choices[0].finish_reason
            }
        except Exception as e:
            raise Exception(f"OpenAI API 错误: {str(e)}")
    
    def analyze(self, prompt: str, image: 'Image.Image') -> Dict[str, Any]:
        """实现OpenAI图像分析"""
        try:
            base64_image = self.encode_image(image)
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            return {
                "raw_content": response.choices[0].message.content,
                "provider": self.provider,
                "model": self.model_name,
                "finish_reason": response.choices[0].finish_reason
            }
        except Exception as e:
            raise Exception(f"OpenAI API 图像分析错误: {str(e)}")

# =======================
# Anthropic服务实现
# =======================

class AnthropicService(BaseLLMService):
    """Anthropic API服务实现"""
    
    def __init__(self, config: LLMServiceConfig):
        super().__init__(config)
        self.client = anthropic.Anthropic(api_key=self.api_key)
    
    def chat(self, prompt: str) -> Dict[str, Any]:
        """实现Anthropic聊天"""
        try:
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return {
                "raw_content": response.content[0].text,
                "provider": self.provider,
                "model": self.model_name,
                "finish_reason": response.stop_reason
            }
        except Exception as e:
            raise Exception(f"Anthropic API 错误: {str(e)}")
    
    def analyze(self, prompt: str, image: 'Image.Image') -> Dict[str, Any]:
        """实现Anthropic图像分析"""
        try:
            base64_image = self.encode_image(image)
            
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{
                    "role": "user", 
                    "content": [
                        {
                            "type": "text", 
                            "text": prompt
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64_image
                            }
                        }
                    ]
                }]
            )
            
            return {
                "raw_content": response.content[0].text,
                "provider": self.provider,
                "model": self.model_name,
                "finish_reason": response.stop_reason
            }
        except Exception as e:
            raise Exception(f"Anthropic API 图像分析错误: {str(e)}")

# =======================
# Google Gemini服务实现
# =======================

class GeminiService(BaseLLMService):
    """Google Gemini API服务实现"""
    
    def __init__(self, config: LLMServiceConfig):
        super().__init__(config)
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=genai.GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_tokens
            )
        )
    
    def chat(self, prompt: str) -> Dict[str, Any]:
        """实现Gemini聊天"""
        try:
            response = self.model.generate_content(prompt)
            
            return {
                "raw_content": response.text,
                "provider": self.provider,
                "model": self.model_name,
                "finish_reason": None  # Gemini不提供finish_reason
            }
        except Exception as e:
            raise Exception(f"Gemini API 错误: {str(e)}")
    
    def analyze(self, prompt: str, image: 'Image.Image') -> Dict[str, Any]:
        """实现Gemini图像分析"""
        try:
            response = self.model.generate_content([prompt, image])
            
            return {
                "raw_content": response.text,
                "provider": self.provider,
                "model": self.model_name,
                "finish_reason": None
            }
        except Exception as e:
            raise Exception(f"Gemini API 图像分析错误: {str(e)}")

# =======================
# 服务工厂
# =======================

class ServiceFactory:
    """LLM服务工厂，创建不同提供商的服务实例"""
    
    @staticmethod
    def create_service(config: LLMServiceConfig) -> BaseLLMService:
        """
        创建LLM服务实例
        
        Args:
            config: 服务配置
            
        Returns:
            BaseLLMService: 服务实例
        """
        if config.provider == "openai":
            return OpenAIService(config)
        elif config.provider == "anthropic":
            return AnthropicService(config)
        elif config.provider == "gemini":
            return GeminiService(config)
        else:
            raise ValueError(f"不支持的服务提供商: {config.provider}")

# =======================
# 稳定LLM服务
# =======================

class StableLLMService:
    """稳定的LLM服务，实现多服务提供商策略和故障转移"""
    
    def __init__(
        self, 
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        service_timeout: float = 10.0,
        failure_threshold: int = 3,
        cool_down_period: float = 60.0,
        service_order: Optional[List[str]] = None
    ):
        """
        初始化稳定LLM服务
        
        Args:
            openai_api_key: OpenAI API密钥
            anthropic_api_key: Anthropic API密钥
            gemini_api_key: Google Gemini API密钥
            service_timeout: 服务超时时间(秒)
            failure_threshold: 触发断路器的连续失败阈值
            cool_down_period: 冷却期(秒)
            service_order: 服务调用顺序
        """
        self.service_timeout = service_timeout
        
        # 从环境变量获取API密钥（如果未提供）
        openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        anthropic_api_key = anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")
        gemini_api_key = gemini_api_key or os.environ.get("GEMINI_API_KEY")
        
        # 初始化服务配置
        self.configs = {}
        
        # 添加主要服务配置
        if openai_api_key:
            self.configs["openai_primary"] = LLMServiceConfig(
                provider="openai",
                model_name="gpt-4o",
                api_key=openai_api_key,
                is_primary=True
            )
            self.configs["openai_fallback"] = LLMServiceConfig(
                provider="openai",
                model_name="gpt-3.5-turbo",
                api_key=openai_api_key,
                is_primary=False
            )
        
        if anthropic_api_key:
            self.configs["anthropic_primary"] = LLMServiceConfig(
                provider="anthropic",
                model_name="claude-3-opus-20240229",
                api_key=anthropic_api_key,
                is_primary=True
            )
            self.configs["anthropic_fallback"] = LLMServiceConfig(
                provider="anthropic",
                model_name="claude-3-haiku-20240307",
                api_key=anthropic_api_key,
                is_primary=False
            )
        
        if gemini_api_key:
            self.configs["gemini_primary"] = LLMServiceConfig(
                provider="gemini",
                model_name="gemini-1.5-pro",
                api_key=gemini_api_key,
                is_primary=True
            )
            self.configs["gemini_fallback"] = LLMServiceConfig(
                provider="gemini",
                model_name="gemini-1.5-flash",
                api_key=gemini_api_key,
                is_primary=False
            )
        
        # 初始化服务缓存
        self.services = {}
        
        # 初始化健康监控器
        self.health_monitor = ServiceHealthMonitor(
            failure_threshold=failure_threshold,
            cool_down_period=cool_down_period
        )
        
        # 设置服务调用顺序
        self.service_order = service_order or self._default_service_order()
        logger.info(f"服务调用顺序: {', '.join(self.service_order)}")
        
        # 初始化基本服务
        self._initialize_services()
    
    def _default_service_order(self) -> List[str]:
        """确定默认服务调用顺序"""
        available_providers = []
        
        # 检查哪些提供商可用
        for config_name in self.configs:
            if "_primary" in config_name:
                provider = config_name.split("_")[0]
                if provider not in available_providers:
                    available_providers.append(provider)
        
        if not available_providers:
            raise ValueError("未配置任何服务提供商，请提供至少一个API密钥")
        
        return available_providers
    
    def _initialize_services(self) -> None:
        """初始化基本服务"""
        for config_name, config in self.configs.items():
            try:
                self.services[config_name] = ServiceFactory.create_service(config)
                logger.info(f"已初始化服务: {config_name} ({config.model_name})")
            except Exception as e:
                logger.error(f"初始化服务 {config_name} 失败: {str(e)}")
    
    def _get_service(self, provider: str, primary: bool = True) -> Optional[BaseLLMService]:
        """获取指定提供商的服务"""
        service_key = f"{provider}_{'primary' if primary else 'fallback'}"
        return self.services.get(service_key)
    
    def _is_rate_limited(self, error: Exception) -> bool:
        """检测是否为限流错误"""
        error_str = str(error).lower()
        
        # 通过错误消息判断是否限流
        rate_limit_keywords = [
            'rate limit', 'ratelimit', 'too many requests', 
            '429', 'quota exceeded', 'capacity', 'throttle'
        ]
        
        # 任何关键词匹配即认为是限流
        for keyword in rate_limit_keywords:
            if keyword in error_str:
                return True
        
        return False
    
    def _call_with_timeout(
        self, 
        service_name: str, 
        method_name: str, 
        *args, 
        **kwargs
    ) -> Dict[str, Any]:
        """带超时控制的服务调用"""
        service = self.services[service_name]
        method = getattr(service, method_name)
        
        with ThreadPoolExecutor() as executor:
            future = executor.submit(method, *args, **kwargs)
            try:
                result = future.result(timeout=self.service_timeout)
                self.health_monitor.record_success(service_name)
                return result
            except TimeoutError:
                self.health_monitor.record_failure(service_name)
                raise Exception(f"服务 {service_name} 响应超时 (>{self.service_timeout}s)")
    
    def _call_service(
        self, 
        method_name: str, 
        *args, 
        **kwargs
    ) -> Dict[str, Any]:
        """
        调用LLM服务，支持自动服务切换
        
        Args:
            method_name: 方法名称，如'chat'或'analyze'
            *args, **kwargs: 传递给具体方法的参数
            
        Returns:
            Dict: 服务响应
        """
        errors = []
        
        # 1. 尝试所有主要服务
        for provider in self.service_order:
            service_name = f"{provider}_primary"
            
            # 检查服务是否可用
            if not self.health_monitor.is_available(service_name):
                logger.warning(f"服务 {service_name} 暂时禁用，跳过")
                errors.append({
                    "service": service_name,
                    "error": "服务暂时禁用（断路器已触发）"
                })
                continue
            
            # 检查服务是否已初始化
            if service_name not in self.services:
                logger.warning(f"服务 {service_name} 未初始化，跳过")
                continue
            
            try:
                logger.info(f"尝试使用服务: {service_name}")
                result = self._call_with_timeout(service_name, method_name, *args, **kwargs)
                logger.info(f"服务 {service_name} 调用成功")
                return result
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"服务 {service_name} 调用失败: {error_msg}")
                
                # 记录失败
                self.health_monitor.record_failure(service_name)
                
                # 记录错误
                errors.append({
                    "service": service_name,
                    "error": error_msg,
                    "is_rate_limited": self._is_rate_limited(e)
                })
                
                # 如果是限流错误，立即尝试下一个服务
                if self._is_rate_limited(e):
                    logger.info(f"检测到限流错误，立即切换到下一个服务")
                
                continue
        
        # 2. 尝试所有备用服务
        logger.info("所有主要服务调用失败，尝试备用服务")
        for provider in self.service_order:
            service_name = f"{provider}_fallback"
            
            # 检查服务是否可用
            if not self.health_monitor.is_available(service_name):
                logger.warning(f"备用服务 {service_name} 暂时禁用，跳过")
                errors.append({
                    "service": service_name,
                    "error": "服务暂时禁用（断路器已触发）"
                })
                continue
            
            # 检查服务是否已初始化
            if service_name not in self.services:
                logger.warning(f"备用服务 {service_name} 未初始化，跳过")
                continue
            
            try:
                logger.info(f"尝试使用备用服务: {service_name}")
                result = self._call_with_timeout(service_name, method_name, *args, **kwargs)
                logger.info(f"备用服务 {service_name} 调用成功")
                return result
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"备用服务 {service_name} 调用失败: {error_msg}")
                
                # 记录失败
                self.health_monitor.record_failure(service_name)
                
                # 记录错误
                errors.append({
                    "service": service_name,
                    "error": error_msg
                })
                
                continue
        
        # 所有服务都失败
        error_msg = "所有LLM服务调用都失败了"
        logger.error(f"{error_msg}: {json.dumps(errors, indent=2)}")
        
        return {
            "error": error_msg,
            "details": errors,
            "raw_content": f"服务调用失败: {error_msg}",
        }
    
    def chat(self, prompt: str) -> Dict[str, Any]:
        """
        发送聊天请求
        
        Args:
            prompt: 用户提示词
            
        Returns:
            Dict: 包含响应内容的字典
        """
        return self._call_service("chat", prompt)
    
    def analyze(self, prompt: str, image: 'Image.Image') -> Dict[str, Any]:
        """
        分析图像
        
        Args:
            prompt: 用户提示词
            image: PIL图像对象
            
        Returns:
            Dict: 包含响应内容的字典
        """
        return self._call_service("analyze", prompt, image)
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        获取所有服务的当前状态
        
        Returns:
            Dict: 服务状态信息
        """
        status = {}
        
        for service_name in self.services:
            status[service_name] = {
                "available": self.health_monitor.is_available(service_name),
                "failure_count": self.health_monitor.failure_counts.get(service_name, 0)
            }
            
            if not self.health_monitor.is_available(service_name):
                cool_down_remaining = self.health_monitor.disabled_until.get(service_name, 0) - time.time()
                status[service_name]["cool_down_remaining"] = max(0, round(cool_down_remaining, 1))
        
        return status

# =======================
# 示例用法
# =======================

def demo_chat():
    """聊天示例"""
    print("=== 聊天示例 ===")
    
    service = StableLLMService(
        # API密钥可以直接提供或通过环境变量设置
        service_timeout=15.0,
        failure_threshold=2,
        cool_down_period=30.0
    )
    
    # 打印服务状态
    print("初始服务状态:")
    print(json.dumps(service.get_service_status(), indent=2))
    
    # 发送聊天请求
    prompt = "用简短的一句话解释什么是断路器模式？"
    print(f"\n发送请求: {prompt}")
    
    response = service.chat(prompt)
    print("\n响应结果:")
    print(json.dumps(response, indent=2, ensure_ascii=False))
    
    # 再次打印服务状态
    print("\n请求后服务状态:")
    print(json.dumps(service.get_service_status(), indent=2))

def demo_image_analysis():
    """图像分析示例"""
    try:
        from PIL import Image
        
        print("\n=== 图像分析示例 ===")
        
        # 创建测试图像 (彩色渐变)
        width, height = 300, 200
        image = Image.new('RGB', (width, height))
        
        for x in range(width):
            for y in range(height):
                r = int(255 * x / width)
                g = int(255 * y / height)
                b = int(255 * (x + y) / (width + height))
                image.putpixel((x, y), (r, g, b))
        
        service = StableLLMService()
        
        # 发送图像分析请求
        prompt = "这是什么样的图像？描述你看到的内容。"
        print(f"\n发送请求: {prompt} (附带测试图像)")
        
        response = service.analyze(prompt, image)
        print("\n响应结果:")
        print(json.dumps(response, indent=2, ensure_ascii=False))
        
    except ImportError:
        print("未安装PIL库，跳过图像分析示例")

def main():
    """主函数"""
    # 检查环境变量是否设置了API密钥
    api_keys_found = any([
        os.environ.get("OPENAI_API_KEY"),
        os.environ.get("ANTHROPIC_API_KEY"),
        os.environ.get("GEMINI_API_KEY")
    ])
    
    if not api_keys_found:
        print("警告: 未找到任何API密钥环境变量。要运行示例，请设置以下环境变量之一:")
        print("  - OPENAI_API_KEY")
        print("  - ANTHROPIC_API_KEY")
        print("  - GEMINI_API_KEY")
        print("\n或者在代码中直接提供API密钥:\n")
        print("  service = StableLLMService(")
        print("      openai_api_key='your-openai-key',")
        print("      anthropic_api_key='your-anthropic-key',")
        print("      gemini_api_key='your-gemini-key'")
        print("  )")
        return
    
    try:
        # 运行聊天示例
        demo_chat()
        
        # 运行图像分析示例
        demo_image_analysis()
        
    except Exception as e:
        print(f"运行示例时出错: {str(e)}")

if __name__ == "__main__":
    main() 