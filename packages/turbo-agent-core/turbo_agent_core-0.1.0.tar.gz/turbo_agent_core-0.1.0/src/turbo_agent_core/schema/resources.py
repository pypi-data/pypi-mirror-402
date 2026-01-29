#  coding=utf-8
#  本文档定义了 TurboAgent项目下的 资源（资源端点、认证配置、业务设置、知识资源和账号密钥）的基础数据模型
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set
from datetime import datetime

from pydantic import BaseModel, Field

from turbo_agent_core.schema.enums import (
    JSON,
    FileType,
    KnowledgeType,
    ResourceStatus,
    BusinessScenario,
)

from turbo_agent_core.schema.refs import (
    ToolCallRecordRef,
    AssistantConversationRef,
    KnowledgeResourceRef
)

class Project(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    name_en: Optional[str] = None
    orgProjectId: str

class BusinessRule(BaseModel):
    id: str
    index: int
    content: str
    activate: bool
    scenarios: List[BusinessScenario] = Field(default_factory=list)

class KnowledgeResource(BaseModel):
    id: str
    belongToProjectId : Optional[str] = None
    name: str
    type: KnowledgeType
    status: ResourceStatus
    fileType: Optional[FileType] = None
    filename: Optional[str] = None
    url: Optional[str] = None
    uri: Optional[str] = None
    content: Optional[str] = None
    mime_type: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

class BusinessSetting(BaseModel):
    id: str
    belongToProjectId : Optional[str] = None
    target: Optional[str] = None
    principles: List[BusinessRule] = Field(default_factory=list)
    knowledges: List[KnowledgeResource] = Field(default_factory=list)
    examples: JSON = Field(default_factory=dict)

class Workset(BaseModel):
    id: str
    belongToProjectId : Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    ownerId: str
    layout: Optional[JSON] = None
    knowledgeResources: list[KnowledgeResourceRef] = []
    conversations: list[AssistantConversationRef] = []
    toolCallRecords: list[ToolCallRecordRef] = []
    ref_id_set: Set[str] = set()



