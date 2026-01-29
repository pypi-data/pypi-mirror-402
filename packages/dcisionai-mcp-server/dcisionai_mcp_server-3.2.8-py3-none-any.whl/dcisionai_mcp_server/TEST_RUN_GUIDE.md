# WebSocket Test Run Guide

**Status**: Ready to Test ✅

---

## Prerequisites Check ✅

- ✅ Python 3.13.7 available
- ✅ Virtual environment (`venv`) exists
- ✅ FastMCP installed
- ✅ websockets installed
- ✅ DcisionAI Graph imports working

---

## How to Run the Test

### Option 1: Using Helper Scripts (Recommended)

**Terminal 1 - Start Server**:
```bash
cd /Users/ameydhavle/Documents/DcisionAI/dcisionai-mcp-platform
./dcisionai_mcp_server_2.0/start_server.sh
```

**Terminal 2 - Run Test**:
```bash
cd /Users/ameydhavle/Documents/DcisionAI/dcisionai-mcp-platform
./dcisionai_mcp_server_2.0/run_test.sh
```

### Option 2: Manual Commands

**Terminal 1 - Start Server**:
```bash
cd /Users/ameydhavle/Documents/DcisionAI/dcisionai-mcp-platform
source venv/bin/activate
python3 -m dcisionai_mcp_server_2.0.start_mcp_server
```

**Terminal 2 - Run Test**:
```bash
cd /Users/ameydhavle/Documents/DcisionAI/dcisionai-mcp-platform
source venv/bin/activate
python3 dcisionai_mcp_server_2.0/test_websocket.py
```

---

## Expected Server Output

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
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```

---

## Expected Test Output

```
================================================================================
🧪 WebSocket Implementation Test
================================================================================

Test 1: Normal Workflow Execution
--------------------------------------------------------------------------------
🔌 Connecting to WebSocket: ws://localhost:8080/ws/test_1234567890
📋 Session ID: test_1234567890

✅ WebSocket connected

📤 Sending initial message:
{
  "problem_description": "Optimize a portfolio of $500K...",
  ...
}

📥 Receiving messages...
--------------------------------------------------------------------------------
✅ [workflow_start] Workflow started
   Session ID: test_1234567890

📊 [step_complete] Step 1: step0_decomposition
   Data keys: decomposition, result, status

📊 [step_complete] Step 2: step0_context
   Data keys: domain_context, result

📊 [step_complete] Step 3: step1_classification
   Data keys: classification, result

... (more steps) ...

🎉 [workflow_complete] Workflow completed!
   Session ID: test_1234567890
   Result keys: solution, objective_value, status, explanation
   ✅ Solution available
   📈 Objective value: 0.125
   📊 Status: optimal

--------------------------------------------------------------------------------
📊 Test Summary:
   Total steps received: 12
   Message types: error, step_complete, workflow_complete, workflow_start

✅ All expected message types received
✅ Workflow completed successfully

Test 2: Error Handling
--------------------------------------------------------------------------------
🧪 Testing error handling...
🔌 Connecting to: ws://localhost:8080/ws/test_error_1234567890
📤 Sending invalid message (missing problem_description)...
✅ Error handling works: Problem description required

================================================================================
📊 Test Results Summary
================================================================================
   Test 1 (Normal Workflow): ✅ PASSED
   Test 2 (Error Handling): ✅ PASSED

🎉 All tests passed!
```

---

## Troubleshooting

### Server Won't Start

**Error**: `ModuleNotFoundError`

**Solution**:
```bash
source venv/bin/activate
pip install -r dcisionai_mcp_server_2.0/requirements.txt
```

### Connection Refused

**Error**: `Connection refused`

**Solution**:
1. Ensure server is running (check Terminal 1)
2. Wait a few seconds after server starts
3. Check port 8080 is not in use: `lsof -i :8080`

### Import Errors

**Error**: `ImportError: cannot import name 'create_dame_supervisor_workflow'`

**Solution**:
```bash
# Ensure dcisionai_graph is installed
pip install -e .
```

---

## Quick Health Check

Before running full test, verify server is responding:

```bash
curl http://localhost:8080/health
```

Should return:
```json
{"status": "ok", "service": "dcisionai-mcp-server-2.0", "version": "2.0.0"}
```

---

**Last Updated**: 2025-11-25

