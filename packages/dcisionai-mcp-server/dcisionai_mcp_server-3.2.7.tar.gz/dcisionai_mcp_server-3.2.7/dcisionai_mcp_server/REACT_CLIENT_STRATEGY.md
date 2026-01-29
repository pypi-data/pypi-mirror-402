# React MCP Client Strategy - Reusing dcisionai_graph/ui

**Date**: 2025-11-25  
**Status**: Strategy Document

---

## 🎯 Overview

**Yes!** The React UI code in `dcisionai_graph/ui/` can be reused for the React MCP client library. Instead of building from scratch, we can **extract and adapt** the existing code.

---

## 📦 What Exists in `dcisionai_graph/ui/`

### ✅ Already Implemented

1. **`mcp-client.js`** - Basic MCP client
   - ✅ JSON-RPC 2.0 implementation
   - ✅ Tool calling (`callMCPTool`)
   - ⚠️ Uses old FastAPI endpoints (needs update)

2. **`useDAME.js`** - WebSocket streaming hook
   - ✅ WebSocket connection management
   - ✅ Real-time streaming (`step_complete`, `workflow_complete`)
   - ✅ State management
   - ⚠️ Uses FastAPI WebSocket endpoints (needs update)

3. **`WorkspaceDetailDAME.js`** - Main component
   - ✅ Full workflow UI
   - ✅ WebSocket integration
   - ✅ Step visualization
   - ✅ Can be used as example/reference

4. **Component Library** - Full UI components
   - ✅ Visualization components
   - ✅ Results display
   - ✅ Workflow steps
   - ✅ Can be reused as-is

---

## 🔄 Strategy: Extract & Adapt

### Phase 1: Extract Reusable Code

**Create**: `dcisionai_mcp_clients/react-mcp-client/`

**Extract from `dcisionai_graph/ui/`**:

1. **Core Client** (`src/utils/mcpClient.js`)
   - Extract from `dcisionai_graph/ui/src/mcp-client.js`
   - Update endpoints to MCP Server 2.0
   - Keep JSON-RPC 2.0 protocol

2. **WebSocket Utilities** (`src/utils/websocket.js`)
   - Extract WebSocket logic from `useDAME.js`
   - Update to use MCP Server 2.0 WebSocket (`/ws/{session_id}`)
   - Keep message parsing logic

3. **React Hooks** (`src/hooks/`)
   - **`useMCPTool.js`**: Extract from `mcp-client.js` + wrap as hook
   - **`useMCPResource.js`**: New (for resource reading)
   - **`useMCPWebSocket.js`**: Extract from `useDAME.js` + adapt

---

### Phase 2: Update for MCP Server 2.0

**Changes Needed**:

#### 1. Update `mcpClient.js` → `src/utils/mcpClient.js`

**Current** (`dcisionai_graph/ui/src/mcp-client.js`):
```javascript
serverUrl: process.env.REACT_APP_MCP_SERVER_URL || "http://localhost:8000/mcp"
```

**New** (`react-mcp-client/src/utils/mcpClient.js`):
```javascript
serverUrl: process.env.REACT_APP_MCP_SERVER_URL || "http://localhost:8080"
// Endpoint: POST /mcp/tools/call (not /mcp)
```

**Update**:
- Change endpoint from `/mcp` to `/mcp/tools/call`
- Keep JSON-RPC 2.0 format (already correct)
- Update tool names to match MCP Server 2.0:
  - `dcisionai_solve` (not `execute_workflow`)
  - `dcisionai_solve_with_model` (new)
  - `dcisionai_nlp_query` (new)
  - etc.

---

#### 2. Update `useDAME.js` → `src/hooks/useMCPWebSocket.js`

**Current** (`dcisionai_graph/ui/src/hooks/useDAME.js`):
```javascript
const WS_URL = process.env.REACT_APP_DAME_WS_URL || 'ws://localhost:8001';
ws = new WebSocket(`${WS_URL}/ws/${newSessionId}`);
```

**New** (`react-mcp-client/src/hooks/useMCPWebSocket.js`):
```javascript
const WS_URL = process.env.REACT_APP_MCP_SERVER_URL || 'ws://localhost:8080';
ws = new WebSocket(`${WS_URL}/ws/${sessionId}`);
```

**Update**:
- Change WebSocket URL to MCP Server 2.0 (`/ws/{session_id}`)
- Keep message parsing (already handles `step_complete`, `workflow_complete`)
- Update message format to match MCP Server 2.0 output

**Message Format** (already compatible):
```javascript
// MCP Server 2.0 sends:
{
  "type": "step_complete",
  "step": "step0_decomposition",
  "step_number": 1,
  "data": {...},
  "session_id": "...",
  "timestamp": "..."
}

// useDAME.js already handles:
case 'node_complete':
case 'on_node_end':
  // Can be adapted to handle 'step_complete'
```

---

#### 3. Create New Hooks

**`useMCPTool.js`**:
```javascript
import { callMCPTool } from '../utils/mcpClient';

export const useMCPTool = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const callTool = async (toolName, arguments) => {
    setLoading(true);
    setError(null);
    try {
      const result = await callMCPTool(toolName, arguments);
      return result;
    } catch (err) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { callTool, loading, error };
};
```

**`useMCPResource.js`**:
```javascript
export const useMCPResource = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const readResource = async (uri) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${MCP_SERVER_URL}/mcp/resources/${encodeURIComponent(uri)}`);
      const result = await response.json();
      setData(result);
      return result;
    } catch (err) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { readResource, data, loading, error };
};
```

---

### Phase 3: Package as Library

**Structure**:
```
dcisionai_mcp_clients/react-mcp-client/
├── package.json              # npm package
├── README.md                 # Usage guide
├── src/
│   ├── index.js             # Main exports
│   ├── hooks/
│   │   ├── useMCPTool.js    # Extract from mcp-client.js
│   │   ├── useMCPResource.js # New
│   │   └── useMCPWebSocket.js # Extract from useDAME.js
│   └── utils/
│       ├── mcpClient.js     # Extract from mcp-client.js
│       └── websocket.js     # Extract from useDAME.js
└── platform/
    └── WorkspaceDetailDAME.js # SaaS platform component
```

**Package.json**:
```json
{
  "name": "@dcisionai/react-mcp-client",
  "version": "1.0.0",
  "main": "src/index.js",
  "peerDependencies": {
    "react": "^18.0.0"
  },
  "dependencies": {
    // No dependencies - pure React hooks
  }
}
```

---

## 📋 Migration Steps

### Step 1: Create Directory Structure
```bash
mkdir -p dcisionai_mcp_clients/react-mcp-client/src/{hooks,utils}
mkdir -p dcisionai_mcp_clients/react-mcp-client/platform
```

### Step 2: Copy & Adapt Files

**Copy**:
- `dcisionai_graph/ui/src/mcp-client.js` → `react-mcp-client/src/utils/mcpClient.js`
- `dcisionai_graph/ui/src/hooks/useDAME.js` → `react-mcp-client/src/hooks/useMCPWebSocket.js`

**Adapt**:
- Update endpoints
- Update tool names
- Generalize (remove DAME-specific code)

### Step 3: Create New Hooks

**Create**:
- `useMCPTool.js` (wrap `mcpClient.js`)
- `useMCPResource.js` (new)

### Step 4: Create Platform Components

**Copy**:
- `dcisionai_graph/ui/src/components/WorkspaceDetailDAME.js` → `platform/WorkspaceDetailDAME.js`

**Update**:
- Replace `useDAME` with `useMCPWebSocket`
- Replace direct `callMCPTool` with `useMCPTool`
- Update imports
- Adapt for SaaS platform use

---

## ✅ Benefits of This Approach

1. **Reuse Existing Code**: Don't rebuild what already works
2. **Faster Development**: Extract and adapt vs build from scratch
3. **Proven Patterns**: Code is already tested in production
4. **Consistent API**: Same patterns across UI and library

---

## ⚠️ Considerations

### What to Keep
- ✅ WebSocket message parsing logic
- ✅ State management patterns
- ✅ Error handling
- ✅ Component structure (as platform components)

### What to Change
- ⚠️ Endpoint URLs (FastAPI → MCP Server 2.0)
- ⚠️ Tool names (old names → MCP Server 2.0 names)
- ⚠️ Generalize (remove DAME-specific assumptions)

### What to Add
- ✅ `useMCPResource` hook (new)
- ✅ Resource reading utilities
- ✅ Better error messages
- ✅ TypeScript types (optional)

---

## 🎯 Implementation Plan

### Week 1: Extract & Adapt
- **Day 1**: Create directory structure
- **Day 2**: Copy and adapt `mcp-client.js` → `mcpClient.js`
- **Day 3**: Copy and adapt `useDAME.js` → `useMCPWebSocket.js`
- **Day 4**: Create `useMCPTool` and `useMCPResource` hooks
- **Day 5**: Test hooks with MCP Server 2.0

### Week 2: Examples & Documentation
- **Day 1**: Create example component
- **Day 2**: Update example to use new hooks
- **Day 3**: Write README and usage guide
- **Day 4**: Test with React UI migration
- **Day 5**: Final validation

---

## 📚 Example Usage

**Before** (using `dcisionai_graph/ui` directly):
```javascript
import { callMCPTool } from '../mcp-client';
import useDAME from '../hooks/useDAME';

// Direct tool call
const result = await callMCPTool('execute_workflow', {...});

// WebSocket streaming
const { optimize, workflowState } = useDAME();
```

**After** (using React MCP Client library):
```javascript
import { useMCPTool, useMCPWebSocket, useMCPResource } from '@dcisionai/react-mcp-client';

// Tool call via hook
const { callTool, loading } = useMCPTool();
const result = await callTool('dcisionai_solve', {...});

// WebSocket streaming
const { connect, stream } = useMCPWebSocket();
connect('ws://localhost:8080/ws/session123');
stream.on('step_complete', (data) => { ... });

// Resource reading
const { readResource, data } = useMCPResource();
const models = await readResource('dcisionai://models/list');
```

---

## 🚀 Next Steps

1. **Create** `dcisionai_mcp_clients/react-mcp-client/` directory
2. **Copy** existing code from `dcisionai_graph/ui/`
3. **Adapt** for MCP Server 2.0 endpoints
4. **Test** with MCP Server 2.0
5. **Document** usage and platform components

---

**Last Updated**: 2025-11-25

