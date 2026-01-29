# Quick Start Guide - MCP Server 2.0

**Date**: 2025-11-25

---

## Prerequisites

1. **Python 3.10+**
2. **DcisionAI Graph installed**:
   ```bash
   pip install -e .
   ```

3. **Install MCP Server 2.0 dependencies**:
   ```bash
   cd dcisionai_mcp_server_2.0
   pip install -r requirements.txt
   ```

---

## Start the Server

```bash
# From project root
python3 -m dcisionai_mcp_server_2.0.start_mcp_server
```

Server will start on `http://localhost:8080` (or `PORT` env var).

**Expected output**:
```
🚀 Starting DcisionAI MCP Server 2.0 on Railway
Domain Filter: all
Server Host: 0.0.0.0
Server Port: 8080
✅ FastMCP server imported successfully
✅ Using FastAPI app with health endpoint and HTTP JSON-RPC endpoints
🚀 Starting server on 0.0.0.0:8080
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080
```

---

## Test WebSocket (Quick Test)

### 1. Install Test Dependencies

```bash
pip install websockets
```

### 2. Run WebSocket Test

In a **new terminal** (keep server running):

```bash
python3 dcisionai_mcp_server_2.0/test_websocket.py
```

**Expected output**:
```
🔌 Connecting to WebSocket: ws://localhost:8080/ws/test_1234567890
✅ WebSocket connected
📤 Sending initial message...
📥 Receiving messages...
✅ [workflow_start] Workflow started
📊 [step_complete] Step 1: step0_decomposition
📊 [step_complete] Step 2: step0_context
...
🎉 [workflow_complete] Workflow completed!
✅ All tests passed!
```

---

## Test HTTP Endpoints

### Health Check

```bash
curl http://localhost:8080/health
```

**Expected**:
```json
{"status": "ok", "service": "dcisionai-mcp-server-2.0", "version": "2.0.0"}
```

### List Models

```bash
curl http://localhost:8080/api/models
```

### Call Tool

```bash
curl -X POST http://localhost:8080/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "dcisionai_solve",
    "arguments": {
      "problem_description": "Optimize portfolio"
    }
  }'
```

---

## Troubleshooting

### Server Won't Start

**Error**: `ModuleNotFoundError: No module named 'dcisionai_graph'`

**Solution**:
```bash
# Install dcisionai_graph
pip install -e .
```

### WebSocket Test Fails

**Error**: `Connection refused`

**Solution**:
1. Ensure server is running (check first terminal)
2. Check port: Default is 8080
3. Verify server started successfully

### Import Errors

**Error**: `ImportError: cannot import name 'create_dame_supervisor_workflow'`

**Solution**:
1. Ensure `dcisionai_graph` is installed: `pip install -e .`
2. Check Python path includes project root
3. Verify you're in the project root directory

---

## Next Steps

1. ✅ **Server Running**: Test WebSocket and HTTP endpoints
2. ✅ **WebSocket Test**: Verify streaming works
3. **React UI**: Update WebSocket URL to `ws://localhost:8080/ws/{session_id}`
4. **Salesforce**: Update endpoint URL to `http://localhost:8080`

---

**Last Updated**: 2025-11-25

