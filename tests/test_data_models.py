"""
测试：数据模型

测试 src/interface/data_models.py 中的所有数据类。
"""
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from src.interface import (
    AgentResponse,
    AgentInfo,
    AgentDescriptor,
    RouteResult,
    Question,
    QuestionStats,
    UploadResult,
    ChatMessage,
    Conversation,
    AgentStatus,
    QuestionType,
    RoutingStrategy,
)


class TestAgentStatus:
    """测试 AgentStatus 枚举"""
    
    def test_enum_values(self):
        assert AgentStatus.ACTIVE.value == "active"
        assert AgentStatus.DISABLED.value == "disabled"
        assert AgentStatus.MAINTENANCE.value == "maintenance"


class TestQuestionType:
    """测试 QuestionType 枚举"""
    
    def test_enum_values(self):
        assert QuestionType.EXAMPLE.value == "example"
        assert QuestionType.EXERCISE.value == "exercise"
        assert QuestionType.UNKNOWN.value == "unknown"


class TestRoutingStrategy:
    """测试 RoutingStrategy 枚举"""
    
    def test_enum_values(self):
        assert RoutingStrategy.DIRECT.value == "direct"
        assert RoutingStrategy.AUTO.value == "auto"
        assert RoutingStrategy.ORCHESTRATED.value == "orchestrated"
        assert RoutingStrategy.FALLBACK.value == "fallback"


class TestChatMessage:
    """测试 ChatMessage 数据类"""
    
    def test_default_values(self):
        msg = ChatMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.metadata == {}
    
    def test_custom_metadata(self):
        msg = ChatMessage(
            role="assistant",
            content="Hi there",
            metadata={"agent_type": "question_bank"}
        )
        assert msg.metadata["agent_type"] == "question_bank"


class TestConversation:
    """测试 Conversation 数据类"""
    
    def test_default_values(self):
        conv = Conversation(conversation_id="test_conv_123")
        assert conv.conversation_id == "test_conv_123"
        assert conv.messages == []
    
    def test_add_message(self):
        conv = Conversation(conversation_id="test")
        conv.messages.append(ChatMessage(role="user", content="Hello"))
        assert len(conv.messages) == 1
        assert conv.messages[0].content == "Hello"


class TestAgentResponse:
    """测试 AgentResponse 数据类"""
    
    def test_creation(self):
        resp = AgentResponse(
            content="This is a response",
            agent_type="question_bank",
            conversation_id="test_conv"
        )
        assert resp.content == "This is a response"
        assert resp.agent_type == "question_bank"
        assert resp.conversation_id == "test_conv"
    
    def test_to_dict(self):
        resp = AgentResponse(
            content="Test",
            agent_type="test",
            conversation_id="conv1",
            metadata={"key": "value"}
        )
        result = resp.to_dict()
        assert result["content"] == "Test"
        assert result["agent_type"] == "test"
        assert result["metadata"]["key"] == "value"


class TestAgentInfo:
    """测试 AgentInfo 数据类"""
    
    def test_creation(self):
        info = AgentInfo(
            agent_id="question_bank",
            name="题库管理Agent",
            description="处理PDF和题目",
            capabilities=["pdf_process", "image_ocr"]
        )
        assert info.agent_id == "question_bank"
        assert info.name == "题库管理Agent"
        assert info.capabilities == ["pdf_process", "image_ocr"]
    
    def test_to_dict(self):
        info = AgentInfo(
            agent_id="test",
            name="Test Agent",
            description="Test",
            capabilities=["test"],
            icon="bi-test",
            status="active"
        )
        result = info.to_dict()
        assert result["agent_id"] == "test"
        assert result["name"] == "Test Agent"
        assert result["icon"] == "bi-test"


class TestAgentDescriptor:
    """测试 AgentDescriptor 数据类"""
    
    def test_creation(self):
        desc = AgentDescriptor(
            agent_id="test_agent",
            name="Test Agent",
            description="Test description",
            capabilities=["cap1", "cap2"],
            dependencies=["langchain"],
            enabled=True,
            priority=100
        )
        assert desc.agent_id == "test_agent"
        assert desc.name == "Test Agent"
        assert desc.capabilities == ["cap1", "cap2"]
        assert desc.dependencies == ["langchain"]
        assert desc.enabled is True
    
    def test_is_available(self):
        desc = AgentDescriptor(
            agent_id="test",
            name="Test",
            description="Test"
        )
        assert desc.is_available() is True
        
        desc.enabled = False
        assert desc.is_available() is False


class TestRouteResult:
    """测试 RouteResult 数据类"""
    
    def test_creation(self):
        result = RouteResult(
            agent_id="question_bank",
            confidence=0.8,
            reasoning="Matched keywords",
            metadata={"strategy": "auto"}
        )
        assert result.agent_id == "question_bank"
        assert result.confidence == 0.8
        assert result.reasoning == "Matched keywords"
    
    def test_to_dict(self):
        result = RouteResult(
            agent_id="test",
            confidence=1.0,
            reasoning="Test"
        )
        data = result.to_dict()
        assert data["agent_id"] == "test"
        assert data["confidence"] == 1.0


class TestQuestion:
    """测试 Question 数据类"""
    
    def test_creation(self):
        q = Question(
            question_id="q001",
            content="求极限 $\\lim_{x \\to 0} \\frac{\\sin x}{x}$",
            question_type=QuestionType.EXAMPLE.value,
            metadata={"page": 1, "source": "高等数学"}
        )
        assert q.question_id == "q001"
        assert q.content.startswith("求极限")
        assert q.question_type == "example"
    
    def test_to_dict(self):
        q = Question(
            question_id="q1",
            content="Test question",
            question_type="exercise"
        )
        data = q.to_dict()
        assert data["question_id"] == "q1"
        assert data["content"] == "Test question"


class TestQuestionStats:
    """测试 QuestionStats 数据类"""
    
    def test_creation(self):
        stats = QuestionStats(
            total=100,
            examples=30,
            exercises=70,
            sources=["高等数学", "线性代数"]
        )
        assert stats.total == 100
        assert stats.examples == 30
        assert stats.exercises == 70
        assert stats.sources == ["高等数学", "线性代数"]
    
    def test_to_dict(self):
        stats = QuestionStats(total=10, examples=3, exercises=7)
        data = stats.to_dict()
        assert data["total"] == 10
        assert data["examples"] == 3


class TestUploadResult:
    """测试 UploadResult 数据类"""
    
    def test_success_result(self):
        result = UploadResult(
            success=True,
            filename="test.pdf",
            original_filename="original.pdf",
            file_type="pdf",
            questions_extracted=5
        )
        assert result.success is True
        assert result.filename == "test.pdf"
        assert result.questions_extracted == 5
    
    def test_error_result(self):
        result = UploadResult(
            success=False,
            error_message="File not found"
        )
        assert result.success is False
        assert result.error_message == "File not found"
    
    def test_to_dict(self):
        result = UploadResult(
            success=True,
            filename="test.pdf",
            questions_extracted=2,
            questions=[
                Question(question_id="q1", content="Q1", question_type="example"),
                Question(question_id="q2", content="Q2", question_type="exercise"),
            ]
        )
        data = result.to_dict()
        assert data["success"] is True
        assert data["questions_extracted"] == 2
        assert len(data["questions"]) == 2
