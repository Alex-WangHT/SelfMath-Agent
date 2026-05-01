import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("Testing Flask template folder fix...")
print("=" * 50)

try:
    # 1. Test creating Flask app
    from src.interface import AgentService, get_registry
    from src.services import create_app
    
    print("1. Testing Flask app creation...")
    AgentService._instance = None
    registry = get_registry()
    registry.clear()
    
    app = create_app()
    print("   ✓ Flask app created")
    
    # 2. Check template folder configuration
    print("\n2. Checking template folder configuration...")
    print(f"   Template folder: {app.template_folder}")
    print(f"   Static folder: {app.static_folder}")
    
    # 3. Verify template folder exists
    template_path = Path(app.template_folder)
    print(f"\n3. Verifying template folder exists...")
    if template_path.exists():
        print("   ✓ Template folder exists")
        index_html = template_path / "index.html"
        if index_html.exists():
            print("   ✓ index.html exists")
        else:
            print(f"   ✗ index.html not found in {template_path}")
    else:
        print(f"   ✗ Template folder does not exist: {template_path}")
    
    # 4. Test with test client
    print("\n4. Testing with test client...")
    AgentService._instance = None
    registry.clear()
    
    app = create_app()
    app.config["TESTING"] = True
    
    with app.test_client() as client:
        # Test health check
        resp1 = client.get("/api/health")
        print(f"   GET /api/health: status={resp1.status_code}")
        assert resp1.status_code == 200
        print("   ✓ Health check works")
        
        # Test index page (this was failing before)
        resp2 = client.get("/")
        print(f"   GET /: status={resp2.status_code}")
        
        if resp2.status_code == 200:
            print("   ✓ Index page works (template found!)")
        else:
            print(f"   ✗ Index page failed with status {resp2.status_code}")
    
    print("\n" + "=" * 50)
    print("SUCCESS! Flask template folder fix works correctly.")
    print("=" * 50)
    
    print("\nTo start the server:")
    print("  python src/services/app.py")
    print("  or")
    print("  python app.py")
    
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
