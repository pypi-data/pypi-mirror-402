from __future__ import annotations

from enum import Enum, auto
from typing import List, Tuple, Any, Optional, Union
from dataclasses import dataclass

class State(Enum):
    ROOT = auto() # Deprecated/Alias for WAIT_JSON_START logic if needed, but we'll use WAIT_JSON_START
    WAIT_JSON_START = auto()
    IN_THINK = auto()
    WAIT_KEY = auto()
    READ_KEY = auto()
    WAIT_COLON = auto()
    WAIT_VALUE = auto()
    READ_STRING = auto()
    READ_PRIMITIVE = auto()
    WAIT_COMMA = auto()
    ESCAPE = auto()
    UNICODE_1 = auto()
    UNICODE_2 = auto()
    UNICODE_3 = auto()
    UNICODE_4 = auto()

class ContextType(Enum):
    OBJECT = auto()
    ARRAY = auto()

@dataclass
class Context:
    type: ContextType
    key: Optional[Union[str, int]] = None

class JsonStreamParser:
    def __init__(self):
        self.stack: List[Context] = []
        self.state = State.WAIT_JSON_START
        self.buffer = []  # 用于累积 key 或 unicode 字符
        self.unicode_buffer = []
        self.previous_state = None  # escape 结束后要回到的状态
        self.scan_buffer = ""

    def reset(self) -> None:
        """重置解析器状态。

        典型场景：上游检测到新的 ```json 代码块、或执行了 rollback 后重试，需要清空解析状态。
        """

        self.stack = []
        self.state = State.WAIT_JSON_START
        self.buffer = []
        self.unicode_buffer = []
        self.previous_state = None
        self.scan_buffer = ""
        
    def _get_path(self) -> List[Union[str, int]]:
        return [ctx.key for ctx in self.stack if ctx.key is not None]

    def _handle_comma(self):
        if not self.stack:
            return
        top = self.stack[-1]
        if top.type == ContextType.ARRAY:
            if isinstance(top.key, int):
                top.key += 1 # Increment index
            self.state = State.WAIT_VALUE
        elif top.type == ContextType.OBJECT:
            top.key = None # Reset key
            self.state = State.WAIT_KEY

    def _resolve_escape(self, char: str) -> str:
        mapping = {
            '"': '"',
            '\\': '\\',
            '/': '/',
            'b': '\b',
            'f': '\f',
            'n': '\n',
            'r': '\r',
            't': '\t'
        }
        return mapping.get(char, char)

    def feed(
        self,
        chunk: str,
        base_path: Optional[List[Union[str, int]]] = None,
    ) -> List[Tuple[List[Union[str, int]], Any]]:
        deltas = []
        prefix = list(base_path) if base_path else None
        
        for char in chunk:
            # Update scan buffer for trigger detection
            self.scan_buffer += char
            if len(self.scan_buffer) > 10:
                self.scan_buffer = self.scan_buffer[-10:]
            
            # Check for triggers
            if self.scan_buffer.endswith("<think>"):
                self.state = State.IN_THINK
                continue
            
            if self.state == State.IN_THINK:
                if self.scan_buffer.endswith("</think>"):
                    self.state = State.WAIT_JSON_START
                continue

            # Check for ```json reset
            if self.scan_buffer.endswith("```json"):
                self.reset()
                continue
            
            if self.state == State.WAIT_JSON_START or self.state == State.ROOT:
                if char == '{':
                    self.stack.append(Context(ContextType.OBJECT))
                    self.state = State.WAIT_KEY
                elif char == '[':
                    self.stack.append(Context(ContextType.ARRAY, 0))
                    self.state = State.WAIT_VALUE
                # Ignore primitives and text in WAIT_JSON_START

            elif self.state == State.WAIT_KEY:
                if char == '"':
                    self.buffer = []
                    self.state = State.READ_KEY
                elif char == '}':
                    if self.stack:
                        self.stack.pop()
                    self.state = State.WAIT_COMMA
                # Ignore whitespace

            elif self.state == State.READ_KEY:
                if char == '\\':
                    self.previous_state = State.READ_KEY
                    self.state = State.ESCAPE
                elif char == '"':
                    key = "".join(self.buffer)
                    if self.stack:
                        self.stack[-1].key = key
                    self.state = State.WAIT_COLON
                else:
                    self.buffer.append(char)

            elif self.state == State.WAIT_COLON:
                if char == ':':
                    self.state = State.WAIT_VALUE
                # Ignore whitespace

            elif self.state == State.WAIT_VALUE:
                if char.strip() == "":
                    continue
                
                if char == '"':
                    self.state = State.READ_STRING
                elif char == '{':
                    self.stack.append(Context(ContextType.OBJECT))
                    self.state = State.WAIT_KEY
                elif char == '[':
                    self.stack.append(Context(ContextType.ARRAY, 0))
                    self.state = State.WAIT_VALUE
                elif char == ']':
                    # Empty array case or closing array
                    if self.stack and self.stack[-1].type == ContextType.ARRAY:
                        self.stack.pop()
                        self.state = State.WAIT_COMMA
                elif char in 'tfn0123456789.-':
                    self.state = State.READ_PRIMITIVE
                    path = self._get_path()
                    if prefix:
                        path = prefix + path
                    deltas.append((path, char))
                
            elif self.state == State.READ_STRING:
                if char == '\\':
                    self.previous_state = State.READ_STRING
                    self.state = State.ESCAPE
                elif char == '"':
                    self.state = State.WAIT_COMMA
                else:
                    path = self._get_path()
                    if prefix:
                        path = prefix + path
                    deltas.append((path, char))

            elif self.state == State.READ_PRIMITIVE:
                if char in ' \t\n\r':
                    self.state = State.WAIT_COMMA
                elif char == ',':
                    self.state = State.WAIT_COMMA
                    self._handle_comma()
                elif char == '}':
                    if self.stack: self.stack.pop()
                    self.state = State.WAIT_COMMA
                elif char == ']':
                    if self.stack: self.stack.pop()
                    self.state = State.WAIT_COMMA
                else:
                    path = self._get_path()
                    if prefix:
                        path = prefix + path
                    deltas.append((path, char))

            elif self.state == State.WAIT_COMMA:
                if char == ',':
                    self._handle_comma()
                elif char == '}':
                    if self.stack and self.stack[-1].type == ContextType.OBJECT:
                        self.stack.pop()
                elif char == ']':
                    if self.stack and self.stack[-1].type == ContextType.ARRAY:
                        self.stack.pop()
                # Ignore whitespace

            elif self.state == State.ESCAPE:
                if char == 'u':
                    self.unicode_buffer = []
                    self.state = State.UNICODE_1
                else:
                    escaped_char = self._resolve_escape(char)
                    if self.previous_state == State.READ_KEY:
                        self.buffer.append(escaped_char)
                    elif self.previous_state == State.READ_STRING:
                        path = self._get_path()
                        if prefix:
                            path = prefix + path
                        deltas.append((path, escaped_char))
                    self.state = self.previous_state

            elif self.state in (State.UNICODE_1, State.UNICODE_2, State.UNICODE_3, State.UNICODE_4):
                self.unicode_buffer.append(char)
                if self.state == State.UNICODE_4:
                    try:
                        hex_str = "".join(self.unicode_buffer)
                        uni_char = chr(int(hex_str, 16))
                        if self.previous_state == State.READ_KEY:
                            self.buffer.append(uni_char)
                        elif self.previous_state == State.READ_STRING:
                            path = self._get_path()
                            if prefix:
                                path = prefix + path
                            deltas.append((path, uni_char))
                    except ValueError:
                        # Invalid unicode, ignore
                        pass
                    self.state = self.previous_state
                else:
                    # Advance state
                    # UNICODE_1 -> UNICODE_2, etc.
                    # Enum values are auto(), so they are sequential integers
                    # But relying on that is brittle if I change order.
                    # Better to be explicit.
                    if self.state == State.UNICODE_1: self.state = State.UNICODE_2
                    elif self.state == State.UNICODE_2: self.state = State.UNICODE_3
                    elif self.state == State.UNICODE_3: self.state = State.UNICODE_4

        return deltas
