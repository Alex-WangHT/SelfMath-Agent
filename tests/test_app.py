"""
Web界面单元测试
测试Flask应用的所有API端点，使用MockAgentManager确保与真实Agent解耦
"""
import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ["USE_MOCK_AGENTS"] = "True"
os.environ["FLASK_SECRET_KEY"] = "test-secret-key-for-unit-testing"

import importlib.util

mock_path = Path(__file__).parent.parent / "src" / "agents" / "mock_agent_manager.py"
spec = importlib.util.spec_from_file_location("mock_agent_manager", str(mock_path))
mock_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mock_module)

MockAgentManager = mock_module.MockAgentManager
get_agent_manager = mock_module.get_agent_manager

sys.modules["src.agents.mock_agent_manager"] = mock_module

app_path = Path(__file__).parent.parent / "app.py"
spec = importlib.util.spec_from_file_location("app", str(app_path))
flask_app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(flask_app)


@pytest.fixture
def client():
    flask_app.app.config["TESTING"] = True
    flask_app.app.config["SECRET_KEY"] = "test-secret-key"
    
    with flask_app.app.test_client() as client:
        with flask_app.app.app_context():
            yield client


class TestHealthCheck:
    """健康检查测试"""
    
    def test_health_check_returns_200(self, client):
        """测试健康检查接口返回200"""
        response = client.get("/api/health")
        assert response.status_code == 200
    
    def test_health_check_contains_status(self, client):
        """测试健康检查返回状态信息"""
        response = client.get("/api/health")
        data = json.loads(response.data)
        
        assert "status" in data
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "mode" in data
        assert data["mode"] == "mock"
    
    def test_mode_endpoint(self, client):
        """测试模式检查端点"""
        response = client.get("/api/mode")
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["mode"] == "mock"


class TestHomepage:
    """主页测试"""
    
    def test_homepage_returns_200(self, client):
        """测试主页返回200"""
        response = client.get("/")
        assert response.status_code == 200
    
    def test_homepage_contains_html(self, client):
        """测试主页返回HTML内容"""
        response = client.get("/")
        content_type = response.headers.get("Content-Type", "")
        assert "text/html" in content_type


class TestChatAPI:
    """聊天API测试"""
    
    def test_chat_with_valid_message(self, client):
        """测试有效消息的聊天"""
        response = client.post(
            "/api/chat",
            json={
                "message": "你好",
                "agent_role": "question_bank"
            },
            content_type="application/json"
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data["success"] is True
        assert "response" in data
        assert "agent_role" in data
        assert "mode" in data
        assert data["mode"] == "mock"
    
    def test_chat_with_empty_message(self, client):
        """测试空消息返回错误"""
        response = client.post(
            "/api/chat",
            json={"message": ""},
            content_type="application/json"
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
    
    def test_chat_without_message(self, client):
        """测试缺少message字段"""
        response = client.post(
            "/api/chat",
            json={"agent_role": "question_bank"},
            content_type="application/json"
        )
        
        assert response.status_code == 400
    
    def test_chat_with_limit_topic(self, client):
        """测试特定主题的聊天响应"""
        response = client.post(
            "/api/chat",
            json={"message": "极限是什么"},
            content_type="application/json"
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data["success"] is True
        response_text = data["response"]
        
        assert "极限" in response_text or "limit" in response_text.lower()


class TestQuestionAPI:
    """题库API测试"""
    
    def test_get_questions_returns_200(self, client):
        """测试获取题目列表"""
        response = client.get("/api/questions")
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["success"] is True
        assert "total" in data
        assert "questions" in data
        assert isinstance(data["questions"], list)
    
    def test_get_questions_with_type_filter(self, client):
        """测试按类型过滤题目"""
        response = client.get("/api/questions?type=example")
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["success"] is True
    
    def test_question_stats(self, client):
        """测试题库统计"""
        response = client.get("/api/questions/stats")
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["success"] is True
        assert "stats" in data
        assert "mode" in data
    
    def test_search_questions_requires_query(self, client):
        """测试搜索需要查询参数"""
        response = client.get("/api/questions/search")
        assert response.status_code == 400
    
    def test_search_questions_with_valid_query(self, client):
        """测试有效搜索"""
        response = client.get("/api/questions/search?q=极限")
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["success"] is True
        assert "results" in data
        assert "query" in data


class TestConversationAPI:
    """对话管理API测试"""
    
    def test_get_conversation(self, client):
        """测试获取对话历史"""
        response = client.get("/api/conversation")
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["success"] is True
        assert "session_id" in data
        assert "history" in data
    
    def test_clear_conversation(self, client):
        """测试清除对话"""
        response = client.post("/api/conversation/clear")
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["success"] is True
        assert "message" in data


class TestAgentsAPI:
    """Agent列表API测试"""
    
    def test_list_agents(self, client):
        """测试列出可用Agent"""
        response = client.get("/api/agents")
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["success"] is True
        assert "agents" in data
        assert isinstance(data["agents"], list)
        
        if len(data["agents"]) > 0:
            agent = data["agents"][0]
            assert "role" in agent
            assert "name" in agent
            assert "status" in agent


class TestFileUpload:
    """文件上传API测试"""
    
    def test_upload_pdf_without_file(self, client):
        """测试没有文件的PDF上传"""
        response = client.post("/api/upload/pdf")
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert "error" in data
    
    def test_upload_image_without_file(self, client):
        """测试没有文件的图片上传"""
        response = client.post("/api/upload/image")
        assert response.status_code == 400
    
    def test_upload_empty_filename(self, client):
        """测试空文件名上传"""
        data = {"file": (b"", "")}
        response = client.post(
            "/api/upload/pdf",
            data=data,
            content_type="multipart/form-data"
        )
        
        assert response.status_code == 400
    
    def test_upload_wrong_file_type(self, client):
        """测试上传错误文件类型"""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"test content")
            temp_path = f.name
        
        try:
            with open(temp_path, "rb") as f:
                data = {"file": (f, "test.txt")}
                response = client.post(
                    "/api/upload/pdf",
                    data=data,
                    content_type="multipart/form-data"
                )
            
            assert response.status_code == 400
        finally:
            os.unlink(temp_path)


class TestErrorHandling:
    """错误处理测试"""
    
    def test_404_error(self, client):
        """测试404错误处理"""
        response = client.get("/api/nonexistent-endpoint")
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert "error" in data


class TestMockAgentManager:
    """MockAgentManager功能测试"""
    
    def test_mock_chat_response(self):
        """测试Mock聊天响应"""
        manager = MockAgentManager()
        
        response = manager.chat(
            user_message="test",
            agent_role="question_bank",
            session_id="test_session"
        )
        
        assert "content" in response
        assert "agent_role" in response
        assert "session_id" in response
        assert "metadata" in response
        assert response["metadata"].get("is_mock") is True
    
    def test_mock_question_stats(self):
        """测试Mock题库统计"""
        manager = MockAgentManager()
        stats = manager.get_question_stats()
        
        assert "total" in stats
        assert "examples" in stats
        assert "exercises" in stats
        assert stats.get("is_mock") is True
    
    def test_mock_list_agents(self):
        """测试Mock Agent列表"""
        manager = MockAgentManager()
        agents = manager.list_agents()
        
        assert len(agents) > 0
        for agent in agents:
            assert "role" in agent
            assert "name" in agent
            assert agent.get("is_mock") is True
    
    def test_mock_get_all_questions(self):
        """测试Mock获取所有题目"""
        manager = MockAgentManager()
        questions = manager.get_all_questions()
        
        assert isinstance(questions, list)
        
        filtered = manager.get_all_questions(question_type="example")
        assert isinstance(filtered, list)
    
    def test_mock_search_questions(self):
        """测试Mock搜索题目"""
        manager = MockAgentManager()
        
        results = manager.search_questions(query="极限", n_results=5)
        assert isinstance(results, list)
        
        results2 = manager.search_questions(query="", n_results=5)
        assert isinstance(results2, list)
    
    def test_mock_pdf_processing(self):
        """测试Mock PDF处理"""
        manager = MockAgentManager()
        
        result = manager.process_pdf(
            pdf_path="/fake/path/test.pdf",
            start_page=1,
            end_page=10
        )
        
        assert result["success"] is True
        assert "total_questions" in result
        assert "questions" in result
        assert result.get("is_mock") is True
    
    def test_mock_image_processing(self):
        """测试Mock图片处理"""
        manager = MockAgentManager()
        
        result = manager.process_image(
            image_path="/fake/path/test.jpg"
        )
        
        assert result["success"] is True
        assert "ocr_text" in result
        assert "questions" in result
        assert result.get("is_mock") is True
    
    def test_session_management(self):
        """测试会话管理"""
        manager = MockAgentManager()
        
        manager.chat(user_message="test", agent_role="question_bank", session_id="session_1")
        
        session = manager.get_session("session_1")
        assert session is not None
        assert session.session_id == "session_1"
        
        assert manager.clear_session("session_1") is True
        assert manager.get_session("session_1") is None
    
    def test_factory_function(self):
        """测试工厂函数"""
        mock_manager = get_agent_manager(use_mock=True)
        assert mock_manager is not None
        assert hasattr(mock_manager, 'chat')


class TestIntegration:
    """集成测试"""
    
    def test_full_chat_flow(self, client):
        """测试完整聊天流程"""
        response1 = client.post(
            "/api/chat",
            json={"message": "你好"},
            content_type="application/json"
        )
        assert response1.status_code == 200
        
        conv_response = client.get("/api/conversation")
        assert conv_response.status_code == 200
        conv_data = json.loads(conv_response.data)
        assert len(conv_data["history"]) > 0
        
        clear_response = client.post("/api/conversation/clear")
        assert clear_response.status_code == 200
        
        conv_response2 = client.get("/api/conversation")
        conv_data2 = json.loads(conv_response2.data)
        assert len(conv_data2["history"]) == 0
    
    def test_question_flow(self, client):
        """测试题目操作流程"""
        stats_response = client.get("/api/questions/stats")
        assert stats_response.status_code == 200
        
        list_response = client.get("/api/questions")
        assert list_response.status_code == 200
        
        search_response = client.get("/api/questions/search?q=积分")
        assert search_response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
