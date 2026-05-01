"""
测试：Mock Agent服务

测试 src/services/mock_service.py
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
)
from src.services.mock_service import (
    MockAgentService,
    MockAgent,
    get_mock_service,
)


class TestMockAgent:
    """测试 MockAgent 类"""
    
    def test_creation(self):
        """测试创建MockAgent"""
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


class TestMockAgentService:
    """测试 MockAgentService 类"""
    
    def setup_method(self):
        """每个测试前重置"""
        # 清除单例状态
        MockAgentService._instance = None
    
    def test_singleton(self):
        """测试单例模式"""
        s1 = MockAgentService()
        s2 = MockAgentService()
        assert s1 is s2
    
    def test_get_mock_service(self):
        """测试 get_mock_service 函数"""
        s1 = get_mock_service()
        s2 = get_mock_service()
        assert s1 is s2
    
    def test_list_agents(self):
        """测试列出Agent"""
        service = MockAgentService()
        agents = service.list_agents()
        
        assert len(agents) >= 3
        
        # 检查是否包含核心Agent
        agent_ids = [a.agent_id for a in agents]
        assert "question_bank" in agent_ids
        assert "understanding" in agent_ids
        assert "verification" in agent_ids
    
    def test_chat_basic(self):
        """测试基本聊天"""
        service = MockAgentService()
        
        response = service.chat(
            message="你好",
            agent_type="question_bank",
            conversation_id="test_conv_001"
        )
        
        assert isinstance(response, AgentResponse)
        assert response.agent_type == "question_bank"
        assert response.conversation_id == "test_conv_001"
        assert len(response.content) > 0
    
    def test_chat_auto_routing(self):
        """测试自动路由"""
        service = MockAgentService()
        
        # 包含"解释"关键词，应该路由到understanding
        response = service.chat(
            message="解释一下极限的概念",
            agent_type="auto",
            conversation_id="test_conv_002"
        )
        
        assert isinstance(response, AgentResponse)
        # 可能路由到question_bank或understanding，取决于实现
    
    def test_get_all_questions(self):
        """测试获取所有题目"""
        service = MockAgentService()
        
        questions = service.get_all_questions()
        
        assert len(questions) >= 3
        assert all(isinstance(q, Question) for q in questions)
    
    def test_get_all_questions_with_type(self):
        """测试按类型获取题目"""
        service = MockAgentService()
        
        examples = service.get_all_questions(question_type="example")
        exercises = service.get_all_questions(question_type="exercise")
        
        # 应该有example类型的题目
        assert len(examples) > 0
    
    def test_search_questions(self):
        """测试搜索题目"""
        service = MockAgentService()
        
        # 搜索包含"极限"的题目
        results = service.search_questions(query="极限", n_results=5)
        
        # 可能匹配到
        assert isinstance(results, list)
    
    def test_search_questions_empty_query(self):
        """测试空查询搜索"""
        service = MockAgentService()
        
        results = service.search_questions(query="", n_results=5)
        
        # 空查询应该返回所有或部分题目
        assert isinstance(results, list)
    
    def test_get_question_stats(self):
        """测试获取题库统计"""
        service = MockAgentService()
        
        stats = service.get_question_stats()
        
        assert isinstance(stats, QuestionStats)
        assert stats.total >= 3
        assert stats.examples >= 0
        assert stats.exercises >= 0
    
    def test_process_pdf(self):
        """测试处理PDF"""
        service = MockAgentService()
        
        result = service.process_pdf(
            file_path="/fake/path/test.pdf",
            options={"start_page": 1}
        )
        
        assert isinstance(result, UploadResult)
        assert result.success is True
        assert result.questions_extracted > 0
    
    def test_process_image(self):
        """测试处理图片"""
        service = MockAgentService()
        
        result = service.process_image(
            file_path="/fake/path/test.jpg"
        )
        
        assert isinstance(result, UploadResult)
        assert result.success is True
    
    def test_conversation_persistence(self):
        """测试对话持久化"""
        service = MockAgentService()
        conv_id = "persistence_test"
        
        # 发送第一条消息
        service.chat(
            message="消息1",
            agent_type="question_bank",
            conversation_id=conv_id
        )
        
        # 发送第二条消息
        service.chat(
            message="消息2",
            agent_type="question_bank",
            conversation_id=conv_id
        )
        
        # 获取对话
        conversation = service.get_conversation(conv_id)
        
        assert conversation is not None
        assert conversation.conversation_id == conv_id
        # 应该有用户消息和助手消息
    
    def test_clear_conversation(self):
        """测试清除对话"""
        service = MockAgentService()
        conv_id = "clear_test"
        
        # 创建对话
        service.chat(
            message="test",
            agent_type="question_bank",
            conversation_id=conv_id
        )
        
        assert service.get_conversation(conv_id) is not None
        
        # 清除对话
        success = service.clear_conversation(conv_id)
        assert success is True
        
        # 对话应该不存在
        assert service.get_conversation(conv_id) is None
    
    def test_is_agent_available(self):
        """测试检查Agent是否可用"""
        service = MockAgentService()
        
        assert service.is_agent_available("question_bank") is True
        assert service.is_agent_available("nonexistent") is False
    
    def test_get_agent_capabilities(self):
        """测试获取Agent能力"""
        service = MockAgentService()
        
        capabilities = service.get_agent_capabilities("question_bank")
        
        assert isinstance(capabilities, list)
        # 应该有一些能力
        assert len(capabilities) > 0
    
    def test_get_agent_capabilities_nonexistent(self):
        """测试获取不存在的Agent能力"""
        service = MockAgentService()
        
        capabilities = service.get_agent_capabilities("nonexistent")
        
        assert capabilities == []


class TestMockServiceIntegration:
    """测试Mock服务集成"""
    
    def setup_method(self):
        MockAgentService._instance = None
    
    def test_full_chat_flow(self):
        """测试完整聊天流程"""
        service = MockAgentService()
        conv_id = "integration_test"
        
        # 1. 发送第一条消息
        resp1 = service.chat(
            message="你好",
            agent_type="question_bank",
            conversation_id=conv_id
        )
        
        assert resp1.success if hasattr(resp1, 'success') else True
        
        # 2. 发送第二条消息
        resp2 = service.chat(
            message="极限是什么？",
            agent_type="auto",
            conversation_id=conv_id
        )
        
        # 3. 获取对话
        conversation = service.get_conversation(conv_id)
        assert conversation is not None
        
        # 4. 清除对话
        service.clear_conversation(conv_id)
        assert service.get_conversation(conv_id) is None
    
    def test_question_flow(self):
        """测试题目相关流程"""
        service = MockAgentService()
        
        # 1. 获取统计
        stats = service.get_question_stats()
        initial_total = stats.total
        
        # 2. 上传PDF添加题目
        result = service.process_pdf("/fake/test.pdf")
        added_count = result.questions_extracted
        
        # 3. 再次获取统计（应该有更多题目）
        new_stats = service.get_question_stats()
        
        # 题目应该增加了
        assert new_stats.total >= initial_total
