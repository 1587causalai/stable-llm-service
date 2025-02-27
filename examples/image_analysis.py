#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像分析示例
==========

演示如何使用StableLLMService进行图像分析。
"""

import os
import sys
import json
import argparse
from PIL import Image

# 添加父级目录到路径，以便可以导入stable_llm_service
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 直接从我们的包导入
from stable_llm_service import StableLLMService

def create_test_image():
    """创建一个测试用的渐变图像"""
    width, height = 300, 200
    image = Image.new('RGB', (width, height))
    
    # 创建渐变效果
    for x in range(width):
        for y in range(height):
            r = int(255 * x / width)
            g = int(255 * y / height)
            b = int(255 * (x + y) / (width + height))
            image.putpixel((x, y), (r, g, b))
    
    return image

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="StableLLMService图像分析示例")
    parser.add_argument("--image", help="图像文件路径（如果未提供，将创建测试图像）")
    parser.add_argument("--prompt", default="描述这张图片。你看到了什么？", 
                       help="提示词")
    args = parser.parse_args()
    
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
    
    # 加载或创建图像
    if args.image:
        try:
            image = Image.open(args.image)
            print(f"已加载图像: {args.image}")
        except Exception as e:
            print(f"加载图像失败: {str(e)}")
            return
    else:
        image = create_test_image()
        print("已创建测试图像 (RGB渐变)")
    
    # 初始化服务
    service = StableLLMService(
        service_timeout=20.0,  # 图像分析可能需要更长时间
        failure_threshold=2,
        cool_down_period=30.0
    )
    
    print(f"\n发送图像分析请求，提示词: '{args.prompt}'")
    
    # 发送图像分析请求
    response = service.analyze(args.prompt, image)
    
    if "error" in response:
        print(f"\n错误: {response['error']}")
        if "details" in response:
            print("\n详细错误信息:")
            print(json.dumps(response["details"], indent=2))
    else:
        print("\n分析结果:")
        print("="*50)
        print(response["raw_content"])
        print("="*50)
        print(f"\n提供商: {response.get('provider')}, 模型: {response.get('model')}")

if __name__ == "__main__":
    main() 