#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务调用顺序测试
==============

测试环境变量和参数对服务调用顺序的影响。
"""

import os
import sys
import json

# 添加父级目录到路径，以便可以导入stable_llm_service
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 直接从我们的包导入
from stable_llm_service import StableLLMService

def test_service_order():
    """测试不同方式设置服务调用顺序"""
    print("=== 服务调用顺序测试 ===\n")
    
    # 1. 测试默认顺序
    print("1. 默认顺序测试:")
    try:
        service = StableLLMService()
        print(f"   默认服务顺序: {', '.join(service.service_order)}")
    except Exception as e:
        print(f"   错误: {str(e)}")
    
    # 2. 测试通过参数设置
    print("\n2. 通过参数设置顺序测试:")
    custom_order = ["anthropic", "gemini", "openai"]
    try:
        service = StableLLMService(service_order=custom_order)
        print(f"   设置顺序: {', '.join(custom_order)}")
        print(f"   实际顺序: {', '.join(service.service_order)}")
    except Exception as e:
        print(f"   错误: {str(e)}")
    
    # 3. 测试通过环境变量设置
    print("\n3. 通过环境变量设置顺序测试:")
    env_order = "gemini,openai,anthropic"
    original_env = os.environ.get("SERVICE_ORDER")
    
    try:
        os.environ["SERVICE_ORDER"] = env_order
        service = StableLLMService()
        print(f"   环境变量设置: SERVICE_ORDER={env_order}")
        print(f"   实际顺序: {', '.join(service.service_order)}")
    except Exception as e:
        print(f"   错误: {str(e)}")
    finally:
        # 恢复原始环境变量
        if original_env:
            os.environ["SERVICE_ORDER"] = original_env
        else:
            if "SERVICE_ORDER" in os.environ:
                del os.environ["SERVICE_ORDER"]
    
    print("\n结论: 如果三次测试的顺序都不同，则说明所有设置方式都有效。")
    print("优先级: 参数设置 > 环境变量设置 > 默认顺序")

if __name__ == "__main__":
    test_service_order() 