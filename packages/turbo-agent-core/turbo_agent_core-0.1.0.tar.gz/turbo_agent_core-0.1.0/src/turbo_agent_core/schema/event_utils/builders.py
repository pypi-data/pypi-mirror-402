"""事件构建与转换辅助函数（v2.0）。

说明：
- 本文件仅负责“构建 v2.0 BaseEvent 体系事件”的便捷函数。
- 事件协议权威定义在 `schema/events.py`。
- 为兼容 UI（如 CopilotKit）消费结构，保留消息转换工具。

注意：旧版事件（如 TextMessageDeltaEvent/RunCompletedEvent 等）已不再属于 v2.0 协议。
若历史代码仍依赖旧事件，应在上层做适配层，而不是在 core 事件协议层混用。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from turbo_agent_core.schema.states import Message, Action
from turbo_agent_core.schema.enums import RunType
from turbo_agent_core.schema.events import (
    BaseEvent,
    StateSyncEvent,
    StateSyncPayload,
    ContentTextDeltaEvent,
    ContentTextDeltaPayload,
    ContentActionResultDeltaEvent,
    ContentActionResultDeltaPayload,
    ContentActionResultEndEvent,
    ContentActionResultEndPayload,
    ContentAgentResultStartEvent,
    ContentAgentResultStartPayload,
    ContentAgentResultDeltaEvent,
    ContentAgentResultDeltaPayload,
    ContentAgentResultEndEvent,
    ContentAgentResultEndPayload,
    ExecutorMetadata,
    UserInfo,
    ResumeContext,
    RunLifecycleCreatedEvent,
    RunLifecycleCreatedPayload,
    RunLifecycleRunningEvent,
    RunLifecycleRunningPayload,
    RunLifecycleSuspendedEvent,
    RunLifecycleSuspendedPayload,
    RunLifecycleResumingEvent,
    RunLifecycleResumingPayload,
    RunLifecycleCompletedEvent,
    RunLifecycleCompletedPayload,
    RunLifecycleFailedEvent,
    RunLifecycleFailedPayload,
    RunLifecycleCancelledEvent,
    RunLifecycleCancelledPayload,
    ControlInterruptEvent,
    ControlInterruptPayload,
)

# ----------------  基础转换  ----------------

def _convert_action_to_copilotkit_messages(action: Action, parent_message_id: str) -> List[Dict[str, Any]]:
    """将内部 Action 转换为一个或多个 ActionExecutionMessage/ResultMessage 结构。"""
    msgs: List[Dict[str, Any]] = []
    msgs.append({
        "type": "ActionExecutionMessage",
        "event": "ActionExecutionMessage",
        "id": action.id,
        "name": action.name or "unknown_action",
        "arguments": {"input": action.input} if action.input else {},
        "parentMessageId": parent_message_id,
    })
    if action.final_answer is not None:
        msgs.append({
            "type": "ResultMessage",
            "event": "ResultMessage",
            "id": f"{action.id}-result",
            "actionExecutionId": action.id,
            "actionName": action.name or "unknown_action",
            "result": action.final_answer,
            "parentMessageId": parent_message_id,
        })
    return msgs


def to_copilotkit_messages(messages: List[Message]) -> List[Dict[str, Any]]:
    """将内部 Message 列表转换为 CopilotKit 前端消费的消息数组。"""
    output: List[Dict[str, Any]] = []
    for m in messages:
        base = {
            "type": m.type,
            "event": m.type,
            "id": m.id,
            "role": m.role.value,
            "content": m.content,
            "reasoningContent": m.reasoning_content,
            "parentMessageId": m.id,
        }
        if m.token_cost is not None:
            base["tokenCost"] = m.token_cost
        if m.money_cost is not None:
            base["moneyCost"] = m.money_cost
        if m.model_used is not None:
            base["modelUsed"] = m.model_used
        output.append(base)
        for act in m.actions:
            output.extend(_convert_action_to_copilotkit_messages(act, parent_message_id=m.id))
    return output

# ----------------  构建函数  ----------------

def build_state_sync_event(
    *,
    trace_id: str,
    run_id: str,
    executor_id: Optional[str],
    executor_type: Optional[RunType],
    executor_path: Optional[List[str]],
    messages: List[Any],
    agent_state: Dict[str, Any],
) -> StateSyncEvent:
    """构建 v2.0 的 state.sync 事件。

    注意：messages 的形态由上层决定。
    - 若面向 CopilotKit，可直接传入 `to_copilotkit_messages()` 的输出。
    - 若面向内部系统，可传入 Message 的 dict 或其它结构。
    """
    return StateSyncEvent(
        trace_id=trace_id,
        run_id=run_id,
        executor_id=executor_id,
        executor_type=executor_type,
        executor_path=executor_path,
        payload=StateSyncPayload(messages=messages, agent_state=agent_state),
    )


def build_content_text_delta_event(
    *,
    trace_id: str,
    run_id: str,
    executor_id: Optional[str],
    executor_type: Optional[RunType],
    executor_path: Optional[List[str]],
    delta: str,
    key_path: Optional[List[Any]] = None,
) -> ContentTextDeltaEvent:
    """构建 v2.0 的 content.text.delta 事件。"""
    return ContentTextDeltaEvent(
        trace_id=trace_id,
        run_id=run_id,
        executor_id=executor_id,
        executor_type=executor_type,
        executor_path=executor_path,
        payload=ContentTextDeltaPayload(delta=delta, key_path=key_path),
    )


def build_action_result_delta_event(
    *,
    trace_id: str,
    run_id: str,
    executor_id: Optional[str],
    executor_type: Optional[RunType],
    executor_path: Optional[List[str]],
    action_id: str,
    part: str,
    delta: str,
    key_path: Optional[List[Any]] = None,
) -> ContentActionResultDeltaEvent:
    """构建 v2.0 的 content.action.result.delta 事件。

    说明：part 用于标识该 delta 的输出位置（如 output/title/summary/error）。
    """
    return ContentActionResultDeltaEvent(
        trace_id=trace_id,
        run_id=run_id,
        executor_id=executor_id,
        executor_type=executor_type,
        executor_path=executor_path,
        payload=ContentActionResultDeltaPayload(action_id=action_id, part=part, delta=delta, key_path=key_path),
    )


def build_action_result_end_event(
    *,
    trace_id: str,
    run_id: str,
    executor_id: Optional[str],
    executor_type: Optional[RunType],
    executor_path: Optional[List[str]],
    action_id: str,
    full_result: Any,
    images: Optional[List[str]] = None,
    files: Optional[List[str]] = None,
) -> ContentActionResultEndEvent:
    """构建 v2.0 的 content.action.result.end 事件。"""
    return ContentActionResultEndEvent(
        trace_id=trace_id,
        run_id=run_id,
        executor_id=executor_id,
        executor_type=executor_type,
        executor_path=executor_path,
        payload=ContentActionResultEndPayload(action_id=action_id, full_result=full_result, images=images, files=files),
    )


def build_agent_result_start_event(
    *,
    trace_id: str,
    run_id: str,
    executor_id: Optional[str],
    executor_type: Optional[RunType],
    executor_path: Optional[List[str]],
    mode: str = "json",
    json_schema: Optional[Dict[str, Any]] = None,
) -> ContentAgentResultStartEvent:
    """构建 v2.0 的 content.agent.result.start 事件。"""
    return ContentAgentResultStartEvent(
        trace_id=trace_id,
        run_id=run_id,
        executor_id=executor_id,
        executor_type=executor_type,
        executor_path=executor_path,
        payload=ContentAgentResultStartPayload(mode=mode, json_schema=json_schema),
    )


def build_agent_result_delta_event(
    *,
    trace_id: str,
    run_id: str,
    executor_id: Optional[str],
    executor_type: Optional[RunType],
    executor_path: Optional[List[str]],
    delta: str,
    part: Optional[str] = None,
    key_path: Optional[List[Any]] = None,
) -> ContentAgentResultDeltaEvent:
    """构建 v2.0 的 content.agent.result.delta 事件。

    说明：part 用于标识该 delta 的输出位置（如 output/text/think/args/error）。
    """
    return ContentAgentResultDeltaEvent(
        trace_id=trace_id,
        run_id=run_id,
        executor_id=executor_id,
        executor_type=executor_type,
        executor_path=executor_path,
        payload=ContentAgentResultDeltaPayload(delta=delta, part=part, key_path=key_path),
    )


def build_agent_result_end_event(
    *,
    trace_id: str,
    run_id: str,
    executor_id: Optional[str],
    executor_type: Optional[RunType],
    executor_path: Optional[List[str]],
    full_result: Any,
) -> ContentAgentResultEndEvent:
    """构建 v2.0 的 content.agent.result.end 事件。"""
    return ContentAgentResultEndEvent(
        trace_id=trace_id,
        run_id=run_id,
        executor_id=executor_id,
        executor_type=executor_type,
        executor_path=executor_path,
        payload=ContentAgentResultEndPayload(full_result=full_result),
    )


def build_run_lifecycle_event(
    *,
    trace_id: str,
    run_id: str,
    executor_id: Optional[str],
    executor_type: Optional[RunType],
    executor_path: Optional[List[str]],
    status: str,
    input_data: Optional[Any] = None,
    resume_context: Optional[Any] = None,
    usage: Optional[Dict[str, Any]] = None,
    error: Optional[Dict[str, str]] = None,
    output: Optional[Any] = None,
    executor_metadata: Optional[ExecutorMetadata] = None,
    user_metadata: Optional[UserInfo] = None,
) -> BaseEvent:
    """构建 v2.0 的 run.lifecycle.* 事件（按 status 映射到不同事件类型）。"""

    if status == "created":
        if executor_metadata is None:
            raise ValueError("status=created 时必须提供 executor_metadata")
        if user_metadata is None:
            raise ValueError("status=created 时必须提供 user_metadata")
        if input_data is None:
            raise ValueError("status=created 时必须提供 input_data")
        return RunLifecycleCreatedEvent(
            trace_id=trace_id,
            run_id=run_id,
            executor_id=executor_id,
            executor_type=executor_type,
            executor_path=executor_path,
            executor_metadata=executor_metadata,
            user_metadata=user_metadata,
            payload=RunLifecycleCreatedPayload(input_data=input_data),
        )

    if status == "running":
        return RunLifecycleRunningEvent(
            trace_id=trace_id,
            run_id=run_id,
            executor_id=executor_id,
            executor_type=executor_type,
            executor_path=executor_path,
            payload=RunLifecycleRunningPayload(),
        )

    if status == "suspended":
        # v2: suspended payload 只有 reason/awaiting。此处不强制 resume_context。
        reason = None
        awaiting = None
        if isinstance(resume_context, dict):
            reason = resume_context.get("reason")
            awaiting = resume_context.get("awaiting")
        return RunLifecycleSuspendedEvent(
            trace_id=trace_id,
            run_id=run_id,
            executor_id=executor_id,
            executor_type=executor_type,
            executor_path=executor_path,
            payload=RunLifecycleSuspendedPayload(reason=str(reason or "suspended"), awaiting=awaiting),
        )

    if status == "resuming":
        if resume_context is None:
            raise ValueError("status=resuming 时必须提供 resume_context")
        ctx = resume_context
        if isinstance(resume_context, dict):
            ctx = ResumeContext.model_validate(resume_context)
        return RunLifecycleResumingEvent(
            trace_id=trace_id,
            run_id=run_id,
            executor_id=executor_id,
            executor_type=executor_type,
            executor_path=executor_path,
            payload=RunLifecycleResumingPayload(resume_context=ctx),
        )

    if status == "completed":
        return RunLifecycleCompletedEvent(
            trace_id=trace_id,
            run_id=run_id,
            executor_id=executor_id,
            executor_type=executor_type,
            executor_path=executor_path,
            payload=RunLifecycleCompletedPayload(output=output, usage=usage),
        )

    if status == "failed":
        if error is None:
            raise ValueError("status=failed 时必须提供 error")
        return RunLifecycleFailedEvent(
            trace_id=trace_id,
            run_id=run_id,
            executor_id=executor_id,
            executor_type=executor_type,
            executor_path=executor_path,
            payload=RunLifecycleFailedPayload(error=error, usage=usage, output=output),
        )

    if status == "cancelled":
        return RunLifecycleCancelledEvent(
            trace_id=trace_id,
            run_id=run_id,
            executor_id=executor_id,
            executor_type=executor_type,
            executor_path=executor_path,
            payload=RunLifecycleCancelledPayload(output=output, usage=usage),
        )

    raise ValueError(f"未知的 run lifecycle status: {status}")


def build_control_interrupt_event(
    *,
    trace_id: str,
    run_id: str,
    executor_id: Optional[str],
    executor_type: Optional[RunType],
    executor_path: Optional[List[str]],
    interrupt_id: str,
    interrupt_type: str,
    reason: str,
    resume_token: str,
    data: Optional[Any] = None,
    action_id: Optional[str] = None,
    action_name: Optional[str] = None,
    action_parameters: Optional[Dict[str, Any]] = None,
    required: Optional[str] = None,
    expected_fields: Optional[List[str]] = None,
    timeout_seconds: Optional[int] = None,
) -> ControlInterruptEvent:
    """构建 v2.0 的 control.interrupt 事件。"""
    return ControlInterruptEvent(
        trace_id=trace_id,
        run_id=run_id,
        executor_id=executor_id,
        executor_type=executor_type,
        executor_path=executor_path,
        payload=ControlInterruptPayload(
            interrupt_id=interrupt_id,
            type=interrupt_type,
            reason=reason,
            action_id=action_id,
            action_name=action_name,
            action_parameters=action_parameters,
            required=required,
            expected_fields=expected_fields,
            timeout_seconds=timeout_seconds,
            data=data,
            resume_token=resume_token,
        ),
    )

# ----------------  序列化  ----------------

def serialize_event(event: BaseEvent) -> Dict[str, Any]:
    """将事件序列化为可 JSON 化的 dict。"""
    return event.model_dump(mode="json")

__all__ = [
    "to_copilotkit_messages",
    "build_state_sync_event",
    "build_content_text_delta_event",
    "build_action_result_delta_event",
    "build_action_result_end_event",
    "build_agent_result_start_event",
    "build_agent_result_delta_event",
    "build_agent_result_end_event",
    "build_run_lifecycle_event",
    "build_control_interrupt_event",
    "serialize_event",
]
