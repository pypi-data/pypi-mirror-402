from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

from turbo_agent_core.schema.events import BaseEvent, ControlRollbackEvent


@dataclass
class _ChannelState:
    """单个通道的 JSON/文本组装状态。

    说明：事件流 v2 协议把 action_id 放在事件信封（Envelope）里，并把流式内容放在 payload.delta。
    因此组装器需要能按 (type/action_id/part) 做隔离，避免不同 action/不同 part 的 delta 混在一起。
    """

    root: Union[Dict, List, str, None] = None
    events: List[Tuple[float, int, List[Union[str, int]], str]] = None

    def __post_init__(self) -> None:
        if self.events is None:
            self.events = []


class JsonEventAssembler:
    """从流式事件中重建 JSON（或根级字符串）。

    支持的输入：
    - 任意携带 payload.delta 的 *.delta 事件（例如 content.action.delta / content.agent.result.delta / content.text.delta）
    - control.rollback：按 target_timestamp 截断并重建

    兼容性：
    - 保持 get_json() 无参时返回“默认通道”的 root（与旧实现一致）。
    """

    def __init__(self):
        self._channels: Dict[Tuple[str, Optional[str], Optional[str]], _ChannelState] = {}
        self._default_channel: Optional[Tuple[str, Optional[str], Optional[str]]] = None
        self._seq: int = 0

    @property
    def root(self) -> Union[Dict, List, str, None]:
        """兼容旧字段：返回默认通道的 root。"""
        if self._default_channel is None:
            return None
        return self._channels[self._default_channel].root

    def on_event(self, event: BaseEvent) -> None:
        """处理单条事件并更新内部组装结果。"""

        if isinstance(event, ControlRollbackEvent) or event.type == "control.rollback":
            self._handle_rollback(event)  # type: ignore[arg-type]
            return

        payload = getattr(event, "payload", None)
        if payload is None:
            return

        # 仅处理带 delta 的事件（协议约定：delta 承载增量内容）
        delta = getattr(payload, "delta", None)
        if delta is None:
            return

        key_path = getattr(payload, "key_path", None)
        path: List[Union[str, int]] = list(key_path) if key_path is not None else []

        part = getattr(payload, "part", None)
        action_id = getattr(event, "action_id", None)

        channel_key = (event.type, action_id, part)
        ch = self._channels.get(channel_key)
        if ch is None:
            ch = _ChannelState()
            self._channels[channel_key] = ch
            if self._default_channel is None:
                self._default_channel = channel_key

        self._seq += 1
        ch.events.append((float(event.timestamp), self._seq, path, str(delta)))
        self._apply_delta_to_channel(ch, path, str(delta))

    def _handle_rollback(self, event: ControlRollbackEvent) -> None:
        target_ts = float(event.payload.target_timestamp)

        for ch in self._channels.values():
            original_count = len(ch.events)
            ch.events = [e for e in ch.events if e[0] <= target_ts]
            if len(ch.events) == original_count:
                continue

            # 发生截断时：从头回放重建
            ch.root = None
            for _, __, path, delta in sorted(ch.events, key=lambda x: (x[0], x[1])):
                self._apply_delta_to_channel(ch, path, delta)

    def _apply_delta_to_channel(self, ch: _ChannelState, path: List[Union[str, int]], delta: str) -> None:
        # Handle Root Value
        if not path:
            if ch.root is None:
                ch.root = ""
            
            if isinstance(ch.root, str):
                ch.root += delta
            # If root is already a dict/list, we can't append string delta to it easily.
            # This implies a mixed stream or error, but we'll ignore for now.
            return

        # Initialize root if needed based on first key
        if ch.root is None:
            if isinstance(path[0], int):
                ch.root = []
            else:
                ch.root = {}

        current = ch.root
        
        # Traverse path to the parent of the leaf
        for i, key in enumerate(path[:-1]):
            next_key = path[i+1]
            
            # Determine expected type of 'current[key]' based on 'next_key'
            expected_type = list if isinstance(next_key, int) else dict
            
            if isinstance(current, list):
                if not isinstance(key, int):
                    # Should not happen if path is consistent
                    return 
                
                # Ensure list is long enough
                while len(current) <= key:
                    current.append(None)
                
                if current[key] is None:
                    current[key] = expected_type()
                elif not isinstance(current[key], expected_type):
                    # Type conflict, overwrite to recover
                    current[key] = expected_type()
                
                current = current[key]
            
            elif isinstance(current, dict):
                if key not in current:
                    current[key] = expected_type()
                elif not isinstance(current[key], expected_type):
                     current[key] = expected_type()
                
                current = current[key]
            else:
                # Current is a leaf (str) but path continues?
                # Overwrite with new structure
                # This is tricky, but let's try to recover
                # But we can't easily replace 'current' reference in parent.
                # We would need to track parent. 
                # For now, assume consistent stream.
                return

        # Handle leaf update
        last_key = path[-1]
        
        if isinstance(current, list):
            if not isinstance(last_key, int):
                return
                
            while len(current) <= last_key:
                current.append(None)
            
            if current[last_key] is None:
                current[last_key] = ""
            
            if isinstance(current[last_key], str):
                current[last_key] += delta
            else:
                # Convert to string if it was something else (unlikely in this logic)
                current[last_key] = str(current[last_key]) + delta

        elif isinstance(current, dict):
            if last_key not in current:
                current[last_key] = ""
            
            if isinstance(current[last_key], str):
                current[last_key] += delta
            else:
                current[last_key] = str(current[last_key]) + delta

    def get_json(self) -> Any:
        """返回默认通道的当前组装结果。"""
        return self.root

    def get_json_by_channel(
        self,
        *,
        event_type: str,
        action_id: Optional[str] = None,
        part: Optional[str] = None,
    ) -> Any:
        """按通道获取组装结果。

        通道键： (event_type, action_id, part)
        - event_type: 例如 content.action.delta / content.agent.result.delta
        - action_id: 协议定义在事件信封；不在 payload
        - part: payload.part（若该事件类型存在）
        """

        ch = self._channels.get((event_type, action_id, part))
        return None if ch is None else ch.root
