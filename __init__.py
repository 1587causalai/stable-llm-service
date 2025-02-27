"""
稳定大模型调用中间层 (Stable LLM Service)
=========================================

提供一个稳定可靠的大模型调用中间层，支持多服务提供商策略、快速限流检测、
多级故障转移、智能超时控制和服务健康监控。

主要类:
- StableLLMService: 稳定的LLM服务，主要对外接口
- ServiceHealthMonitor: 服务健康监控器，实现断路器模式
"""

from .stable_llm_service import (
    StableLLMService,
    ServiceHealthMonitor,
    BaseLLMService,
    LLMServiceConfig
)

__version__ = "0.1.0" 