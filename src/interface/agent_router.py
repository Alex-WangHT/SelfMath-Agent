"""
Agent路由器（桥接器）

这是 Web 层和具体 Agent 实现之间的桥梁。
提供统一的路由接口，根据消息内容选择合适的 Agent。
"""
import logging
from typing import Dict, Any, List, Optional

from .data_models import RouteResult, RoutingStrategy


logger = logging.getLogger(__name__)


class AgentRouter:
    """
    Agent 路由器基类
    
    负责将用户消息路由到最合适的 Agent。
    """
    
    def __init__(self):
        self._default_agent = "question_bank"
        logger.info("AgentRouter initialized")
    
    def route(
        self,
        message: str,
        explicit_agent: Optional[str] = None,
        strategy: RoutingStrategy = RoutingStrategy.DIRECT,
        context: Optional[Dict[str, Any]] = None
    ) -> RouteResult:
        """
        路由消息到合适的 Agent
        
        Args:
            message: 用户消息内容
            explicit_agent: 显式指定的 Agent ID
            strategy: 路由策略
            context: 上下文信息
        
        Returns:
            RouteResult: 路由结果
        """
        if explicit_agent and strategy == RoutingStrategy.DIRECT:
            return RouteResult(
                agent_id=explicit_agent,
                confidence=1.0,
                reasoning=f"Direct routing to agent: {explicit_agent}"
            )
        
        return self._do_route(message, context)
    
    def _do_route(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> RouteResult:
        """
        实际执行路由（子类重写）
        
        Args:
            message: 用户消息
            context: 上下文
        
        Returns:
            RouteResult: 路由结果
        """
        return RouteResult(
            agent_id=self._default_agent,
            confidence=0.5,
            reasoning="Default routing (no specific rules matched)"
        )


class SimpleKeywordRouter(AgentRouter):
    """
    基于关键词匹配的简单路由器
    
    根据消息中的关键词自动选择合适的 Agent。
    """
    
    def __init__(self):
        super().__init__()
        self._routing_rules = self._get_default_rules()
        logger.info("SimpleKeywordRouter initialized")
    
    def _get_default_rules(self) -> List[Dict[str, Any]]:
        """获取默认的路由规则"""
        return [
            {
                "agent_id": "question_bank",
                "keywords": ["pdf", "题目", "题库", "上传", "ocr", "识别", "提取", "搜索"],
                "confidence": 0.9,
                "reasoning": "Detected question bank operation keywords"
            },
            {
                "agent_id": "understanding",
                "keywords": ["解释", "概念", "原理", "什么是", "什么叫", "如何理解", "理解", "讲解"],
                "confidence": 0.85,
                "reasoning": "Detected concept explanation request"
            },
            {
                "agent_id": "verification",
                "keywords": ["验证", "检查", "对吗", "正确吗", "对不对", "错了", "错误", "哪里错"],
                "confidence": 0.8,
                "reasoning": "Detected answer verification request"
            },
            {
                "agent_id": "planning",
                "keywords": ["计划", "规划", "安排", "学习", "复习", "准备", "备考"],
                "confidence": 0.75,
                "reasoning": "Detected learning plan request"
            },
            {
                "agent_id": "assessment",
                "keywords": ["评估", "水平", "能力", "薄弱", "诊断", "测试"],
                "confidence": 0.75,
                "reasoning": "Detected assessment request"
            },
        ]
    
    def _do_route(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> RouteResult:
        """
        基于关键词的路由
        
        Args:
            message: 用户消息
            context: 上下文
        
        Returns:
            RouteResult: 路由结果
        """
        message_lower = message.lower()
        
        for rule in self._routing_rules:
            matched = any(kw in message_lower for kw in rule["keywords"])
            if matched:
                logger.info(f"Routing to {rule['agent_id']}: {rule['reasoning']}")
                return RouteResult(
                    agent_id=rule["agent_id"],
                    confidence=rule["confidence"],
                    reasoning=rule["reasoning"]
                )
        
        logger.info(f"No specific keywords matched, using default: {self._default_agent}")
        return RouteResult(
            agent_id=self._default_agent,
            confidence=0.5,
            reasoning="Default routing (no specific keywords matched)"
        )
    
    def add_rule(
        self,
        agent_id: str,
        keywords: List[str],
        confidence: float = 0.8,
        reasoning: Optional[str] = None
    ):
        """
        添加路由规则
        
        Args:
            agent_id: 目标 Agent ID
            keywords: 触发关键词列表
            confidence: 置信度
            reasoning: 路由原因说明
        """
        self._routing_rules.append({
            "agent_id": agent_id,
            "keywords": [kw.lower() for kw in keywords],
            "confidence": confidence,
            "reasoning": reasoning or f"Custom rule for {agent_id}"
        })
        logger.info(f"Added routing rule for {agent_id} with keywords: {keywords}")


def get_router() -> AgentRouter:
    """获取默认的路由器实例"""
    return SimpleKeywordRouter()
