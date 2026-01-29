from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Literal, Union, Dict, Any

from pydantic import BaseModel, Field

from turbo_agent_core.schema.enums import (
	JSON,
	ApprovedStatus,
	MessageRole,
	MessageStatus,
	MessageShowType,
	ConversationStatus,
	ActionStatus,
    JobTaskStatus,
)
from turbo_agent_core.schema.refs import ToolRef, WorksetRef, ToolCallRecordRef, KnowledgeResourceRef,JobExecutorRef
from turbo_agent_core.schema.resources import (
	Workset
)

class ToolCallRecord(BaseModel):
	"""运行期工具调用记录（精简版，去除 ORM 注解）。"""
	id: str
	tool_project_id: Optional[str] = None
	tool_name_id: Optional[str] = None
	tool_version_id: Optional[str] = None
	tool_type: Literal["API", "LLM", "Agent"] = "API"

	title: Optional[str] = None
	intent: Optional[str] = None
	summary: Optional[str] = None

	input: Optional[JSON] = None
	result: Optional[JSON] = None
	tokenCost: Optional[float] = None
	moneyCost: Optional[float] = None
	modelUsed: Optional[str] = None
	error_message: Optional[JSON] = None
	status: Literal["pending", "running", "succeeded", "failed"] = "pending"
	time_cost: Optional[float] = None

	# 图关系（可选，运行期用于前后记录关联）
	pre_edges: List[str] = Field(default_factory=list)
	next_edges: List[str] = Field(default_factory=list)

	# 调用方信息
	agent_caller_id: Optional[str] = None
	agent_project_id: Optional[str] = None
	related_message_action_ids: List[str] = Field(default_factory=list)

	# 执行环境信息
	worker_id: Optional[str] = None # 智能体所运行的执行器 ID
	worker_host: Optional[str] = None # 智能体所运行的执行器主机标识
	worker_type: Optional[str] = None # 智能体所运行的主机类型（云主机、本地PC、具身边缘设备）

	# 凭据引用
	secret_id: Optional[str] = None

	# 用户信息
	user_caller_id: Optional[str] = None
	root_user_id: Optional[str] = None

	created_at: datetime = Field(default_factory=datetime.utcnow)
	updated_at: datetime = Field(default_factory=datetime.utcnow)


class Action(BaseModel):
	"""精简动作结构：嵌套工具调用记录引用，不使用分散的 id 字段。"""
	id: str
	type: Literal["ActionExecutionMessage"] = "ActionExecutionMessage"
	name: Optional[str] = None
	thought: Optional[str] = None
	intent: Optional[str] = None
	title: Optional[str] = None
	summary: Optional[str] = None
	input: Optional[Union[str, Dict[str, Any]]] = None
	observation: Optional[Union[str, Dict[str, Any]]] = None
	final_answer: Optional[Union[str, Dict[str, Any]]] = None
	approved_status: Optional[ApprovedStatus] = None
	tokenCost: Optional[float] = None
	moneyCost: Optional[float] = None
	status: ActionStatus = ActionStatus.Pending
	tool:ToolRef = None
	# 多个工具调用记录（引用形式）
	records: List[ToolCallRecord] = Field(default_factory=list)
	created_at: datetime = Field(default_factory=datetime.utcnow)
	updated_at: datetime = Field(default_factory=datetime.utcnow)

class  ReActRound(BaseModel):
	"""智能体单轮 ReAct 行为记录（ORM 版）"""
	id : str 
	thought : Optional[str] = None
	content: Optional[Union[str, Dict[str, Any]]] = None
	belongToMessageId : str
	# 多个动作（关联形式）
	actions: List[Action] = Field(default_factory=list)

class Message(BaseModel):
	"""精简消息结构：嵌套 Action 列表，避免散落的外键 id。"""
	id: str
	type: Literal["TextMessage"] = "TextMessage"
	role: MessageRole
	content: Optional[Union[str, List[Union[str, Dict[str, Any]]]]] = None
	reasoning_content: Optional[str] = None
	reactRounds: List[ReActRound] = Field(default_factory=list)
	# 多个动作（嵌套形式）
	actions: List[Action] = Field(default_factory=list)
	status: MessageStatus = MessageStatus.started
	tokenCost: Optional[float] = None
	moneyCost: Optional[float] = None
	modelUsed: Optional[str] = None
	created_at: datetime = Field(default_factory=datetime.utcnow)
	updated_at: datetime = Field(default_factory=datetime.utcnow)
	ancestors: List[str] = Field(default_factory=list)
	children: List[str] = Field(default_factory=list)
	


class Conversation(BaseModel):
	"""精简会话结构：直接包含 Message 列表与引用集合。"""
	id: str
	title: Optional[str] = None
	status: ConversationStatus = ConversationStatus.started
	assistant_id: str
	root_message_id: Optional[str] = None
	messages: List[Message] = Field(default_factory=list)
	context: Optional[Workset] = None
	# 关联的引用（知识资源、工作集等）可嵌入 BasicRef 派生类型
	knowledge_refs: List[KnowledgeResourceRef] = Field(default_factory=list)
	workset_refs: List[WorksetRef] = Field(default_factory=list)
	toolcall_refs: List[ToolCallRecordRef] = Field(default_factory=list)
	created_at: datetime = Field(default_factory=datetime.utcnow)
	updated_at: datetime = Field(default_factory=datetime.utcnow)

	def get_history(self, leaf_message_id: Optional[str] = None) -> List[Message]:
		"""根据叶子节点ID构建消息历史（子树路径）"""
		if not self.messages:
			return []
			
		# 如果没有指定 leaf_message_id，默认使用最后一条消息
		target_id = leaf_message_id
		if not target_id:
			target_id = self.messages[-1].id

		if not self.root_message_id:
			# 线性模式（兼容旧数据）
			for i, m in enumerate(self.messages):
				if m.id == target_id:
					return self.messages[:i+1]
			raise ValueError(f"Message {target_id} not found")
		
		# 树状模式
		message = next((m for m in self.messages if m.id == target_id), None)
		if not message:
			raise ValueError(f"Message {target_id} not found")

		history = []
		# 按顺序查找祖先
		for ancestor_id in message.ancestors:
			anc = next((m for m in self.messages if m.id == ancestor_id), None)
			if anc:
				history.append(anc)
			else:
				# 祖先丢失，可能数据不一致
				pass
		history.append(message)
		return history

	def add_child(self, message: Message, parent_id: Optional[str] = None) -> Message:
		"""添加子消息"""
		# 1. 空会话，作为根节点
		if not self.messages:
			self.root_message_id = message.id
			message.ancestors = []
			message.children = []
			self.messages.append(message)
			return message

		if not parent_id:
			raise ValueError("You need to specify a parentId if this is not the first message")

		# 2. 查找父节点
		parent = next((m for m in self.messages if m.id == parent_id), None)
		
		if not self.root_message_id:
			# Legacy 模式兼容
			if parent_id != self.messages[-1].id:
				raise ValueError("This is a legacy conversation, you can only append to the last message")
			message.ancestors = [] 
			self.messages.append(message)
			return message

		if not parent:
			raise ValueError(f"Parent message {parent_id} not found")

		# 3. 设置祖先
		message.ancestors = list(parent.ancestors) + [parent_id]
		message.children = []
		self.messages.append(message)

		# 4. 更新父节点 children
		if parent.children is None:
			parent.children = []
		parent.children.append(message.id)
		
		return message

	def add_sibling(self, message: Message, sibling_id: str) -> str:
		"""添加兄弟节点"""
		if not self.messages:
			raise ValueError("Cannot add a sibling to an empty conversation")
		if not self.root_message_id:
			raise ValueError("Cannot add a sibling to a legacy conversation")

		sibling = next((m for m in self.messages if m.id == sibling_id), None)
		if not sibling:
			raise ValueError("The sibling message doesn't exist")
			
		if not sibling.ancestors:
			raise ValueError("The sibling message is the root message, therefore we can't add a sibling")

		# 复制祖先
		message.ancestors = list(sibling.ancestors)
		message.children = []
		self.messages.append(message)

		# 更新共同父节点的 children
		nearest_ancestor_id = sibling.ancestors[-1]
		nearest_ancestor = next((m for m in self.messages if m.id == nearest_ancestor_id), None)
		if nearest_ancestor:
			if nearest_ancestor.children is None:
				nearest_ancestor.children = []
			nearest_ancestor.children.append(message.id)
			
		return message.id


class Secret(BaseModel):
	"""最小凭据模型：保持与运行期使用相关的必要字段。"""
	id: str
	name: Optional[str] = None
	identifier: Optional[str] = None
	data: Optional[JSON] = None  # access_token / api_key / cookies 等
	expires_at: Optional[datetime] = None
	valid_from: Optional[datetime] = None
	status: str = "active"
	last_refreshed: Optional[datetime] = None
	created_at: datetime = Field(default_factory=datetime.utcnow)
	updated_at: datetime = Field(default_factory=datetime.utcnow)


class JobTask(BaseModel):
    """离线任务执行记录（运行状态层）
    
    设计理念：
    - JobTask **仅用于离线任务**，在线请求直接产生 Conversation/ToolCallRecord
    - 真实的执行记录在 Conversation 中（对于 Agent/Character）
    - 支持评估 Agent（judge_agent）：接收任务说明和执行记录，形成结果判断
    - 职责：记录调度信息 + 引用执行记录 + 引用评估 Agent
    """
    
    # -------- 核心标识 --------
    id: str = Field(description="任务实例 ID")
    job_id: str = Field(description="所属 Job ID（若为独立任务则为空）")
    
    # -------- 执行者配置（可覆盖 Job 的默认值）--------
    executor_ref: Optional[JobExecutorRef] = Field(
        default=None, 
        description="本次任务的执行者（Agent 引用）"
    )
    
    # -------- 执行记录引用（核心）--------
    record_id: str = Field(
        default=None, 
        description="关联的记录 ID（真实的执行记录，对于 Agent/Character 该记录为 conversation，对于 tool 调用该记录为 tool_call_record）"
    )
    
    # -------- 评估配置（离线任务特有）--------
    judge_agent_ref: Optional[JobExecutorRef] = Field(
        default=None, 
        description="评估 Agent ID（收尾 Agent，接收任务说明和执行记录，形成执行结果判断）"
    )
    judge_conversation_id: Optional[str] = Field(
        default=None, 
        description="评估过程的会话 ID（judge_agent 的执行记录）"
    )
    
    # -------- 任务元信息 --------
    run_index: Optional[int] = Field(
        default=None, 
        description="运行索引（第几次运行，用于重试场景）"
    )
    purpose: Optional[str] = Field(
        default=None, 
        description="本次任务的目的/意图（可由系统生成或用户指定）"
    )
    summary: Optional[str] = Field(
        default=None, 
        description="任务总结（执行完成后生成）"
    )
    
    # -------- 时间规划 --------
    expected_start_time: datetime = Field(
        description="预期开始时间（调度器目标时间）"
    )
    execution_time: Optional[datetime] = Field(
        default=None, 
        description="实际开始时间（worker 开始执行时间）"
    )
    end_time: Optional[datetime] = Field(
        default=None, 
        description="结束时间（成功/失败/取消时间）"
    )
    
    # -------- 状态 --------
    status: JobTaskStatus = Field(
        default=JobTaskStatus.PENDING, 
        description="任务状态（调度状态，非执行细节）"
    )
    
    # -------- 成本统计（聚合信息）--------
    token_cost: Optional[int] = Field(
        default=None, 
        description="Token 消耗（从 Conversation 聚合）"
    )
    money_cost: Optional[float] = Field(
        default=None, 
        description="费用消耗（从 Conversation 聚合）"
    )
    
    # -------- 运行链（同一 Job 的历史运行顺序）--------
    next_task_id: Optional[str] = Field(
        default=None, 
        description="同一个 Job 下按时间顺序的下一次运行 Task ID（用于历史追溯）"
    )
