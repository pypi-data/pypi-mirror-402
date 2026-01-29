from __future__ import annotations

from typing import List, Optional, Set, Union, Literal

from datetime import datetime

from pydantic import BaseModel, Field

from turbo_agent_core.schema.enums import AgentMode, RefType

class BasicRef(BaseModel):
    id: str
    type: RefType
    name: Optional[str] = None
    belongToProjectId: Optional[str] = None
    createTime: Optional[datetime] = None
    updateTime: Optional[datetime] = None

class KnowledgeResourceRef(BasicRef):
    type: RefType = RefType.KnowledgeResource

class ToolCallRecordRef(BasicRef):
    type: RefType = RefType.ActionRecords

class AssistantConversationRef(BasicRef):
    type: RefType = RefType.Conversation

class WorksetRef(BasicRef):
    type: RefType = RefType.Workset

class AgentRef(BasicRef):
    type: RefType = RefType.Agent

class ModelRef(BasicRef):
    type: RefType = RefType.Model

class ToolRef(BasicRef):
    type: RefType = RefType.Tool

class CharacterRef(BasicRef):
    type: RefType = RefType.Character


class JobExecutorRef(BasicRef):
    """Job 执行者引用（Agent）"""
    type: Literal[RefType.Agent, RefType.Tool, RefType.Character] = RefType.Agent
    # -------- 默认智能体配置（仅当 executor_ref 为 None 时有效）--------
    agent_mode: AgentMode = Field(
        default=AgentMode.QA_MODE,
        description="智能体执行模式（权限等级：qa/assistant/autonomous/admin）"
    )
