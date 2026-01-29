# Turbo-Agent Core 设计文档

**最后更新**: 2025-12-12  
**版本**: 2.0  
**定位**: Turbo-Agent 后端体系的数据模型与协议定义层

---

## 📖 目录

1. [什么是 Turbo-Agent Core](#什么是-turbo-agent-core)
2. [核心设计理念](#核心设计理念)
3. [快速开始](#快速开始)
4. [模块导览](#模块导览)
5. [核心概念详解](#核心概念详解)
6. [使用指南](#使用指南)
7. [扩展开发](#扩展开发)
8. [最佳实践](#最佳实践)

---

## 什么是 Turbo-Agent Core

`turbo-agent-core` 是整个 Turbo-Agent 系统的**数据模型与协议定义层**，它定义了智能体运行时的所有核心数据结构、I/O 契约和事件协议。

### 设计目标

| 目标 | 说明 |
|-----|------|
| **最小运行集合** | 仅包含智能体运行必需的数据结构，剥离权限、租户、审计等外围关注点 |
| **领域纯粹性** | 严格遵循 DDD 原则，模型只表达业务语义，不含基础设施字段 |
| **协议统一性** | 统一 Tool/Agent/LLM 的 I/O 契约，事件协议兼容 CopilotKit 与 LangGraph |
| **演进可控性** | 版本追溯通过字段实现，接口强制实现（ABC），避免运行时错误 |

### 适用场景

- ✅ 构建新的智能体运行时（Runtime）
- ✅ 开发工具插件系统
- ✅ 实现对话历史管理
- ✅ 设计流式事件处理
- ✅ 数据持久化层适配（Prisma/SQLAlchemy）
- ❌ 直接的用户权限管理（由上层 auth 模块负责）
- ❌ HTTP API 层实现（由 server 模块负责）

---

## 核心设计理念

### 1️⃣ 抽象基类模式 (TurboEntity as ABC)

所有可运行实体继承自 `TurboEntity` (Abstract Base Class)，强制实现统一接口：

```python
from turbo_agent_core.schema.basic import TurboEntity

class MyTool(TurboEntity):
    run_type = RunType.API
    
    def run(self, input: JSON, **kwargs) -> JSON:
        # 同步执行逻辑
        return {"result": "success"}
    
    async def a_run(self, input: JSON, **kwargs) -> JSON:
        # 异步执行逻辑
        return {"result": "success"}
    
    def stream(self, input: JSON, **kwargs) -> Iterator[BaseEvent]:
        # 同步流式执行
        yield TextMessageDeltaEvent(...)
    
    async def a_stream(self, input: JSON, **kwargs) -> AsyncIterator[BaseEvent]:
        # 异步流式执行
        yield TextMessageDeltaEvent(...)
```

**核心价值**：
- ✅ 编译期类型检查，避免运行时错误
- ✅ IDE 自动补全与类型推断
- ✅ 统一的 I/O 契约定义

### 2️⃣ 版本追溯而非版本容器

不使用独立的 `ToolVersion` 类，而是在实体上直接持有版本字段：

```python
tool = Tool(
    id="tool_123",
    version_id="v_456",
    version_tag="v1.2.0",
    prev_version_id="v_455",
    is_default=True,
    # ... 其他字段
)
```

**职责分离**：
- **Core 层**：持有当前版本的运行快照
- **Data 层**：维护完整的版本历史与关联关系

### 3️⃣ I/O 契约根据 run_type 区分

| 实体类型 | run_type | 输入 | 输出 |
|---------|----------|------|------|
| Tool | `RunType.API` | `JSON` | `JSON` |
| LLMModel | `RunType.LLM` | `Conversation` | `Message` |
| Agent/Character | `RunType.AGENT` | `Conversation` | `Message` |

### 4️⃣ 组合优先于继承

`LLMTool` 是"使用大模型驱动的工具"，采用**单继承 + 组合**模式：

```python
class LLMTool(Tool):  # 继承 Tool 的 JSON I/O 契约
    # 组合 Agent 的配置字段
    model: Optional[LLMModel] = None
    modelParameter: ModelParameters = Field(default_factory=ModelParameters)
    setting: Optional[BusinessSetting] = None
```

**避免**：`class LLMTool(Tool, BasicAgent)`（多重继承冲突）

### 5️⃣ 参数声明与校验内置化

Tool 内置参数定义与自动校验：

```python
tool = Tool(
    name="search_api",
    input=[
        Parameter(name="query", type=BasicType.string, required=True),
        Parameter(name="limit", type=BasicType.integer, default=10)
    ]
)

# 自动校验（内部动态构造 Pydantic 模型）
validated_input = tool.validate_input({"query": "hello", "limit": 5})
```

**自动派生 JSON Schema**：
- 从 `List[Parameter]` 自动生成 `input_schema`
- 支持缓存优化（内存 + 磁盘）

---

## 快速开始

### 安装

```bash
# 使用 uv（推荐）
cd backend/packages/turbo-agent-core
uv sync

# 或使用 pip
pip install -e .
```

### 基础用法

```python
from turbo_agent_core.schema import (
    Tool, Agent, LLMModel, Conversation, Message,
    ModelParameters, Parameter, BasicType, RunType, MessageRole
)

# 1. 创建工具
tool = Tool(
    id="search_001",
    name="web_search",
    belongToProjectId="proj_1",
    name_id="search",
    run_type=RunType.API,
    input=[
        Parameter(name="query", type=BasicType.string, required=True)
    ],
    output=[
        Parameter(name="results", type=BasicType.array)
    ]
)

# 2. 创建智能体
agent = Agent(
    id="agent_001",
    name="助手",
    belongToProjectId="proj_1",
    name_id="assistant",
    run_type=RunType.AGENT,
    model=llm_model,
    tools=[tool],
    modelParameter=ModelParameters(temperature=0.7)
)

# 3. 创建对话
conversation = Conversation(
    id="conv_001",
    assistant_id="agent_001",
    messages=[]
)

# 4. 添加消息
user_msg = Message(
    id="msg_001",
    role=MessageRole.user,
    content="帮我搜索 Python 教程"
)
conversation.add_child(user_msg)
```

---

## 模块导览

```
turbo_agent_core/
├── schema/
│   ├── enums.py          # 通用枚举（RunType/MessageRole/BasicType 等）
│   ├── basic.py          # 基础类（TurboEntity/Parameter/ModelParameters）
│   ├── agents.py         # 实体类（Tool/LLMModel/Agent/Character）
│   ├── states.py         # 状态模型（Message/Conversation/ToolCallRecord）
│   ├── resources.py      # 资源类（KnowledgeResource/BusinessSetting/Workset）
│   ├── external.py       # 外部平台（Platform/AuthMethod/Secret）
│   ├── refs.py           # 引用类型（BasicRef 及其子类）
│   └── events.py         # 事件协议（BaseEvent/Content/State/Control 事件）
└── utils/
    ├── json_stream.py    # 流式 JSON 解析器
    ├── json_assembler.py # JSON 事件组装器
    ├── param_schema.py   # 参数 -> JSON Schema 转换
    └── schema_tool.py    # JSON Schema -> Pydantic 模型动态构造
```

### 核心模块说明

| 模块 | 职责 | 关键类型 |
|------|------|---------|
| `enums.py` | 定义系统级枚举与类型别名 | `JSON`, `RunType`, `MessageRole`, `BasicType` |
| `basic.py` | 定义抽象基类与基础类型 | `TurboEntity`, `Parameter`, `ModelParameters`, `Endpoint` |
| `agents.py` | 定义可运行实体（工具/模型/智能体） | `Tool`, `LLMModel`, `BasicAgent`, `Agent`, `Character` |
| `states.py` | 定义运行状态与对话结构 | `Message`, `Action`, `Conversation`, `ToolCallRecord` |
| `resources.py` | 定义业务资源与知识库 | `KnowledgeResource`, `BusinessSetting`, `Workset` |
| `events.py` | 定义流式事件协议 | `BaseEvent`, `ContentTextDeltaEvent`, `ActionExecutionEvent` |

---

## 核心概念详解

### 🔧 TurboEntity 实体体系

```
TurboEntity (ABC)
├── Tool (run_type=API)
│   ├── APITool      # HTTP/HTTPS API 工具
│   ├── LLMTool      # 大模型驱动的工具
│   └── AgentTool    # 智能体作为工具
├── LLMModel (run_type=LLM)
└── BasicAgent (run_type=AGENT)
    ├── Character    # 角色实体
    └── Agent        # 完整智能体
```

**关键属性**：
- `id`: 全局唯一标识
- `name_id`: 项目内唯一标识（用于引用）
- `run_type`: 运行类型（决定 I/O 契约）
- `version_id/version_tag/prev_version_id`: 版本追溯

### 💬 Message 与 Conversation

#### Message 聚合模型

`Message` 聚合单轮对话的完整生命周期：

```python
message = Message(
    id="msg_001",
    role=MessageRole.assistant,
    content="最终答案",                    # 最终响应
    reasoning_content="让我思考一下...",   # 思维链（CoT）
    actions=[                             # 工具调用序列
        Action(
            name="search",
            input={"query": "Python"},
            records=[ToolCallRecord(...)]
        )
    ],
    status=MessageStatus.success,
    token_cost=1500,
    ancestors=["msg_000"],               # 父消息 ID
    children=["msg_002", "msg_003"]      # 子消息 ID 列表
)
```

**与 LangChain 的映射**：
- **运行时展开**：`Message` → `[AIMessage(content=reasoning), ToolMessage(...), AIMessage(content=final)]`
- **持久化收缩**：`[AIMessage, ToolMessage, ...]` → 单个 `Message`（actions 数组）

#### Conversation 树形管理

支持非线性对话分支：

```python
conversation = Conversation(id="conv_001", assistant_id="agent_001")

# 添加根消息
root_msg = Message(id="msg_root", role=MessageRole.user, content="你好")
conversation.add_child(root_msg)

# 添加子消息
reply_1 = Message(id="msg_1", role=MessageRole.assistant, content="你好！")
conversation.add_child(reply_1, parent_id="msg_root")

# 添加兄弟消息（分支）
reply_2 = Message(id="msg_2", role=MessageRole.assistant, content="嗨！")
conversation.add_sibling(reply_2, sibling_id="msg_1")

# 获取历史
history = conversation.get_history(leaf_message_id="msg_1")
# 返回: [root_msg, reply_1]
```

### 🛠️ Tool 参数系统

#### 参数定义

```python
from turbo_agent_core.schema import Parameter, BasicType

search_tool = Tool(
    name="search",
    input=[
        Parameter(
            name="query",
            type=BasicType.string,
            required=True,
            description="搜索关键词"
        ),
        Parameter(
            name="filters",
            type=BasicType.object,
            parameters=[  # 嵌套参数
                Parameter(name="date_from", type=BasicType.datetime),
                Parameter(name="date_to", type=BasicType.datetime)
            ]
        ),
        Parameter(
            name="category",
            type=BasicType.enum,
            enum_values=["tech", "news", "blog"]
        )
    ]
)
```

#### 自动校验

```python
# 正确的输入
valid_input = {
    "query": "Python",
    "filters": {"date_from": "2024-01-01T00:00:00Z"},
    "category": "tech"
}
result = search_tool.validate_input(valid_input)  # ✅ 通过

# 错误的输入
invalid_input = {"query": 123}  # query 应该是 string
try:
    search_tool.validate_input(invalid_input)
except ValueError as e:
    print(e)  # ❌ 抛出校验错误
```

### 📊 ToolCallRecord 执行记录

```python
record = ToolCallRecord(
    id="call_001",
    tool_name_id="search",
    tool_version_id="v_001",
    input={"query": "Python"},
    result={"items": [...]},
    status="succeeded",
    token_cost=100,
    time_cost=0.5,  # 秒
    pre_edges=["call_000"],   # 前置依赖
    next_edges=["call_002"],  # 后续调用
    agent_caller_id="agent_001"
)
```

支持图结构（并行/串行工具调用）：

```
call_000 (search)
    ├── call_001 (analyze) ──┐
    └── call_002 (filter)   ─┤
                             ├──> call_003 (summarize)
```

---

## 使用指南

### 场景 1：创建自定义工具

```python
from turbo_agent_core.schema import Tool, Parameter, BasicType, RunType
from typing import AsyncIterator

class WeatherTool(Tool):
    run_type = RunType.API
    
    def __init__(self):
        super().__init__(
            id="weather_001",
            name="天气查询",
            belongToProjectId="proj_1",
            name_id="weather",
            input=[
                Parameter(name="city", type=BasicType.string, required=True)
            ],
            output=[
                Parameter(name="temperature", type=BasicType.number),
                Parameter(name="condition", type=BasicType.string)
            ]
        )
    
    async def a_run(self, input: dict, **kwargs) -> dict:
        city = input["city"]
        # 调用天气 API
        return {"temperature": 25.5, "condition": "晴天"}
    
    async def a_stream(self, input: dict, **kwargs) -> AsyncIterator:
        # 流式响应（如果需要）
        yield ContentTextDeltaEvent(...)
```

### 场景 2：构建对话历史

```python
from turbo_agent_core.schema import Conversation, Message, MessageRole, Action

# 初始化对话
conv = Conversation(id="conv_123", assistant_id="agent_001")

# 用户提问
user_msg = Message(
    id="msg_001",
    role=MessageRole.user,
    content="今天天气怎么样？"
)
conv.add_child(user_msg)

# 助手响应（带工具调用）
assistant_msg = Message(
    id="msg_002",
    role=MessageRole.assistant,
    reasoning_content="我需要查询天气信息",
    actions=[
        Action(
            name="weather",
            input={"city": "北京"},
            records=[...]
        )
    ],
    content="北京今天晴天，温度 25.5°C"
)
conv.add_child(assistant_msg, parent_id="msg_001")

# 获取完整历史
history = conv.get_history(leaf_message_id="msg_002")
# [user_msg, assistant_msg]
```

### 场景 3：处理流式事件

```python
from turbo_agent_core.schema.events import BaseEvent

async def process_events(event_stream: AsyncIterator[BaseEvent]):
    async for event in event_stream:
        match event.type:
            case "content.text.delta":
                # 处理文本增量
                print(event.payload.delta, end="", flush=True)
            
            case "content.action.start":
                # 工具调用开始
                print(f"\n[调用工具: {event.payload.name}]")
            
            case "content.action.result.end":
                # 工具执行完成
                print(f"[结果: {event.payload.result}]")
            
            case "run.lifecycle":
                if event.payload.stage == "completed":
                    print("\n✅ 运行完成")
```

### 场景 4：数据持久化适配

```python
from turbo_agent_core.schema import Conversation, Message
from prisma import Prisma

async def save_conversation_to_db(conv: Conversation):
    db = Prisma()
    await db.connect()
    
    # Core DTO -> Prisma Model
    await db.assistantconversation.create(
        data={
            "id": conv.id,
            "assistant_id": conv.assistant_id,
            "title": conv.title,
            "status": conv.status.value,
            # 创建关联的 Message 记录
            "messages": {
                "create": [
                    {
                        "id": msg.id,
                        "role": msg.role.value,
                        "content": msg.content,
                        "reasoning_content": msg.reasoning_content,
                        "ancestors": msg.ancestors,
                        # ...
                    }
                    for msg in conv.messages
                ]
            }
        }
    )
```

---

## 扩展开发

### 实现自定义 Agent

```python
from turbo_agent_core.schema import BasicAgent, Conversation, Message, RunType

class MyCustomAgent(BasicAgent):
    run_type = RunType.AGENT
    
    async def a_run(
        self, 
        conversation: Conversation,
        leaf_message_id: str = None,
        tools: List[Tool] = None,
        **kwargs
    ) -> Message:
        # 1. 获取历史
        history = conversation.get_history(leaf_message_id)
        
        # 2. 构造 Prompt
        prompt = self._build_prompt(history)
        
        # 3. 调用 LLM
        llm_response = await self.model.a_run(conversation, ...)
        
        # 4. 解析工具调用
        if llm_response.actions:
            for action in llm_response.actions:
                tool = self._find_tool(action.name)
                result = await tool.a_run(action.input)
                # 记录到 ToolCallRecord
        
        # 5. 返回最终消息
        return Message(
            role=MessageRole.assistant,
            content=llm_response.content,
            actions=llm_response.actions
        )
```

### 自定义事件类型

```python
from turbo_agent_core.schema.events import BaseEvent
from pydantic import BaseModel
from typing import Literal

class CustomThinkingPayload(BaseModel):
    step: int
    reasoning: str

class CustomThinkingEvent(BaseEvent):
    type: Literal["custom.thinking"] = "custom.thinking"
    payload: CustomThinkingPayload
```

---

## 最佳实践

### ✅ 推荐做法

1. **使用类型注解**
   ```python
   def process_tool(tool: Tool) -> JSON:
       result: JSON = tool.run({"query": "test"})
       return result
   ```

2. **版本追溯字段完整填写**
   ```python
   tool = Tool(
       version_id=generate_uuid(),
       version_tag="v1.0.0",
       prev_version_id=old_tool.version_id,
       is_default=True
   )
   ```

3. **参数校验前置**
   ```python
   # 在执行前校验
   validated_input = tool.validate_input(user_input)
   result = tool.run(validated_input)
   ```

4. **使用 Conversation 树形 API**
   ```python
   # 正确：使用 add_child/add_sibling
   conv.add_child(message, parent_id="msg_001")
   
   # 错误：直接操作 messages 列表
   conv.messages.append(message)  # ❌ 不会更新 ancestors/children
   ```

### ❌ 避免的做法

1. **不要多重继承 TurboEntity**
   ```python
   # ❌ 错误
   class BadTool(Tool, BasicAgent):
       pass
   
   # ✅ 正确：使用组合
   class GoodTool(Tool):
       agent_config: BasicAgent = ...
   ```

2. **不要在 Core 层硬编码权限逻辑**
   ```python
   # ❌ 错误
   class Tool(TurboEntity):
       def run(self, input, user_id):
           if not self.check_permission(user_id):  # 权限检查属于上层
               raise PermissionError()
   ```

3. **不要绕过参数校验**
   ```python
   # ❌ 错误
   result = tool._execute(raw_input)  # 跳过 validate_input
   
   # ✅ 正确
   validated = tool.validate_input(raw_input)
   result = tool.run(validated)
   ```

---

## 与 Prisma Schema 对齐

Core 层专注于运行时数据结构，Prisma 负责持久化。两者通过**适配器模式**映射：

| Core 模型 | Prisma 模型 | 映射方式 |
|----------|------------|---------|
| `Tool` | `Tool` + `ToolVersion` | Core 持有当前版本快照，Prisma 维护历史 |
| `Agent` | `Agent` + `AgentVersion` | 同上 |
| `Message` | `Message` + `MessageAction` | Core 聚合，Prisma 关联表 |
| `Conversation` | `AssistantConversation` | 直接映射 + 树形关系处理 |
| `ToolCallRecord` | `ToolCallRecord` | 精简字段对齐 |

**适配器示例**（由 `config` 模块实现）：
```python
# Core -> Prisma
def to_prisma_tool(core_tool: Tool) -> PrismaToolCreateInput:
    return {
        "id": core_tool.id,
        "name": core_tool.name,
        "version_id": core_tool.version_id,
        # ... 映射其他字段
    }

# Prisma -> Core
def to_core_tool(prisma_tool: PrismaTool) -> Tool:
    return Tool(
        id=prisma_tool.id,
        name=prisma_tool.name,
        # ... 重构为 Core 结构
    )
```

---

## 相关文档

- 📄 [Core 设计思路](../../docs/backend-refactor/progress/core-models.md)
- 📄 [后端架构总览](../../docs/backend-refactor/architecture.md)
- 📄 [事件协议设计](../../docs/backend-refactor/event_design.md)
- 📄 [数据结构映射](../../docs/backend-refactor/data_structures.md)

---

## 常见问题

**Q: 为什么 Tool 不直接继承 Agent？**  
A: Tool 和 Agent 的 I/O 契约不同（JSON vs Conversation），多重继承会导致字段冲突。采用**组合模式**（如 LLMTool）更清晰。

**Q: Message 的 `ancestors` 和 `children` 什么时候更新？**  
A: 调用 `Conversation.add_child/add_sibling` 时自动维护。不要直接修改 `messages` 列表。

**Q: 如何扩展新的事件类型？**  
A: 继承 `BaseEvent`，定义新的 `type` 和 `payload`，并在 `EventType` 枚举中添加（可选）。

**Q: Core 层是否包含数据库操作？**  
A: 不包含。Core 定义数据结构，具体 CRUD 由 `config` 模块的 `ConfigProvider` 实现。

---

**最后更新**: 2025-12-12  
**维护者**: Turbo-Agent Team
