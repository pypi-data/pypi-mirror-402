#!/usr/bin/env python
"""
Test script to verify Railway startup works correctly.
This simulates what Railway does when starting the server.
"""
import os
import sys
import time
import subprocess
import signal

# Set Railway-like environment
os.environ['PORT'] = os.environ.get('PORT', '8080')
os.environ['PYTHONPATH'] = '/app'
os.environ['PYTHONUNBUFFERED'] = '1'

print("=" * 80)
print("🧪 Testing Railway Startup")
print("=" * 80)
print(f"PORT: {os.environ.get('PORT')}")
print(f"PYTHONPATH: {os.environ.get('PYTHONPATH')}")
print(f"Working directory: {os.getcwd()}")
print()

# Test 1: Can we import the module?
print("Test 1: Importing start_mcp_server...")
try:
    from dcisionai_mcp_server.start_mcp_server import main
    print("✅ Import successful")
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Can we import fastmcp_server?
print("\nTest 2: Importing fastmcp_server...")
try:
    import dcisionai_mcp_server.fastmcp_server as server_module
    app = server_module.app
    mcp = server_module.mcp
    print(f"✅ fastmcp_server imported")
    print(f"✅ app type: {type(app)}")
    print(f"✅ mcp type: {type(mcp)}")
    
    # Check health endpoint
    routes = [route.path for route in app.routes]
    if '/health' in routes:
        print("✅ /health endpoint found")
    else:
        print("❌ /health endpoint NOT found")
        print(f"Available routes: {routes[:10]}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Try to start server in background and check health
print("\nTest 3: Starting server and checking health endpoint...")
port = int(os.environ.get('PORT', '8080'))
host = '0.0.0.0'

try:
    import uvicorn
    import threading
    
    def start_server():
        uvicorn.run(app, host=host, port=port, log_level="info")
    
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    print(f"Waiting for server to start on {host}:{port}...")
    time.sleep(3)
    
    # Check health endpoint
    import urllib.request
    try:
        health_url = f"http://{host}:{port}/health"
        print(f"Checking {health_url}...")
        response = urllib.request.urlopen(health_url, timeout=5)
        health_data = response.read().decode('utf-8')
        print(f"✅ Health check successful!")
        print(f"Response: {health_data[:200]}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        sys.exit(1)
    
    print("\n✅ All tests passed! Server should work on Railway.")
    
except Exception as e:
    print(f"❌ Server startup test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

