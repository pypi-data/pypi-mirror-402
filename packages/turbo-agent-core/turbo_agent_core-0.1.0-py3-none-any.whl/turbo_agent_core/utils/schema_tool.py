from typing import Any, Type, Optional, List, Dict
from pydantic import BaseModel, Field, create_model
from enum import Enum
import os, json, hashlib, threading, tempfile, time

# NOTE:
# __json_schema_to_base_model provides a recursive transformation from a JSON Schema-like
# dictionary into a Pydantic BaseModel subclass. It supports:
# - primitive types (string, integer, number, boolean)
# - nested objects (type: object with properties)
# - arrays (including arrays of nested objects and arrays of enums)
# - enum values on string types (converted to Python Enum)
# - nullable fields (nullable: true)
# - default values and description propagation
# The generated model preserves field optionality based on the 'required' list.
# This utility is intentionally lightweight and reusable so higher-level entities
# (e.g., BasicTool) can delegate schema -> model construction here without becoming bloated.

_IN_MEMORY_CACHE: Dict[str, tuple[Type[BaseModel], float]] = {}
_DISK_CACHE_LOCK = threading.Lock()

def _schema_cache_key(schema: dict[str, Any], class_name: str | None) -> str:
    # stable sorted JSON -> sha256
    try:
        dumped = json.dumps(schema, sort_keys=True, separators=(",", ":"))
    except Exception:
        dumped = str(schema)
    h = hashlib.sha256(dumped.encode("utf-8")).hexdigest()
    return f"{class_name or schema.get('title','DynamicModel')}__{h}"

def _disk_cache_dir() -> Optional[str]:
    path = os.getenv("TA_SCHEMA_CACHE_DIR")
    if path:
        os.makedirs(path, exist_ok=True)
        return path
    return None

def _get_ttl_seconds() -> int:
    val = os.getenv("TA_SCHEMA_CACHE_TTL_SECONDS")
    if not val:
        return 0  # 0 => no TTL
    try:
        i = int(val)
        return max(i, 0)
    except ValueError:
        return 0

def _load_disk_cache(key: str) -> Optional[dict]:
    directory = _disk_cache_dir()
    if not directory:
        return None
    file_path = os.path.join(directory, f"{key}.json")
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            blob = json.load(f)
        if not isinstance(blob, dict):
            return None
        ttl = _get_ttl_seconds()
        if ttl > 0:
            ts = blob.get("ts")
            if isinstance(ts, (int, float)) and (time.time() - ts) > ttl:
                # expired; attempt removal
                try:
                    os.remove(file_path)
                except Exception:
                    pass
                return None
        schema = blob.get("schema") if "schema" in blob else blob
        if not isinstance(schema, dict):
            return None
        return schema
    except Exception:
        return None

def _write_disk_cache(key: str, schema: dict):
    directory = _disk_cache_dir()
    if not directory:
        return
    tmp_fd, tmp_path = tempfile.mkstemp(prefix=f"{key}_", suffix=".tmp", dir=directory)
    try:
        payload = {"schema": schema, "ts": time.time()}
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
        final_path = os.path.join(directory, f"{key}.json")
        os.replace(tmp_path, final_path)  # atomic move
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass

def __json_schema_to_base_model(schema: dict[str, Any], class_name: str | None = None) -> Type[BaseModel]:
    # caching strategy: build per-process Pydantic model; share raw schema via disk for multi-process warm start
    key = _schema_cache_key(schema, class_name)
    if key in _IN_MEMORY_CACHE:
        model, ts = _IN_MEMORY_CACHE[key]
        ttl = _get_ttl_seconds()
        if ttl == 0 or (time.time() - ts) <= ttl:
            return model
        else:
            # expired in-memory
            _IN_MEMORY_CACHE.pop(key, None)
    # attempt disk load (not a compiled model, just original schema)
    disk_schema = _load_disk_cache(key)
    if disk_schema is not None:
        schema = disk_schema  # trust stored schema
    type_mapping: dict[str, type] = {
        "string": str,
        "str": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "array": list,
        "object": dict,
    }

    properties = schema.get("properties", {})
    required_fields = schema.get("required", [])
    model_fields = {}

    def process_field(field_name: str, field_props: dict[str, Any]) -> tuple:
        # print("field_props:",field_props)
        """Recursively processes a field and returns its type and Field instance."""
        json_type = field_props.get("type", "string")
        enum_values = field_props.get("enum")

        # Handle Enums
        if enum_values:
            enum_name: str = f"{field_name.capitalize()}Enum"
            field_type = Enum(enum_name, {v: v for v in enum_values})
        # Handle Nested Objects
        elif json_type == "object" and "properties" in field_props:
            field_type = __json_schema_to_base_model(
                field_props,field_name
            )  # Recursively create submodel
        # Handle Arrays with Nested Objects
        elif json_type == "array" and "items" in field_props:
            item_props = field_props["items"]
            if item_props.get("type") == "object":
                item_type: type[BaseModel] = __json_schema_to_base_model(item_props,field_name)
            elif item_props.get("type") == "string" and "enum" in item_props:
                item_type = Enum(f"{field_name.capitalize()}Enum", {v: v for v in item_props["enum"]})
            else:
                item_type: type = type_mapping.get(item_props.get("type"), Any)
            field_type = List[item_type]
        else:
            field_type = type_mapping.get(json_type, Any)

        # Handle default values and optionality
        default_value = field_props.get("default", ...)
        nullable = field_props.get("nullable", False)
        description = field_props.get("description", "")

        if nullable:
            field_type = Optional[field_type]

        if field_name not in required_fields:
            default_value = field_props.get("default", None)
        
        # if sig_type=="input" and is_root:
        #     return field_type, InputField(default = default_value, description=description)
        # elif sig_type=="output" and is_root:
        #     return field_type, OutputField(default = default_value, description=description)
        # else:
        return field_type, Field(default=default_value, description=description)
        

    # Process each field
    for field_name, field_props in properties.items():
        # print(field_name,field_props)
        model_fields[field_name] = process_field(field_name, field_props)

    # Get schema-level description
    schema_description = schema.get("description", "")
    model_config = {}
    if schema_description:
        model_config["__doc__"] = schema_description

    # if is_root:
    #     return model_fields
    model_name = class_name or schema.get("title", "DynamicModel")
    model = create_model(model_name, **model_fields)
    _IN_MEMORY_CACHE[key] = (model, time.time())
    # write through to disk cache (store original normalized schema for other processes)
    with _DISK_CACHE_LOCK:
        _write_disk_cache(key, schema)
    
    # Add schema description as class docstring if available
    if schema_description:
        model.__doc__ = schema_description
    
    return model

def json_schema_to_pydantic_model(schema: dict[str, Any], class_name: str | None = None) -> Type[BaseModel]:
    """Public helper: convert JSON schema dict to a Pydantic model.

    Args:
        schema: JSON schema-like dictionary (draft subset).
        class_name: Optional explicit class name for the dynamic model.
    Returns:
        A dynamically constructed Pydantic model class.
    """
    return __json_schema_to_base_model(schema, class_name)

def json_schema_to_signature(input_schema,output_schema,instructions):
    class DynamicSignature():
            # user:User=InputField(descriptions="学生信息")
            # scores: List[Score] = InputField(descriptions="各学科成绩")
            # result: Result = OutputField(descriptions="评价")
            pass
        

    # print(json_schema_to_base_model(input_schema,"input",True))
    for name, field in __json_schema_to_base_model(input_schema,None,"input",True).items():
        DynamicSignature = DynamicSignature.insert(index=-1,name=name,field=field[1],type_=field[0])
    for name, field in __json_schema_to_base_model(output_schema,None,"output",True).items():
        DynamicSignature = DynamicSignature.insert(index=-1,name=name,field=field[1],type_=field[0])
    
    DynamicSignature = DynamicSignature.with_instructions(instructions=instructions)

    return DynamicSignature