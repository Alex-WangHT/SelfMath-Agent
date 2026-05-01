"""
Service Interface Layer
服务接口层 - 定义所有接口和数据模型

这个包只定义接口协议和数据模型，
不包含任何具体实现，确保完全解耦。
"""

from .data_models import (
    AgentResponse,
    AgentInfo,
    AgentDescriptor,
    RouteResult,
    RoutingStrategy,
    Question,
    QuestionStats,
    UploadResult,
    ChatMessage,
    Conversation,
)

from .i_agent_service import IAgentService
from .i_agent_registry import IAgentRegistry
from .i_agent_router import IAgentRouter

__all__ = [
    "AgentResponse",
    "AgentInfo",
    "AgentDescriptor",
    "RouteResult",
    "RoutingStrategy",
    "Question",
    "QuestionStats",
    "UploadResult",
    "ChatMessage",
    "Conversation",
    "IAgentService",
    "IAgentRegistry",
    "IAgentRouter",
]
