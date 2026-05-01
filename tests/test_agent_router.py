"""
测试：AgentRouter 桥接器

测试 src/interface/agent_router.py （桥接器层）
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from src.interface import (
    RoutingStrategy,
    RouteResult,
    AgentRouter,
    SimpleKeywordRouter,
    get_router,
    get_registry,
    register_agent,
)


class TestAgentRouter:
    """测试 AgentRouter 桥接器"""
    
    def setup_method(self):
        """每个测试前清空注册中心"""
        registry = get_registry()
        registry.clear()
        
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
    
    def test_creation(self):
        """测试创建路由器"""
        router = AgentRouter()
        assert router is not None
    
    def test_get_router(self):
        """测试 get_router 工厂函数"""
        router = get_router()
        assert isinstance(router, SimpleKeywordRouter)
    
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


class TestSimpleKeywordRouter:
    """测试 SimpleKeywordRouter 桥接器"""
    
    def setup_method(self):
        """每个测试前清空注册中心"""
        registry = get_registry()
        registry.clear()
        
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
    
    def test_creation(self):
        """测试创建关键词路由器"""
        router = SimpleKeywordRouter()
        assert router is not None
    
    def test_route_with_keyword(self):
        """测试关键词路由"""
        router = SimpleKeywordRouter()
        
        result = router.route(
            message="我想上传PDF题库",
            explicit_agent=None
        )
        
        assert result.agent_id == "question_bank"
    
    def test_route_with_explicit_agent(self):
        """测试显式指定 Agent"""
        router = SimpleKeywordRouter()
        
        result = router.route(
            message="test",
            explicit_agent="understanding",
            strategy=RoutingStrategy.DIRECT
        )
        
        assert result.agent_id == "understanding"
    
    def test_route_fallback_when_no_match(self):
        """测试无匹配时 fallback"""
        router = SimpleKeywordRouter()
        
        result = router.route(
            message="xyz123 无匹配关键词",
            explicit_agent=None
        )
        
        # 应该有一个默认值
        assert result.agent_id is not None
        assert len(result.agent_id) > 0
    
    def test_add_rule(self):
        """测试添加路由规则"""
        router = SimpleKeywordRouter()
        
        router.add_rule(
            agent_id="custom_agent",
            keywords=["自定义", "测试"],
            confidence=0.85,
            reasoning="Custom test rule"
        )
        
        # 验证规则已添加（间接测试）
        registry = get_registry()
        register_agent(
            agent_id="custom_agent",
            name="Custom Agent",
            description="Test"
        )
        
        result = router.route(
            message="这是自定义测试",
            explicit_agent=None
        )
        
        # 可能匹配到 custom_agent 或其他，但至少有结果
        assert result.agent_id is not None
    
    def test_multiple_keywords(self):
        """测试多关键词匹配"""
        router = SimpleKeywordRouter()
        
        result = router.route(
            message="我想上传PDF并搜索题库中的题目",
            explicit_agent=None
        )
        
        assert result.agent_id == "question_bank"


class TestRoutingIntegration:
    """测试路由集成"""
    
    def setup_method(self):
        """每个测试前清空注册中心"""
        registry = get_registry()
        registry.clear()
        
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
        register_agent(
            agent_id="verification",
            name="答案验证",
            description="Test"
        )
        register_agent(
            agent_id="planning",
            name="学习规划",
            description="Test"
        )
        register_agent(
            agent_id="assessment",
            name="能力评估",
            description="Test"
        )
    
    def test_real_world_scenario_pdf(self):
        """测试真实场景：上传 PDF"""
        router = SimpleKeywordRouter()
        
        result = router.route(
            message="我有一个数学教材PDF，想提取里面的题目",
            explicit_agent=None
        )
        
        assert result.agent_id == "question_bank"
    
    def test_real_world_scenario_concept(self):
        """测试真实场景：概念解释"""
        router = SimpleKeywordRouter()
        
        result = router.route(
            message="能不能解释一下极限的概念？",
            explicit_agent=None
        )
        
        assert result.agent_id == "understanding"
    
    def test_real_world_scenario_verification(self):
        """测试真实场景：答案验证"""
        router = SimpleKeywordRouter()
        
        result = router.route(
            message="这个答案对吗？",
            explicit_agent=None
        )
        
        assert result.agent_id == "verification"
    
    def test_direct_route_takes_precedence(self):
        """测试直接路由优先级"""
        router = SimpleKeywordRouter()
        
        result = router.route(
            message="我想了解极限的概念",
            explicit_agent="question_bank",
            strategy=RoutingStrategy.DIRECT
        )
        
        assert result.agent_id == "question_bank"
    
    def test_route_result_to_dict(self):
        """测试路由结果转换为字典"""
        router = SimpleKeywordRouter()
        
        result = router.route(
            message="测试",
            explicit_agent="question_bank",
            strategy=RoutingStrategy.DIRECT
        )
        
        result_dict = result.to_dict()
        assert "agent_id" in result_dict
        assert "confidence" in result_dict
        assert "reasoning" in result_dict
