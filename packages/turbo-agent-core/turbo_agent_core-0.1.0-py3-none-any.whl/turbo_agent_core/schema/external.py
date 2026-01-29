#  coding=utf-8
# 本文档定义了 TurboAgent项目下的 外部平台（Platform）以及关联授权的基础数据模型
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime

from pydantic import BaseModel, Field

from turbo_agent_core.schema.enums import (
    JSON,
    AuthType,
    Availablility
)

from turbo_agent_core.schema.basic import Endpoint

class AuthMethod(BaseModel):
    id: str
    name: str
    authType: AuthType = AuthType.APIKey
    description: Optional[str] = None
    loginFlow: Optional[JSON] = None
    loginFieldsSchema: Optional[JSON] = None
    refreshFlow: Optional[JSON] = None
    refreshFieldsSchema: Optional[JSON] = None
    authFieldsSchema: Optional[JSON] = None
    authFieldPlacements: Optional[JSON] = None
    responseMapping: Optional[JSON] = None
    defaultValiditySeconds: Optional[int] = None
    refreshBeforeSeconds: Optional[int] = None

class Secret(BaseModel):
    id: str
    name: str = ""
    identifier: str = ""
    availability: Availablility = Availablility.personal_visible
    credential: Optional[JSON] = None # 存储秘钥数据。如 access_token/refresh_token/apikey/cookies 等
    authDataSources: Optional[JSON] = None
    loginPayload: Optional[JSON] = None # 存储第一阶段登录字段，便于服务端代办登录
    autoLoginEnabled: bool = False # 是否保存第一阶段登录字段，便于服务端代办登录
    expiresAt: Optional[datetime] = None
    validFrom: Optional[datetime] = None
    lastRefreshed: Optional[datetime] = None
    authMethodId: Optional[str] = None
    platformId: Optional[str] = None

class Platform(BaseModel):
    id: str
    image_url: str
    name_en: str
    name: str
    officialUrl: str # 平台官网地址，仅做浏览使用
    description: str
    endpoint: Endpoint # 平台API访问地址
    secrets: List[Secret] = []
    authMethods: List[AuthMethod] = []


class DeviceResourceStats(BaseModel):
    """设备资源状态（具身/桌面本机）。

    说明：
    - 本结构仅用于协议与数据交换，不约束采集方式。
    - 采集实现由 server/local 决定（如 psutil、系统 API、硬件 SDK）。
    """

    timestamp_ms: Optional[float] = None
    cpu_percent: Optional[float] = None
    mem_used_bytes: Optional[int] = None
    mem_total_bytes: Optional[int] = None
    battery_percent: Optional[float] = None
    battery_is_charging: Optional[bool] = None
    extra: Optional[JSON] = None


class McpTransport(str, Enum):
    """MCP 服务的连接方式。"""
    stdio = "stdio"
    http = "http"
    ws = "ws"


class McpServerSpec(BaseModel):
    """MCP 服务描述（与 Platform 同层）。"""

    id: str
    name: str
    description: Optional[str] = None

    transport: McpTransport = McpTransport.stdio

    # 对于 http/ws 模式：可使用 endpoint 描述访问地址
    endpoint: Optional[Endpoint] = None

    # 对于 stdio 模式：可用 command/args/env 描述进程启动参数（实现由 local 负责）
    command: Optional[str] = None
    args: List[str] = Field(default_factory=list)
    env: Dict[str, str] = Field(default_factory=dict)

    enabled: bool = True
    tags: List[str] = Field(default_factory=list)
    extra: Optional[JSON] = None


class McpResourceDescriptor(BaseModel):
    """MCP 资源描述。

    说明：
    - 可被 server/local 包装为 Tool（由上层决定）。
    - schema 字段用于描述输入输出，不代表实现细节。
    """

    id: str
    server_id: str
    name: str
    description: Optional[str] = None
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    extra: Optional[JSON] = None


class McpCallRequest(BaseModel):
    """对 MCP 资源的调用请求（协议 DTO）。"""

    server_id: str
    resource_id: str
    method: str = "call"
    params: Optional[JSON] = None
    timeout_ms: Optional[int] = None


class McpCallResult(BaseModel):
    """对 MCP 资源的调用结果（协议 DTO）。"""

    ok: bool
    result: Optional[JSON] = None
    error: Optional[str] = None
