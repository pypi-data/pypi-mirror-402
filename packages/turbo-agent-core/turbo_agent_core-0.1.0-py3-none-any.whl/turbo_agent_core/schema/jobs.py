# coding=utf-8
from __future__ import annotations
from typing import Optional, List, Set, Dict, Any,Union
from datetime import datetime
from croniter import croniter
from pydantic import BaseModel, Field, model_validator

from turbo_agent_core.schema.enums import (
    JobType, 
    JSON, 
    TaskAction, 
    TaskExecutionMode, 
    AgentMode,
    TaskSource,
    TaskOrigin,
    TaskLabelDimension
)
from turbo_agent_core.schema.refs import JobExecutorRef
from turbo_agent_core.schema.states import Message
from turbo_agent_core.schema.events import UserInfo

# 使用 TYPE_CHECKING 延迟导入，避免循环导入
from turbo_agent_core.schema.agents import Agent, Character, AgentTool,APITool, LLMTool
from turbo_agent_core.schema.resources import Workset

class AgentPayload(BaseModel):
    """Agent/Character 的输入载荷"""
    conversation_id: Optional[str] = Field(None, description="会话 ID（可选，若为 None 则创建新会话）")
    leaf_id: Optional[str] = Field(None, description="当前活跃分支的叶子节点 ID")
    messages: List[Message] = Field(default_factory=list, description="历史消息列表（可选，用于上下文）")
    current_input: Union[Message, Dict[str, Any]] = Field(..., description="当前输入消息（Message 对象或简化字典）")

class ToolPayload(BaseModel):
    """Tool/LLMTool/APITool 的输入载荷"""
    parameters: Dict[str, Any] = Field(..., description="工具输入参数")

class ResumePayload(BaseModel):
    """RESUME 操作的输入载荷"""
    interrupt_id: str = Field(..., description="中断请求 ID")
    resume_token: str = Field(..., description="恢复令牌（用于验证）")
    approval: bool = Field(..., description="用户授权结果")
    user_input: Optional[Union[str, Dict[str, Any]]] = Field(None, description="用户补充输入")
    message: Optional[str] = Field(None, description="用户消息（可选）")
    
    # Context info
    action_id: str = Field(..., description="Action ID")
    action_name: str = Field(..., description="Action Name")
    action_parameters: Dict[str, Any] = Field(..., description="Action Parameters")
    conversation_id: str = Field(..., description="Conversation ID")
    leaf_id: str = Field(..., description="Leaf Message ID")

class Job(BaseModel):
    """任务定义（调度模板）
    
    设计理念：
    - Job 本身是"配置"而非"运行实例"
    - 类似于 Kubernetes 的 CronJob：定义"如何调度"，不记录"运行历史"
    - 运行历史由 TaskRun（运行状态层）记录
    """
    
    # -------- 核心标识 --------
    id: str = Field(description="任务 ID")
    name: str = Field(description="任务名称")
    description: str = Field(default="", description="任务描述")
    type: JobType = Field(default=JobType.TEMP, description="任务类型")
    tags: List[str] = Field(default_factory=list, description="任务标签（用于分类与检索）")
    
    # -------- 执行者配置 --------
    executors: List[JobExecutorRef] = Field(
        default_factory=list, 
        description="默认执行者列表（Agent 引用）"
    )
    
    # -------- 运行模式配置 --------
    
    # execution_mode 已移除，仅在 JobTask 中定义
    
    # -------- 调度配置 --------
    crontab: Optional[str] = Field(default=None, description="Cron 表达式（例行任务）")
    cron_begin: Optional[datetime] = Field(default=None, description="调度开始时间")
    cron_end: Optional[datetime] = Field(default=None, description="调度结束时间")
    start_times: List[datetime] = Field(default_factory=list, description="手动指定特殊时间点触发任务")
    next_start_times: List[datetime] = Field(default_factory=list, description="下几次运行时间（自动计算）")
    
    # -------- 任务链配置 --------
    next_start_task_id: Optional[str] = Field(
        default=None, 
        description="下一个起始任务 ID（用于任务链编排）"
    )
    
    # -------- 上下文配置 --------
    initial_workset_ids: List[str] = Field(
        default_factory=list, 
        description="初始工作集 ID 列表"
    )
    prompt_template: Optional[str] = Field(
        default=None, 
        description="提示词模板（可被 TaskRun 实例化时插值）"
    )
    instruction: Optional[str] = Field(
        default=None, 
        description="任务指令（明确的执行目标）"
    )
    # -------- 工具约束 --------
    required_tool_id: Optional[str] = Field(
        default=None, 
        description="必需工具 ID（若指定，则任务执行时必须使用该工具）"
    )
    # -------- 评估配置（离线任务特有）--------
    judge_agent_ref: Optional[JobExecutorRef] = Field(
        default=None, 
        description="评估 Agent 引用（收尾 Agent，接收任务说明和执行记录，形成执行结果判断）"
    )
    judge_policy: Optional[str] = Field(
        default=None, 
        description="评估策略（如何判断任务成功/失败，供 judge_agent 使用）"
    )
    failed_policy: Optional[str] = Field(
        default=None, 
        description="失败处理策略（重试次数、降级方案等）"
    )
    cost_limit: Optional[float] = Field(
        default=None, 
        description="成本限制（单位：美元或其他货币）"
    )

    # -------- 状态字段 --------
    is_active: bool = Field(default=True, description="是否激活（停用后不再调度）")

    # -------- 版本追溯（可选，若 Job 配置需要版本化）--------
    version_id: Optional[str] = Field(default=None, description="当前版本 ID")
    version_tag: Optional[str] = Field(default=None, description="版本标签（如 v1.0）")
    prev_version_id: Optional[str] = Field(default=None, description="前序版本 ID")

    @model_validator(mode='after')
    def compute_next_start_times(self) -> 'Job':
        if not self.next_start_times:
             self.next_start_times = self.get_next_run_times(count=5)
        return self

    def get_next_run_times(self, count: int = 5, start_time: Optional[datetime] = None) -> List[datetime]:
        """
        根据 crontab 配置和 start_times 推断下几次运行时间。
        Args:
            count: 返回的时间点数量
            start_time: 计算起始时间，默认为当前时间
        Returns:
            List[datetime]: 下几次运行的时间列表
        """
        base_time = start_time or datetime.utcnow()
        # Ensure base_time is naive if it's aware, or handle timezone consistently.
        # For simplicity, let's make base_time naive if it has tzinfo, assuming local time.
        if base_time.tzinfo is not None:
            base_time = base_time.replace(tzinfo=None)

        candidates = []

        # 1. 处理手动指定的时间点
        if self.start_times:
            for t in self.start_times:
                # Convert to naive local time for comparison with base_time
                if t.tzinfo:
                    t_naive = t.astimezone().replace(tzinfo=None)
                else:
                    t_naive = t

                # 必须在 base_time 之后
                if t_naive > base_time:
                    # 如果有结束时间限制，必须在结束时间之前
                    if self.cron_end:
                        if self.cron_end.tzinfo:
                            end_naive = self.cron_end.astimezone().replace(tzinfo=None)
                        else:
                            end_naive = self.cron_end
                        
                        if t_naive > end_naive:
                            continue
                    candidates.append(t) # Keep original t (aware or naive)

        # 2. 处理 Crontab
        if self.crontab:
            try:
                # 确定 cron 计算的起始时间
                cron_start = base_time
                if self.cron_begin:
                    begin_naive = self.cron_begin.replace(tzinfo=None) if self.cron_begin.tzinfo else self.cron_begin
                    if begin_naive > base_time:
                        cron_start = begin_naive

                # 如果起始时间已经超过了结束时间，则不再生成
                should_generate = True
                if self.cron_end:
                    end_naive = self.cron_end.replace(tzinfo=None) if self.cron_end.tzinfo else self.cron_end
                    if cron_start > end_naive:
                        should_generate = False

                if should_generate:
                    iter = croniter(self.crontab, cron_start)
                    # 预取 count 个，因为可能会和 start_times 混合排序
                    for _ in range(count):
                        next_time = iter.get_next(datetime)
                        if self.cron_end:
                            end_naive = self.cron_end.replace(tzinfo=None) if self.cron_end.tzinfo else self.cron_end
                            next_naive = next_time.replace(tzinfo=None) if next_time.tzinfo else next_time
                            if next_naive > end_naive:
                                break
                        candidates.append(next_time)
            except Exception:
                pass

        # 3. 排序并去重
        # Normalize for sorting: convert all to naive for comparison if mixed?
        # Or just rely on Python's comparison if all are same type.
        # Prisma returns aware datetimes (UTC).
        # Let's sort by timestamp to be safe.
        candidates.sort(key=lambda x: x.timestamp())

        # Remove duplicates (simple loop to handle potential tz diffs but same instant)
        unique_candidates = []
        if candidates:
            unique_candidates.append(candidates[0])
            for i in range(1, len(candidates)):
                if abs(candidates[i].timestamp() - candidates[i-1].timestamp()) > 0.001:
                    unique_candidates.append(candidates[i])

        # 4. 返回前 count 个
        return unique_candidates[:count]

class TaskSpec(BaseModel):
    """任务规格（运行时请求 DTO）
    
    设计理念：
    - TaskSpec 是 job master 向 worker 传递的轻量级"指令单"
    - 包含执行所需的全部信息（实体引用、输入、配置、标签）
    - 不持久化（或仅临时存储在队列中）
    - Worker 执行后产出 JobTask 持久化记录
    """
    
    # -------- 操作类型 --------
    action: TaskAction = Field(
        default=TaskAction.START,
        description="任务操作类型（start/interrupt/retry/resume）"
    )
    
    # -------- 任务标签（用于队列路由）--------
    task_source: TaskSource = Field(
        default=TaskSource.ONLINE,
        description="任务来源（online: 在线请求触发，offline: 离线批处理）"
    )
    task_origin: TaskOrigin = Field(
        default=TaskOrigin.EXTERNAL,
        description="请求归属（external: 外部用户发起，internal: 内部网络触发）"
    )

    # -------- 用户信息 --------
    user: Optional[UserInfo] = Field(
        default=None,
        description="发起任务的用户信息（用于鉴权、审计与上下文绑定）"
    )
        
    # -------- 任务标识 --------
    # 仅在离线任务场景下使用，对应 JobTask.id
    task_id: Optional[str] =   Field(default=None, description="任务 ID（对应 JobTask.id）")
    trace_id: Optional[str] = Field(default=None, description="任务追踪ID（Trace ID），在 Online 模式下，可以直接指定该 ID 作为 Message ID")
    
    # -------- 恢复点配置（RETRY/RESUME 时必填）--------
    resume_from_message_id: Optional[str] = Field(
        default=None,
        description="""恢复点消息 ID（等同于 breakpoint_trace_id）：
        - RETRY: 指向失败的 message_id，重试时创建新的 Message 分支（parent_id = leaf_id）
        - RESUME: 指向断点的 message_id，从此消息继续执行（trace_id = message_id）
        - 用于从 ExecutionCheckpoint 表查找断点数据
        """
    )
    
    action_id: Optional[str] = Field(
        default=None,
        description="""需要授权的 action ID（RESUME 操作时必填）：
        - 精确指定用户授权的是哪个 action
        - 从 ExecutionCheckpoint.checkpoint_data["action_id"] 读取
        - 用于 Worker 恢复执行时定位到具体的 action
        - 避免恢复时执行错误的 action
        """
    )
    
    # -------- 执行配置 --------
    stream_mode: bool = Field(
        default=True,
        description="是否启用流式输出（stream 模式）。默认为 True"
    )

    # -------- 执行者引用（可选，支持默认智能体模式）--------
    executor: Optional[Union[Agent,Character,AgentTool,APITool,LLMTool]] = Field(
        default=None,
        description="要执行的实体引用（Agent/Tool/Model）。若为 None，则使用默认智能体模式（从 YAML 配置加载）",
    )
    agent_mode: Optional[AgentMode] = Field(
        default=None,
        description="智能体执行模式（权限等级：qa/assistant/autonomous/admin）。仅当 executor 不为 None 时有效"
    )
    
    # -------- 默认智能体配置（仅当 executor_ref 为 None 时有效）--------
    model: Optional[dict] = Field(
        default=None,
        description="LLMModel 结构（按 core 中的 LLMModel 格式传入，包含 instances、defaultParameters 等）"
    )
    tool_ids: List[str] = Field(
        default_factory=list,
        description="工具 ID 列表（默认智能体模式下可用的工具）"
    )
        # -------- 依赖资源（可选）--------
    required_secrets: List[str] = Field(
        default_factory=list, 
        description="必需的密钥 ID 列表"
    )
    
    # -------- 输入配置 --------
    payload: Union[AgentPayload, ToolPayload, ResumePayload] = Field(
        description="""输入数据（支持多种类型，根据 executor.type 决定）：
        
        **根据执行者类型的输入契约**：
        - Agent/Character: 使用 AgentPayload
        - Tool/LLMTool/APITool: 使用 ToolPayload
        - RESUME 操作: 使用 ResumePayload
        """
    )
    

