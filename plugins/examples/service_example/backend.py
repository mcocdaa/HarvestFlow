# @file plugins/examples/service-example/backend.py
# @brief Example service plugin implementation
# @create 2026-03-28

import logging
import requests
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


class ExampleService:
    name = "service-example"
    description = "Example service plugin - demonstrates how to build a custom service"

    def __init__(self, config: Dict = None, secrets: Dict = None):
        self.config = config or {}
        self.secrets = secrets or {}
        self.custom_config = self.config.get("custom_config", {})

        self.api_key = self.secrets.get("API_KEY", "")
        self.api_secret = self.secrets.get("API_SECRET", "")
        self.api_endpoint = self.custom_config.get("api_endpoint", "https://api.example.com")
        self.timeout = self.custom_config.get("timeout", 30)

    def on_load(self):
        """服务加载时调用"""
        logger.info(f"[ExampleService] Service loaded with endpoint: {self.api_endpoint}")

        # 可以在这里初始化连接、测试连接等
        if self.api_key and self.api_secret:
            try:
                self._test_connection()
                logger.info("[ExampleService] Connection test successful")
            except Exception as e:
                logger.error(f"[ExampleService] Connection test failed: {e}")
        else:
            logger.warning("[ExampleService] API key or secret not provided")

    def on_unload(self):
        """服务卸载时调用"""
        logger.info("[ExampleService] Service unloaded")

        # 可以在这里清理资源、关闭连接等

    def _test_connection(self) -> bool:
        """测试与外部服务的连接

        Returns:
            是否连接成功
        """
        # 示例：发送一个简单的请求测试连接
        logger.debug(f"[ExampleService] Testing connection to {self.api_endpoint}")

        # 这里可以实现真实的连接测试逻辑
        # 例如：
        # response = requests.get(
        #     f"{self.api_endpoint}/health",
        #     headers={
        #         "X-API-Key": self.api_key,
        #         "X-API-Secret": self.api_secret
        #     },
        #     timeout=self.timeout
        # )
        # response.raise_for_status()

        return True

    def call_api(self, endpoint: str, method: str = "GET", data: Dict = None) -> Optional[Dict]:
        """调用外部 API

        Args:
            endpoint: API 端点
            method: HTTP 方法
            data: 请求数据

        Returns:
            API 响应
        """
        try:
            url = f"{self.api_endpoint}/{endpoint.lstrip('/')}"

            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.api_key,
                "X-API-Secret": self.api_secret
            }

            logger.debug(f"[ExampleService] Calling API: {method} {url}")

            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=data, timeout=self.timeout)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=self.timeout)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data, timeout=self.timeout)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"[ExampleService] API call failed: {e}")
            return None

    def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息

        Returns:
            服务信息字典
        """
        return {
            "name": self.name,
            "description": self.description,
            "version": "1.0.0",
            "api_endpoint": self.api_endpoint,
            "has_api_key": bool(self.api_key),
            "has_api_secret": bool(self.api_secret),
        }

    def custom_action(self, action: str, params: Dict = None) -> Dict[str, Any]:
        """执行自定义操作

        Args:
            action: 操作名称
            params: 操作参数

        Returns:
            操作结果
        """
        logger.info(f"[ExampleService] Executing custom action: {action}")

        # 根据不同的 action 执行不同的逻辑
        if action == "example_action":
            return {
                "success": True,
                "message": "Example action executed successfully",
                "params": params
            }
        elif action == "get_status":
            return {
                "success": True,
                "status": "healthy",
                "timestamp": "now"
            }
        else:
            return {
                "success": False,
                "message": f"Unknown action: {action}"
            }


service_plugin = ExampleService()


def on_load():
    logger.info("[ExampleService] Plugin loaded")
    service_plugin.on_load()


def on_unload():
    service_plugin.on_unload()
    logger.info("[ExampleService] Plugin unloaded")


def get_service():
    return service_plugin


def call_action(action: str, params: Dict = None) -> Dict[str, Any]:
    """调用服务动作（供外部调用的接口）"""
    return service_plugin.custom_action(action, params)
