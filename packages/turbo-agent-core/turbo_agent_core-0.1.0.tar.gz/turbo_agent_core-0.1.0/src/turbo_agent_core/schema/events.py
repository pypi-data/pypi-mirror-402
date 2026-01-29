# coding=utf-8
"""Turbo-Agent 事件协议定义 (v2.0)。

基于 docs/backend-refactor/event_design.md 设计。
全链路流式、结构化、响应式。

关键语义说明（与嵌套事件设计一致）：

1) trace_id 与嵌套调用
- 每一次“调用”（顶层或子调用）都会生成自己的 trace（trace_id）。
- 当发生嵌套事件转发时：
    - 对外呈现的 `trace_id` 始终是“当前观察视角的根 trace”（通常是顶层调用的 trace_id）。
    - 子执行者的原始 `trace_id` 会被追加到 `trace_path` 中，用于保留嵌套路径。

2) 生命周期状态（run.lifecycle）
- `created/resuming/suspended/completed/failed/cancelled` 属于“标记态”：用于标记流的开始/恢复/挂起/结束。
- `running` 属于“存在态（心跳/回声）”：用于标识流仍存在，避免调用方超时；不用于充当开始标记。

协议约束（设计要求，后续会补齐为 schema 强校验）：
- `created/resuming` 必须携带 input_data
- `resuming` 必须携带 resume_context

实现现状：
- 当前 schema 已按设计强校验：`created/resuming` 必须携带 input_data；`resuming` 必须携带 resume_context。
- `running` 作为心跳/存在态事件，不强制携带 input_data。

3) 存储落地与时间戳
- Store 落库时应使用事件信封的 `timestamp` 作为排序与更新时间依据（而非消费时间），以支持断线重连与去重。
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, List, Literal, Any, Dict, Union

import os
import socket

from pydantic import BaseModel, Field, model_validator

from turbo_agent_core.schema.enums import RunType

EventType = Literal[
    # Data Flow - Text
    "content.text.start",
    "content.text.delta",
    "content.text.end",
    "content.reasoning.delta",
    "content.reasoning.start",
    "content.reasoning.end",
    
    # Data Flow - Action
    "content.action.start",
    "content.action.delta",
    "content.action.end",
    
    # Data Flow - Action Result (Renamed from content.result)
    "content.action.result.start",
    "content.action.result.delta",
    "content.action.result.end",

    # Data Flow - Agent Result (New)
    "content.agent.result.start",
    "content.agent.result.delta",
    "content.agent.result.end",
    
    # State Flow
    "run.lifecycle.created",
    "run.lifecycle.running",
    "run.lifecycle.suspended",
    "run.lifecycle.resuming",
    "run.lifecycle.completed",
    "run.lifecycle.failed",
    "run.lifecycle.cancelled",
    "run.step",
    "state.sync",
    
    # Control Flow
    "control.interrupt",
    "control.suggestions",
    "control.rollback"
]

class ExecutorMetadata(BaseModel):
    """执行者元数据。"""
    id: str
    name: str
    belongToProjectId: Optional[str] = None
    name_id: Optional[str] = None
    description: Optional[str] = None
    avatar_uri: Optional[str] = None
    run_type: Optional[str] = None
    version_id: Optional[str] = None
    version: Optional[str] = None

class UserInfo(BaseModel):
    """用户信息。"""
    id: str
    avatar_uri: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    role: Optional[str] = None

class BaseEvent(BaseModel):
    """所有事件的基础信封结构。"""
    type: EventType
    timestamp: float = Field(default_factory=lambda: datetime.now(timezone.utc).timestamp() * 1000)
    
    # Identity & Context
    trace_id: str                  # 当前观察视角的根 trace_id（对外呈现的 root）。嵌套转发时由父级覆盖。
    trace_path: List[str] = Field(default_factory=list)  # Nested Trace IDs. Root 应为空数组（或省略；本实现默认空数组）。
    
    run_id: str                    # Current Run ID

    # Run 递归队列：用于描述“同一 trace 节点下的多次运行链路”（典型原因：重试、挂起后恢复）。
    # 约定：
    # - 第一次运行：run_path = [run_id]
    # - 重试/恢复产生新 run：run_path = 旧 run_path + [new_run_id]
    # - 该字段用于观察侧/Store 管理重试关系与展示，不参与 trace 的嵌套（嵌套由 trace_path 表达）。
    run_path: Optional[List[str]] = None

    # Execution Context
    worker_id: str = Field(default_factory=lambda: f"{socket.gethostname()}:{os.getenv('RANK') or os.getenv('LOCAL_RANK') or '0'}")
    executor_id: str
    executor_type: RunType = None # Current Executor Type (e.g., AGENT, LLM, API)
    executor_path: List[str] = None # Call Chain. Root 为 [executor_id]，子流由父级在转发时拼接。

    react_id: Optional[str] = None  # 关联的 ReAct Round ID（如果有的话）
    action_id: Optional[str] = None  # 关联的 action_id（如果有的话）
    
    # Metadata & User Info (v2.0 New)
    executor_metadata: Optional[ExecutorMetadata] = None  # Mandatory for trace creation (run.lifecycle created)
    # 仅在 run.lifecycle.created 事件上强制要求存在，其余事件允许为 None
    user_metadata: Optional[UserInfo] = None  # Mandatory for trace creation (run.lifecycle created)

    payload: Any

    @model_validator(mode="after")
    def _validate_envelope(self) -> "BaseEvent":
        # 1) timestamp：必须是 UTC epoch 毫秒浮点（禁止秒级）
        try:
            ts = float(self.timestamp)
        except Exception as exc:  # pragma: no cover
            raise ValueError("BaseEvent.timestamp 必须是数值（UTC epoch 毫秒浮点）") from exc

        # 秒级时间戳通常在 1e9 量级；毫秒在 1e12 量级。
        # 为避免误判极早期历史时间，阈值取 1e11（约 1973 年）。
        if ts < 1e11:
            raise ValueError("BaseEvent.timestamp 必须是 UTC epoch 毫秒（禁止秒级）")

        # 2) worker_id：必须为 host:rank（rank 为非负整数）
        if not isinstance(self.worker_id, str) or not self.worker_id:
            raise ValueError("BaseEvent.worker_id 必须是非空字符串，格式为 host:rank")
        if ":" not in self.worker_id:
            raise ValueError("BaseEvent.worker_id 格式错误，应为 host:rank")
        host, rank_str = self.worker_id.rsplit(":", 1)
        if not host:
            raise ValueError("BaseEvent.worker_id 格式错误，应为 host:rank（host 不能为空）")
        try:
            rank = int(rank_str)
        except Exception as exc:  # pragma: no cover
            raise ValueError("BaseEvent.worker_id 格式错误，应为 host:rank（rank 必须是整数）") from exc
        if rank < 0:
            raise ValueError("BaseEvent.worker_id 格式错误，rank 必须为非负整数")

        # 3) executor_metadata & user_metadata 校验
        # 仅在 run.lifecycle.created 状态下强制校验
        if self.type == "run.lifecycle.created":
            if self.executor_metadata is None:
                raise ValueError("BaseEvent.executor_metadata 在 run.lifecycle.created 状态下必须存在")
            if self.user_metadata is None:
                raise ValueError("BaseEvent.user_metadata 在 run.lifecycle.created 状态下必须存在")

        return self


# --- Data Flow: Text & Reasoning ---

class ContentTextStartPayload(BaseModel):
    format: Literal["plain", "json","markdown","html"] = "plain"
    json_schema: Optional[Dict[str, Any]] = None

class ContentTextStartEvent(BaseEvent):
    type: Literal["content.text.start"] = "content.text.start"
    payload: ContentTextStartPayload

class ContentTextDeltaPayload(BaseModel):
    delta: str
    key_path: Optional[List[Union[str, int]]] = None

class ContentTextDeltaEvent(BaseEvent):
    type: Literal["content.text.delta"] = "content.text.delta"
    payload: ContentTextDeltaPayload

class ContentTextEndPayload(BaseModel):
    full_text: str

class ContentTextEndEvent(BaseEvent):
    type: Literal["content.text.end"] = "content.text.end"
    payload: ContentTextEndPayload                                                                                                                                                                                  

class ContentReasoningDeltaPayload(BaseModel):
    delta: str

class ContentReasoningStartPayload(BaseModel):
    format: Literal["plain", "json","markdown","html"] = "plain"

class ContentReasoningEndPayload(BaseModel):
    full_text: str

class ContentReasoningStartEvent(BaseEvent):
    type: Literal["content.reasoning.start"] = "content.reasoning.start"
    payload: ContentReasoningStartPayload

class ContentReasoningDeltaEvent(BaseEvent):
    type: Literal["content.reasoning.delta"] = "content.reasoning.delta"
    payload: ContentReasoningDeltaPayload

class ContentReasoningEndEvent(BaseEvent):
    type: Literal["content.reasoning.end"] = "content.reasoning.end"
    payload: ContentReasoningEndPayload


# --- Data Flow: Action ---

class ContentActionStartPayload(BaseModel):
    name: str
    call_type: Literal["TOOL", "AGENT", "LLM", "CHARACTER", "API"] = "API"
    intent: Optional[str] = None
    arguments_schema: Optional[Dict[str, Any]] = None

class ContentActionStartEvent(BaseEvent):
    type: Literal["content.action.start"] = "content.action.start"
    payload: ContentActionStartPayload

# 执行阶段需要输出思考过程/调用意图/调用参数
class ContentActionDeltaPayload(BaseModel):
    part: Literal["intent", "args"]
    delta: str
    key_path: Optional[List[Union[str, int]]] = None

class ContentActionDeltaEvent(BaseEvent):
    type: Literal["content.action.delta"] = "content.action.delta"
    payload: ContentActionDeltaPayload

class ContentActionEndPayload(BaseModel):
    arguments: Dict[str, Any]
    intent: Optional[str] = None

class ContentActionEndEvent(BaseEvent):
    type: Literal["content.action.end"] = "content.action.end"
    payload: ContentActionEndPayload


# --- Data Flow: Action Result ---

class ContentActionResultStartPayload(BaseModel):
    record_id: Optional[str] = None
    status: Optional[Literal["success", "error"]]
    mode: Literal["json", "text", "binary"] = "json"
    json_schema: Optional[Dict[str, Any]] = None

class ContentActionResultStartEvent(BaseEvent):
    type: Literal["content.action.result.start"] = "content.action.result.start"
    payload: ContentActionResultStartPayload

class ContentActionResultDeltaPayload(BaseModel):
    record_id: Optional[str] = None
    part: Literal["reasoning", "title", "summary", "output", "error"]
    delta: str
    key_path: Optional[List[Union[str, int]]] = None

class ContentActionResultDeltaEvent(BaseEvent):
    type: Literal["content.action.result.delta"] = "content.action.result.delta"
    payload: ContentActionResultDeltaPayload

class ContentActionResultEndPayload(BaseModel):
    record_id: Optional[str] = None
    full_result: Any
    images: Optional[List[str]] = None
    files: Optional[List[str]] = None
    status: Optional[Literal["success", "error"]]
    mode: Optional[Literal["json", "text", "binary"]] = "json"
    json_schema: Optional[Dict[str, Any]] = None

class ContentActionResultEndEvent(BaseEvent):
    type: Literal["content.action.result.end"] = "content.action.result.end"
    payload: ContentActionResultEndPayload


# --- Data Flow: Agent Result ---
# 最终结果构建事件（区别于 Action Result）
class ContentAgentResultStartPayload(BaseModel):
    mode: Literal["json", "text", "binary"] = "json"
    json_schema: Optional[Dict[str, Any]] = None

class ContentAgentResultStartEvent(BaseEvent):
    type: Literal["content.agent.result.start"] = "content.agent.result.start"
    payload: ContentAgentResultStartPayload

class ContentAgentResultDeltaPayload(BaseModel):
    delta: str
    # 用于标识该 delta 应写入的“位置/片段”。
    # 例如：output / text / reasoning / args / error 等。
    # 说明：此字段用于 UI 与流式 JSON 组装的定位，具体取值由上层约定；
    # core 不强制枚举，以便后续扩展。
    part: Literal["reasoning", "title", "summary", "output", "error"]
    key_path: Optional[List[Union[str, int]]] = None

class ContentAgentResultDeltaEvent(BaseEvent):
    type: Literal["content.agent.result.delta"] = "content.agent.result.delta"
    payload: ContentAgentResultDeltaPayload

class ContentAgentResultEndPayload(BaseModel):
    full_result: Any
    images: Optional[List[str]] = None
    files: Optional[List[str]] = None
    status: Optional[Literal["success", "error"]]
    mode: Optional[Literal["json", "text", "binary"]] = "json"
    json_schema: Optional[Dict[str, Any]] = None

class ContentAgentResultEndEvent(BaseEvent):
    type: Literal["content.agent.result.end"] = "content.agent.result.end"
    payload: ContentAgentResultEndPayload


# --- State Flow ---

class ResumeContext(BaseModel):
    """恢复上下文：用于从断点恢复执行。"""
    conversation_id: Optional[str] = None  # 对话 ID（Agent/LLM/Character 类型需要）
    breakpoint_trace_id: str  # 断点位置的 trace_id（对应 message_id 或 tool_call_record_id）
    breakpoint_type: Literal["message", "action", "tool_call"] = "message"  # 断点类型

class RunLifecycleCreatedPayload(BaseModel):
    """run.lifecycle.created payload。

    约束：created 必须携带 input_data（用于审计/恢复绑定）。
    """
    input_data: Any


class RunLifecycleCreatedEvent(BaseEvent):
    type: Literal["run.lifecycle.created"] = "run.lifecycle.created"
    payload: RunLifecycleCreatedPayload


class RunLifecycleRunningPayload(BaseModel):
    """run.lifecycle.running payload。

    运行心跳/存在态：无强制字段。
    """

    pass


class RunLifecycleRunningEvent(BaseEvent):
    type: Literal["run.lifecycle.running"] = "run.lifecycle.running"
    payload: RunLifecycleRunningPayload


class RunLifecycleSuspendedPayload(BaseModel):
    """run.lifecycle.suspended payload。"""

    reason: str
    awaiting: Optional[Dict[str, Any]] = None


class RunLifecycleSuspendedEvent(BaseEvent):
    type: Literal["run.lifecycle.suspended"] = "run.lifecycle.suspended"
    payload: RunLifecycleSuspendedPayload


class RunLifecycleResumingPayload(BaseModel):
    """run.lifecycle.resuming payload。

    约束：resuming 必须携带 resume_context；不要求 input_data。
    """

    resume_context: ResumeContext


class RunLifecycleResumingEvent(BaseEvent):
    type: Literal["run.lifecycle.resuming"] = "run.lifecycle.resuming"
    payload: RunLifecycleResumingPayload


class RunLifecycleCompletedPayload(BaseModel):
    """run.lifecycle.completed payload。"""

    output: Optional[Any] = None
    usage: Optional[Dict[str, Any]] = None


class RunLifecycleCompletedEvent(BaseEvent):
    type: Literal["run.lifecycle.completed"] = "run.lifecycle.completed"
    payload: RunLifecycleCompletedPayload


class RunLifecycleFailedPayload(BaseModel):
    """run.lifecycle.failed payload。

    约束：failed 必须携带 error。
    """

    error: Dict[str, str]
    usage: Optional[Dict[str, Any]] = None
    output: Optional[Any] = None


class RunLifecycleFailedEvent(BaseEvent):
    type: Literal["run.lifecycle.failed"] = "run.lifecycle.failed"
    payload: RunLifecycleFailedPayload


class RunLifecycleCancelledPayload(BaseModel):
    """run.lifecycle.cancelled payload。"""

    output: Optional[Any] = None
    usage: Optional[Dict[str, Any]] = None


class RunLifecycleCancelledEvent(BaseEvent):
    type: Literal["run.lifecycle.cancelled"] = "run.lifecycle.cancelled"
    payload: RunLifecycleCancelledPayload

class RunStepPayload(BaseModel):
    step_id: str
    type: Literal["retrieval", "tool_execution", "llm_inference"]
    status: Literal["started", "in_progress", "completed", "failed"]
    label: str
    details: Optional[Any] = None

class RunStepEvent(BaseEvent):
    type: Literal["run.step"] = "run.step"
    payload: RunStepPayload

class StateSyncPayload(BaseModel):
    messages: List[Any] # 暂用 Any，后续可替换为具体的 Message 模型
    agent_state: Dict[str, Any]

class StateSyncEvent(BaseEvent):
    type: Literal["state.sync"] = "state.sync"
    payload: StateSyncPayload


# --- Control Flow ---

class ControlInterruptPayload(BaseModel):
    interrupt_id: str
    type: Literal["approval", "input_request"]
    reason: str

    # 关联到具体 action（用于精确授权/确认）
    action_id: Optional[str] = Field(default=None, description="需要授权或确认的 action_id")
    action_name: Optional[str] = Field(default=None, description="action 名称")
    action_parameters: Optional[Dict[str, Any]] = Field(default=None, description="action 参数")

    # 交互约束（可选）：用于提示前端/调用方需要哪些字段、是否超时等
    required: Optional[str] = Field(default=None, description="必填要求（自由文本或标识符）")
    expected_fields: Optional[List[str]] = Field(default=None, description="期望用户补充的字段名列表")
    timeout_seconds: Optional[int] = Field(default=None, description="等待超时时间（秒）")

    data: Optional[Any] = None
    resume_token: str

class ControlInterruptEvent(BaseEvent):
    type: Literal["control.interrupt"] = "control.interrupt"
    payload: ControlInterruptPayload

class ControlSuggestionsPayload(BaseModel):
    suggestions: List[Dict[str, Any]] # { label, payload, type }

class ControlSuggestionsEvent(BaseEvent):
    type: Literal["control.suggestions"] = "control.suggestions"
    payload: ControlSuggestionsPayload

class ControlRollbackPayload(BaseModel):
    target_timestamp: float
    reason: str

class ControlRollbackEvent(BaseEvent):
    type: Literal["control.rollback"] = "control.rollback"
    payload: ControlRollbackPayload
