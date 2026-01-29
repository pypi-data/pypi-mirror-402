#  coding=utf-8
#  本文档定义了 智能体（Agent）、角色（Character）和工具（Tool）数据模型，以支持 运行、迁移、存储等功能
from __future__ import annotations

from typing import AsyncIterator, Iterator, List, Optional, Set, Literal, Union

from pydantic import BaseModel, Field, ValidationError, SerializeAsAny
from typing import Optional

from turbo_agent_core.schema.enums import JSON, RequestMethod, RunType,JSON, RequestMethod, RunType, ModelType
from turbo_agent_core.schema.events import BaseEvent
from turbo_agent_core.schema.basic import  ModelParameters,ModelInstance,TurboEntity,Parameter
from turbo_agent_core.schema.external import Platform,Secret
from turbo_agent_core.schema.resources import BusinessSetting
from turbo_agent_core.schema.states import Conversation, Message

from turbo_agent_core.utils.schema_tool import json_schema_to_pydantic_model
from turbo_agent_core.utils.param_schema import parameters_to_json_schema



# ToolVersion 已移除，统一以 Tool 为可运行工具实体

# TODO 实现run方法
class Tool(TurboEntity):
    run_type: Literal[RunType.Tool] = RunType.Tool
    # 版本追溯字段（核心层保留追溯而不维护版本容器）
    version_id: Optional[str] = None
    version_tag: Optional[str] = None
    prev_version_id: Optional[str] = None
    is_default: Optional[bool] = None
    refSet: Set[str] = Field(default_factory=set) # 该工具所依赖的实体ID集合（如模型实例、工具、agent、character等）
    async def a_run(self, input: JSON, **kwargs) -> JSON:
        raise NotImplementedError()
    
    async def a_stream(self, input: JSON,**kwargs) -> AsyncIterator[BaseEvent]:
        # 初始化一个事件流
        raise NotImplementedError()

    
    def run(self, input: JSON,  **kwargs) -> JSON:
        raise NotImplementedError()
    
    def stream(self, input: JSON,  **kwargs) -> Iterator[BaseEvent]:
        raise NotImplementedError()
    

    # 原始参数声明列表（前端/配置层给出）
    input: List[Parameter] = Field(default_factory=list)
    output: List[Parameter] = Field(default_factory=list)
    # 自动派生或显式指定的 JSON Schema（若外部直接提供则不覆盖）
    input_schema: JSON = Field(default_factory=dict)
    output_schema: JSON = Field(default_factory=dict)

    # 动态构造的校验模型（不参与序列化）
    _input_model: type[BaseModel] | None = None
    _output_model: type[BaseModel] | None = None

    def __init__(self, **data):
        super().__init__(**data)
        self._build_models()

    def model_post_init(self, __context):  # pydantic v2 hook
        # 若未显式提供 schema，则由参数列表派生
        if not self.input_schema and self.input:
            self.input_schema = parameters_to_json_schema(self.input)
        if not self.output_schema and self.output:
            self.output_schema = parameters_to_json_schema(self.output)
        self._build_models()

    # -------- public validation methods --------
    def validate_input(self, data: dict) -> dict:
        if not isinstance(self.input_schema, dict) or not self.input_schema:
            return data
        if not isinstance(data, dict):
            raise ValueError("Input must be dict for schema validation")
        if self._input_model is None:
            self._build_models()
        try:
            obj = self._input_model.model_validate(data)  # type: ignore
        except ValidationError as e:
            raise ValueError(e.errors()) from e
        return obj.model_dump()

    def validate_output(self, raw: JSON) -> dict:
        if not isinstance(self.output_schema, dict) or not self.output_schema:
            return {"result": raw}
        if self._output_model is None:
            self._build_models()
        if isinstance(raw, dict):
            try:
                obj = self._output_model.model_validate(raw)  # type: ignore
                return obj.model_dump()
            except ValidationError:
                pass
        props = self.output_schema.get("properties", {}) or {}
        if not props:
            return {"result": raw}
        if len(props) == 1:
            sole = next(iter(props.keys()))
            return {sole: raw}
        shaped = {k: None for k in props.keys()}
        first = next(iter(props.keys()))
        shaped[first] = raw
        return shaped

    # -------- internal helpers --------
    def _build_models(self):
        self._input_model = json_schema_to_pydantic_model(self.input_schema, "ToolInputModel") if isinstance(self.input_schema, dict) and self.input_schema else None
        self._output_model = json_schema_to_pydantic_model(self.output_schema, "ToolOutputModel") if isinstance(self.output_schema, dict) and self.output_schema else None


class LLMModel(TurboEntity):
    model_config = {'protected_namespaces': ()}
    space_id: str
    source_urls: List[str]
    defaultParameters: ModelParameters = Field(default_factory=ModelParameters)
    run_type: Literal[RunType.LLM] = RunType.LLM
    tool_calling_enabled: bool = False
    thinking_model:bool = False
    model_type: ModelType = ModelType.LargeLanguageModel
    instances: List[ModelInstance] = Field(default_factory=list)
    async def a_run(self, conversation: Conversation,leaf_message_id: Optional[str] = None, tools:Optional[List[Tool]] = None, **kwargs) -> Message:
        raise NotImplementedError()
    
    async def a_stream(self, conversation: Conversation, leaf_message_id: Optional[str] = None, tools:Optional[List[Tool]] = None, **kwargs) -> AsyncIterator[BaseEvent]:
        # 初始化一个事件流
        raise NotImplementedError()

    
    def run(self, conversation: Conversation, leaf_message_id: Optional[str] = None, tools:Optional[List[Tool]] = None, **kwargs) -> Message:
        return super().run(**kwargs)
    
    def stream(self, conversation: Conversation, leaf_message_id: Optional[str] = None, tools:Optional[List[Tool]] = None, **kwargs) -> Iterator[BaseEvent]:
        raise NotImplementedError()


class BasicAgent(TurboEntity):
    run_type: Literal[RunType.AGENT] = RunType.AGENT 
    model: Optional[LLMModel] = None
    modelParameter: ModelParameters = Field(default_factory=ModelParameters)
    setting: Optional[BusinessSetting] = None
    tools: List[Union["LLMTool", "APITool", "AgentTool", Tool]] = Field(default_factory=list)
    refSet: Set[str] = Field(default_factory=set) # 该工具所依赖的实体ID集合（如模型实例、工具、agent、character等）
    # 版本追溯字段
    version_id: Optional[str] = None
    version_tag: Optional[str] = None
    prev_version_id: Optional[str] = None
    is_default: Optional[bool] = None
    async def a_run(self, conversation: Conversation, leaf_message_id: Optional[str] = None, tools:Optional[List[Tool]] = None, **kwargs) -> Message:
        raise NotImplementedError()
    
    async def a_stream(self, conversation: Conversation, leaf_message_id: Optional[str] = None, tools:Optional[List[Tool]] = None, **kwargs) -> AsyncIterator[BaseEvent]:
        # 初始化一个事件流
        raise NotImplementedError()

    
    def run(self, conversation: Conversation,  leaf_message_id: Optional[str] = None, tools:Optional[List[Tool]] = None, **kwargs) -> Message:
        return super().run(**kwargs)
    
    def stream(self, conversation: Conversation, leaf_message_id: Optional[str] = None, tools:Optional[List[Tool]] = None, **kwargs) -> Iterator[BaseEvent]:
        raise NotImplementedError()

# CharacterVersion 已移除，统一以 Character 为可运行角色实体
class Character(BasicAgent):
    run_type: Literal[RunType.Character] = RunType.Character
    # 版本追溯字段
    version_id: Optional[str] = None
    version_tag: Optional[str] = None
    prev_version_id: Optional[str] = None
    is_default: Optional[bool] = None

class Agent(BasicAgent):
    run_type: Literal[RunType.AGENT] = RunType.AGENT
    hasMemory: bool = False
    expose_inner_thought: bool = True
    actAsCharacters: List[Character] = Field(default_factory=list)
    accountSecrets: List[Secret] = Field(default_factory=list)
    assistantAgents: List[Agent] = Field(default_factory=list)
    refSet: Set[str] = Field(default_factory=set) # 该工具所依赖的实体ID集合（如模型实例、工具、agent、character等）

# BasicTool 扩展，增加API工具相关字段,底层结构 refset为空
class APITool(Tool):
    method: RequestMethod = RequestMethod.POST
    needAccessSecret: Optional[bool] = None
    platform: Platform
    url_path_template: str

# BasicTool 扩展，作为一种特殊类型的智能体（大模型扮演工具）,底层结构 refset为空
class LLMTool(Tool):
    run_type: Literal[RunType.LLMTool] = RunType.LLMTool
    # 背靠大模型驱动的工具：具备类似 Agent 的配置，但遵循 Tool 的 I/O 契约
    model: Optional[LLMModel] = None
    modelParameter: ModelParameters = Field(default_factory=ModelParameters)
    setting: Optional[BusinessSetting] = None

# BasicTool 扩展，使用特定智能体执行（智能体作为工具人）
class AgentTool(Tool):
    run_type: Literal[RunType.AgentTool] = RunType.AgentTool
    backendAgent : Optional[BasicAgent] = None
    refSet: Set[str] = Field(default_factory=set)

# Rebuild models to resolve forward references
BasicAgent.model_rebuild()
Character.model_rebuild()
Agent.model_rebuild()

