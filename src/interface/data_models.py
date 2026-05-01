"""
数据模型定义

所有数据传输对象 (DTO) 和数据类都在这里定义，
确保各层之间使用统一的数据格式。
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional


class AgentStatus(str, Enum):
    """Agent状态枚举"""
    ACTIVE = "active"
    DISABLED = "disabled"
    MAINTENANCE = "maintenance"


class QuestionType(str, Enum):
    """题目类型枚举"""
    EXAMPLE = "example"
    EXERCISE = "exercise"
    UNKNOWN = "unknown"


class RoutingStrategy(str, Enum):
    """路由策略枚举"""
    DIRECT = "direct"
    AUTO = "auto"
    ORCHESTRATED = "orchestrated"
    FALLBACK = "fallback"


@dataclass
class ChatMessage:
    """聊天消息"""
    role: str
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Conversation:
    """对话"""
    conversation_id: str
    messages: List[ChatMessage] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResponse:
    """Agent响应"""
    content: str
    agent_type: str
    conversation_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "agent_type": self.agent_type,
            "conversation_id": self.conversation_id,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


@dataclass
class AgentInfo:
    """Agent信息（用于前端展示）"""
    agent_id: str
    name: str
    description: str
    capabilities: List[str]
    icon: str = "bi-robot"
    status: str = AgentStatus.ACTIVE.value
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "icon": self.icon,
            "status": self.status,
        }


@dataclass
class AgentDescriptor:
    """Agent描述符（用于注册中心）"""
    agent_id: str
    name: str
    description: str
    capabilities: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    config_schema: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    priority: int = 0
    
    # 实例相关
    factory: Optional[Any] = None
    instance: Optional[Any] = None
    
    def is_available(self) -> bool:
        """检查Agent是否可用"""
        if not self.enabled:
            return False
        return True


@dataclass
class RouteResult:
    """路由结果"""
    agent_id: str
    confidence: float
    reasoning: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "metadata": self.metadata,
        }


@dataclass
class Question:
    """题目"""
    question_id: str = ""
    content: str = ""
    question_type: str = QuestionType.EXERCISE.value
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "question_id": self.question_id,
            "content": self.content,
            "question_type": self.question_type,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


@dataclass
class QuestionStats:
    """题库统计"""
    total: int = 0
    examples: int = 0
    exercises: int = 0
    sources: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "examples": self.examples,
            "exercises": self.exercises,
            "sources": self.sources,
        }


@dataclass
class UploadResult:
    """文件上传结果"""
    success: bool
    filename: str = ""
    original_filename: str = ""
    file_type: str = ""
    questions_extracted: int = 0
    questions: List[Question] = field(default_factory=list)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "success": self.success,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_type": self.file_type,
            "questions_extracted": self.questions_extracted,
            "metadata": self.metadata,
        }
        
        if self.questions:
            result["questions"] = [q.to_dict() for q in self.questions]
        
        if self.error_message:
            result["error"] = self.error_message
        
        return result
