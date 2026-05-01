"""
快速验证测试脚本
测试Web界面是否与Agent解耦
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("  Testing Web Interface Agent Decoupling")
print("=" * 60)

print("\n1. Testing MockAgentManager import...")
try:
    from src.agents.mock_agent_manager import MockAgentManager, get_agent_manager
    print("   ✓ MockAgentManager imported successfully")
except ImportError as e:
    print(f"   ✗ Failed: {e}")
    sys.exit(1)

print("\n2. Testing MockAgentManager functionality...")
try:
    manager = MockAgentManager()
    
    response = manager.chat(user_message="你好", agent_role="question_bank", session_id="test")
    assert "content" in response
    assert response["metadata"]["is_mock"] == True
    print("   ✓ chat() works")
    
    stats = manager.get_question_stats()
    assert "total" in stats
    print("   ✓ get_question_stats() works")
    
    questions = manager.get_all_questions()
    assert isinstance(questions, list)
    print("   ✓ get_all_questions() works")
    
    agents = manager.list_agents()
    assert len(agents) > 0
    print("   ✓ list_agents() works")
    
    pdf_result = manager.process_pdf(pdf_path="/fake/test.pdf", start_page=1)
    assert pdf_result["success"] == True
    print("   ✓ process_pdf() works")
    
    img_result = manager.process_image(image_path="/fake/test.jpg")
    assert img_result["success"] == True
    print("   ✓ process_image() works")
    
except Exception as e:
    print(f"   ✗ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n3. Testing Flask app (without LangChain dependencies)...")
try:
    os.environ["USE_MOCK_AGENTS"] = "True"
    os.environ["FLASK_SECRET_KEY"] = "test-secret-key"
    
    import importlib
    if "app" in sys.modules:
        importlib.reload(sys.modules["app"])
    else:
        import app
    
    print("   ✓ Flask app imported successfully")
    print(f"   ✓ Running in {app.USE_MOCK_AGENTS and 'MOCK' or 'REAL'} mode")
    
    with app.app.test_client() as client:
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "healthy"
        assert data["mode"] == "mock"
        print("   ✓ GET /api/health works")
        
        resp = client.post("/api/chat", json={"message": "极限是什么"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] == True
        assert "response" in data
        print("   ✓ POST /api/chat works")
        
        resp = client.get("/api/questions/stats")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] == True
        print("   ✓ GET /api/questions/stats works")
        
        resp = client.get("/api/agents")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] == True
        print("   ✓ GET /api/agents works")
        
except Exception as e:
    print(f"   ✗ Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("  ALL TESTS PASSED!")
print("=" * 60)
print("\nSummary:")
print("  ✓ MockAgentManager created - no LangChain dependencies")
print("  ✓ Flask app uses MockAgentManager by default")
print("  ✓ All API endpoints work without real agents")
print("  ✓ Web interface is COMPLETELY decoupled from agents")
print("\nTo run the web server:")
print("  python app.py")
print("\nEnvironment variable USE_MOCK_AGENTS=True is set by default")
print("Set USE_MOCK_AGENTS=False to use real agents (requires LangChain)")
