"""
一键运行验证
"""
import os
import sys
from pathlib import Path

print("=" * 60)
print("  Verifying Web Interface Setup")
print("=" * 60)

os.environ["USE_MOCK_AGENTS"] = "True"
os.environ["FLASK_SECRET_KEY"] = "test"

sys.path.insert(0, str(Path(__file__).parent))

print("\n[1/4] Loading MockAgentManager...")
import importlib.util

mock_path = Path(__file__).parent / "src" / "agents" / "mock_agent_manager.py"
spec = importlib.util.spec_from_file_location("mock_agent_manager", str(mock_path))
mock_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mock_module)

MockAgentManager = mock_module.MockAgentManager
get_agent_manager = mock_module.get_agent_manager

print(f"    ✓ MockAgentManager loaded")
print(f"    ✓ get_agent_manager loaded")

print("\n[2/4] Testing MockAgentManager functionality...")
manager = MockAgentManager()

response = manager.chat(
    user_message="极限是什么",
    agent_role="question_bank",
    session_id="test"
)
print(f"    ✓ chat() works - response length: {len(response.get('content', ''))}")

stats = manager.get_question_stats()
print(f"    ✓ get_question_stats() works - total: {stats.get('total')}")

agents = manager.list_agents()
print(f"    ✓ list_agents() works - count: {len(agents)}")

print("\n[3/4] Loading Flask app...")
app_path = Path(__file__).parent / "app.py"
spec = importlib.util.spec_from_file_location("app", str(app_path))
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)

print(f"    ✓ Flask app loaded")
print(f"    ✓ USE_MOCK_AGENTS = {app_module.USE_MOCK_AGENTS}")
print(f"    ✓ agent_manager type: {type(app_module.agent_manager)}")

print("\n[4/4] Testing Flask endpoints...")
with app_module.app.test_client() as client:
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.get_json()
    print(f"    ✓ GET /api/health - status: {data['status']}, mode: {data['mode']}")
    
    resp2 = client.post("/api/chat", json={"message": "积分是什么"})
    assert resp2.status_code == 200
    data2 = resp2.get_json()
    print(f"    ✓ POST /api/chat - success: {data2['success']}")
    
    resp3 = client.get("/api/questions/stats")
    assert resp3.status_code == 200
    data3 = resp3.get_json()
    print(f"    ✓ GET /api/questions/stats - success: {data3['success']}")
    
    resp4 = client.get("/api/agents")
    assert resp4.status_code == 200
    data4 = resp4.get_json()
    print(f"    ✓ GET /api/agents - count: {len(data4.get('agents', []))}")

print("\n" + "=" * 60)
print("  ALL TESTS PASSED!")
print("=" * 60)
print("""
Summary:
  ✓ MockAgentManager - No LangChain dependencies
  ✓ Flask app - Uses direct file import (bypasses __init__.py)
  ✓ All API endpoints working correctly
  
To run the web server:
  python app.py
  
To run tests:
  python -m pytest tests/test_app.py -v

Environment variables:
  USE_MOCK_AGENTS=True  (default, no LangChain needed)
  USE_MOCK_AGENTS=False (requires LangChain and real agents)
""")
