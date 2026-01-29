from __future__ import annotations

from typing import List, Dict, Any
from turbo_agent_core.schema.basic import Parameter
from turbo_agent_core.schema.enums import BasicType

_TYPE_MAP: Dict[BasicType, str] = {
    BasicType.string: "string",
    BasicType.integer: "integer",
    BasicType.number: "number",
    BasicType.boolean: "boolean",
    BasicType.enum: "string",  # enum will attach enum list
    BasicType.datetime: "string",  # add format
    BasicType.file: "string",  # treat as binary string
    BasicType.object: "object",
    BasicType.array: "array",
    BasicType.null: "null",  # may fallback to nullable string during model build
}

def _param_to_schema(param: Parameter) -> Dict[str, Any]:
    # explicit override
    if param.json_schema and isinstance(param.json_schema, dict):
        base = param.json_schema.copy()
    else:
        t = _TYPE_MAP.get(param.type, "string")
        base: Dict[str, Any] = {"type": t}
        if param.type == BasicType.datetime:
            base["format"] = "date-time"
        if param.type == BasicType.file:
            # 使用 knowledge_resource_id 标记运行时需要替换为知识资源内容
            base["format"] = "knowledge_resource_id"
        if param.type == BasicType.null:
            # represent as nullable string to avoid pydantic 'null' incompatibility
            base["type"] = "string"
            base["nullable"] = True
        if param.type == BasicType.enum and param.enum_values:
            base["enum"] = param.enum_values
        if param.type == BasicType.object and param.parameters:
            obj_schema = parameters_to_json_schema(param.parameters)
            # merge object nested properties
            base.update({
                "type": "object",
                "properties": obj_schema.get("properties", {}),
                "required": obj_schema.get("required", []),
            })
        if param.type == BasicType.array:
            items: Dict[str, Any] = {}
            if param.type_ref == BasicType.object and param.parameters:
                items = parameters_to_json_schema(param.parameters)
                # ensure items schema is object only
                items = {
                    "type": "object",
                    "properties": items.get("properties", {}),
                    "required": items.get("required", []),
                }
            elif param.type_ref == BasicType.enum and param.enum_values:
                items = {"type": "string", "enum": param.enum_values}
            elif param.type_ref and param.type_ref in _TYPE_MAP:
                mapped = _TYPE_MAP[param.type_ref]
                if param.type_ref == BasicType.datetime:
                    items = {"type": "string", "format": "date-time"}
                elif param.type_ref == BasicType.file:
                    items = {"type": "string", "format": "knowledge_resource_id"}
                elif param.type_ref == BasicType.null:
                    items = {"type": "string", "nullable": True}
                else:
                    items = {"type": mapped}
            elif param.parameters:  # array of object fallback
                items = parameters_to_json_schema(param.parameters)
                items = {
                    "type": "object",
                    "properties": items.get("properties", {}),
                    "required": items.get("required", []),
                }
            else:
                items = {"type": "string"}
            base["items"] = items
    # common attributes
    if param.description:
        base["description"] = param.description
    if param.default is not None:
        base["default"] = param.default
    return base

def parameters_to_json_schema(parameters: List[Parameter]) -> Dict[str, Any]:
    properties: Dict[str, Any] = {}
    required_list: List[str] = []
    for p in sorted(parameters, key=lambda x: x.idx):
        properties[p.name] = _param_to_schema(p)
        if p.required:
            required_list.append(p.name)
    schema: Dict[str, Any] = {
        "type": "object",
        "properties": properties,
    }
    if required_list:
        schema["required"] = required_list
    return schema
