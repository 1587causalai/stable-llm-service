"""
测试StableLLMService功能
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os
from concurrent.futures import TimeoutError

# 确保可以导入stable_llm_service
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from stable_llm_service import StableLLMService

# 导入PIL库用于创建测试图像
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

class TestStableLLMService(unittest.TestCase):
    """测试StableLLMService类"""
    
    def setUp(self):
        """设置测试环境"""
        # 使用环境变量模拟API密钥
        os.environ["OPENAI_API_KEY"] = "test_openai_key"
        os.environ["ANTHROPIC_API_KEY"] = "test_anthropic_key"
        os.environ["GEMINI_API_KEY"] = "test_gemini_key"
    
    def tearDown(self):
        """清理测试环境"""
        # 清除环境变量
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]
        if "ANTHROPIC_API_KEY" in os.environ:
            del os.environ["ANTHROPIC_API_KEY"]
        if "GEMINI_API_KEY" in os.environ:
            del os.environ["GEMINI_API_KEY"]
    
    @patch('stable_llm_service.ServiceFactory.create_service')
    def test_initialization(self, mock_create_service):
        """测试服务初始化"""
        # 模拟服务创建
        mock_service = MagicMock()
        mock_create_service.return_value = mock_service
        
        # 初始化服务
        service = StableLLMService(
            service_timeout=5.0,
            failure_threshold=2,
            cool_down_period=10.0
        )
        
        # 验证服务配置
        self.assertEqual(service.service_timeout, 5.0)
        
        # 验证服务顺序
        self.assertTrue(len(service.service_order) > 0)
        
        # 验证健康监控器配置
        self.assertEqual(service.health_monitor.failure_threshold, 2)
        self.assertEqual(service.health_monitor.cool_down_period, 10.0)
    
    @patch('stable_llm_service.ServiceFactory.create_service')
    def test_service_order_customization(self, mock_create_service):
        """测试自定义服务顺序"""
        # 模拟服务创建
        mock_service = MagicMock()
        mock_create_service.return_value = mock_service
        
        # 初始化服务，自定义顺序
        custom_order = ["anthropic", "openai", "gemini"]
        service = StableLLMService(service_order=custom_order)
        
        # 验证服务顺序
        self.assertEqual(service.service_order, custom_order)
    
    @patch('stable_llm_service.ServiceFactory.create_service')
    def test_is_rate_limited(self, mock_create_service):
        """测试限流检测"""
        # 模拟服务创建
        mock_service = MagicMock()
        mock_create_service.return_value = mock_service
        
        # 初始化服务
        service = StableLLMService()
        
        # 测试各种错误消息
        self.assertTrue(service._is_rate_limited(Exception("Rate limit exceeded")))
        self.assertTrue(service._is_rate_limited(Exception("429 Too Many Requests")))
        self.assertTrue(service._is_rate_limited(Exception("Quota exceeded for this month")))
        self.assertFalse(service._is_rate_limited(Exception("Invalid API key")))
    
    @patch('stable_llm_service.ThreadPoolExecutor')
    @patch('stable_llm_service.ServiceFactory.create_service')
    def test_timeout_handling(self, mock_create_service, mock_executor):
        """测试超时处理"""
        # 模拟服务创建
        mock_service = MagicMock()
        mock_create_service.return_value = mock_service
        
        # 模拟线程池执行器
        mock_future = MagicMock()
        mock_future.result.side_effect = TimeoutError("Request timed out")
        
        mock_executor_instance = MagicMock()
        mock_executor_instance.__enter__.return_value = mock_executor_instance
        mock_executor_instance.submit.return_value = mock_future
        
        mock_executor.return_value = mock_executor_instance
        
        # 初始化服务
        service = StableLLMService()
        
        # 强制服务初始化
        service.services = {
            "openai_primary": mock_service
        }
        
        # 记录健康监控器以验证失败记录
        health_monitor_spy = MagicMock(wraps=service.health_monitor)
        service.health_monitor = health_monitor_spy
        
        # 执行带超时的调用
        with self.assertRaises(Exception):
            service._call_with_timeout("openai_primary", "chat", "test prompt")
        
        # 验证失败被记录
        health_monitor_spy.record_failure.assert_called_once_with("openai_primary")
    
    @unittest.skipIf(not PIL_AVAILABLE, "PIL库未安装，跳过图像分析测试")
    @patch('stable_llm_service.ServiceFactory.create_service')
    def test_image_analysis(self, mock_create_service):
        """测试图像分析功能"""
        # 创建一个简单的测试图像（渐变色图像）
        width, height = 300, 200
        test_image = Image.new('RGB', (width, height))
        
        # 填充渐变色
        for x in range(width):
            for y in range(height):
                r = int(255 * x / width)
                g = int(255 * y / height)
                b = int(255 * (x + y) / (width + height))
                test_image.putpixel((x, y), (r, g, b))
        
        # 模拟服务响应
        expected_response = {
            "raw_content": "这是一个RGB渐变色图像",
            "provider": "openai",
            "model": "chatgpt-4o-latest",
            "finish_reason": "stop"
        }
        
        # 设置模拟
        mock_service = MagicMock()
        mock_service.analyze.return_value = expected_response
        mock_create_service.return_value = mock_service
        
        # 初始化服务
        service = StableLLMService()
        service.services = {"openai_primary": mock_service}
        
        # 调用分析方法
        prompt = "描述这个图像"
        result = service._call_service("analyze", prompt, test_image)
        
        # 验证结果
        self.assertEqual(result, expected_response)
        mock_service.analyze.assert_called_once_with(prompt, test_image)

if __name__ == '__main__':
    unittest.main() 