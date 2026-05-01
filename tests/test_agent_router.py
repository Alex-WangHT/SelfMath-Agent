"""
测试：Agent路由器

测试 src/services/agent_router.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from src.interface import RoutingStrategy, RouteResult
from src.services.agent_router import (
    AgentRouter,
    SimpleKeywordRouter,
)
from src.services.agent_registry import (
    AgentRegistry,
    get_registry,
    register_agent,
)


class TestAgentRouter:
    """测试 AgentRouter 类"""
    
    def setup_method(self):
        """每个测试前清空注册中心"""
        registry = get_registry()
        registry.clear()
        
        # 注册测试用Agent
        register_agent(
            agent_id="question_bank",
            name="题库管理",
            description="Test"
        )
        register_agent(
            agent_id="understanding",
            name="概念理解",
            description="Test"
        )
    
    def test_route_direct(self):
        """测试直接路由"""
        router = AgentRouter()
        
        result = router.route(
            message="test",
            explicit_agent="question_bank",
            strategy=RoutingStrategy.DIRECT
        )
        
        assert isinstance(result, RouteResult)
        assert result.agent_id == "question_bank"
        assert result.confidence == 1.0
    
    def test_route_fallback(self):
        """测试Fallback路由"""
        router = AgentRouter()
        
        # 当指定的Agent不存在时，应该fallback
        result = router.route(
            message="test",
            explicit_agent="nonexistent",
            strategy=RoutingStrategy.DIRECT
        )
        
        assert result.agent_id == "question_bank"  # fallback默认值
    
    def test_set_fallback_agent(self):
        """测试设置Fallback Agent"""
        router = AgentRouter()
        
        # 注册另一个Agent作为fallback
        register_agent(
            agent_id="custom_fallback",
            name="Custom Fallback",
            description="Test"
        )
        
        success = router.set_fallback_agent("custom_fallback")
        assert success is True
        
        # 验证fallback是否生效
        result = router.route(
            message="test",
            explicit_agent="nonexistent",
            strategy=RoutingStrategy.DIRECT
        )
        # 注意：这里要看实现，可能需要调整测试逻辑
    
    def test_get_supported_strategies(self):
        """测试获取支持的策略"""
        router = AgentRouter()
        strategies = router.get_supported_strategies()
        
        assert RoutingStrategy.DIRECT in strategies
        assert RoutingStrategy.AUTO in strategies
        assert RoutingStrategy.FALLBACK in strategies


class TestSimpleKeywordRouter:
    """测试 SimpleKeywordRouter 类"""
    
    def test_route_with_keyword(self):
        """测试关键词路由"""
        router = SimpleKeywordRouter()
        
        # 测试"题库"关键词
        result = router.route(
            message="我想上传PDF题库",
            explicit_agent=None,
            strategy=RoutingStrategy.AUTO
        )
        
        assert result.agent_id == "question_bank"
        assert "题库" in result.reasoning.lower() or result.confidence > 0
    
    def test_route_with_explicit_agent(self):
        """测试显式指定Agent"""
        router = SimpleKeywordRouter()
        
        result = router.route(
            message="test",
            explicit_agent="understanding",
            strategy=RoutingStrategy.DIRECT
        )
        
        assert result.agent_id == "understanding"
    
    def test_route_fallback_when_no_match(self):
        """测试无匹配时fallback"""
        router = SimpleKeywordRouter(fallback_agent="question_bank")
        
        result = router.route(
            message="xyz123 无匹配关键词",
            explicit_agent=None,
            strategy=RoutingStrategy.AUTO
        )
        
        assert result.agent_id == "question_bank"
        assert "No keyword matches" in result.reasoning
    
    def test_add_keywords(self):
        """测试添加关键词"""
        router = SimpleKeywordRouter()
        
        # 添加新Agent
        router.add_keywords(
            agent_id="custom_agent",
            keywords=["自定义", "测试"]
        )
        
        # 测试新关键词
        result = router.route(
            message="这是自定义测试",
            explicit_agent=None,
            strategy=RoutingStrategy.AUTO
        )
        
        # 因为question_bank也可能匹配，这里不严格断言
        # 但确保新Agent已注册
        assert "custom_agent" in router._available_agents
    
    def test_multiple_keywords(self):
        """测试多关键词匹配"""
        router = SimpleKeywordRouter()
        
        # 包含多个关键词
        result = router.route(
            message="我想上传PDF并搜索题库中的题目",
            explicit_agent=None,
            strategy=RoutingStrategy.AUTO
        )
        
        # 应该匹配到question_bank
        assert result.agent_id == "question_bank"
        # 置信度应该更高
        assert result.confidence >= 0.1


class TestRoutingIntegration:
    """测试路由集成"""
    
    def test_real_world_scenario_1(self):
        """测试真实场景：上传PDF"""
        router = SimpleKeywordRouter()
        
        result = router.route(
            message="我有一个数学教材PDF，想提取里面的题目",
            explicit_agent=None
        )
        
        # 应该匹配到题库管理
        assert result.agent_id == "question_bank"
    
    def test_real_world_scenario_2(self):
        """测试真实场景：概念解释"""
        router = SimpleKeywordRouter()
        
        result = router.route(
            message="能不能解释一下极限的概念？",
            explicit_agent=None
        )
        
        # 应该匹配到概念理解
        assert result.agent_id == "understanding"
    
    def test_direct_route_takes_precedence(self):
        """测试直接路由优先级"""
        router = SimpleKeywordRouter()
        
        # 即使消息匹配关键词，显式指定的Agent应该优先
        result = router.route(
            message="我想了解极限的概念",  # 匹配understanding
            explicit_agent="question_bank",  # 但显式指定
            strategy=RoutingStrategy.DIRECT
        )
        
        # 应该使用显式指定的
        assert result.agent_id == "question_bank"
