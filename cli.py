#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
命令行界面
=========

提供StableLLMService的命令行界面，使其可以直接从终端使用。

使用方式:
- 聊天: `stable-llm-chat`
- 图像分析: `stable-llm-analyze image.jpg`
"""

import os
import sys
import argparse
import json
from PIL import Image

from .stable_llm_service import StableLLMService

def chat_command():
    """提供交互式聊天命令行界面"""
    parser = argparse.ArgumentParser(description="与大模型进行聊天")
    parser.add_argument("--timeout", type=float, default=15.0, help="服务超时时间(秒)")
    parser.add_argument("--service-order", type=str, help="逗号分隔的服务调用顺序，例如：openai,anthropic,gemini")
    parser.add_argument("--prompt", type=str, help="直接传递的提示词，而非交互式聊天")
    parser.add_argument("--json", action="store_true", help="以JSON格式输出结果")
    args = parser.parse_args()
    
    # 解析服务顺序
    service_order = None
    if args.service_order:
        service_order = args.service_order.split(",")
    
    # 初始化服务
    try:
        service = StableLLMService(
            service_timeout=args.timeout,
            service_order=service_order
        )
    except Exception as e:
        print(f"初始化服务失败: {str(e)}")
        print("请确保您已设置必要的API密钥环境变量(OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY)")
        sys.exit(1)
    
    # 如果提供了prompt参数，直接处理
    if args.prompt:
        response = service.chat(args.prompt)
        if args.json:
            print(json.dumps(response, indent=2, ensure_ascii=False))
        else:
            if "error" in response:
                print(f"错误: {response['error']}")
            else:
                print(response["raw_content"])
        return
    
    # 交互式聊天循环
    print("=== 稳定LLM服务聊天 (输入'exit'退出) ===")
    print(f"使用的服务顺序: {', '.join(service.service_order)}")
    
    while True:
        try:
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
                
        except KeyboardInterrupt:
            print("\n程序被中断")
            break
        except Exception as e:
            print(f"\n发生错误: {str(e)}")

def analyze_command():
    """提供图像分析命令行界面"""
    parser = argparse.ArgumentParser(description="使用大模型分析图像")
    parser.add_argument("image", help="要分析的图像文件路径")
    parser.add_argument("--prompt", default="描述这张图片。你看到了什么？", help="分析提示词")
    parser.add_argument("--timeout", type=float, default=30.0, help="服务超时时间(秒)")
    parser.add_argument("--service-order", type=str, help="逗号分隔的服务调用顺序，例如：openai,anthropic,gemini")
    parser.add_argument("--json", action="store_true", help="以JSON格式输出结果")
    args = parser.parse_args()
    
    # 检查图像文件
    if not os.path.exists(args.image):
        print(f"错误: 图像文件'{args.image}'不存在")
        sys.exit(1)
    
    # 加载图像
    try:
        image = Image.open(args.image)
    except Exception as e:
        print(f"加载图像失败: {str(e)}")
        sys.exit(1)
    
    # 解析服务顺序
    service_order = None
    if args.service_order:
        service_order = args.service_order.split(",")
    
    # 初始化服务
    try:
        service = StableLLMService(
            service_timeout=args.timeout,
            service_order=service_order
        )
    except Exception as e:
        print(f"初始化服务失败: {str(e)}")
        print("请确保您已设置必要的API密钥环境变量(OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY)")
        sys.exit(1)
    
    print(f"正在分析图像 '{args.image}'...")
    
    # 发送图像分析请求
    response = service.analyze(args.prompt, image)
    
    # 输出结果
    if args.json:
        print(json.dumps(response, indent=2, ensure_ascii=False))
    else:
        if "error" in response:
            print(f"错误: {response['error']}")
            if "details" in response:
                print("\n详细错误信息:")
                for detail in response["details"]:
                    print(f"  - {detail.get('service', '未知')}: {detail.get('error', '未知错误')}")
        else:
            print("\n分析结果:")
            print("="*50)
            print(response["raw_content"])
            print("="*50)
            if "provider" in response and "model" in response:
                print(f"\n提供商: {response['provider']}, 模型: {response['model']}")

if __name__ == "__main__":
    chat_command() 