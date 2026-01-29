from __future__ import annotations

from typing import Iterator, AsyncIterator, Optional, List, Iterable, Any

from turbo_agent_core.schema.events import (
    BaseEvent,
    ContentActionResultStartEvent,
    ContentActionResultStartPayload,
    ContentActionResultDeltaEvent,
    ContentActionResultDeltaPayload,
    ContentActionResultEndEvent,
    ContentActionResultEndPayload,
)



class ChildEventStreamIntegrator:
    """
    子事件流集成器。负责：
    1. 自动修补 Child 事件的上下文（trace_id, executor_path）
    2. 捕获 Child 的最终结果（agent.result.end）
    3. 生成 Parent 的 Action Result 事件
    """
    
    def __init__(
        self,
        root_trace_id: str,
        parent_trace_path: Optional[List[str]] = None,
        parent_executor_path: Optional[List[str]] = None,
        action_id: Optional[str] = None,
        react_id: Optional[str] = None,
        ignore_child_trace_id: bool = False,
        parent_run_id: Optional[str] = None,
        forward_as_parent_events: bool = False,
    ):
        # Parent 的根 trace_id（对外视角）
        self.root_trace_id = root_trace_id
        # Parent 的 trace_path（当 Parent 自身也是被转发的子流时需要）
        self.parent_trace_path = list(parent_trace_path or [])
        # Parent 的 executor_path（用于把 Child 的 executor_path 拼接到父链路后面）
        self.parent_executor_path = list(parent_executor_path or [])
        # 当前这段 Child 子流所归属的 action_id/react_id（仅对 Child 根子流注入，避免覆盖内部 action）
        self.action_id = action_id
        self.react_id = react_id
        
        self.ignore_child_trace_id = ignore_child_trace_id
        self.parent_run_id = parent_run_id
        self.forward_as_parent_events = forward_as_parent_events

        self.child_final_result: Any = None
        self.child_error: Any = None

    def _patch_event(self, event: BaseEvent) -> tuple[Optional[BaseEvent], str, List[str]]:
        """修补单个事件的上下文。

        返回：
        - patched_event
        - child_trace_id（修补前的 trace_id）
        - child_trace_path（修补前的 trace_path）
        """

        child_trace_id = event.trace_id
        child_trace_path = list(event.trace_path or [])

        # 5) 捕获最终结果 (先捕获，因为后面可能会 suppress event)
        if event.type == "content.agent.result.end":
            self.child_final_result = event.payload.full_result
        elif event.type == "run.lifecycle.completed":
            if getattr(event.payload, "output", None) is not None:
                self.child_final_result = event.payload.output
        elif event.type == "run.lifecycle.failed":
            self.child_error = getattr(event.payload, "error", None)

        if self.forward_as_parent_events:
            # 当伪装成 Parent 事件时：
            # 1. 因为 Parent 已经在由外部控制生命周期，所以子流的生命周期事件应该被压制/忽略
            if event.type.startswith("run.lifecycle"):
                return None, child_trace_id, child_trace_path
            
            # 2. 修改 executor_id, executor_path, trace_path 为 Parent 的身份
            event.trace_id = self.root_trace_id
            event.trace_path = list(self.parent_trace_path)
            
            event.executor_path = list(self.parent_executor_path)
            if self.parent_executor_path:
                event.executor_id = self.parent_executor_path[-1]
                
            # 3. 如果提供了 parent_run_id，则归属到 Parent 的 run
            if self.parent_run_id:
                event.run_id = self.parent_run_id
                event.run_path = [self.parent_run_id]
                
            # 4. 清除原 executor_metadata 以免混淆（UI 应使用 executor_id 反查 Parent 信息）
            event.executor_metadata = None
            
            # 5. 特殊处理：保留 action/react 关联（如果需要）
            if self.action_id and event.action_id is None:
                event.action_id = self.action_id
            if self.react_id and event.react_id is None:
                event.react_id = self.react_id
                
            return event, child_trace_id, child_trace_path

        # 1) trace_id：对外呈现为根 trace
        event.trace_id = self.root_trace_id

        # 2) trace_path：parent_trace_path + (child_trace_id if child 是独立 trace) + child_trace_path
        if self.ignore_child_trace_id:
             event.trace_path = list(self.parent_trace_path) + child_trace_path
        elif child_trace_id != self.root_trace_id:
            event.trace_path = list(self.parent_trace_path) + [child_trace_id] + child_trace_path
        else:
            # Child 可能已经是“全局视角事件”（例如多级 forwarder 已修补）
            event.trace_path = list(self.parent_trace_path) + child_trace_path

        # 3) executor_path：parent_executor_path + child_executor_path
        child_executor_path = event.executor_path
        if not child_executor_path:
            child_executor_path = [event.executor_id]
        if self.parent_executor_path:
            event.executor_path = list(self.parent_executor_path) + list(child_executor_path)
        else:
            event.executor_path = list(child_executor_path)

        # 4) action_id/react_id 注入：仅对 Child 根子流注入，避免覆盖 Child 内部并发 action
        is_child_root_stream = len(child_trace_path) == 0
        if is_child_root_stream and (event.type.startswith("run.lifecycle.") or event.type.startswith("content.") or event.type.startswith("control.")):
             # if self.action_id and event.action_id is None:
             #     event.action_id = self.action_id
             # if self.react_id and event.react_id is None:
             #     event.react_id = self.react_id
             pass

        return event, child_trace_id, child_trace_path

    def _map_agent_result_to_action_result(self, patched_event: BaseEvent, child_trace_id:str, original_type: str, original_payload: Any, child_trace_path: List[str]) -> Optional[BaseEvent]:
        if not self.action_id:
            return None

        # 仅对 Child 的根子流做映射，避免把 Child 内部更深层嵌套的 agent.result 误当作当前 action 的结果。
        if len(child_trace_path) != 0:
            return None

        if original_type == "content.agent.result.start":
            return ContentActionResultStartEvent(
                timestamp=patched_event.timestamp,
                trace_id=patched_event.trace_id,
                trace_path=list(patched_event.trace_path or []),
                run_id=patched_event.run_id,
                run_path=patched_event.run_path,
                worker_id=patched_event.worker_id,
                executor_id=patched_event.executor_id,
                executor_type=patched_event.executor_type,
                executor_path=list(patched_event.executor_path or []),
                react_id=patched_event.react_id,
                action_id=self.action_id,
                executor_metadata=patched_event.executor_metadata,
                user_metadata=patched_event.user_metadata,
                payload=ContentActionResultStartPayload(
                    record_id=child_trace_id,
                    status=None,
                    mode=getattr(original_payload, "mode", "json"),
                    json_schema=getattr(original_payload, "json_schema", None),
                ),
            )

        if original_type == "content.agent.result.delta":
            return ContentActionResultDeltaEvent(
                timestamp=patched_event.timestamp,
                trace_id=patched_event.trace_id,
                trace_path=list(patched_event.trace_path or []),
                run_id=patched_event.run_id,
                run_path=patched_event.run_path,
                worker_id=patched_event.worker_id,
                executor_id=patched_event.executor_id,
                executor_type=patched_event.executor_type,
                executor_path=list(patched_event.executor_path or []),
                react_id=patched_event.react_id,
                action_id=self.action_id,
                executor_metadata=patched_event.executor_metadata,
                user_metadata=patched_event.user_metadata,
                payload=ContentActionResultDeltaPayload(
                    record_id=child_trace_id,
                    part=original_payload.part,
                    delta=original_payload.delta,
                    key_path=getattr(original_payload, "key_path", None),
                ),
            )

        if original_type == "content.agent.result.end":
            status = getattr(original_payload, "status", None)
            if status is None:
                status = "success"
            return ContentActionResultEndEvent(
                timestamp=patched_event.timestamp,
                trace_id=patched_event.trace_id,
                trace_path=list(patched_event.trace_path or []),
                run_id=patched_event.run_id,
                run_path=patched_event.run_path,
                worker_id=patched_event.worker_id,
                executor_id=patched_event.executor_id,
                executor_type=patched_event.executor_type,
                executor_path=list(patched_event.executor_path or []),
                react_id=patched_event.react_id,
                action_id=self.action_id,
                executor_metadata=patched_event.executor_metadata,
                user_metadata=patched_event.user_metadata,
                payload=ContentActionResultEndPayload(
                    record_id=child_trace_id,
                    full_result=original_payload.full_result,
                    images=getattr(original_payload, "images", None),
                    files=getattr(original_payload, "files", None),
                    status=status,
                    mode=getattr(original_payload, "mode", "json"),
                    json_schema=getattr(original_payload, "json_schema", None),
                ),
            )

        return None

    def _integrate_one(self, event: BaseEvent) -> Iterable[BaseEvent]:
        original_type = event.type
        original_payload = event.payload
        patched_event, _child_trace_id, child_trace_path = self._patch_event(event)

        # 始终先转发修补后的子事件
        if patched_event is not None:
            yield patched_event

        # 对所有 agent.result.* 子事件，立即生成一条当前层的 action.result.* 事件
        # 注意：如果 forwarded a parent event，patched_event 被修改了，但 mapping 逻辑仍可能需要原始信息？
        # 目前 mapping 限制为 len(child_trace_path)==0，如果是 parent event，trace_path 被清空？
        # _patch_event 返回的是 original child_trace_path，所以判断逻辑不受影响。
        # 但我们需要 patched_event 存在才能 map。
        # 如果 patched_event 被 suppress (None), 这里的 mapping 也无法进行。
        # 但通常 content.agent.result 不会被 suppress (它是 content.*)。
        # 除非 forward_as_parent_events=True，且 LLM 不产生 agent.result?
        # LLM 产生 text.end，通常不产生 agent.result。
        if patched_event is not None:
            mapped = self._map_agent_result_to_action_result(
                patched_event,
                child_trace_id = _child_trace_id,
                original_type=original_type,
                original_payload=original_payload,
                child_trace_path=child_trace_path,
            )
            if mapped is not None:
                yield mapped

    def integrate_sync(self, stream: Iterator[BaseEvent]) -> Iterator[BaseEvent]:
        """同步迭代并修补 Child 事件"""
        for event in stream:
            yield from self._integrate_one(event)

    async def integrate_async(self, stream: AsyncIterator[BaseEvent]) -> AsyncIterator[BaseEvent]:
        """异步迭代并修补 Child 事件"""
        async for event in stream:
            for out_event in self._integrate_one(event):
                yield out_event
