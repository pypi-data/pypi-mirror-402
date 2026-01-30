# Testing Guide for MCP Server 2.0

**Date**: 2025-11-25  
**Status**: Testing Phase

---

## Quick Start

### 1. Start the Server

```bash
# From project root
cd dcisionai_mcp_server_2.0
python -m start_mcp_server
```

Or:

```bash
python -m dcisionai_mcp_server_2.0.start_mcp_server
```

Server will start on `http://localhost:8080` (or `PORT` env var).

---

## Test WebSocket Implementation

### Prerequisites

```bash
pip install websockets
```

### Run WebSocket Test

```bash
# From project root
python dcisionai_mcp_server_2.0/test_websocket.py
```

Or set custom WebSocket URL:

```bash
WS_URL=ws://localhost:8080 python dcisionai_mcp_server_2.0/test_websocket.py
```

### Expected Output

```
✅ WebSocket connected
📤 Sending initial message...
📥 Receiving messages...
✅ [workflow_start] Workflow started
📊 [step_complete] Step 1: step0_decomposition
📊 [step_complete] Step 2: step0_context
📊 [step_complete] Step 3: step1_classification
...
🎉 [workflow_complete] Workflow completed!
✅ All tests passed!
```

---

## Test HTTP JSON-RPC 2.0 Endpoints

### Test Tool Call

```bash
curl -X POST http://localhost:8080/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "dcisionai_solve",
    "arguments": {
      "problem_description": "Optimize portfolio allocation"
    }
  }'
```

### Test Resource Read

```bash
curl http://localhost:8080/mcp/resources/dcisionai://models/list
```

### Test Health Endpoint

```bash
curl http://localhost:8080/health
```

---

## Test Deployed Models

### List Models

```bash
curl http://localhost:8080/api/models
```

### Execute Model

```bash
curl -X POST http://localhost:8080/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "dcisionai_solve_with_model",
    "arguments": {
      "model_id": "portfolio_optimization_v1",
      "data": {
        "concentration_limit": 0.12,
        "generate_data": true,
        "seed": 42
      }
    }
  }'
```

---

## Test NLP Query

```bash
curl -X POST http://localhost:8080/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "dcisionai_nlp_query",
    "arguments": {
      "question": "What is the total portfolio value?"
    }
  }'
```

---

## Test Concept Mapping

```bash
curl -X POST http://localhost:8080/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "dcisionai_map_concepts",
    "arguments": {
      "required_concepts": ["client", "portfolio", "AUM"],
      "schema_json": "{\"objects\": {\"Account\": {\"fields\": {\"Name\": {\"type\": \"string\"}}}}}"
    }
  }'
```

---

## Integration Tests

### Test with React UI

1. Start MCP Server 2.0:
   ```bash
   python -m dcisionai_mcp_server_2.0.start_mcp_server
   ```

2. Update React UI WebSocket URL:
   ```javascript
   // In dcisionai_graph/ui/src/components/WorkspaceDetailDAME.js
   const wsUrl = 'ws://localhost:8080/ws/${sessionId}';
   ```

3. Test workflow execution in React UI

### Test with Salesforce

Salesforce MCP client should work without changes (same HTTP JSON-RPC 2.0 protocol).

Update endpoint URL in Salesforce:
```apex
String mcpServerUrl = 'http://localhost:8080';  // Or production URL
```

---

## Troubleshooting

### WebSocket Connection Refused

**Error**: `Connection refused`

**Solution**:
1. Ensure server is running: `python -m dcisionai_mcp_server_2.0.start_mcp_server`
2. Check port: Default is 8080, or set `PORT` env var
3. Check firewall/network settings

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'dcisionai_graph'`

**Solution**:
1. Ensure `dcisionai_graph` is installed: `pip install -e .`
2. Check Python path includes project root
3. Verify `dcisionai_graph` directory exists

### Workflow Timeout

**Error**: `Workflow timeout after 600 seconds`

**Solution**:
1. Check problem description is valid
2. Verify API keys are set (ANTHROPIC_API_KEY)
3. Check network connectivity
4. Review server logs for errors

---

## Performance Testing

### Measure Latency

```bash
time curl -X POST http://localhost:8080/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name": "dcisionai_solve", "arguments": {"problem_description": "Test"}}'
```

### WebSocket Streaming Performance

Monitor step completion times in test output.

---

**Last Updated**: 2025-11-25

