"""
Service Interface Layer（桥接器层）

这是 Web 层和具体 Agent 实现之间的桥梁。
使用桥接器模式，提供统一的调用入口，内部调用具体的 Agent。

设计模式：桥接器模式 (Bridge Pattern)
- Web 层只依赖这个桥接器层
- 桥接器层内部调用具体的 Agent 实现
- 可以通过配置切换 Mock/Real Agent

核心组件：
- AgentService: 统一的服务入口
- AgentRegistry: Agent 注册中心
- AgentRouter: Agent 路由器
- SimpleKeywordRouter: 基于关键词的简单路由器
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
    AgentStatus,
    QuestionType,
)

from .agent_registry import (
    AgentRegistry,
    get_registry,
    register_agent,
)

from .agent_router import (
    AgentRouter,
    SimpleKeywordRouter,
    get_router,
)

from .agent_service import (
    AgentService,
    get_service,
)

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
    "AgentStatus",
    "QuestionType",
    "AgentRegistry",
    "get_registry",
    "register_agent",
    "AgentRouter",
    "SimpleKeywordRouter",
    "get_router",
    "AgentService",
    "get_service",
]
