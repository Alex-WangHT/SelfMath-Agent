"""
Agent路由器接口定义

路由器负责根据请求内容选择最合适的Agent，
支持多种路由策略。
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Protocol, runtime_checkable

from .data_models import RouteResult, RoutingStrategy


@runtime_checkable
class IAgentRouter(Protocol):
    """
    Agent路由器接口协议
    
    职责：
    1. 根据请求内容选择最佳Agent
    2. 支持多种路由策略
    3. 提供路由结果的置信度和推理
    """
    
    @abstractmethod
    def route(
        self,
        message: str,
        explicit_agent: Optional[str] = None,
        strategy: RoutingStrategy = RoutingStrategy.DIRECT,
        context: Optional[Dict[str, Any]] = None
    ) -> RouteResult:
        """
        路由请求到合适的Agent
        
        Args:
            message: 用户消息
            explicit_agent: 显式指定的Agent（用于DIRECT策略）
            strategy: 路由策略
            context: 上下文信息
        
        Returns:
            RouteResult: 路由结果
        """
        ...
    
    @abstractmethod
    def set_fallback_agent(self, agent_id: str) -> bool:
        """
        设置Fallback Agent
        
        Args:
            agent_id: Agent ID
        
        Returns:
            bool: 是否成功设置
        """
        ...
    
    @abstractmethod
    def get_supported_strategies(self) -> list[RoutingStrategy]:
        """
        获取支持的路由策略
        
        Returns:
            list[RoutingStrategy]: 支持的策略列表
        """
        ...


class BaseAgentRouter(ABC):
    """
    Agent路由器抽象基类
    
    提供通用路由逻辑框架。
    """
    
    def __init__(self, fallback_agent: str = "question_bank"):
        self._fallback_agent = fallback_agent
    
    @abstractmethod
    def route(
        self,
        message: str,
        explicit_agent: Optional[str] = None,
        strategy: RoutingStrategy = RoutingStrategy.DIRECT,
        context: Optional[Dict[str, Any]] = None
    ) -> RouteResult:
        ...
    
    def _route_direct(self, explicit_agent: Optional[str]) -> RouteResult:
        """直接路由策略"""
        if explicit_agent:
            return RouteResult(
                agent_id=explicit_agent,
                confidence=1.0,
                reasoning=f"Direct routing to {explicit_agent}",
                metadata={"strategy": "direct"}
            )
        return self._route_fallback("No explicit agent specified")
    
    def _route_fallback(self, reason: str) -> RouteResult:
        """Fallback路由策略"""
        return RouteResult(
            agent_id=self._fallback_agent,
            confidence=0.5,
            reasoning=f"Fallback: {reason}",
            metadata={"strategy": "fallback"}
        )
    
    def set_fallback_agent(self, agent_id: str) -> bool:
        self._fallback_agent = agent_id
        return True
    
    def get_supported_strategies(self) -> list[RoutingStrategy]:
        return [
            RoutingStrategy.DIRECT,
            RoutingStrategy.AUTO,
            RoutingStrategy.ORCHESTRATED,
            RoutingStrategy.FALLBACK
        ]
