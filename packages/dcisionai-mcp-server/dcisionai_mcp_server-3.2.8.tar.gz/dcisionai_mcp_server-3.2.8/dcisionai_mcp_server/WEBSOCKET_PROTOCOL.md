# WebSocket Protocol for MCP Server 2.0

**Date**: 2025-11-25  
**Status**: Implemented ✅

---

## Overview

MCP Server 2.0 provides WebSocket support for React UI real-time streaming. This enables progressive rendering of workflow steps and real-time updates.

---

## Connection

**Endpoint**: `ws://host:port/ws/{session_id}`

**Example**:
```javascript
const sessionId = `dame_${Date.now()}`;
const ws = new WebSocket(`ws://localhost:8080/ws/${sessionId}`);
```

---

## Protocol

### 1. Client → Server: Initial Message

After connecting, client sends initial message with problem description:

```json
{
  "problem_description": "Optimize portfolio allocation...",
  "enabled_features": ["intent", "data", "optimize"],
  "enabled_tools": ["data", "optimize"],
  "reasoning_model": "claude-3-5-haiku-20241022",
  "code_model": "codestral-latest",
  "enable_validation": false,
  "enable_templates": true,
  "template_preferences": {},
  "template_fallback": true
}
```

### 2. Server → Client: Workflow Start

Server sends workflow start confirmation:

```json
{
  "type": "workflow_start",
  "session_id": "dame_1234567890"
}
```

### 3. Server → Client: Step Complete Events

Server streams step completion events as workflow progresses:

```json
{
  "type": "step_complete",
  "step": "step0_decomposition",
  "step_number": 1,
  "data": {
    "decomposition": {
      "result": "...",
      "status": "success"
    }
  },
  "session_id": "dame_1234567890",
  "timestamp": "2025-11-25T19:30:00Z"
}
```

**Step Identifiers**:
- `step0_decomposition` - Query decomposition
- `step0_context` - Context building
- `step1_classification` - Problem classification
- `step2_assumptions` - Assumptions generation
- `step3_entities` - Entity extraction
- `step4_objectives` - Objective extraction
- `step5_constraints` - Constraint extraction
- `solver_router` - Solver selection
- `run_both_solvers` - Dual solver execution
- `dame_solver` - DAME solver execution
- `generate_business_explanation` - Business explanation

### 4. Server → Client: Workflow Complete

When workflow completes, server sends final result:

```json
{
  "type": "workflow_complete",
  "session_id": "dame_1234567890",
  "result": {
    "solution": {...},
    "objective_value": 0.125,
    "status": "optimal",
    "explanation": "..."
  },
  "timestamp": "2025-11-25T19:35:00Z"
}
```

### 5. Server → Client: Error

If an error occurs:

```json
{
  "type": "error",
  "message": "Error description",
  "session_id": "dame_1234567890"
}
```

---

## React UI Integration

### Connection Example

```javascript
const sessionId = `dame_${Date.now()}`;
const wsUrl = process.env.NODE_ENV === 'production' 
  ? `wss://dcisionai-mcp-platform-production.up.railway.app/ws/${sessionId}`
  : `ws://localhost:8080/ws/${sessionId}`;

const ws = new WebSocket(wsUrl);

ws.onopen = () => {
  console.log('🧬 DAME Connected');
  ws.send(JSON.stringify({ 
    problem_description: input,
    enabled_features: ["intent", "data", "optimize"],
    enabled_tools: ["data", "optimize"]
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'workflow_start':
      console.log('Workflow started');
      break;
      
    case 'step_complete':
      console.log(`Step ${data.step} completed`);
      // Update UI with step data
      updateWorkflowChart(data.step, data.data);
      break;
      
    case 'workflow_complete':
      console.log('Workflow completed');
      setResult(data.result);
      break;
      
    case 'error':
      console.error('Error:', data.message);
      break;
  }
};
```

---

## Benefits

1. **Progressive Rendering**: UI updates as each step completes
2. **Real-time Feedback**: Users see progress immediately
3. **Better UX**: No need to wait for entire workflow to complete
4. **Error Handling**: Immediate error feedback

---

## Implementation Details

- Uses `workflow.astream_events()` for granular streaming
- Filters out token-level streaming events (not needed for UI)
- Sends `step_complete` events for each workflow node completion
- Handles WebSocket disconnections gracefully
- 10-minute timeout for workflow execution

---

**Last Updated**: 2025-11-25

