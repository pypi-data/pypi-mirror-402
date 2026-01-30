# Quick Test Instructions

## ✅ Prerequisites Verified

- ✅ Python 3.13.7
- ✅ Virtual environment activated
- ✅ FastMCP installed
- ✅ websockets installed
- ✅ DcisionAI Graph imports working

## 🚀 Run the Test

### Step 1: Start Server (Terminal 1)

```bash
cd /Users/ameydhavle/Documents/DcisionAI/dcisionai-mcp-platform
source venv/bin/activate
python3 -m dcisionai_mcp_server_2.0.start_mcp_server
```

**Wait for**: `INFO:     Uvicorn running on http://0.0.0.0:8080`

### Step 2: Run Test (Terminal 2)

```bash
cd /Users/ameydhavle/Documents/DcisionAI/dcisionai-mcp-platform
source venv/bin/activate
python3 dcisionai_mcp_server_2.0/test_websocket.py
```

## ✅ Success Indicators

- Server starts without errors
- Test connects to WebSocket
- Receives `workflow_start` message
- Receives multiple `step_complete` messages
- Receives `workflow_complete` message
- Test shows "✅ All tests passed!"

## 📝 Notes

- Server must be running before test
- Test will timeout if server not responding
- Full workflow may take 1-2 minutes
- Check server logs for detailed progress

