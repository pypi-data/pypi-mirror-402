# coding=utf-8

"""统一标识构造工具（Core 公共组件）。

约定：
- scoped_id（实体稳定 ID）统一使用 `name_id@belongToProjectId`。
- executor_id 统一使用 `executor_type:scoped_id`。
- tool_call_name / action_name（工具调用名称）统一使用 tool 的 scoped_id。

说明：
- 该约定用于跨产品线（云/端/worker）统一审计与展示。
- 若缺少必要字段（name_id/belongToProjectId），会回退到 `id` 字段，确保不中断运行。
"""

from __future__ import annotations

from typing import Any, Optional

from turbo_agent_core.schema.enums import RunType


def build_scoped_id(entity: Any) -> str:
    """构造稳定实体 ID：`name_id@belongToProjectId`。"""

    name_id = getattr(entity, "name_id", None)
    belong_to_project_id = getattr(entity, "belongToProjectId", None)
    version_id = getattr(entity, "version", None)

    if isinstance(name_id, str) and name_id and isinstance(belong_to_project_id, str) and belong_to_project_id:
        return f"{name_id}@{belong_to_project_id}:{version_id}" if version_id else f"{name_id}@{belong_to_project_id}"

    fallback_id = getattr(entity, "id", None)
    if isinstance(fallback_id, str) and fallback_id:
        return fallback_id

    return "unknown"


def build_executor_id(entity: Any, executor_type: Optional[RunType] = None) -> str:
    """构造统一 executor_id：`executor_type:name_id@belongToProjectId:version`。"""

    rt = executor_type or getattr(entity, "run_type", None)
    if isinstance(rt, RunType):
        type_str = rt.value
    else:
        type_str = str(rt) if rt is not None else "Unknown"

    return f"{type_str}:{build_scoped_id(entity)}"


def build_tool_call_name(tool: Any) -> str:
    """构造工具调用 name（用于 OpenAI function.name / action.name）。

    约定：tool_call_name = tool 的 `name_id@belongToProjectId`。
    """

    return build_scoped_id(tool)

def parse_executor_id(executor_id: str) -> Optional[dict]:
    """解析 executor_id 为组件信息字典。

    格式：`executor_type:scoped_id:version`。
    例子：
    - "TOOL:my_tool@project_123:1.0"
    - "AGENT:my_agent@project_456"
    """

    try:
        parts = executor_id.split(":")
        if len(parts) < 2:
            return None

        executor_type = parts[0]
        scoped_part = ":".join(parts[1:])  # 处理可能存在的多个冒号

        if "@" in scoped_part:
            name_id_part, belong_to_part = scoped_part.split("@", 1)
            if ":" in belong_to_part:
                belong_to_project_id, version = belong_to_part.split(":", 1)
            else:
                belong_to_project_id = belong_to_part
                version = None
        else:
            name_id_part = scoped_part
            belong_to_project_id = None
            version = None

        return {
            "type": executor_type,
            "name_id": name_id_part,
            "project_id": belong_to_project_id,
            "version": version
        }
    except Exception:
        return None

def parse_run_type(executor_type_str: str) -> Optional[RunType]:
    """将 executor_type 字符串解析为 RunType 枚举。"""

    try:
        return RunType(executor_type_str)
    except ValueError:
        return None

def is_tool_executor(executor_type: RunType) -> bool:
    """判断 executor_type 字符串是否表示工具执行者。"""
    is_tool = False
    executor_type_str = str(executor_type)
    # 判断是否为 Tool 类型
            # RunType: Tool, LLMTool, AgentTool, APITool, MCP, CodeScript, BUILTIN -> ToolCallRecord
            # RunType: LLM, AGENT, Character -> Message
    if "Tool" in executor_type_str: # Covers Tool, LLMTool, AgentTool, APITool
        is_tool = True
    elif executor_type_str in ["MCP", "CodeScript", "BUILTIN"]:
        is_tool = True

    return is_tool
