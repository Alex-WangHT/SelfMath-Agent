"""
Agent路由器实现

负责根据请求内容选择最合适的Agent。
"""
import logging
from typing import Dict, Any, List, Optional

from src.interface import (
    RouteResult,
    RoutingStrategy,
    BaseAgentRouter,
    IAgentRegistry,
)

logger = logging.getLogger(__name__)


class AgentRouter(BaseAgentRouter):
    """
    Agent路由器
    
    支持多种路由策略：
    1. DIRECT: 直接路由到指定Agent
    2. AUTO: 自动选择最佳Agent
    3. ORCHESTRATED: 使用编排器协调
    4. FALLBACK: 使用默认Agent
    """
    
    def __init__(
        self,
        registry: Optional[IAgentRegistry] = None,
        fallback_agent: str = "question_bank"
    ):
        super().__init__(fallback_agent)
        self._registry = registry
        
        if self._registry is None:
            try:
                from .agent_registry import get_registry
                self._registry = get_registry()
            except ImportError:
                logger.warning("No registry available for router")
        
        logger.info("AgentRouter initialized")
    
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
            explicit_agent: 显式指定的Agent
            strategy: 路由策略
            context: 上下文信息
        
        Returns:
            RouteResult: 路由结果
        """
        if strategy == RoutingStrategy.DIRECT:
            if explicit_agent and self._is_agent_available(explicit_agent):
                return self._route_direct(explicit_agent)
            logger.warning(f"Agent {explicit_agent} not available, falling back")
            return self._route_fallback(f"Agent {explicit_agent} not available")
        
        if strategy == RoutingStrategy.AUTO:
            return self._route_auto(message, context)
        
        if strategy == RoutingStrategy.ORCHESTRATED:
            return self._route_orchestrated(message, context)
        
        # 默认使用Fallback
        return self._route_fallback("Default fallback")
    
    def _is_agent_available(self, agent_id: str) -> bool:
        """检查Agent是否可用"""
        if self._registry is None:
            return True
        return self._registry.is_available(agent_id)
    
    def _route_auto(
        self, 
        message: str, 
        context: Optional[Dict[str, Any]]
    ) -> RouteResult:
        """
        自动路由策略
        
        基于关键词匹配选择最合适的Agent。
        在实际实现中，可以使用：
        1. 关键词匹配
        2. 语义相似度
        3. 小模型分类
        """
        if not self._registry:
            return self._route_fallback("No registry available")
        
        message_lower = message.lower()
        
        routing_rules = [
            ("question_bank", ["pdf", "题目", "题库", "上传", "ocr", "搜索", "图片", "上传文件"]),
            ("understanding", ["解释", "概念", "原理", "什么是", "理解", "讲解", "怎么", "为什么"]),
            ("verification", ["验证", "检查", "对吗", "正确吗", "错误", "答案", "是否正确"]),
            ("planning", ["计划", "安排", "学习", "复习", "备考", "规划"]),
            ("assessment", ["评估", "测试", "诊断", "水平", "能力", "检测"]),
        ]
        
        scores: Dict[str, int] = {}
        
        for agent_id, keywords in routing_rules:
            if not self._registry.is_available(agent_id):
                continue
            
            score = 0
            for kw in keywords:
                if kw in message_lower:
                    score += 1
            
            if score > 0:
                scores[agent_id] = score
        
        if scores:
            best_agent = max(scores.items(), key=lambda x: x[1])
            return RouteResult(
                agent_id=best_agent[0],
                confidence=best_agent[1] / 10.0,
                reasoning=f"Matched {best_agent[1]} keywords for {best_agent[0]}",
                metadata={"strategy": "auto", "scores": scores}
            )
        
        return self._route_fallback("No keyword matches")
    
    def _route_orchestrated(
        self, 
        message: str, 
        context: Optional[Dict[str, Any]]
    ) -> RouteResult:
        """
        编排路由策略
        
        复杂任务可能需要多个Agent协作。
        这里简单地检查是否有编排器Agent可用。
        """
        if self._registry and self._registry.is_available("orchestrator"):
            return RouteResult(
                agent_id="orchestrator",
                confidence=0.9,
                reasoning="Using orchestrator for complex task",
                metadata={"strategy": "orchestrated"}
            )
        
        return self._route_auto(message, context)
    
    def get_supported_strategies(self) -> list[RoutingStrategy]:
        """获取支持的路由策略"""
        return [
            RoutingStrategy.DIRECT,
            RoutingStrategy.AUTO,
            RoutingStrategy.ORCHESTRATED,
            RoutingStrategy.FALLBACK
        ]


class SimpleKeywordRouter(AgentRouter):
    """
    简单关键词路由器
    
    一个更轻量级的实现，专门基于关键词路由。
    """
    
    def __init__(
        self,
        fallback_agent: str = "question_bank"
    ):
        super().__init__(registry=None, fallback_agent=fallback_agent)
        
        self._keyword_map: Dict[str, List[str]] = {
            "question_bank": ["pdf", "题目", "题库", "上传", "ocr", "搜索", "图片", "提取"],
            "understanding": ["解释", "概念", "原理", "什么是", "理解", "讲解"],
            "verification": ["验证", "检查", "对吗", "正确吗", "错误"],
        }
        
        self._available_agents = set(self._keyword_map.keys())
    
    def _is_agent_available(self, agent_id: str) -> bool:
        return agent_id in self._available_agents
    
    def route(
        self,
        message: str,
        explicit_agent: Optional[str] = None,
        strategy: RoutingStrategy = RoutingStrategy.DIRECT,
        context: Optional[Dict[str, Any]] = None
    ) -> RouteResult:
        """简化的路由实现"""
        if explicit_agent and explicit_agent in self._available_agents:
            return self._route_direct(explicit_agent)
        
        message_lower = message.lower()
        
        best_agent = self._fallback_agent
        best_score = 0
        scores: Dict[str, int] = {}
        
        for agent_id, keywords in self._keyword_map.items():
            score = sum(1 for kw in keywords if kw in message_lower)
            if score > 0:
                scores[agent_id] = score
                if score > best_score:
                    best_score = score
                    best_agent = agent_id
        
        if best_score > 0:
            return RouteResult(
                agent_id=best_agent,
                confidence=best_score / 10.0,
                reasoning=f"Matched {best_score} keywords for {best_agent}",
                metadata={"strategy": "keyword", "scores": scores}
            )
        
        return self._route_fallback("No keyword matches")
    
    def add_keywords(self, agent_id: str, keywords: List[str]) -> None:
        """添加关键词"""
        if agent_id not in self._keyword_map:
            self._keyword_map[agent_id] = []
            self._available_agents.add(agent_id)
        self._keyword_map[agent_id].extend(keywords)
