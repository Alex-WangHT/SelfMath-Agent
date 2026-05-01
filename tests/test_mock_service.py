"""
测试：AgentService 桥接器

测试 src/interface/agent_service.py （核心桥接器）
和 src/agents/mock_agents.py （具体实现）
"""
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from src.interface import (
    AgentResponse,
    AgentInfo,
    Question,
    QuestionStats,
    UploadResult,
    QuestionType,
    AgentService,
    get_service,
    AgentRegistry,
    get_registry,
)
from src.agents.mock_agents import MockAgent


class TestMockAgent:
    """测试 MockAgent 具体实现"""
    
    def test_creation(self):
        """测试创建 MockAgent"""
        agent = MockAgent(
            agent_id="test_agent",
            name="Test Agent",
            description="Test description"
        )
        
        assert agent.agent_id == "test_agent"
        assert agent.name == "Test Agent"
        assert agent.description == "Test description"
    
    def test_chat_keyword_limit(self):
        """测试聊天 - 极限关键词"""
        agent = MockAgent(
            agent_id="test",
            name="Test",
            description="Test"
        )
        
        result = agent.chat("极限是什么？")
        
        assert "极限" in result["content"]
        assert "lim" in result["content"].lower()
    
    def test_chat_keyword_integral(self):
        """测试聊天 - 积分关键词"""
        agent = MockAgent(
            agent_id="test",
            name="Test",
            description="Test"
        )
        
        result = agent.chat("积分是什么？")
        
        assert "积分" in result["content"]
        assert "int" in result["content"].lower()
    
    def test_chat_keyword_derivative(self):
        """测试聊天 - 导数关键词"""
        agent = MockAgent(
            agent_id="test",
            name="Test",
            description="Test"
        )
        
        result = agent.chat("导数怎么求？")
        
        assert "导数" in result["content"]
    
    def test_chat_hello(self):
        """测试聊天 - 你好"""
        agent = MockAgent(
            agent_id="test",
            name="Test",
            description="Test"
        )
        
        result = agent.chat("你好")
        
        assert "你好" in result["content"] or "学习助手" in result["content"]
    
    def test_chat_default(self):
        """测试聊天 - 默认响应"""
        agent = MockAgent(
            agent_id="test",
            name="Test Agent",
            description="Test"
        )
        
        result = agent.chat("这是一个测试消息，没有匹配任何关键词")
        
        assert "Test Agent" in result["content"] or "mock" in result["content"].lower()


class TestAgentService:
    """测试 AgentService 桥接器"""
    
    def setup_method(self):
        """每个测试前重置"""
        AgentService._instance = None
        registry = get_registry()
        registry.clear()
    
    def test_singleton(self):
        """测试单例模式"""
        s1 = AgentService(use_mock=False)
        s2 = AgentService(use_mock=False)
        assert s1 is s2
    
    def test_get_service(self):
        """测试 get_service 工厂函数"""
        s1 = get_service(use_mock=True)
        s2 = get_service(use_mock=True)
        assert s1 is s2
    
    def test_init_mock_agents(self):
        """测试初始化 Mock Agent"""
        service = AgentService(use_mock=True)
        service.init_mock_agents()
        
        agents = service.list_agents()
        assert len(agents) >= 3
        
        agent_ids = [a.agent_id for a in agents]
        assert "question_bank" in agent_ids
        assert "understanding" in agent_ids
        assert "verification" in agent_ids
    
    def test_chat_basic(self):
        """测试基本聊天"""
        service = AgentService(use_mock=True)
        service.init_mock_agents()
        
        response = service.chat(
            message="你好",
            agent_type="question_bank",
            conversation_id="test_conv_001"
        )
        
        assert isinstance(response, AgentResponse)
        assert response.agent_type == "question_bank"
        assert response.conversation_id == "test_conv_001"
        assert len(response.content) > 0
    
    def test_get_all_questions(self):
        """测试获取所有题目"""
        service = AgentService(use_mock=True)
        service.init_mock_agents()
        
        questions = service.get_all_questions()
        
        assert len(questions) >= 3
        assert all(isinstance(q, Question) for q in questions)
    
    def test_get_question_stats(self):
        """测试获取题库统计"""
        service = AgentService(use_mock=True)
        service.init_mock_agents()
        
        stats = service.get_question_stats()
        
        assert isinstance(stats, QuestionStats)
        assert stats.total >= 3
        assert stats.examples >= 0
        assert stats.exercises >= 0
    
    def test_process_pdf(self):
        """测试处理 PDF"""
        service = AgentService(use_mock=True)
        service.init_mock_agents()
        
        result = service.process_pdf(
            file_path="/fake/path/test.pdf",
            options={"start_page": 1}
        )
        
        assert isinstance(result, UploadResult)
        assert result.success is True
        assert result.questions_extracted > 0
    
    def test_process_image(self):
        """测试处理图片"""
        service = AgentService(use_mock=True)
        service.init_mock_agents()
        
        result = service.process_image(
            file_path="/fake/path/test.jpg"
        )
        
        assert isinstance(result, UploadResult)
        assert result.success is True
    
    def test_conversation_persistence(self):
        """测试对话持久化"""
        service = AgentService(use_mock=True)
        service.init_mock_agents()
        conv_id = "persistence_test"
        
        service.chat(
            message="消息1",
            agent_type="question_bank",
            conversation_id=conv_id
        )
        
        service.chat(
            message="消息2",
            agent_type="question_bank",
            conversation_id=conv_id
        )
        
        conversation = service.get_conversation(conv_id)
        
        assert conversation is not None
        assert conversation.conversation_id == conv_id
    
    def test_clear_conversation(self):
        """测试清除对话"""
        service = AgentService(use_mock=True)
        service.init_mock_agents()
        conv_id = "clear_test"
        
        service.chat(
            message="test",
            agent_type="question_bank",
            conversation_id=conv_id
        )
        
        assert service.get_conversation(conv_id) is not None
        
        success = service.clear_conversation(conv_id)
        assert success is True
        
        assert service.get_conversation(conv_id) is None
    
    def test_is_agent_available(self):
        """测试检查 Agent 是否可用"""
        service = AgentService(use_mock=True)
        service.init_mock_agents()
        
        assert service.is_agent_available("question_bank") is True
        assert service.is_agent_available("nonexistent") is False
    
    def test_get_agent_capabilities(self):
        """测试获取 Agent 能力"""
        service = AgentService(use_mock=True)
        service.init_mock_agents()
        
        capabilities = service.get_agent_capabilities("question_bank")
        
        assert isinstance(capabilities, list)
        assert len(capabilities) > 0
    
    def test_get_agent_capabilities_nonexistent(self):
        """测试获取不存在的 Agent 能力"""
        service = AgentService(use_mock=True)
        service.init_mock_agents()
        
        capabilities = service.get_agent_capabilities("nonexistent")
        
        assert capabilities == []


class TestAgentServiceIntegration:
    """测试 AgentService 集成"""
    
    def setup_method(self):
        AgentService._instance = None
        registry = get_registry()
        registry.clear()
    
    def test_full_chat_flow(self):
        """测试完整聊天流程"""
        service = AgentService(use_mock=True)
        service.init_mock_agents()
        conv_id = "integration_test"
        
        resp1 = service.chat(
            message="你好",
            agent_type="question_bank",
            conversation_id=conv_id
        )
        
        assert isinstance(resp1, AgentResponse)
        
        resp2 = service.chat(
            message="极限是什么？",
            agent_type="auto",
            conversation_id=conv_id
        )
        
        assert isinstance(resp2, AgentResponse)
        
        conversation = service.get_conversation(conv_id)
        assert conversation is not None
        
        service.clear_conversation(conv_id)
        assert service.get_conversation(conv_id) is None
    
    def test_question_flow(self):
        """测试题目相关流程"""
        service = AgentService(use_mock=True)
        service.init_mock_agents()
        
        stats = service.get_question_stats()
        initial_total = stats.total
        
        result = service.process_pdf("/fake/test.pdf")
        added_count = result.questions_extracted
        
        new_stats = service.get_question_stats()
        
        assert new_stats.total >= initial_total
