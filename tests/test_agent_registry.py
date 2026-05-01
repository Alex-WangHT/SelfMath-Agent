"""
测试：AgentRegistry 桥接器

测试 src/interface/agent_registry.py （桥接器层）
"""
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from src.interface import (
    AgentRegistry,
    get_registry,
    register_agent,
)


class TestAgentRegistry:
    """测试 AgentRegistry 桥接器"""
    
    def setup_method(self):
        """每个测试前清空注册中心"""
        registry = get_registry()
        registry.clear()
    
    def test_singleton(self):
        """测试单例模式"""
        r1 = AgentRegistry()
        r2 = AgentRegistry()
        assert r1 is r2
    
    def test_get_registry(self):
        """测试 get_registry 工厂函数"""
        r1 = get_registry()
        r2 = get_registry()
        assert r1 is r2
    
    def test_register_agent(self):
        """测试注册 Agent"""
        registry = get_registry()
        
        registry.register(
            agent_id="test_agent",
            name="Test Agent",
            description="Test description",
            capabilities=["cap1", "cap2"],
            priority=100
        )
        
        desc = registry.get_descriptor("test_agent")
        assert desc is not None
        assert desc.agent_id == "test_agent"
        assert desc.name == "Test Agent"
        assert desc.capabilities == ["cap1", "cap2"]
    
    def test_register_agent_function(self):
        """测试 register_agent 便捷函数"""
        desc = register_agent(
            agent_id="conv_agent",
            name="Convenience Agent",
            description="Test",
            capabilities=["test"]
        )
        
        assert desc.agent_id == "conv_agent"
        assert desc.name == "Convenience Agent"
    
    def test_unregister(self):
        """测试注销 Agent"""
        registry = get_registry()
        
        registry.register(
            agent_id="to_remove",
            name="To Remove",
            description="Test"
        )
        
        assert registry.get_descriptor("to_remove") is not None
        
        result = registry.unregister("to_remove")
        assert result is True
        
        assert registry.get_descriptor("to_remove") is None
    
    def test_unregister_nonexistent(self):
        """测试注销不存在的 Agent"""
        registry = get_registry()
        result = registry.unregister("nonexistent")
        assert result is False
    
    def test_list_agents(self):
        """测试列出 Agent"""
        registry = get_registry()
        
        registry.register(
            agent_id="agent1",
            name="Agent 1",
            description="Test",
            priority=50
        )
        
        registry.register(
            agent_id="agent2",
            name="Agent 2",
            description="Test",
            priority=100
        )
        
        agents = registry.list_agents()
        assert len(agents) == 2
    
    def test_list_agents_include_disabled(self):
        """测试包含禁用的 Agent"""
        registry = get_registry()
        
        registry.register(
            agent_id="enabled_agent",
            name="Enabled",
            description="Test",
            enabled=True
        )
        
        registry.register(
            agent_id="disabled_agent",
            name="Disabled",
            description="Test",
            enabled=False
        )
        
        agents_enabled = registry.list_agents(include_disabled=False)
        assert len(agents_enabled) == 1
        assert agents_enabled[0].agent_id == "enabled_agent"
        
        agents_all = registry.list_agents(include_disabled=True)
        assert len(agents_all) == 2
    
    def test_list_agent_info(self):
        """测试列出 Agent 信息（用于前端）"""
        registry = get_registry()
        
        registry.register(
            agent_id="question_bank",
            name="题库管理Agent",
            description="处理PDF",
            capabilities=["pdf_process"]
        )
        
        infos = registry.list_agent_info()
        assert len(infos) == 1
        
        info = infos[0]
        assert info.agent_id == "question_bank"
        assert info.name == "题库管理Agent"
        assert info.capabilities == ["pdf_process"]
    
    def test_find_by_capability(self):
        """测试根据能力查找 Agent"""
        registry = get_registry()
        
        registry.register(
            agent_id="pdf_agent",
            name="PDF Agent",
            description="Test",
            capabilities=["pdf_process", "image_ocr"]
        )
        
        registry.register(
            agent_id="search_agent",
            name="Search Agent",
            description="Test",
            capabilities=["question_search"]
        )
        
        results = registry.find_by_capability("pdf_process")
        assert len(results) == 1
        assert results[0].agent_id == "pdf_agent"
        
        results2 = registry.find_by_capability("nonexistent")
        assert len(results2) == 0
    
    def test_is_available(self):
        """测试检查 Agent 是否可用"""
        registry = get_registry()
        
        registry.register(
            agent_id="available",
            name="Available",
            description="Test",
            enabled=True
        )
        
        registry.register(
            agent_id="unavailable",
            name="Unavailable",
            description="Test",
            enabled=False
        )
        
        assert registry.is_available("available") is True
        assert registry.is_available("unavailable") is False
        assert registry.is_available("nonexistent") is False
    
    def test_enable_disable(self):
        """测试启用/禁用 Agent"""
        registry = get_registry()
        
        registry.register(
            agent_id="test_agent",
            name="Test",
            description="Test",
            enabled=True
        )
        
        assert registry.is_available("test_agent") is True
        
        registry.disable("test_agent")
        assert registry.is_available("test_agent") is False
        
        registry.enable("test_agent")
        assert registry.is_available("test_agent") is True
    
    def test_enable_disable_nonexistent(self):
        """测试启用/禁用不存在的 Agent"""
        registry = get_registry()
        
        assert registry.enable("nonexistent") is False
        assert registry.disable("nonexistent") is False
    
    def test_get_with_factory(self):
        """测试使用工厂函数获取 Agent 实例"""
        registry = get_registry()
        
        class MockAgent:
            def __init__(self):
                self.value = "test"
            
            def chat(self, message, **kwargs):
                return {"content": f"Got: {message}"}
        
        factory_called = [False]
        
        def mock_factory():
            factory_called[0] = True
            return MockAgent()
        
        registry.register(
            agent_id="factory_agent",
            name="Factory Agent",
            description="Test",
            factory=mock_factory
        )
        
        instance = registry.get("factory_agent")
        assert factory_called[0] is True
        assert isinstance(instance, MockAgent)
        assert instance.value == "test"
        
        factory_called[0] = False
        instance2 = registry.get("factory_agent")
        assert instance is instance2
        assert factory_called[0] is False
    
    def test_get_nonexistent(self):
        """测试获取不存在的 Agent"""
        registry = get_registry()
        instance = registry.get("nonexistent")
        assert instance is None
    
    def test_clear(self):
        """测试清空注册中心"""
        registry = get_registry()
        
        registry.register(
            agent_id="agent1",
            name="Agent 1",
            description="Test"
        )
        
        registry.register(
            agent_id="agent2",
            name="Agent 2",
            description="Test"
        )
        
        assert len(registry.list_agents()) == 2
        
        registry.clear()
        
        assert len(registry.list_agents()) == 0
