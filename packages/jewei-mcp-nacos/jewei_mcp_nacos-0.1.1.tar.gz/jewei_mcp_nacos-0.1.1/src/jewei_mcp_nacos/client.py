"""Nacos API 客户端"""

import os
import time
from typing import Any, Optional

import httpx


class NacosClient:
    """Nacos 3.x Console API 客户端

    支持双端口设计：
    - API 端口 (8848): 用于登录获取 token
    - Console 端口 (8080): 用于配置操作
    """

    def __init__(self) -> None:
        self.host = os.getenv("NACOS_HOST", "localhost")
        self.api_port = int(os.getenv("NACOS_API_PORT", "8848"))
        self.console_port = int(os.getenv("NACOS_CONSOLE_PORT", "8080"))
        self.username = os.getenv("NACOS_USERNAME")
        self.password = os.getenv("NACOS_PASSWORD")
        self.default_namespace = os.getenv("NACOS_NAMESPACE", "public")

        self._access_token: Optional[str] = None
        self._token_expire_time: Optional[float] = None

    @property
    def api_base_url(self) -> str:
        """API 端口 URL（用于登录）"""
        return f"http://{self.host}:{self.api_port}"

    @property
    def console_base_url(self) -> str:
        """Console 端口 URL（用于配置操作）"""
        return f"http://{self.host}:{self.console_port}"

    async def _ensure_token(self) -> Optional[str]:
        """确保有有效的 access token（如果需要认证）

        认证策略：
        1. 如果未配置用户名密码，返回 None（尝试无认证访问）
        2. 如果已有 token 且未过期，直接返回
        3. 如果 token 过期，自动重新登录
        """
        # 未配置认证信息，尝试无认证访问
        if not self.username or not self.password:
            return None

        # 检查 token 是否过期（预留 5 分钟缓冲）
        if self._access_token and self._token_expire_time:
            if time.time() < self._token_expire_time - 300:
                return self._access_token

        # 登录获取新 token
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base_url}/nacos/v3/auth/user/login",
                data={"username": self.username, "password": self.password},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            self._access_token = data.get("accessToken")
            # tokenTtl 单位是秒，默认 18000 (5小时)
            ttl = data.get("tokenTtl", 18000)
            self._token_expire_time = time.time() + ttl

            return self._access_token

    def _get_namespace(self, namespace_id: Optional[str]) -> str:
        """获取命名空间 ID

        优先级：工具参数 > 环境变量 > 默认 public
        """
        if namespace_id:
            return namespace_id
        return self.default_namespace

    async def get_config(
        self,
        data_id: str,
        group_name: str = "DEFAULT_GROUP",
        namespace_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """获取配置

        Args:
            data_id: 配置 ID
            group_name: 配置分组
            namespace_id: 命名空间 ID

        Returns:
            配置详情字典

        Raises:
            httpx.HTTPStatusError: API 请求失败
            Exception: 业务错误
        """
        token = await self._ensure_token()
        ns = self._get_namespace(namespace_id)

        params: dict[str, str] = {
            "dataId": data_id,
            "groupName": group_name,
            "namespaceId": ns,
        }
        headers: dict[str, str] = {}
        if token:
            headers["accessToken"] = token

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.console_base_url}/v3/console/cs/config",
                params=params,
                headers=headers,
                timeout=30.0,
            )
            response.raise_for_status()
            result: dict[str, Any] = response.json()

            if result.get("code") != 0:
                raise Exception(result.get("message", "Unknown error"))

            data: dict[str, Any] = result.get("data", {})
            return data

    async def publish_config(
        self,
        data_id: str,
        content: str,
        group_name: str = "DEFAULT_GROUP",
        namespace_id: Optional[str] = None,
        config_type: str = "yaml",
        desc: Optional[str] = None,
    ) -> bool:
        """发布配置

        Args:
            data_id: 配置 ID
            content: 配置内容
            group_name: 配置分组
            namespace_id: 命名空间 ID
            config_type: 配置类型 (yaml, json, properties, text 等)
            desc: 配置描述

        Returns:
            是否发布成功

        Raises:
            httpx.HTTPStatusError: API 请求失败
            Exception: 业务错误
        """
        token = await self._ensure_token()
        ns = self._get_namespace(namespace_id)

        params: dict[str, str] = {
            "dataId": data_id,
            "groupName": group_name,
            "namespaceId": ns,
            "content": content,
            "type": config_type,
        }
        if desc:
            params["desc"] = desc

        headers: dict[str, str] = {}
        if token:
            headers["accessToken"] = token

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.console_base_url}/v3/console/cs/config",
                params=params,
                headers=headers,
                timeout=30.0,
            )
            response.raise_for_status()
            result: dict[str, Any] = response.json()

            if result.get("code") != 0:
                raise Exception(result.get("message", "Unknown error"))

            success: bool = result.get("data", False)
            return success


# 全局客户端实例
nacos_client = NacosClient()
