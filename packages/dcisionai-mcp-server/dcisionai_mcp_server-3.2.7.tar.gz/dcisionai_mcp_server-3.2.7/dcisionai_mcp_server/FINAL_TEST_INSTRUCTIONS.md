# Final Test Instructions - WebSocket Implementation

## ✅ Prerequisites Status

- ✅ Python 3.13.7 available
- ✅ Virtual environment (`venv`) exists and activated
- ✅ FastMCP 2.13.0 installed
- ✅ websockets 15.0.1 installed
- ✅ DcisionAI Graph imports working
- ✅ Port 8080 available

## 🚀 Ready to Test!

### Step 1: Start the Server

**Open Terminal 1** and run:

```bash
cd /Users/ameydhavle/Documents/DcisionAI/dcisionai-mcp-platform
source venv/bin/activate
python3 -m dcisionai_mcp_server_2.0.start_mcp_server
```

**Wait for this message**:
```
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```

### Step 2: Run the WebSocket Test

**Open Terminal 2** (keep Terminal 1 running) and run:

```bash
cd /Users/ameydhavle/Documents/DcisionAI/dcisionai-mcp-platform
source venv/bin/activate
python3 dcisionai_mcp_server_2.0/test_websocket.py
```

## ✅ Expected Results

### Server Output (Terminal 1)
- Server starts successfully
- Shows "✅ FastMCP server imported successfully"
- Shows "✅ Using FastAPI app with health endpoint"
- Listens on port 8080

### Test Output (Terminal 2)
- Connects to WebSocket
- Sends problem description
- Receives `workflow_start` message
- Receives multiple `step_complete` messages
- Receives `workflow_complete` message
- Shows "✅ All tests passed!"

## 🔍 Quick Verification

Before running full test, verify server is up:

```bash
curl http://localhost:8080/health
```

Should return:
```json
{"status": "ok", "service": "dcisionai-mcp-server-2.0", "version": "2.0.0"}
```

## 📝 Notes

- **Keep server running** while testing
- Full workflow test may take 1-2 minutes
- Test will show step-by-step progress
- Check server logs in Terminal 1 for detailed info

## 🐛 Troubleshooting

### Connection Refused
- Ensure server is running (Terminal 1)
- Wait 5 seconds after server starts
- Check: `curl http://localhost:8080/health`

### Import Errors
- Ensure venv is activated: `source venv/bin/activate`
- Check dependencies: `pip list | grep fastmcp`

### Port Already in Use
- Find process: `lsof -ti:8080`
- Kill process: `kill -9 $(lsof -ti:8080)`
- Or use different port: `PORT=8081 python3 -m dcisionai_mcp_server_2.0.start_mcp_server`

---

**Ready to test!** 🚀

