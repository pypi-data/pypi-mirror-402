#!/usr/bin/env python
# coding=utf-8
"""事件树聚合器（按节点自聚合）。

设计目标：
1. 每个 Trace 节点只负责聚合自身的 run 与数据流；不跨节点做合并。
2. TraceEventAggregator 仅维护树结构与事件分发，不做数据聚合逻辑。
3. run 负责流式累积，trace 负责跨 run 聚合；最终由 trace 映射到 states：
   - Agent/Character 执行者 -> Message，message.id == trace_id
   - Tool 执行者 -> ToolCallRecord，tool_call_record.id == trace_id
   - action_id 与状态模型 Action.id 保持一致
   - react_id 与状态模型 ReActRound.id 保持一致
4. run 状态可多次中断/恢复，trace 是其所有 run 的累积结果。

兼容性不考虑，直接以 v2 事件模型为基准实现最简可维护方案。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from turbo_agent_core.schema.states import (
    Conversation,
    Message,
    Action,
    ToolCallRecord,
    ReActRound,
)
from turbo_agent_core.schema.refs import ToolRef, RefType
from turbo_agent_core.schema.enums import (
    MessageRole,
    MessageStatus,
    ActionStatus,
    ConversationStatus,
)
from turbo_agent_core.schema.events import (
    BaseEvent,
    ContentTextStartEvent,
    ContentTextDeltaEvent,
    ContentTextEndEvent,
    ContentReasoningStartEvent,
    ContentReasoningDeltaEvent,
    ContentReasoningEndEvent,
    ContentActionStartEvent,
    ContentActionDeltaEvent,
    ContentActionEndEvent,
    ContentActionResultStartEvent,
    ContentActionResultDeltaEvent,
    ContentActionResultEndEvent,
    ContentAgentResultStartEvent,
    ContentAgentResultDeltaEvent,
    ContentAgentResultEndEvent,
    RunLifecycleCreatedEvent,
    RunLifecycleRunningEvent,
    RunLifecycleSuspendedEvent,
    RunLifecycleResumingEvent,
    RunLifecycleCompletedEvent,
    RunLifecycleFailedEvent,
    RunLifecycleCancelledEvent,
    ControlInterruptEvent,
    ControlSuggestionsEvent,
    ControlRollbackEvent,
)


# -------------------- 基础工具 --------------------

def _now_ts_ms() -> float:
    return datetime.utcnow().timestamp() * 1000


def _is_agent_like(executor_type: Optional[str]) -> bool:
    if not executor_type:
        return False
    upper = str(executor_type).upper()
    return "AGENT" in upper or "CHARACTER" in upper


def _is_tool_like(executor_type: Optional[str]) -> bool:
    if not executor_type:
        return False
    upper = str(executor_type).upper()
    return "TOOL" in upper or "LLM" in upper or "API" in upper


def _message_status_from_run(status: Optional[str]) -> MessageStatus:
    # 保守映射，默认 started，避免未知枚举导致校验失败
    if status in {"completed"}:
        return MessageStatus.completed if hasattr(MessageStatus, "completed") else MessageStatus.started
    if status in {"failed", "cancelled"}:
        return MessageStatus.failed if hasattr(MessageStatus, "failed") else MessageStatus.started
    return MessageStatus.started


def _action_status_from_result(status: Optional[str]) -> ActionStatus:
    if status in {"succeeded", "completed"}:
        return getattr(ActionStatus, "Succeed", ActionStatus.Succeed)
    if status in {"failed", "error"}:
        return getattr(ActionStatus, "Failed", ActionStatus.Failed)
    if status in {"running"}:
        return getattr(ActionStatus, "Running", ActionStatus.Pending)
    return ActionStatus.Pending


# -------------------- 聚合结构 --------------------

@dataclass
class TextBuffer:
    format: Optional[str] = None
    json_schema: Optional[Dict[str, Any]] = None
    deltas: List[str] = field(default_factory=list)
    full_text: Optional[str] = None

    def add_delta(self, delta: str) -> None:
        self.deltas.append(delta)

    def set_full(self, full_text: str) -> None:
        self.full_text = full_text

    def merged(self) -> str:
        if self.full_text is not None:
            return self.full_text
        return "".join(self.deltas)


@dataclass
class AggregatedFlow:
    """Run 内的独立数据流，按 type/trace 内 react 维度拆分。

    - text: 文本/推理流（带 react_id 区分轮次）
    - action_call: 单个 action_id 的意图/结果流
    - agent_result: agent 交付物流
    """

    type: str  # text | action_call | agent_result
    react_id: Optional[str] = None
    action_id: Optional[str] = None
    text: TextBuffer = field(default_factory=TextBuffer)
    reasoning: TextBuffer = field(default_factory=TextBuffer)
    action: Optional["ActionAggregate"] = None
    created_at: Optional[float] = None
    updated_at: Optional[float] = None

    def touch(self, ts: float) -> None:
        if self.created_at is None:
            self.created_at = ts
        self.updated_at = ts


@dataclass
class ActionAggregate:
    action_id: str
    react_id: Optional[str] = None
    name: Optional[str] = None
    call_type: Optional[str] = None
    intent_parts: List[str] = field(default_factory=list)
    arguments: Optional[Any] = None
    result_status: Optional[str] = None
    result_mode: Optional[str] = None
    result_json_schema: Optional[Dict[str, Any]] = None
    result_output: Optional[Any] = None
    result_error: Optional[Any] = None
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    updated_at: Optional[float] = None

    def touch(self, ts: float) -> None:
        if self.started_at is None:
            self.started_at = ts
        self.updated_at = ts

    def on_action_event(self, event: BaseEvent) -> None:
        ts = float(event.timestamp)
        self.touch(ts)
        if isinstance(event, ContentActionStartEvent):
            self.name = event.payload.name
            self.call_type = event.payload.call_type
            if event.payload.intent:
                self.intent_parts.append(event.payload.intent)
        elif isinstance(event, ContentActionDeltaEvent):
            if event.payload.part == "intent":
                self.intent_parts.append(event.payload.delta)
            elif event.payload.part == "args":
                # 简化处理，直接追加文本；若上游传 dict，会在 end 覆盖
                if isinstance(self.arguments, str):
                    self.arguments += event.payload.delta
                elif self.arguments is None:
                    self.arguments = event.payload.delta
        elif isinstance(event, ContentActionEndEvent):
            self.arguments = dict(event.payload.arguments)
            if event.payload.intent:
                self.intent_parts.append(event.payload.intent)
            self.finished_at = ts

    def on_result_event(self, event: BaseEvent) -> None:
        ts = float(event.timestamp)
        self.touch(ts)
        if isinstance(event, ContentActionResultStartEvent):
            self.result_status = event.payload.status
            self.result_mode = event.payload.mode
            self.result_json_schema = event.payload.json_schema
        elif isinstance(event, ContentActionResultDeltaEvent):
            part = event.payload.part
            if part == "error":
                if isinstance(self.result_error, str):
                    self.result_error += event.payload.delta
                elif self.result_error is None:
                    self.result_error = event.payload.delta
            elif part == "output":
                if isinstance(self.result_output, str):
                    self.result_output += event.payload.delta
                elif self.result_output is None:
                    self.result_output = event.payload.delta
        elif isinstance(event, ContentActionResultEndEvent):
            self.result_output = event.payload.full_result
            self.result_status = event.payload.status or self.result_status
            self.result_mode = event.payload.mode or self.result_mode
            self.result_json_schema = event.payload.json_schema or self.result_json_schema
            self.finished_at = ts

    def to_action(self, tool_records: List[ToolCallRecord]) -> Action:
        intent = "".join(self.intent_parts) if self.intent_parts else None
        observation = None
        if self.result_error is not None:
            observation = str(self.result_error)
        action_status = _action_status_from_result(self.result_status)

        tool_ref: Optional[ToolRef] = None
        if tool_records:
            first = tool_records[0]
            tool_ref = ToolRef(
                id=first.tool_version_id or first.id,
                type=RefType.Tool,
                name=first.tool_name_id,
                belongToProjectId=first.tool_project_id,
            )
        elif self.name:
            parts = self.name.split("@", 1)
            name_id = parts[0]
            belong = parts[1] if len(parts) > 1 else None
            tool_ref = ToolRef(
                id=self.name,
                type=RefType.Tool,
                name=name_id,
                belongToProjectId=belong,
            )
        else:
            tool_ref = ToolRef(
                id=self.action_id,
                type=RefType.Tool,
                name=None,
                belongToProjectId=None,
            )

        return Action(
            id=self.action_id,
            type="ActionExecutionMessage",
            name=self.name,
            thought=intent,
            intent=intent,
            title=None,
            summary=None,
            input=self.arguments,
            observation=observation,
            final_answer=self.result_output,
            approved_status=None,
            tokenCost=None,
            moneyCost=None,
            status=action_status,
            tool=tool_ref,
            records=tool_records,
            created_at=datetime.fromtimestamp(self.started_at / 1000) if self.started_at else datetime.utcnow(),
            updated_at=datetime.fromtimestamp((self.finished_at or self.updated_at or _now_ts_ms()) / 1000),
        )


@dataclass
class RunAggregate:
    run_id: str
    run_path: Optional[List[str]] = None
    executor_id: Optional[str] = None
    executor_type: Optional[str] = None
    executor_path: Optional[List[str]] = None
    status: Optional[str] = None
    input_data: Any = None
    resume_context: Optional[Dict[str, Any]] = None
    usage: Optional[Dict[str, Any]] = None
    error: Optional[Any] = None
    output: Optional[Any] = None
    agent_result: Dict[str, Any] = field(default_factory=dict)
    # 累积多个数据流，按 react_id/action_id 拆分
    data_flows: List[AggregatedFlow] = field(default_factory=list)
    actions: Dict[str, ActionAggregate] = field(default_factory=dict)
    control: Dict[str, Any] = field(default_factory=lambda: {"latest_interrupt": None, "suggestions": []})
    created_at: Optional[float] = None
    finished_at: Optional[float] = None
    updated_at: Optional[float] = None
    keepalive: List[float] = field(default_factory=list)

    def touch(self, ts: float) -> None:
        if self.created_at is None:
            self.created_at = ts
        self.updated_at = ts

    # 生命周期处理
    def on_lifecycle(self, event: BaseEvent) -> None:
        ts = float(event.timestamp)
        status_map = {
            "run.lifecycle.created": "created",
            "run.lifecycle.running": "running",
            "run.lifecycle.suspended": "suspended",
            "run.lifecycle.resuming": "resuming",
            "run.lifecycle.completed": "completed",
            "run.lifecycle.failed": "failed",
            "run.lifecycle.cancelled": "cancelled",
        }
        self.status = status_map.get(event.type, self.status)
        if isinstance(event, RunLifecycleCreatedEvent):
            self.input_data = getattr(event.payload, "input_data", None)
        if isinstance(event, RunLifecycleResumingEvent):
            self.resume_context = getattr(event.payload, "resume_context", None)
        if isinstance(event, (RunLifecycleCompletedEvent, RunLifecycleFailedEvent, RunLifecycleCancelledEvent)):
            self.usage = getattr(event.payload, "usage", None) or self.usage
            self.output = getattr(event.payload, "output", None) or self.output
            self.error = getattr(event.payload, "error", None) or self.error
            self.finished_at = ts
        if isinstance(event, RunLifecycleRunningEvent):
            self.keepalive.append(ts)
        self.touch(ts)

    # 文本/推理
    def _ensure_flow(self, flow_type: str, react_id: Optional[str] = None, action_id: Optional[str] = None) -> AggregatedFlow:
        for f in self.data_flows:
            if f.type == flow_type and f.react_id == react_id and f.action_id == action_id:
                return f
        flow = AggregatedFlow(type=flow_type, react_id=react_id, action_id=action_id)
        self.data_flows.append(flow)
        return flow

    def _get_text_flow(self, react_id: Optional[str]) -> AggregatedFlow:
        return self._ensure_flow("text", react_id=react_id)

    def _get_action_flow(self, action_id: str, react_id: Optional[str]) -> AggregatedFlow:
        return self._ensure_flow("action_call", react_id=react_id, action_id=action_id)

    # action
    def _get_action(self, action_id: str, react_id: Optional[str]) -> ActionAggregate:
        if action_id not in self.actions:
            self.actions[action_id] = ActionAggregate(action_id=action_id, react_id=react_id)
        act = self.actions[action_id]
        if react_id and act.react_id is None:
            act.react_id = react_id
        return act

    # 事件分派
    def on_event(self, event: BaseEvent) -> None:
        ts = float(event.timestamp)
        self.touch(ts)
        if event.run_path is not None and self.run_path is None:
            self.run_path = list(event.run_path)
        if event.executor_id:
            self.executor_id = event.executor_id
        if event.executor_type:
            self.executor_type = str(event.executor_type)
        if event.executor_path:
            self.executor_path = list(event.executor_path)

        if isinstance(event, (
            RunLifecycleCreatedEvent,
            RunLifecycleRunningEvent,
            RunLifecycleSuspendedEvent,
            RunLifecycleResumingEvent,
            RunLifecycleCompletedEvent,
            RunLifecycleFailedEvent,
            RunLifecycleCancelledEvent,
        )):
            self.on_lifecycle(event)
            return

        if isinstance(event, ControlInterruptEvent):
            self.control["latest_interrupt"] = event.payload.model_dump()
            return
        if isinstance(event, ControlSuggestionsEvent):
            self.control["suggestions"] = list(event.payload.suggestions)
            return

        # 文本/推理
        if isinstance(event, ContentTextStartEvent):
            flow = self._get_text_flow(event.react_id)
            flow.touch(ts)
            flow.text.format = event.payload.format
            flow.text.json_schema = event.payload.json_schema
            return
        if isinstance(event, ContentTextDeltaEvent):
            flow = self._get_text_flow(event.react_id)
            flow.touch(ts)
            flow.text.add_delta(event.payload.delta)
            return
        if isinstance(event, ContentTextEndEvent):
            flow = self._get_text_flow(event.react_id)
            flow.touch(ts)
            flow.text.set_full(event.payload.full_text)
            return
        if isinstance(event, ContentReasoningStartEvent):
            flow = self._get_text_flow(event.react_id)
            flow.touch(ts)
            flow.reasoning.format = event.payload.format
            return
        if isinstance(event, ContentReasoningDeltaEvent):
            flow = self._get_text_flow(event.react_id)
            flow.touch(ts)
            flow.reasoning.add_delta(event.payload.delta)
            return
        if isinstance(event, ContentReasoningEndEvent):
            flow = self._get_text_flow(event.react_id)
            flow.touch(ts)
            flow.reasoning.set_full(event.payload.full_text)
            return

        # 行为流
        if isinstance(event, (ContentActionStartEvent, ContentActionDeltaEvent, ContentActionEndEvent)):
            act = self._get_action(event.action_id, event.react_id)
            flow = self._get_action_flow(event.action_id, event.react_id)
            flow.action = act
            flow.touch(ts)
            act.on_action_event(event)
            return
        if isinstance(event, (ContentActionResultStartEvent, ContentActionResultDeltaEvent, ContentActionResultEndEvent)):
            act = self._get_action(event.action_id, event.react_id)
            flow = self._get_action_flow(event.action_id, event.react_id)
            flow.action = act
            flow.touch(ts)
            act.on_result_event(event)
            return

        # Agent 结果
        if isinstance(event, ContentAgentResultStartEvent):
            flow = self._ensure_flow("agent_result")
            flow.touch(ts)
            self.agent_result["mode"] = event.payload.mode
            self.agent_result["json_schema"] = event.payload.json_schema
            return
        if isinstance(event, ContentAgentResultDeltaEvent):
            flow = self._ensure_flow("agent_result")
            flow.touch(ts)
            part = event.payload.part or "text"
            key = f"delta_{part}"
            prev = self.agent_result.get(key)
            if prev is None:
                self.agent_result[key] = event.payload.delta
            else:
                self.agent_result[key] = str(prev) + event.payload.delta
            return
        if isinstance(event, ContentAgentResultEndEvent):
            flow = self._ensure_flow("agent_result")
            flow.touch(ts)
            self.agent_result["full_result"] = event.payload.full_result
            return


@dataclass
class TraceSnapshot:
    status: Optional[str]
    text_by_react: Dict[Optional[str], str]
    reasoning_by_react: Dict[Optional[str], str]
    actions: Dict[str, ActionAggregate]
    agent_result: Dict[str, Any]
    usage: Optional[Dict[str, Any]]
    created_at: Optional[float]
    updated_at: Optional[float]
    executor_id: Optional[str]
    executor_type: Optional[str]


@dataclass
class TraceNode:
    trace_id: str
    parent_trace_id: Optional[str] = None
    parent_action_id: Optional[str] = None
    children_trace_ids: List[str] = field(default_factory=list)
    runs: Dict[str, RunAggregate] = field(default_factory=dict)
    run_order: List[str] = field(default_factory=list)

    def ensure_run(self, run_id: str) -> RunAggregate:
        if run_id not in self.runs:
            self.runs[run_id] = RunAggregate(run_id=run_id)
            self.run_order.append(run_id)
        return self.runs[run_id]

    def on_event(self, event: BaseEvent) -> None:
        run = self.ensure_run(event.run_id)
        run.on_event(event)

    def aggregate(self) -> TraceSnapshot:
        # 按运行时间顺序累积，不再简单覆盖，保留多次运行的输出
        ordered_runs = [self.runs[rid] for rid in self.run_order if rid in self.runs]
        text_by_react: Dict[Optional[str], str] = {}
        reasoning_by_react: Dict[Optional[str], str] = {}
        actions: Dict[str, ActionAggregate] = {}
        agent_result: Dict[str, Any] = {}
        usage: Optional[Dict[str, Any]] = None
        status: Optional[str] = None
        created_at: Optional[float] = None
        updated_at: Optional[float] = None
        executor_id: Optional[str] = None
        executor_type: Optional[str] = None

        for run in ordered_runs:
            for flow in run.data_flows:
                # 文本/推理按 react_id 追加
                if flow.type == "text":
                    merged_text = flow.text.merged()
                    merged_reasoning = flow.reasoning.merged()
                    if merged_text:
                        prev = text_by_react.get(flow.react_id, "")
                        text_by_react[flow.react_id] = prev + merged_text
                    if merged_reasoning:
                        prev_r = reasoning_by_react.get(flow.react_id, "")
                        reasoning_by_react[flow.react_id] = prev_r + merged_reasoning
                elif flow.type == "action_call" and flow.action is not None:
                    actions[flow.action.action_id] = flow.action
                elif flow.type == "agent_result" and run.agent_result:
                    agent_result = run.agent_result

            if run.usage:
                usage = run.usage
            if run.status:
                status = run.status
            if run.executor_id:
                executor_id = run.executor_id
            if run.executor_type:
                executor_type = run.executor_type
            created_at = created_at or run.created_at
            updated_at = run.updated_at or updated_at
        return TraceSnapshot(
            status=status,
            text_by_react=text_by_react,
            reasoning_by_react=reasoning_by_react,
            actions=actions,
            agent_result=agent_result,
            usage=usage,
            created_at=created_at,
            updated_at=updated_at,
            executor_id=executor_id,
            executor_type=executor_type,
        )

    def is_agent(self) -> bool:
        snapshot = self.aggregate()
        return _is_agent_like(snapshot.executor_type)

    def is_tool(self) -> bool:
        snapshot = self.aggregate()
        return _is_tool_like(snapshot.executor_type)

    def to_tool_call_record(self, snapshot: TraceSnapshot) -> ToolCallRecord:
        status_map = {
            "completed": "succeeded",
            "failed": "failed",
            "cancelled": "failed",
            "running": "running",
        }
        record_status = status_map.get(snapshot.status or "", "pending")
        return ToolCallRecord(
            id=self.trace_id,
            tool_project_id=None,
            tool_name_id=None,
            tool_version_id=snapshot.executor_id,
            tool_type="API",
            title=None,
            intent=None,
            summary=None,
            input=None,
            result=snapshot.agent_result.get("full_result") if snapshot.agent_result else None,
            tokenCost=None,
            moneyCost=None,
            modelUsed=snapshot.executor_id,
            error_message=None,
            status=record_status,
            time_cost=None,
            pre_edges=[],
            next_edges=[],
            agent_caller_id=None,
            agent_project_id=None,
            related_message_action_ids=[],
            worker_id=None,
            worker_host=None,
            worker_type=None,
            secret_id=None,
            user_caller_id=None,
            root_user_id=None,
            created_at=datetime.fromtimestamp((snapshot.created_at or _now_ts_ms()) / 1000),
            updated_at=datetime.fromtimestamp((snapshot.updated_at or _now_ts_ms()) / 1000),
        )

    def to_message(self, snapshot: TraceSnapshot, tool_records_by_action: Dict[str, List[ToolCallRecord]]) -> Tuple[Message, List[Action]]:
        # 文本优先顺序：默认 react None 文本 -> agent_result.full_result
        content = snapshot.text_by_react.get(None)
        if content is None and snapshot.agent_result:
            full = snapshot.agent_result.get("full_result")
            if isinstance(full, dict):
                content = full.get("content") or str(full)
            elif full is not None:
                content = str(full)
        reasoning_content = snapshot.reasoning_by_react.get(None)

        msg_status = _message_status_from_run(snapshot.status)
        message = Message(
            id=self.trace_id,
            type="TextMessage",
            role=MessageRole.assistant,
            content=content or "",
            reasoning_content=reasoning_content,
            reactRounds=[],
            actions=[],
            status=msg_status,
            tokenCost=snapshot.usage.get("total_tokens") if snapshot.usage else None,
            moneyCost=snapshot.usage.get("total_cost") if snapshot.usage else None,
            modelUsed=snapshot.executor_id,
            created_at=datetime.fromtimestamp((snapshot.created_at or _now_ts_ms()) / 1000),
            updated_at=datetime.fromtimestamp((snapshot.updated_at or _now_ts_ms()) / 1000),
            ancestors=[],
            children=[],
        )

        actions: List[Action] = []
        for act_id, act in snapshot.actions.items():
            records = tool_records_by_action.get(act_id, [])
            actions.append(act.to_action(records))

        # ReAct 轮次：整合文本/推理/动作，只要 react_id 存在即可建轮次
        react_rounds: List[ReActRound] = []
        react_ids: set[Optional[str]] = set(k for k in snapshot.text_by_react.keys())
        react_ids.update(a.react_id for a in actions if getattr(a, "react_id", None) is not None)
        for react_id in react_ids:
            if react_id is None:
                continue
            rr = ReActRound(
                id=react_id,
                thought=snapshot.reasoning_by_react.get(react_id),
                content=snapshot.text_by_react.get(react_id),
                belongToMessageId=message.id,
                actions=[a for a in actions if getattr(a, "react_id", None) == react_id],
            )
            react_rounds.append(rr)

        # 将 React 轮次附加到 message，其他动作直接挂 message.actions
        message.reactRounds = react_rounds
        message.actions = actions
        return message, actions


# -------------------- 聚合器 --------------------

class TraceEventAggregator:
    """维护 trace 树并分发事件，聚合逻辑下沉到节点内部。"""

    def __init__(self, root_trace_id: Optional[str] = None):
        self.root_trace_id = root_trace_id
        self._nodes: Dict[str, TraceNode] = {}
        if root_trace_id:
            self._nodes[root_trace_id] = TraceNode(trace_id=root_trace_id)

    def _ensure_node(self, trace_id: str) -> TraceNode:
        if trace_id not in self._nodes:
            self._nodes[trace_id] = TraceNode(trace_id=trace_id)
        return self._nodes[trace_id]

    def _link_path(self, trace_path: List[str], action_id: Optional[str]) -> TraceNode:
        if self.root_trace_id is None:
            base_trace_id = trace_path[0] if trace_path else None
            if base_trace_id is None:
                raise ValueError("root trace 未初始化且事件未包含 trace_path")
            self.root_trace_id = base_trace_id
            self._nodes[self.root_trace_id] = TraceNode(trace_id=self.root_trace_id)

        current = self._ensure_node(self.root_trace_id)
        # trace_path 为空表示根节点事件，不应形成自环
        for tid in trace_path:
            child = self._ensure_node(tid)
            if child.parent_trace_id is None:
                child.parent_trace_id = current.trace_id
            if tid not in current.children_trace_ids:
                current.children_trace_ids.append(tid)
            current = child
        if action_id and current.parent_action_id is None:
            current.parent_action_id = action_id
        return current

    def on_event(self, event: BaseEvent) -> None:
        # rollback：按时间戳截断重建，改为简单跳过（无状态回放需求时可扩展）
        if isinstance(event, ControlRollbackEvent):
            return

        # 首事件可用 trace_id 初始化根，避免空 trace_path 抛错
        if self.root_trace_id is None:
            self.root_trace_id = event.trace_id
            self._nodes[self.root_trace_id] = TraceNode(trace_id=self.root_trace_id)

        # trace_path 可能为空（例如 root run 创建事件未带 trace_path），用空列表表示根，不再把 root 当作自己的子节点
        normalized_path = event.trace_path if event.trace_path is not None else []
        target = self._link_path(normalized_path, event.action_id)
        target.on_event(event)

    # -------- 导出 states --------
    def to_states(self) -> Dict[str, Any]:
        if self.root_trace_id is None or self.root_trace_id not in self._nodes:
            return {"conversation": None, "messages": [], "actions": [], "tool_call_records": []}

        # 预聚合：收集每个节点的 snapshot
        snapshots: Dict[str, TraceSnapshot] = {tid: node.aggregate() for tid, node in self._nodes.items()}

        # 先收集 tool call，以便动作挂载
        tool_call_records: List[ToolCallRecord] = []
        tool_records_by_action: Dict[str, List[ToolCallRecord]] = {}
        for tid, node in self._nodes.items():
            snap = snapshots[tid]
            if _is_tool_like(snap.executor_type):
                record = node.to_tool_call_record(snap)
                tool_call_records.append(record)
                if node.parent_action_id:
                    tool_records_by_action.setdefault(node.parent_action_id, []).append(record)

        # 构造会话与消息
        root_snapshot = snapshots[self.root_trace_id]
        assistant_id = root_snapshot.executor_id or "unknown"
        conversation = Conversation(
            id=self.root_trace_id,
            title=None,
            status=ConversationStatus.started,
            assistant_id=assistant_id,
            root_message_id=None,
            messages=[],
            context=None,
            knowledge_refs=[],
            workset_refs=[],
            toolcall_refs=[],
        )

        messages: List[Message] = []
        actions: List[Action] = []

        visited: set[str] = set()

        def dfs_build(trace_id: str, parent_msg_id: Optional[str]) -> None:
            # 防循环：trace_path 异常时可能形成环，跳过已访问节点
            if trace_id in visited:
                return
            visited.add(trace_id)
            node = self._nodes[trace_id]
            snap = snapshots[trace_id]
            current_msg_id = parent_msg_id

            if _is_agent_like(snap.executor_type):
                msg, acts = node.to_message(snap, tool_records_by_action)
                messages.append(msg)
                actions.extend(acts)
                # 树挂载：优先使用 parent_msg_id；无父则 conversation 根
                try:
                    if parent_msg_id:
                        conversation.add_child(msg, parent_id=parent_msg_id)
                    else:
                        conversation.add_child(msg)
                except Exception:
                    # 兜底追加，保证不丢数据
                    conversation.messages.append(msg)
                    if not conversation.root_message_id:
                        conversation.root_message_id = msg.id
                current_msg_id = msg.id

            for child_id in node.children_trace_ids:
                dfs_build(child_id, current_msg_id)

        dfs_build(self.root_trace_id, None)

        if conversation.messages and not conversation.root_message_id:
            conversation.root_message_id = conversation.messages[0].id

        return {
            "conversation": conversation,
            "messages": messages,
            "actions": actions,
            "tool_call_records": tool_call_records,
        }

    def get_tree_snapshot(self) -> Dict[str, Any]:
        """导出简单树形快照，便于调试。

        说明：
        - 节点只包含最小运行摘要，不再尝试跨节点聚合数据流。
        - run 下提供文本/推理/动作/agent_result 的粗略快照，供 CLI 展示使用。
        """

        if self.root_trace_id is None or self.root_trace_id not in self._nodes:
            return {"root_trace_id": None, "trace_nodes": []}

        trace_nodes: List[Dict[str, Any]] = []
        for trace_id, node in self._nodes.items():
            runs: List[Dict[str, Any]] = []
            for rid in node.run_order:
                if rid not in node.runs:
                    continue
                run = node.runs[rid]
                text_by_react: Dict[Optional[str], str] = {}
                reasoning_by_react: Dict[Optional[str], str] = {}
                flows_dump: List[Dict[str, Any]] = []
                for f in run.data_flows:
                    if f.type == "text":
                        t = f.text.merged()
                        r = f.reasoning.merged()
                        if t:
                            prev = text_by_react.get(f.react_id, "")
                            text_by_react[f.react_id] = prev + t
                        if r:
                            prev_r = reasoning_by_react.get(f.react_id, "")
                            reasoning_by_react[f.react_id] = prev_r + r
                    flows_dump.append({
                        "type": f.type,
                        "react_id": f.react_id,
                        "action_id": f.action_id,
                        "text": f.text.merged(),
                        "reasoning": f.reasoning.merged(),
                        "action": {
                            "react_id": f.action.react_id if f.action else None,
                            "name": f.action.name if f.action else None,
                            "status": f.action.result_status if f.action else None,
                            "output": f.action.result_output if f.action else None,
                            "error": f.action.result_error if f.action else None,
                        } if f.action else None,
                        "created_at": f.created_at,
                        "updated_at": f.updated_at,
                    })

                runs.append(
                    {
                        "run_id": rid,
                        "status": run.status,
                        "run_path": run.run_path,
                        "executor_id": run.executor_id,
                        "executor_type": run.executor_type,
                        "executor_path": run.executor_path,
                        "input_data": run.input_data,
                        "resume_context": run.resume_context,
                        "usage": run.usage,
                        "error": run.error,
                        "output": run.output,
                        "agent_result": run.agent_result,
                        "text_by_react": text_by_react,
                        "reasoning_by_react": reasoning_by_react,
                        "actions": {aid: {
                            "react_id": act.react_id,
                            "name": act.name,
                            "status": act.result_status,
                            "output": act.result_output,
                            "error": act.result_error,
                        } for aid, act in run.actions.items()},
                        "data_flows": flows_dump,
                        "keepalive": list(run.keepalive),
                        "created_at": run.created_at,
                        "updated_at": run.updated_at,
                    }
                )

            trace_nodes.append(
                {
                    "trace_id": trace_id,
                    "parent_trace_id": node.parent_trace_id,
                    "parent_action_id": node.parent_action_id,
                    "children_trace_ids": list(node.children_trace_ids),
                    "runs": runs,
                }
            )

        return {"root_trace_id": self.root_trace_id, "trace_nodes": trace_nodes}
