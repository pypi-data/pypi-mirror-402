# Migration Guide: MCP Server v1.0 → v2.0

**Date**: 2025-11-25  
**Status**: Planning Phase

---

## Overview

MCP Server 2.0 is a complete rewrite that makes MCP the primary interface, directly integrating with `dcisionai_graph` instead of going through FastAPI. This guide helps you migrate from v1.0 to v2.0.

---

## Key Changes

### Architecture Changes

| Aspect | v1.0 (Thin Adapter) | v2.0 (Primary Interface) |
|--------|---------------------|--------------------------|
| **Integration** | HTTP calls to FastAPI | Direct Python imports |
| **Services** | 2 (FastAPI + MCP) | 1 (MCP only) |
| **Latency** | ~150-300ms | ~0-50ms |
| **Protocol** | Mixed (HTTP + MCP) | Unified (MCP) |

### Code Changes

**v1.0**:
```python
# HTTP client wrapper
from ..client import DcisionAIClient
_client = DcisionAIClient()
result = await _client.optimize(problem_description)
```

**v2.0**:
```python
# Direct import
from dcisionai_graph.core.agents.optimization_agent import run_optimization_workflow
result = await run_optimization_workflow(problem_description)
```

---

## Migration Steps

### Step 1: React UI Migration

**Current (v1.0)**:
```javascript
// Uses FastAPI endpoints
const response = await fetch('/api/optimize', {
  method: 'POST',
  body: JSON.stringify({ problem_description: input })
});

// WebSocket connection
const ws = new WebSocket(`ws://localhost:8001/ws/${sessionId}`);
```

**New (v2.0)**:
```javascript
// Use MCP client library
import { useMCPTool, useMCPWebSocket } from '@dcisionai/mcp-client-react';

const { callTool } = useMCPTool();
const { connect, stream } = useMCPWebSocket();

// Call tool
const result = await callTool('dcisionai_solve', {
  problem_description: input
});

// WebSocket streaming
connect(`ws://localhost:8080/ws/${sessionId}`);
stream.on('thinking', (data) => { ... });
stream.on('result', (data) => { ... });
```

### Step 2: Salesforce Client Migration

**Current (v1.0)**: ✅ **No changes needed**
- Already uses HTTP JSON-RPC 2.0
- Same protocol in v2.0
- Just update endpoint URL

**Change**:
```apex
// Update endpoint URL
String mcpServerUrl = 'https://dcisionai-mcp-platform-production.up.railway.app';
// Same protocol, same format
```

### Step 3: Backend Migration

**Current**: FastAPI backend serves both UI and MCP
**New**: MCP Server 2.0 serves all clients

**Action**: 
- Deploy MCP Server 2.0 alongside FastAPI
- Migrate clients gradually
- Deprecate FastAPI after migration

---

## Compatibility

### Backward Compatibility

- ✅ **Salesforce**: No changes needed (same protocol)
- ⚠️ **React UI**: Needs MCP client library
- ✅ **IDEs**: No changes needed (standard MCP)

### Parallel Deployment

Both versions can run simultaneously:
- v1.0: `dcisionai-mcp-platform-production.up.railway.app` (existing)
- v2.0: `dcisionai-mcp-platform-v2.up.railway.app` (new)

---

## Testing Checklist

- [ ] Test Salesforce client with v2.0
- [ ] Test React UI with v2.0 MCP client
- [ ] Test IDE integrations (Cursor, VS Code)
- [ ] Performance benchmarking
- [ ] Error handling validation
- [ ] WebSocket streaming validation

---

## Rollback Plan

If issues occur:
1. Keep v1.0 running
2. Route clients back to v1.0
3. Fix issues in v2.0
4. Re-test and re-deploy

---

**Last Updated**: 2025-11-25

