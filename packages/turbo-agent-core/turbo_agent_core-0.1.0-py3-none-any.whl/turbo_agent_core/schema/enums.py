# coding=utf-8
#  本文档定义了 TurboAgent项目下的通用枚举类型和别名

from __future__ import annotations

from enum import Enum
from typing import Any


# Generic JSON alias
JSON = Any

class RefType(str, Enum):
    Conversation = "Conversation"
    Workset = "Workset"
    ActionRecords = "ActionRecords"
    KnowledgeResource = "KnowledgeResource"
    Agent = "Agent"
    Tool = "Tool"
    Model = "Model"
    Character = "Character"

# Enums aligned with Prisma schema (subset used by core schemas)
class LLMPromptMode(str, Enum):
    Basic = "Basic"
    ChainOfThought = "ChainOfThought"
    ReAct = "ReAct"
    Function = "Function"
    RAG = "RAG"


class ModelType(str, Enum):
    LargeLanguageModel = "LargeLanguageModel"
    VisionLanguageModel = "VisionLanguageModel"
    ImageGenerationModel = "ImageGenerationModel"
    VideoGenerationModel = "VideoGenerationModel"
    OminiModel = "OmniModel"

class WebProtocol(str, Enum):
    HTTP = "HTTP"
    HTTPS = "HTTPS"
    SOCKET = "SOCKET"
    Redis = "Redis"


class ToolOutputParseFormat(str, Enum):
    json = "json"
    string = "string"


class KnowledgeType(str, Enum):
    Document = "Document"
    Text = "Text"
    WebPage = "WebPage"
    Presentation = "Presentation"
    DataTable = "DataTable"
    Code = "Code"
    Picture = "Picture"
    Audio = "Audio"
    Video = "Video"


class Availablility(str, Enum):
    personal_visible = "personal_visible"
    project_visible = "project_visible"
    organization_visible = "organization_visible"
    public_visible = "public_visible"


class FileType(str, Enum):
    string = "string"
    json = "json"
    md = "md"
    pdf = "pdf"
    doc = "doc"
    docx = "docx"
    xls = "xls"
    xlsx = "xlsx"
    ppt = "ppt"
    pptx = "pptx"
    txt = "txt"
    csv = "csv"
    mp4 = "mp4"
    mov = "mov"
    mkv = "mkv"
    flv = "flv"
    wmv = "wmv"
    mpeg = "mpeg"
    mpg = "mpg"
    avi = "avi"
    webm = "webm"
    m4v = "m4v"
    rmvb = "rmvb"
    rm = "rm"
    ts = "ts"
    ogv = "ogv"
    m3u8 = "m3u8"
    wav = "wav"
    ogg = "ogg"
    aac = "aac"
    flac = "flac"
    wma = "wma"
    mp4a = "mp4a"
    m4a = "m4a"
    mp3 = "mp3"
    gif = "gif"
    tiff = "tiff"
    png = "png"
    bmp = "bmp"
    webp = "webp"
    jpg = "jpg"
    svg = "svg"
    jpeg = "jpeg"


class JobType(str, Enum):
    """任务类型"""
    TEMP = "temp"                # 临时任务（一次性）
    ROUTINE = "routine"          # 例行任务（周期性）
    SPECIAL_ORDER = "special_order"  # 特殊指令任务


class JobTaskStatus(str, Enum):
    """任务状态（复用 ConversationStatus 的语义）"""
    SCHEDULED = "scheduled"      # 已调度（等待时间到达）
    PENDING = "pending"          # 待执行（已入队）
    RUNNING = "running"          # 执行中
    PAUSED = "paused"            # 已暂停
    SUCCESS = "success"          # 已完成（成功）
    FAILED = "failed"            # 执行失败
    CANCELLED = "cancelled"      # 已取消
    TIMEOUT = "timeout"          # 超时


class TaskExecutionMode(str, Enum):
    """任务执行模式"""
    RUN = "run"                  # 同步模式（阻塞等待结果）
    STREAM = "stream"            # 流式模式（实时事件流）


class TaskLabelDimension(str, Enum):
    """任务标签维度（用于 worker 分组）"""
    # 任务来源
    ONLINE = "online"            # 在线请求触发
    OFFLINE = "offline"          # 离线批处理
    
    # 请求归属
    EXTERNAL = "external"        # 在公网处理任务
    INTERNAL = "internal"        # 需要依赖内部服务处理任务


class TaskSource(str, Enum):
    """任务来源标签（用于队列路由）
    
    - ONLINE: 在线请求触发（用户实时发起）
    - OFFLINE: 离线批处理（定时任务或后台触发）
    """
    ONLINE = "online"
    OFFLINE = "offline"

class ApprovedStatus(str, Enum):
    approved = "approved"
    rejected = "rejected"
    pending = "pending"
    not_required = "not_required"


class TaskOrigin(str, Enum):
    """请求归属标签（用于队列路由）
    
    - EXTERNAL: 外部用户发起（公网请求）
    - INTERNAL: 内部网络触发（系统内部链路）
    """
    EXTERNAL = "external"
    INTERNAL = "internal"


class AgentMode(str, Enum):
    """智能体执行模式（权限等级）
    
    权限由低到高：
    - QA_MODE: 问答模式，仅与用户对话式沟通
    - ASSISTANT_MODE: 助手协同模式，可创建项目、文件、代码、智能体等
    - AUTONOMOUS_MODE: 自主执行模式，可自主使用带权限工具
    - ADMIN_MODE: 管理者模式，具有自我设定能力的管理权限
    """
    TEST_MODE = "test"                # 测试模式（仅用于开发调试）
    QA_MODE = "qa"                      # 问答模式
    ASSISTANT_MODE = "assistant"        # 助手协同模式
    AUTONOMOUS_MODE = "autonomous"      # 自主执行模式
    ADMIN_MODE = "admin"                # 管理者模式


class TaskAction(str, Enum):
    """任务操作类型
    
    - START: 启动新任务（默认）
    - INTERRUPT: 中断正在执行的任务
    - RETRY: 重试失败的任务（从头开始）
    - RESUME: 恢复被中断的任务（从中断点继续）
    """
    START = "start"          # 启动新任务
    INTERRUPT = "interrupt"  # 中断任务
    RETRY = "retry"          # 重试任务
    RESUME = "resume"        # 恢复任务


class ResourceStatus(str, Enum):
    pending = "pending"
    uploaded = "uploaded"
    handling = "handling"
    ready = "ready"
    failed = "failed"


# 通过对rule的适用场景进行标记，引导不同场景下的智能体行为
class BusinessScenario(str, Enum):
    metacognition = "metacognition" #智能体价值观建立对任务、自我、环境以及不确定性的认知，让智能体能够意识到自身的推理过程、知识范围、限制条件及决策依据，从而提升智能体的自我调节和适应能力。
    user = "user" #用户扮演场景，让智能体作为用户身份对其它智能体进行需求任务构建，
    assistant = "assistant" #助手扮演场景，让智能体作为助手身份协助用户完成任务。
    tooluser = "tooluser" #工具使用者场景，让智能体作为工具使用者身份，能够根据任务需求提升对工具的定制使用能力。
    improve = "improve" #自我提升，智能体此时能够根据执行路径、用户评价等信息调整和固化用户偏好到自身设定中。
    taskPlan = "taskplan" #任务与规划场景，让智能体专注于任务分解与规划，提升其在复杂任务中的组织与执行能力。
    all = "all" #适用于所有场景(除元认知、自我提升外的场景)

class AuthType(str, Enum):
    JWT = "JWT"
    OAuth1 = "OAuth1"
    OAuth2 = "OAuth2"
    APIKey = "APIKey"
    Cookies = "Cookies"
    SMTP = "SMTP"
    POP3 = "POP3"

class KeyLocation(str, Enum):
    Header = "Header"
    Query = "Query"
    Body = "Body"


class RefreshPeriod(str, Enum):
    Immediate = "Immediate"
    Hour = "Hour"
    Day = "Day"
    Week = "Week"
    Month = "Month"
    Temporary = "Temporary"


class RunType(str, Enum):
    Tool = "Tool"
    Frontend = "Frontend"
    MCP = "MCP"
    CodeScript = "CodeScript"
    LLM = "LLM"
    LLMTool = "LLMTool"
    AgentTool = "AgentTool"
    AGENT = "AGENT"
    Character = "Character"
    BUILTIN = "BUILTIN"
    NoneType = "None"


class RequestMethod(str, Enum):
    POST = "POST"
    GET = "GET"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class ModelApiProvider(str, Enum):
    openai = "openai"
    sglang = "sglang"
    anthropic = "anthropic"
    azure = "azure"
    tgi = "tgi"
    tei = "tei"
    dashscope = "dashscope"
    vllm = "vllm"
    ollama = "ollama"
    llamacpp = "llamacpp"
    langchain = "langchain"


class SourceType(str, Enum):
    Local = "Local"
    Internal = "Internal"
    External = "External"


class SaveMode(str, Enum):
    credentials = "credentials"
    token = "token"
    both = "both"


class ToolCallStatus(str, Enum):
    started = "started"
    pending = "pending"
    success = "success"
    error = "error"
    running = "running"
    interrupted = "interrupted"


class ConversationStatus(str, Enum):
    started = "started"
    pending = "pending"
    worker_running = "worker_running"
    worker_finished = "worker_finished"
    finished = "finished"
    error = "error"
    running = "running"
    interrupted = "interrupted"


class MessageShowType(str, Enum):
    Code = "Code"
    Image = "Image"
    Video = "Video"
    EntityCard = "EntityCard"
    Table = "Table"
    Text = "Text"
    HTML = "HTML"
    SearchItem = "SearchItem"
    DownloadLink = "DownloadLink"


class MessageRole(str, Enum):
    system = "system"
    assistant = "assistant"
    user = "user"
    tool = "tool"


class MessageStatus(str, Enum):
    started = "started"
    pending = "pending"
    finished = "finished"
    error = "error"
    running = "running"
    interrupted = "interrupted"
    cancelled = "cancelled"


class ActionStatus(str, Enum):
    Pending = "Pending" #指令待执行
    Generating = "Generating" #指令生成中
    Aborted = "Aborted" #指令中止
    Thinking = "Thinking" #任务执行前思考中
    Acting = "Acting" #开始执行任务
    Submitted = "Submitted" #任务已提交
    Waitting = "Waitting" 
    Running = "Running" #指令执行中
    Failed = "Failed" #指令执行失败
    Succeed = "Succeed" #指令执行成功
    Stopped = "Stopped" #指令执行停止
    Finished = "Finished" #指令执行结束

class BasicType(str, Enum):
    enum = "enum"
    number = "number"
    integer = "integer"
    string = "string"
    boolean = "boolean"
    array = "array"
    datetime = "date-time"
    file = "file"
    object = "object"
    null = "null"

class ParameterPosition(str, Enum):
    body = "body"
    path = "path"
    query = "query"
