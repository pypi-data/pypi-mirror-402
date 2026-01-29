
"""事件流聚合器（单节点、单 run 简化版）。

设计意图：
1. 面向最简单场景：一个 trace 对应一个 run，不考虑嵌套子 trace。
2. 支持三类数据流：文本/推理流、action 调用与结果流、agent 交付结果流。
3. 以生命周期事件为骨架，聚合出可直接用于落库或上层消费的快照。
"""

from __future__ import annotations
import json
from loguru import logger
from dataclasses import dataclass, field, is_dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

class EnhancedJSONEncoder(json.JSONEncoder):
	def default(self, o):
		if is_dataclass(o):
			return asdict(o)
		if isinstance(o, datetime):
			return o.isoformat()
		if isinstance(o, set):
			return list(o)
		try:
			return super().default(o)
		except TypeError:
			return str(o)

def _dump_json(obj: Any) -> str:
	return json.dumps(obj, cls=EnhancedJSONEncoder, ensure_ascii=False)


from turbo_agent_core.schema.enums import (
	ActionStatus,
	MessageRole,
	MessageStatus,
)
from turbo_agent_core.schema.states import Action, Message, ReActRound, ToolCallRecord
from turbo_agent_core.schema.events import (
	BaseEvent,
	ContentActionDeltaEvent,
	ContentActionEndEvent,
	ContentActionResultDeltaEvent,
	ContentActionResultEndEvent,
	ContentActionResultStartEvent,
	ContentActionStartEvent,
	ContentAgentResultDeltaEvent,
	ContentAgentResultEndEvent,
	ContentAgentResultStartEvent,
	ContentReasoningDeltaEvent,
	ContentReasoningEndEvent,
	ContentReasoningStartEvent,
	ContentTextDeltaEvent,
	ContentTextEndEvent,
	ContentTextStartEvent,
	ControlInterruptEvent,
	ControlRollbackEvent,
	ControlSuggestionsEvent,
	RunLifecycleCancelledEvent,
	RunLifecycleCompletedEvent,
	RunLifecycleCreatedEvent,
	RunLifecycleFailedEvent,
	RunLifecycleResumingEvent,
	RunLifecycleRunningEvent,
	RunLifecycleSuspendedEvent,
)


# -------------------- 基础结构 --------------------


@dataclass
class TextBuffer:
	"""流式文本累积器。"""

	format: Optional[str] = None
	json_schema: Optional[Dict[str, Any]] = None
	deltas: List[str] = field(default_factory=list)
	full_text: Optional[str] = None

	def add_delta(self, delta: str) -> None:
		self.deltas.append(delta)

	def set_full(self, text: str) -> None:
		self.full_text = text

	def merged(self) -> str:
		if self.full_text is not None:
			return self.full_text
		return "".join(self.deltas)

@dataclass
class AgentResultAggregate:
	"""Agent 交付结果聚合。"""

	mode: Optional[str] = None
	json_schema: Optional[Dict[str, Any]] = None
	deltas: Dict[str, str] = field(default_factory=dict)
	full_result: Any = None
	status: Optional[str] = None
	images: List[str] = field(default_factory=list)
	files: List[str] = field(default_factory=list)
	created_at: Optional[float] = None
	updated_at: Optional[float] = None

	def touch(self, ts: float) -> None:
		if self.created_at is None:
			self.created_at = ts
		self.updated_at = ts

	def add_delta(self, part: str, delta: str, ts: float) -> None:
		self.touch(ts)
		prev = self.deltas.get(part)
		self.deltas[part] = (prev or "") + delta

	def set_start(self, mode: str, json_schema: Optional[Dict[str, Any]], ts: float) -> None:
		self.touch(ts)
		self.mode = mode
		self.json_schema = json_schema

	def set_end(self, full_result: Any, status: Optional[str], mode: Optional[str], json_schema: Optional[Dict[str, Any]], images: Optional[List[str]], files: Optional[List[str]], ts: float) -> None:
		self.touch(ts)
		self.full_result = full_result
		self.status = status or self.status
		if mode:
			self.mode = mode
		if json_schema:
			self.json_schema = json_schema
		if images:
			self.images = list(images)
		if files:
			self.files = list(files)


@dataclass
class ActionAggregate:
	"""Action 调用与结果聚合。

	状态维护说明：
	- is_closed: 是否终结。由事件流（End事件）或 Trace 级终结决定。
	- is_stored: 是否已持久化。由外部通过 set_stored 控制。
	"""

	action_id: str
	react_id: Optional[str] = None
	name: Optional[str] = None
	call_type: Optional[str] = None
	intent_parts: List[str] = field(default_factory=list)
	arguments: Any = None
	result_record_id: Optional[str] = None
	result_status: Optional[str] = None
	result_mode: Optional[str] = None
	result_json_schema: Optional[Dict[str, Any]] = None
	result_output: Any = None
	result_error: Any = None
	started_at: Optional[float] = None
	finished_at: Optional[float] = None
	updated_at: Optional[float] = None
	is_closed: bool = False
	is_stored: bool = False
	stored_at: Optional[float] = None

	def set_closed(self, closed: bool) -> None:
		self.is_closed = closed

	def set_stored(self, stored: bool, ts: float) -> None:
		self.is_stored = stored
		self.stored_at = ts

	def to_state(self) -> Action:
		# 转换时间戳
		start_ts = self.started_at
		if start_ts and start_ts > 1e11:
			start_ts = start_ts / 1000.0
			
		update_ts = self.updated_at
		if update_ts and update_ts > 1e11:
			update_ts = update_ts / 1000.0

		dt_created = datetime.utcfromtimestamp(start_ts) if start_ts else datetime.utcnow()
		dt_updated = datetime.utcfromtimestamp(update_ts) if update_ts else datetime.utcnow()

		# 映射状态
		tc_status = "pending"
		act_status = ActionStatus.Pending

		if self.result_status == "success":
			tc_status = "succeeded"
			act_status = ActionStatus.Succeed
		elif self.result_status == "error":
			tc_status = "failed"
			act_status = ActionStatus.Failed
		elif self.status == "running" or self.result_status == "running":
			tc_status = "running"
			act_status = ActionStatus.Running
		elif self.finished_at:
			# 如果已结束但非明确成功/失败，视为 Finish
			act_status = ActionStatus.Finished

		# 构造 ToolCallRecord (id 使用 result_record_id 以对应子 trace)
		record_id = self.result_record_id or f"call_{self.action_id}"
		record = ToolCallRecord(
			id=record_id,
			tool_name_id=self.name,
			tool_type="API",
			intent=self.merged_intent(),
			input=self.arguments,
			result=self.result_output,
			error_message=self.result_error,
			status=tc_status,
			created_at=dt_created,
			updated_at=dt_updated,
		)

		return Action(
			id=self.action_id,
			name=self.name,
			intent=self.merged_intent(),
			input=self.arguments,
			observation=self.result_output,
			status=act_status,
			records=[record],
			created_at=dt_created,
			updated_at=dt_updated,
		)

	def touch(self, ts: float) -> None:
		if self.started_at is None:
			self.started_at = ts
		self.updated_at = ts

	def on_action_event(self, event: BaseEvent, ts: float) -> None:
		self.touch(ts)
		
		# 兼容 dict 类型的 payload
		payload = event.payload
		
		if event.type == "content.action.start":
			self.name = payload.get("name") if isinstance(payload, dict) else getattr(payload, "name", None)
			self.call_type = payload.get("call_type") if isinstance(payload, dict) else getattr(payload, "call_type", None)
			intent = payload.get("intent") if isinstance(payload, dict) else getattr(payload, "intent", None)
			if intent:
				self.intent_parts.append(intent)
		elif event.type == "content.action.delta":
			part = payload.get("part") if isinstance(payload, dict) else getattr(payload, "part", None)
			delta = payload.get("delta") if isinstance(payload, dict) else getattr(payload, "delta", None)
			
			if part == "intent":
				self.intent_parts.append(delta)
			elif part == "args":
				# 简化处理：追加字符串参数
				current = self.arguments or ""
				self.arguments = f"{current}{delta}" if isinstance(current, str) else delta
		elif event.type == "content.action.end":
			args = payload.get("arguments") if isinstance(payload, dict) else getattr(payload, "arguments", None)
			self.arguments = dict(args) if args else {}
			
			intent = payload.get("intent") if isinstance(payload, dict) else getattr(payload, "intent", None)
			if intent:
				self.intent_parts.append(intent)
			

	def on_result_event(self, event: BaseEvent, ts: float) -> None:
		self.touch(ts)
		
		# 兼容 dict 类型的 payload
		payload = event.payload
		
		if event.type == "content.action_result.start":
			self.result_record_id = payload.get("record_id") if isinstance(payload, dict) else getattr(payload, "record_id", None)
			self.result_status = payload.get("status") if isinstance(payload, dict) else getattr(payload, "status", None)
			self.result_mode = payload.get("mode") if isinstance(payload, dict) else getattr(payload, "mode", None)
			self.result_json_schema = payload.get("json_schema") if isinstance(payload, dict) else getattr(payload, "json_schema", None)
		elif event.type == "content.action_result.delta":
			self.result_record_id = payload.get("record_id") if isinstance(payload, dict) else getattr(payload, "record_id", None)
			part = payload.get("part") if isinstance(payload, dict) else getattr(payload, "part", None)
			delta = payload.get("delta") if isinstance(payload, dict) else getattr(payload, "delta", None)
			
			if part == "error":
				current = self.result_error or ""
				self.result_error = f"{current}{delta}" if isinstance(current, str) else delta
			elif part == "output":
				current = self.result_output or ""
				self.result_output = f"{current}{delta}" if isinstance(current, str) else delta
		elif event.type == "content.action_result.end":
			self.result_record_id = payload.get("record_id") if isinstance(payload, dict) else getattr(payload, "record_id", None)
			self.result_output = payload.get("full_result") if isinstance(payload, dict) else getattr(payload, "full_result", None)
			
			status = payload.get("status") if isinstance(payload, dict) else getattr(payload, "status", None)
			mode = payload.get("mode") if isinstance(payload, dict) else getattr(payload, "mode", None)
			json_schema = payload.get("json_schema") if isinstance(payload, dict) else getattr(payload, "json_schema", None)
			
			self.result_status = status or self.result_status
			self.result_mode = mode or self.result_mode
			self.result_json_schema = json_schema or self.result_json_schema
			self.finished_at = ts
			self.set_closed(True)

	def merged_intent(self) -> Optional[str]:
		if not self.intent_parts:
			return None
		return "".join(self.intent_parts)


@dataclass
class ReActFlow:
	"""按 react_id 聚合的文本/推理流。

	状态维护说明：
	- is_closed: 是否终结。跟随所属 Run 或 Trace 的终结状态。
	- is_stored: 是否已持久化。由外部通过 set_stored 控制。
	"""

	react_id: Optional[str]
	text: TextBuffer = field(default_factory=TextBuffer)
	reasoning: TextBuffer = field(default_factory=TextBuffer)
	actions: Dict[str, ActionAggregate] = field(default_factory=dict)
	created_at: Optional[float] = None
	updated_at: Optional[float] = None
	is_closed: bool = False
	is_stored: bool = False
	stored_at: Optional[float] = None

	def set_closed(self, closed: bool) -> None:
		self.is_closed = closed

	def set_stored(self, stored: bool, ts: float) -> None:
		self.is_stored = stored
		self.stored_at = ts

	def to_state(self, belong_to_message_id: str) -> ReActRound:
		return ReActRound(
			id=self.react_id or f"react_{belong_to_message_id}_default",
			thought=self.reasoning.merged(),
			content=self.text.merged(),
			belongToMessageId=belong_to_message_id,
			actions=[act.to_state() for act in self.actions.values()],
		)

	def touch(self, ts: float) -> None:
		if self.created_at is None:
			self.created_at = ts
		self.updated_at = ts

	def _ensure_action(self, action_id: str) -> ActionAggregate:
		if action_id not in self.actions:
			self.actions[action_id] = ActionAggregate(action_id=action_id, react_id=self.react_id)
		return self.actions[action_id]

	def on_event(self, event: BaseEvent, ts: float) -> None:
		self.touch(ts)

		# 兼容 dict 类型的 payload
		payload = event.payload

		# Text
		if event.type == "content.text.start":
			self.text.format = payload.get("format") if isinstance(payload, dict) else getattr(payload, "format", None)
			self.text.json_schema = payload.get("json_schema") if isinstance(payload, dict) else getattr(payload, "json_schema", None)
		elif event.type == "content.text.delta":
			delta = payload.get("delta") if isinstance(payload, dict) else getattr(payload, "delta", None)
			self.text.add_delta(delta)
		elif event.type == "content.text.end":
			full_text = payload.get("full_text") if isinstance(payload, dict) else getattr(payload, "full_text", None)
			self.text.set_full(full_text)
		
		# Reasoning
		elif event.type == "content.reasoning.start":
			self.reasoning.format = payload.get("format") if isinstance(payload, dict) else getattr(payload, "format", None)
		elif event.type == "content.reasoning.delta":
			delta = payload.get("delta") if isinstance(payload, dict) else getattr(payload, "delta", None)
			self.reasoning.add_delta(delta)
		elif event.type == "content.reasoning.end":
			full_text = payload.get("full_text") if isinstance(payload, dict) else getattr(payload, "full_text", None)
			self.reasoning.set_full(full_text)

		# Action Call
		elif event.type.startswith("content.action."):
			act = self._ensure_action(event.action_id)
			act.on_action_event(event, ts)
		
		# Action Result
		elif event.type.startswith("content.action_result."):
			act = self._ensure_action(event.action_id)
			act.on_result_event(event, ts)

@dataclass
class NodeAggregationResult:
	"""聚合结果快照。"""
	trace_id: str
	run_id: str
	status: Optional[str]
	input_data: Any
	resume_context: Optional[Dict[str, Any]]
	usage: Optional[Dict[str, Any]]
	output: Any
	error: Any
	text_by_react: Dict[Optional[str], str]
	reasoning_by_react: Dict[Optional[str], str]
	actions: Dict[str, ActionAggregate]
	agent_result: AgentResultAggregate
	executor_id: Optional[str]
	executor_type: Optional[str]
	executor_path: Optional[List[str]]
	created_at: Optional[float]
	finished_at: Optional[float]
	updated_at: Optional[float]
	keepalive: List[float]
	is_closed: bool
	is_stored: bool
	react_closed: Dict[Optional[str], bool] = field(default_factory=dict)
	action_closed: Dict[str, bool] = field(default_factory=dict)
	react_stored: Dict[Optional[str], bool] = field(default_factory=dict)
	action_stored: Dict[str, bool] = field(default_factory=dict)

@dataclass
class TraceAggregationResult:
	"""Trace 级聚合快照（按多个 run 有序累积）。"""
	trace_id: str
	parent_trace_id: Optional[str]
	children: List[str]
	status: Optional[str]
	input_data: Any
	usage: Optional[Dict[str, Any]]
	usage_by_run: List[Optional[Dict[str, Any]]]
	text_by_react: Dict[Optional[str], str]
	reasoning_by_react: Dict[Optional[str], str]
	actions: Dict[str, ActionAggregate]
	agent_result: AgentResultAggregate
	output: Any
	error: Any
	executor_id: Optional[str]
	executor_type: Optional[str]
	executor_path: Optional[List[str]]
	created_at: Optional[float]
	finished_at: Optional[float]
	updated_at: Optional[float]
	keepalive: List[float]
	control: Dict[str, Any]
	is_closed: bool
	is_stored: bool
	react_closed: Dict[Optional[str], bool]
	action_closed: Dict[str, bool]
	react_stored: Dict[Optional[str], bool]
	action_stored: Dict[str, bool]
	auth_pending: List[Any]
	auth_granted: List[Any]

# -------------------- 聚合器主体 --------------------
class SingleRunEventAggregator:
	"""单节点单 run 事件聚合器。"""
	def __init__(self, trace_id: Optional[str] = None, run_id: Optional[str] = None):
		self.trace_id = trace_id
		self.run_id = run_id
		self.status: Optional[str] = None
		self.input_data: Any = None
		self.resume_context: Optional[Dict[str, Any]] = None
		self.usage: Optional[Dict[str, Any]] = None
		self.output: Any = None
		self.error: Any = None
		self.executor_id: Optional[str] = None
		self.executor_type: Optional[str] = None
		self.executor_path: Optional[List[str]] = None
		self.created_at: Optional[float] = None
		self.finished_at: Optional[float] = None
		self.updated_at: Optional[float] = None
		self.keepalive: List[float] = []
		self.react_flows: Dict[Optional[str], ReActFlow] = {}
		
		# action_id -> react_id 映射，用于 Action Delta/End 事件在无 react_id 时寻址
		self.action_react_map: Dict[str, Optional[str]] = {}
		
		self.agent_result = AgentResultAggregate()
		self.is_stored: bool = False

	# ---------- 内部工具 ----------
	def _ensure_trace_and_run(self, event: BaseEvent) -> None:
		if self.trace_id is None:
			self.trace_id = event.trace_id
		if self.run_id is None:
			self.run_id = event.run_id
		if event.trace_id != self.trace_id:
			raise ValueError(f"trace_id 不一致: {event.trace_id} != {self.trace_id}")
		if event.run_id != self.run_id:
			raise ValueError(f"run_id 不一致: {event.run_id} != {self.run_id}")

	def _touch(self, ts: float) -> None:
		if self.created_at is None:
			self.created_at = ts
		self.updated_at = ts

	def _ensure_flow(self, react_id: Optional[str]) -> ReActFlow:
		if react_id not in self.react_flows:
			logger.info(f"创建新的 ReActFlow 聚合器，react_id={react_id}, run_id={self.run_id} trace_id={self.trace_id}")
			self.react_flows[react_id] = ReActFlow(react_id=react_id)
		return self.react_flows[react_id]

	def _register_action(self, action_id: str, react_id: Optional[str]) -> None:
		if action_id not in self.action_react_map:
			self.action_react_map[action_id] = react_id
	
	def _get_react_id_by_action(self, action_id: str) -> Optional[str]:
		return self.action_react_map.get(action_id)

	# ---------- 事件入口 ----------
	def on_event(self, event: BaseEvent) -> None:
		ts = float(event.timestamp)
		self._ensure_trace_and_run(event)
		self._touch(ts)
		logger.debug(f"Run {self.run_id} 接收事件: {event}")

		if event.executor_id:
			self.executor_id = event.executor_id
		if getattr(event, "executor_type", None):
			self.executor_type = str(event.executor_type)
		if getattr(event, "executor_path", None):
			self.executor_path = list(event.executor_path)
		
		# 生命周期事件
		# 使用 type 判断以兼容反序列化类型丢失的情况，并兼容 payload 为 dict 的情况
		if event.type == "run.lifecycle.created":
			self.status = "created"
			payload = event.payload
			self.input_data = payload.get("input_data") if isinstance(payload, dict) else getattr(payload, "input_data", None)
			return
		if event.type == "run.lifecycle.resuming":
			self.status = "resuming"
			payload = event.payload
			self.resume_context = payload.get("resume_context") if isinstance(payload, dict) else getattr(payload, "resume_context", None)
			return
		if event.type == "run.lifecycle.running":
			self.status = "running"
			self.keepalive.append(ts)
			return
		if event.type == "run.lifecycle.suspended":
			self.status = "suspended"
			return
		if event.type == "run.lifecycle.completed":
			self.status = "completed"
			payload = event.payload
			usage = payload.get("usage") if isinstance(payload, dict) else getattr(payload, "usage", None)
			output = payload.get("output") if isinstance(payload, dict) else getattr(payload, "output", None)
			self.usage = usage or self.usage
			self.output = output or self.output
			self.finished_at = ts
			logger.debug(f"Run {self.run_id} 完成，状态更新为 {self.status}")
			return
		if event.type == "run.lifecycle.failed":
			self.status = "failed"
			payload = event.payload
			usage = payload.get("usage") if isinstance(payload, dict) else getattr(payload, "usage", None)
			output = payload.get("output") if isinstance(payload, dict) else getattr(payload, "output", None)
			error = payload.get("error") if isinstance(payload, dict) else getattr(payload, "error", None)
			self.usage = usage or self.usage
			self.output = output or self.output
			self.error = error or self.error
			self.finished_at = ts
			return
		if event.type == "run.lifecycle.cancelled":
			self.status = "cancelled"
			payload = event.payload
			usage = payload.get("usage") if isinstance(payload, dict) else getattr(payload, "usage", None)
			self.usage = usage or self.usage
			self.finished_at = ts
			return

		# 文本/推理流
		if event.type.startswith("content.text") or event.type.startswith("content.reasoning"):
			flow = self._ensure_flow(event.react_id)
			flow.on_event(event, ts)
			return

		# Action 调用与结果：下沉给 ReActFlow
		if event.type.startswith("content.action") or event.type.startswith("content.action_result"):
			action_id = event.action_id
			# 尝试获取 react_id
			# 1. Start 事件携带 react_id，优先使用并注册
			if event.type == "content.action.start":
				react_id = event.react_id
				self._register_action(action_id, react_id)
			else:
				# 2. Delta/End 可能不带 react_id，查表
				react_id = event.react_id # 协议中 Delta/End 也有 react_id 字段，若有则优先
				if react_id is None:
					react_id = self._get_react_id_by_action(action_id)
				else:
					# 确保记录
					self._register_action(action_id, react_id)

			flow = self._ensure_flow(react_id)
			flow.on_event(event, ts)
			return

		# Agent 交付结果
		if event.type == "content.agent_result.start":
			# 兼容 payload 为 dict
			payload = event.payload
			mode = payload.get("mode") if isinstance(payload, dict) else getattr(payload, "mode", None)
			json_schema = payload.get("json_schema") if isinstance(payload, dict) else getattr(payload, "json_schema", None)
			self.agent_result.set_start(mode, json_schema, ts)
			return
		if event.type == "content.agent_result.delta":
			payload = event.payload
			part = (payload.get("part") if isinstance(payload, dict) else getattr(payload, "part", None)) or "output"
			delta = (payload.get("delta") if isinstance(payload, dict) else getattr(payload, "delta", None)) or ""
			self.agent_result.add_delta(part, delta, ts)
			return
		if event.type == "content.agent_result.end":
			payload = event.payload
			full_result = payload.get("full_result") if isinstance(payload, dict) else getattr(payload, "full_result", None)
			status = payload.get("status") if isinstance(payload, dict) else getattr(payload, "status", None)
			mode = payload.get("mode") if isinstance(payload, dict) else getattr(payload, "mode", None)
			json_schema = payload.get("json_schema") if isinstance(payload, dict) else getattr(payload, "json_schema", None)
			images = payload.get("images") if isinstance(payload, dict) else getattr(payload, "images", None)
			files = payload.get("files") if isinstance(payload, dict) else getattr(payload, "files", None)
			
			self.agent_result.set_end(
				full_result=full_result,
				status=status,
				mode=mode,
				json_schema=json_schema,
				images=images,
				files=files,
				ts=ts,
			)
			return

	# ---------- 导出快照 ----------
	def snapshot(self) -> NodeAggregationResult:
		text_by_react: Dict[Optional[str], str] = {}
		reasoning_by_react: Dict[Optional[str], str] = {}
		actions: Dict[str, ActionAggregate] = {}
		for rid, flow in self.react_flows.items():
			merged_text = flow.text.merged()
			merged_reasoning = flow.reasoning.merged()
			if merged_text:
				text_by_react[rid] = merged_text
			if merged_reasoning:
				reasoning_by_react[rid] = merged_reasoning
			# action 归属到对应 react 流，一并汇总
			for act_id, act in flow.actions.items():
				actions[act_id] = act

		logger.debug(f"Run Trace {self.trace_id} 聚合结果：{_dump_json({ 'status': self.status, 'is_closed': self.is_closed(), 'actions_count': len(actions) })}")

		return NodeAggregationResult(
			trace_id=self.trace_id or "",
			run_id=self.run_id or "",
			status=self.status,
			input_data=self.input_data,
			resume_context=self.resume_context,
			usage=self.usage,
			output=self.output,
			error=self.error,
			text_by_react=text_by_react,
			reasoning_by_react=reasoning_by_react,
			actions=actions,
			agent_result=self.agent_result,
			executor_id=self.executor_id,
			executor_type=self.executor_type,
			executor_path=self.executor_path,
			created_at=self.created_at,
			finished_at=self.finished_at,
			updated_at=self.updated_at,
			keepalive=list(self.keepalive),
			is_closed=self.is_closed(),
			is_stored=self.is_stored,
			react_closed={rid: self.is_closed() for rid in self.react_flows.keys()},
			action_closed={aid: self.is_closed() for aid in actions.keys()},
			react_stored={rid: False for rid in self.react_flows.keys()},
			action_stored={aid: False for aid in actions.keys()},
		)

	def is_closed(self) -> bool:
		return self.status in {"completed", "failed", "cancelled"}


class TraceEventAggregator:
	"""Trace 级事件聚合器：维护有序 run 列表并做跨 run 合并，同时承载树结构元信息。

	状态维护说明：
	- is_closed: 运行是否终结。通常由 run 的状态（completed/failed/cancelled）决定，但在某些场景下可能由事件流直接控制。
	- is_stored: 是否已持久化写库。由外部调用方通过 set_stored 控制，聚合器本身不负责落库逻辑。
	- stored_at: 最近一次写库时间。
	- history: 事件历史记录，用于支持回滚操作。
	"""

	def __init__(self, trace_id: Optional[str] = None, parent_trace_id: Optional[str] = None, parent_action_id: Optional[str] = None):
		self.trace_id = trace_id
		self.parent_trace_id = parent_trace_id
		self.parent_action_id = parent_action_id
		self.children: List[str] = []
		self.runs: Dict[str, SingleRunEventAggregator] = {}
		self.run_order: List[str] = []
		self.control: Dict[str, Any] = {
			"latest_interrupt": None,
			"suggestions": [],
			"rollback": None,
			"auth_pending": [],
			"auth_granted": [],
		}
		self.is_stored: bool = False
		self.stored_at: Optional[float] = None
		# 事件历史：用于回滚重放
		self.history: List[tuple[float, BaseEvent]] = []

	def set_stored(self, stored: bool, ts: float) -> None:
		self.is_stored = stored
		self.stored_at = ts

	def _ensure_trace(self, event: BaseEvent) -> None:
		if self.trace_id is None:
			self.trace_id = event.trace_id
		elif event.trace_id != self.trace_id:
			raise ValueError(f"trace_id 不一致: {event.trace_id} != {self.trace_id}")

	def _ensure_run(self, run_id: str) -> SingleRunEventAggregator:
		if run_id not in self.runs:
			self.runs[run_id] = SingleRunEventAggregator(trace_id=self.trace_id, run_id=run_id)
			self.run_order.append(run_id)
		return self.runs[run_id]

	def _replay_from_history(self) -> None:
		"""从历史记录重放事件以重建状态。
		
		用于回滚后重建派生状态。假设 history 已经被截断到目标时间戳。
		"""
		# 清空派生状态
		self.runs.clear()
		self.run_order.clear()
		self.control = {
			"latest_interrupt": None,
			"suggestions": [],
			"rollback": None,
			"auth_pending": [],
			"auth_granted": [],
		}
		
		# 按时间戳排序重放（理论上 history 已经有序，但确保万无一失）
		sorted_history = sorted(self.history, key=lambda x: x[0])
		
		for ts, event in sorted_history:
			# 跳过 rollback 事件本身（避免递归）
			if event.type == "control.rollback":
				continue
			
			payload = event.payload
			
			# 重放控制事件
			if event.type == "control.interrupt":
				# 兼容 dict 和 object
				data = payload.model_dump() if hasattr(payload, "model_dump") else (payload if isinstance(payload, dict) else payload.__dict__)
				self.control["latest_interrupt"] = data
				continue
			if event.type == "control.suggestions":
				suggestions = payload.get("suggestions") if isinstance(payload, dict) else getattr(payload, "suggestions", [])
				self.control["suggestions"] = list(suggestions)
				continue
			
			# 重放其他事件到对应 run
			run = self._ensure_run(event.run_id)
			run.on_event(event)

	def on_event(self, event: BaseEvent) -> None:
		self._ensure_trace(event)
		ts = float(event.timestamp)
		payload = event.payload
		
		# 处理回滚事件：截断历史并重放
		if event.type == "control.rollback":
			target_timestamp = payload.get("target_timestamp") if isinstance(payload, dict) else getattr(payload, "target_timestamp", None)
			
			# 记录回滚信息到 control（用于审计）
			data = payload.model_dump() if hasattr(payload, "model_dump") else (payload if isinstance(payload, dict) else payload.__dict__)
			self.control["rollback"] = data
			
			# 截断历史：丢弃所有 timestamp > target_timestamp 的事件
			self.history = [(t, e) for t, e in self.history if t <= target_timestamp]
			
			# 重放历史重建状态
			self._replay_from_history()
			return
		
		# 记录事件到历史（rollback 事件不记录，避免重放时递归）
		if event.type != "control.rollback":
			self.history.append((ts, event))
		
		# 控制事件在 trace 层统一处理
		if event.type == "control.interrupt":
			data = payload.model_dump() if hasattr(payload, "model_dump") else (payload if isinstance(payload, dict) else payload.__dict__)
			self.control["latest_interrupt"] = data
			return
		if event.type == "control.suggestions":
			suggestions = payload.get("suggestions") if isinstance(payload, dict) else getattr(payload, "suggestions", [])
			self.control["suggestions"] = list(suggestions)
			return

		run = self._ensure_run(event.run_id)
		run.on_event(event)

	def to_state(self) -> Union[Message, ToolCallRecord]:
		ordered_runs = [self.runs[rid] for rid in self.run_order if rid in self.runs]

		# Timestamp calculations
		first_ts = ordered_runs[0].created_at if ordered_runs else None
		last_ts = ordered_runs[-1].finished_at if ordered_runs else None
		last_updated = ordered_runs[-1].updated_at if ordered_runs else None

		# Check for millisecond timestamps (simple heuristic: > 1e11 is ms for current era)
		if first_ts and first_ts > 1e11:
			first_ts = first_ts / 1000.0
		if last_ts and last_ts > 1e11:
			last_ts = last_ts / 1000.0
		if last_updated and last_updated > 1e11:
			last_updated = last_updated / 1000.0

		dt_created = datetime.utcfromtimestamp(first_ts) if first_ts else datetime.utcnow()
		dt_updated = datetime.utcfromtimestamp(last_updated or first_ts) if (last_updated or first_ts) else datetime.utcnow()

		# Determine executor type
		ex_type = None
		for r in ordered_runs:
			if r.executor_type:
				ex_type = r.executor_type
				break

		is_tool = (ex_type == "Tool" or ex_type == "API")

		if is_tool:
			status = "pending"
			if ordered_runs:
				last_status = ordered_runs[-1].status
				if last_status == "completed":
					status = "succeeded"
				elif last_status == "failed":
					status = "failed"
				elif last_status == "running":
					status = "running"

			input_data = ordered_runs[0].input_data if ordered_runs else None
			output_data = ordered_runs[-1].output if ordered_runs else None
			error_data = ordered_runs[-1].error if ordered_runs else None

			return ToolCallRecord(
				id=self.trace_id or "",
				tool_type="API",
				input=input_data,
				result=output_data,
				error_message=error_data,
				status=status,
				created_at=dt_created,
				updated_at=dt_updated,
			)
		else:
			full_content = ""
			full_reasoning = ""
			merged_reacts: Dict[str, ReActFlow] = {}
			merged_actions: Dict[str, Action] = {}

			for run in ordered_runs:
				for rid, flow in run.react_flows.items():
					if rid is None:
						if flow.text.merged():
							full_content += flow.text.merged()
						if flow.reasoning.merged():
							full_reasoning += flow.reasoning.merged()
						for aid, act in flow.actions.items():
							merged_actions[aid] = act.to_state()
					else:
						if rid not in merged_reacts:
							merged_reacts[rid] = ReActFlow(react_id=rid)

						target = merged_reacts[rid]
						target.text.set_full((target.text.merged() or "") + flow.text.merged())
						target.reasoning.set_full((target.reasoning.merged() or "") + flow.reasoning.merged())
						target.actions.update(flow.actions)

			react_rounds = [
				flow.to_state(belong_to_message_id=self.trace_id or "") for flow in merged_reacts.values()
			]
			top_actions = list(merged_actions.values())

			msg_status = MessageStatus.started
			if ordered_runs:
				last_status = ordered_runs[-1].status
				if last_status == "completed":
					msg_status = MessageStatus.finished
				elif last_status == "failed":
					msg_status = MessageStatus.error
				elif last_status == "cancelled":
					msg_status = MessageStatus.cancelled
				elif last_status == "running":
					msg_status = MessageStatus.running

			return Message(
				id=self.trace_id or "",
				role=MessageRole.assistant,
				content=full_content,
				reasoning_content=full_reasoning,
				reactRounds=react_rounds,
				actions=top_actions,
				status=msg_status,
				created_at=dt_created,
				updated_at=dt_updated,
				children=self.children,
				ancestors=[self.parent_trace_id] if self.parent_trace_id else []
			)

	def snapshot(self) -> TraceAggregationResult:
		# 有序累计 run
		input_data = None
		usage: Optional[Dict[str, Any]] = None
		usage_by_run: List[Optional[Dict[str, Any]]] = []
		text_by_react: Dict[Optional[str], str] = {}
		reasoning_by_react: Dict[Optional[str], str] = {}
		actions: Dict[str, ActionAggregate] = {}
		agent_result = AgentResultAggregate()
		output = None
		error = None
		executor_id = None
		executor_type = None
		executor_path = None
		created_at = None
		finished_at = None
		updated_at = None
		keepalive: List[float] = []
		status: Optional[str] = None
		react_closed: Dict[Optional[str], bool] = {}
		action_closed: Dict[str, bool] = {}
		react_stored: Dict[Optional[str], bool] = {}
		action_stored: Dict[str, bool] = {}

		ordered_runs = [self.runs[rid] for rid in self.run_order if rid in self.runs]
		logger.debug(f"Trace {self.trace_id} 聚合 {len(ordered_runs)} 个 run")
		if not ordered_runs:
			return TraceAggregationResult(
				trace_id=self.trace_id or "",
				parent_trace_id=self.parent_trace_id,
				children=list(self.children),
				status=None,
				input_data=None,
				usage=None,
				usage_by_run=[],
				text_by_react={},
				reasoning_by_react={},
				actions={},
				agent_result=AgentResultAggregate(),
				output=None,
				error=None,
				executor_id=None,
				executor_type=None,
				executor_path=None,
				created_at=None,
				finished_at=None,
				updated_at=None,
				keepalive=[],
				control=self.control,
				is_closed=False,
				is_stored=self.is_stored,
				react_closed={},
				action_closed={},
				react_stored={},
				action_stored={},
				auth_pending=list(self.control.get("auth_pending", [])),
				auth_granted=list(self.control.get("auth_granted", [])),
			)

		for idx, run in enumerate(ordered_runs):
			snap = run.snapshot()
			if idx == 0:
				input_data = snap.input_data
				created_at = snap.created_at
			# 文本/推理按 run 顺序追加
			for rid, txt in snap.text_by_react.items():
				text_by_react[rid] = text_by_react.get(rid, "") + txt
			for rid, rtxt in snap.reasoning_by_react.items():
				reasoning_by_react[rid] = reasoning_by_react.get(rid, "") + rtxt
			for act_id, act in snap.actions.items():
				actions[act_id] = act
			# react/action 完结标记：沿用 run 的 is_closed 语义
			for rid in snap.text_by_react.keys():
				react_closed[rid] = snap.is_closed
				react_stored.setdefault(rid, False)
			for aid_for_react, act_obj in snap.actions.items():
				react_id = act_obj.react_id
				if react_id is not None:
					react_closed[react_id] = snap.is_closed
					react_stored.setdefault(react_id, False)
			for aid in snap.actions.keys():
				action_closed[aid] = snap.is_closed
				action_stored.setdefault(aid, False)

			usage = snap.usage or usage
			usage_by_run.append(snap.usage)
			keepalive.extend(snap.keepalive)
			updated_at = snap.updated_at or updated_at
			status = snap.status or status
			executor_id = snap.executor_id or executor_id
			executor_type = snap.executor_type or executor_type
			executor_path = snap.executor_path or executor_path
			# 以最后一次 run 的结果为准
			if idx == len(ordered_runs) - 1:
				agent_result = snap.agent_result
				output = snap.output
				error = snap.error
				finished_at = snap.finished_at

		is_closed = status in {"completed", "failed", "cancelled"}
		
		return TraceAggregationResult(
			trace_id=self.trace_id or "",
			parent_trace_id=self.parent_trace_id,
			children=list(self.children),
			status=status,
			input_data=input_data,
			usage=usage,
			usage_by_run=usage_by_run,
			text_by_react=text_by_react,
			reasoning_by_react=reasoning_by_react,
			actions=actions,
			agent_result=agent_result,
			output=output,
			error=error,
			executor_id=executor_id,
			executor_type=executor_type,
			executor_path=executor_path,
			created_at=created_at,
			finished_at=finished_at,
			updated_at=updated_at,
			keepalive=keepalive,
			control=self.control,
			is_closed=is_closed,
			is_stored=self.is_stored,
			react_closed=react_closed,
			action_closed=action_closed,
			react_stored=react_stored,
			action_stored=action_stored,
			auth_pending=list(self.control.get("auth_pending", [])),
			auth_granted=list(self.control.get("auth_granted", [])),
		)


class EventTreeAggregator:
	"""事件树聚合器：根据流式协议的 trace_path 构建 Trace 节点树并路由事件。

	设计要点：
	1) trace_id 取根视角，trace_path 的末尾元素代表当前事件所属的子 trace 节点；若 trace_path 为空，则事件属于根 trace。
	2) 每个 trace 节点使用 TraceEventAggregator 管理其下的有序 run，并独立聚合。
	3) 控制/中断事件按所属 trace 节点处理；树层负责结构维护与事件转发，不做内容聚合。
	4) 转发时若事件的 trace_id 与目标节点 id 不一致，会使用 pydantic 的 model_copy 覆写 trace_id，确保节点内部校验通过。
	"""

	def __init__(self, root_trace_id: Optional[str] = None):
		self.root_trace_id = root_trace_id
		self.nodes: Dict[str, TraceEventAggregator] = {}
		if root_trace_id:
			self.nodes[root_trace_id] = TraceEventAggregator(trace_id=root_trace_id)

	def _ensure_node(self, trace_id: str, parent_trace_id: Optional[str] = None) -> TraceEventAggregator:
		if trace_id not in self.nodes:
			self.nodes[trace_id] = TraceEventAggregator(trace_id=trace_id, parent_trace_id=parent_trace_id)
		else:
			# 若已存在但未记录父节点信息，补充链路信息
			if parent_trace_id and self.nodes[trace_id].parent_trace_id is None:
				self.nodes[trace_id].parent_trace_id = parent_trace_id
		return self.nodes[trace_id]

	def _link_path(self, trace_path: List[str], action_id: Optional[str]) -> TraceEventAggregator:
		"""根据 trace_path 创建/维护父子关系并返回末尾节点聚合器。"""
		if self.root_trace_id is None:
			# 初次事件到达时用 path 首元素或后续 fallback 在 on_event 中处理
			pass

		current_id = self.root_trace_id
		# 若无 root，且 path 存在，用第一个作为 root
		if current_id is None:
			current_id = trace_path[0] if trace_path else None
			if current_id is None:
				raise ValueError("无法建立 trace 树：缺少 root trace_id 与 trace_path")
			self.root_trace_id = current_id
			self.nodes[current_id] = TraceEventAggregator(trace_id=current_id)

		current = self._ensure_node(current_id)
		for tid in trace_path:
			child = self._ensure_node(tid, parent_trace_id=current.trace_id)
			if tid not in current.children:
				current.children.append(tid)
			current = child

		if action_id and current.parent_action_id is None:
			current.parent_action_id = action_id

		return current

	def on_event(self, event: BaseEvent) -> None:
		"""将事件路由至对应 trace 节点。

		- 目标 trace 节点 id = trace_path 的最后一个元素；若 trace_path 为空，则为 root。
		- 当事件 trace_id 与目标节点 id 不一致时，使用 model_copy 覆写 trace_id，以通过节点内校验。
		"""
		path = event.trace_path or []
		target_trace_id = path[-1] if path else event.trace_id

		if self.root_trace_id is None and not path:
			self.root_trace_id = target_trace_id
			self._ensure_node(self.root_trace_id)

		# 建链并获取目标节点
		target_agg = self._link_path(path, event.action_id)

		# 若节点 id 未初始化（可能 root 未设且 path 为空），确保存在
		if target_agg is None:
			target_agg = self._ensure_node(target_trace_id)

		# patch trace_id 以满足节点内部校验
		patched_event = event
		if getattr(event, "trace_id", None) != target_trace_id:
			patched_event = event.model_copy(update={"trace_id": target_trace_id})

		target_agg.on_event(patched_event)

	def snapshot_all(self) -> Dict[str, TraceAggregationResult]:
		"""输出所有 trace 节点的聚合快照。"""
		return {tid: agg.snapshot() for tid, agg in self.nodes.items()}

	def snapshot_root(self) -> Optional[TraceAggregationResult]:
		"""输出根节点快照，若未初始化则返回 None。"""
		if self.root_trace_id is None or self.root_trace_id not in self.nodes:
			return None
		return self.nodes[self.root_trace_id].snapshot()


