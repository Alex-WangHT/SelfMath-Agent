"""
测试：Flask路由

测试 src/services/flask_routes.py
"""
import sys
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from src.services.flask_routes import create_app
from src.interface import (
    AgentResponse,
    AgentInfo,
    Question,
    QuestionStats,
    UploadResult,
    IAgentService,
)


class MockServiceForTest:
    """用于测试的Mock服务"""
    
    def chat(self, message, agent_type, conversation_id, context=None):
        return AgentResponse(
            content=f"Response to: {message}",
            agent_type=agent_type,
            conversation_id=conversation_id
        )
    
    def list_agents(self):
        return [
            AgentInfo(
                agent_id="question_bank",
                name="题库管理",
                description="Test",
                capabilities=["test"]
            )
        ]
    
    def get_agent_capabilities(self, agent_type):
        return ["test"]
    
    def process_pdf(self, file_path, options=None):
        return UploadResult(
            success=True,
            filename="test.pdf",
            original_filename="original.pdf",
            file_type="pdf",
            questions_extracted=2
        )
    
    def process_image(self, file_path, options=None):
        return UploadResult(
            success=True,
            filename="test.jpg",
            original_filename="original.jpg",
            file_type="image",
            questions_extracted=1
        )
    
    def get_all_questions(self, question_type=None, limit=100):
        return [
            Question(question_id="q1", content="Question 1", question_type="example"),
            Question(question_id="q2", content="Question 2", question_type="exercise"),
        ]
    
    def search_questions(self, query, n_results=10, question_type=None):
        return [
            Question(question_id="q1", content=f"Search result for: {query}", question_type="example")
        ]
    
    def get_question_stats(self):
        return QuestionStats(
            total=10,
            examples=3,
            exercises=7
        )
    
    def get_conversation(self, conversation_id):
        return None
    
    def clear_conversation(self, conversation_id):
        return True
    
    def is_agent_available(self, agent_type):
        return agent_type in ["question_bank", "understanding"]


@pytest.fixture
def client():
    """创建测试客户端"""
    mock_service = MockServiceForTest()
    app = create_app(agent_service=mock_service)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret-key"
    
    with app.test_client() as client:
        with app.app_context():
            yield client


class TestHealthCheck:
    """测试健康检查"""
    
    def test_health_check(self, client):
        """测试 /api/health"""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        
        data = response.get_json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["mode"] == "mock"
    
    def test_mode_endpoint(self, client):
        """测试 /api/mode"""
        response = client.get("/api/mode")
        
        assert response.status_code == 200
        
        data = response.get_json()
        assert data["mode"] == "mock"


class TestChatAPI:
    """测试聊天API"""
    
    def test_chat_valid_message(self, client):
        """测试有效消息"""
        response = client.post(
            "/api/chat",
            json={
                "message": "Hello",
                "agent_role": "question_bank"
            },
            content_type="application/json"
        )
        
        assert response.status_code == 200
        
        data = response.get_json()
        assert data["success"] is True
        assert "response" in data
        assert "Hello" in data["response"]
    
    def test_chat_empty_message(self, client):
        """测试空消息"""
        response = client.post(
            "/api/chat",
            json={"message": ""},
            content_type="application/json"
        )
        
        assert response.status_code == 400
        
        data = response.get_json()
        assert "error" in data
    
    def test_chat_no_message(self, client):
        """测试缺少消息"""
        response = client.post(
            "/api/chat",
            json={"agent_role": "question_bank"},
            content_type="application/json"
        )
        
        # 可能返回400或500，取决于实现
        assert response.status_code in [400, 500]


class TestQuestionAPI:
    """测试题库API"""
    
    def test_get_questions(self, client):
        """测试获取题目列表"""
        response = client.get("/api/questions")
        
        assert response.status_code == 200
        
        data = response.get_json()
        assert data["success"] is True
        assert "total" in data
        assert "questions" in data
        assert len(data["questions"]) == 2
    
    def test_get_questions_with_type(self, client):
        """测试按类型获取"""
        response = client.get("/api/questions?type=example")
        
        assert response.status_code == 200
        
        data = response.get_json()
        assert data["success"] is True
    
    def test_get_question_stats(self, client):
        """测试获取统计"""
        response = client.get("/api/questions/stats")
        
        assert response.status_code == 200
        
        data = response.get_json()
        assert data["success"] is True
        assert data["stats"]["total"] == 10
        assert data["stats"]["examples"] == 3
        assert data["stats"]["exercises"] == 7
    
    def test_search_questions(self, client):
        """测试搜索题目"""
        response = client.get("/api/questions/search?q=test")
        
        assert response.status_code == 200
        
        data = response.get_json()
        assert data["success"] is True
        assert data["query"] == "test"
        assert len(data["results"]) == 1
    
    def test_search_questions_no_query(self, client):
        """测试无查询搜索"""
        response = client.get("/api/questions/search")
        
        assert response.status_code == 400


class TestAgentsAPI:
    """测试Agent列表API"""
    
    def test_list_agents(self, client):
        """测试列出Agent"""
        response = client.get("/api/agents")
        
        assert response.status_code == 200
        
        data = response.get_json()
        assert data["success"] is True
        assert len(data["agents"]) == 1
        assert data["agents"][0]["agent_id"] == "question_bank"


class TestConversationAPI:
    """测试对话管理API"""
    
    def test_get_conversation(self, client):
        """测试获取对话"""
        response = client.get("/api/conversation")
        
        assert response.status_code == 200
        
        data = response.get_json()
        assert data["success"] is True
        assert "session_id" in data
        assert "history" in data
    
    def test_clear_conversation(self, client):
        """测试清除对话"""
        response = client.post("/api/conversation/clear")
        
        assert response.status_code == 200
        
        data = response.get_json()
        assert data["success"] is True


class TestErrorHandling:
    """测试错误处理"""
    
    def test_404(self, client):
        """测试404"""
        response = client.get("/api/nonexistent")
        
        assert response.status_code == 404
        
        data = response.get_json()
        assert "error" in data


class TestFileUpload:
    """测试文件上传"""
    
    def test_upload_pdf_no_file(self, client):
        """测试无文件上传"""
        response = client.post("/api/upload/pdf")
        
        assert response.status_code == 400
        
        data = response.get_json()
        assert "error" in data
    
    def test_upload_image_no_file(self, client):
        """测试无文件上传图片"""
        response = client.post("/api/upload/image")
        
        assert response.status_code == 400


class TestFlaskAppCreation:
    """测试Flask应用创建"""
    
    def test_create_app_without_service(self):
        """测试不提供service时创建应用"""
        # 这会使用默认的MockService
        app = create_app()
        
        assert app is not None
        assert hasattr(app, 'agent_service')
    
    def test_create_app_with_service(self):
        """测试提供service时创建应用"""
        mock_service = MockServiceForTest()
        app = create_app(agent_service=mock_service)
        
        assert app is not None
        assert app.agent_service is mock_service


class TestIntegration:
    """集成测试"""
    
    def test_full_flow(self, client):
        """测试完整流程"""
        # 1. 健康检查
        resp1 = client.get("/api/health")
        assert resp1.status_code == 200
        
        # 2. 发送消息
        resp2 = client.post(
            "/api/chat",
            json={"message": "Test message", "agent_role": "question_bank"},
            content_type="application/json"
        )
        assert resp2.status_code == 200
        
        # 3. 获取题目统计
        resp3 = client.get("/api/questions/stats")
        assert resp3.status_code == 200
        
        # 4. 列出Agent
        resp4 = client.get("/api/agents")
        assert resp4.status_code == 200
        
        # 5. 清除对话
        resp5 = client.post("/api/conversation/clear")
        assert resp5.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
