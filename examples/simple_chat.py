#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单聊天示例
===========

演示如何使用StableLLMService进行基本的聊天交互。
"""

import os
import sys
import json

# 添加父级目录到路径，以便可以导入stable_llm_service
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 直接从我们的包导入
from stable_llm_service import StableLLMService

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
        return
    
    # 初始化服务
    service = StableLLMService(
        service_timeout=15.0,
        failure_threshold=2,
        cool_down_period=30.0
    )
    
    # 打印服务状态
    print("服务状态:")
    print(json.dumps(service.get_service_status(), indent=2))
    
    # 进入聊天循环
    print("\n=== 开始聊天 (输入'exit'退出) ===")
    
    while True:
        user_input = input("\n用户: ")
        
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("再见！")
            break
        
        # 发送聊天请求
        print("AI: ", end="", flush=True)
        
        response = service.chat(user_input)
        
        if "error" in response:
            print(f"错误: {response['error']}")
        else:
            print(response["raw_content"])

if __name__ == "__main__":
    main() 