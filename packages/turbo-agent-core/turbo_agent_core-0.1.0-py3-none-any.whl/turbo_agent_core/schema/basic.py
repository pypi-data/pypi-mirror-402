#  coding=utf-8
#  本文档定义了 基础数据模型，以支持 智能体（Agent）、角色（Character）和工具（Tool）构建过程中所使用到的基础类型
from __future__ import annotations

from enum import Enum
from typing import List, Optional, Dict,Any
from abc import ABC, abstractmethod

from pydantic import BaseModel, Field, ValidationError
from turbo_agent_core.schema.enums import JSON, ModelApiProvider, SourceType, WebProtocol,RunType, BasicType, ParameterPosition

class ModelParameters(BaseModel):
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    stop: Optional[List[str]] = None
    presence_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    frequency_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None
    extra: Optional[JSON] = None

#  大模型实例信息,每个用户可能通过自己搭建、购买同一个模型的不同实例，在实际使用时，根据用户的权限、场景等信息，选择合适的实例进行调用
class ModelInstance(BaseModel):
    id: str
    label: str
    description: str
    request_model_id: str
    is_active: bool
    provider: ModelApiProvider
    endpoint: Optional[Endpoint] = None
    local_launch_spec: Optional["LocalLaunchSpec"] = None


class LocalLaunchMode(str, Enum):
    """本地模型启动方式的描述（仅用于配置表达，不包含具体实现）。"""
    external = "external"   # 不由本地启动，仅使用既有 endpoint
    ollama = "ollama"       # 本地 Ollama 管理（通常仍通过 endpoint 访问）
    vllm = "vllm"           # 本地 vLLM 服务（通常通过 endpoint 访问）
    llamacpp = "llamacpp"   # llama.cpp 本地进程/服务


class LocalLaunchSpec(BaseModel):
    """本地启动描述：用于 local 模块拉起/探活/停止本地模型。

    说明：
    - core 只定义“如何描述启动”，不定义“如何启动”的实现。
    - local 模块可根据 provider/endpoint.source_type/mode 选择不同适配器（vLLM、Ollama、llama.cpp 等）。
    """

    # pydantic 会把 model_ 作为受保护的命名空间；这里显式关闭，避免 model_path/served_model_name 警告。
    model_config = {"protected_namespaces": ()}

    mode: LocalLaunchMode = LocalLaunchMode.external
    command: Optional[str] = None
    args: List[str] = Field(default_factory=list)
    env: Dict[str, str] = Field(default_factory=dict)
    workdir: Optional[str] = None

    host: Optional[str] = None
    port: Optional[int] = None

    model_path: Optional[str] = None
    served_model_name: Optional[str] = None

    healthcheck_url: Optional[str] = None
    startup_timeout_ms: int = 60_000

    extra: Optional[JSON] = None

# 版本管理基础信息
class VersionInfo(BaseModel):
    version: str = "0.0.1"
    update_info: str = "initial"
    version_hash: str

class Endpoint(BaseModel):
    id: str
    protocol: WebProtocol = WebProtocol.HTTP
    source_type: SourceType = SourceType.External
    url: Optional[str] = None
    baseURL: Optional[str] = None
    accessKey: Optional[str] = None # 仅在大模型请求时使用，其余条件下请使用 secret 以及 authMethod配套获取授权信息

# TurboAgent项目下的基础实体类型，原则上，如果定义为TurboEntity，并且run_type类型非NONE说明该实体可以直接运行
class TurboEntity(BaseModel, ABC):
    id: str
    name: str
    belongToProjectId: str
    name_id: str
    description: Optional[str] = None
    avatar_uri: Optional[str] = None
    run_type: RunType = RunType.NoneType #定义了实体运行时的输入类型
    # 此处定义一个待实现方法，用于当前实体完成任务
    @abstractmethod
    def run(self, **kwargs):
        raise NotImplementedError()
    @abstractmethod
    def stream(self, **kwargs):
        raise NotImplementedError()
    @abstractmethod
    async def a_run(self, **kwargs):
        raise NotImplementedError()
    # 此处定义一个待实现方法，用于当前实体完成任务，返回流式结果，当前方法输入输出可以调整。
    @abstractmethod
    async def a_stream(self, **kwargs):
        raise NotImplementedError()


class Parameter(BaseModel):
    id: Optional[str] = None
    idx: int = 0
    required: bool = False
    name: str
    description: str = ""
    default: Optional[Any] = None
    enum_values: Optional[List[str]] = None
    position: Optional[ParameterPosition] = None
    type: BasicType
    type_ref: Optional[BasicType] = None  # when type is array, type_ref indicates item type
    parameters: Optional[List[Parameter]] = None  # nested parameters for object or array of object
    json_schema: Optional[dict] = None  # explicit override schema for this parameter

    class Config:
        arbitrary_types_allowed = True
