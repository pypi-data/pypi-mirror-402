# MCP Server 2.0 Implementation Plan

**Date**: 2025-11-25  
**Status**: Planning Phase

---

## Phase 1: Core MCP Server with Direct Integration

### Goal
Create MCP Server 2.0 that directly imports `dcisionai_graph`, eliminating the FastAPI HTTP layer.

### Tasks

#### Task 1.1: Directory Structure ✅
- [x] Create `dcisionai_mcp_server_2.0/` directory
- [x] Create basic structure (tools/, resources/, transports/, etc.)
- [x] Create README and architecture docs

#### Task 1.2: Direct dcisionai_graph Integration
- [ ] Identify all functions to import from `dcisionai_graph`
- [ ] Create tool implementations with direct imports
- [ ] Test imports work correctly
- [ ] Handle dependency management

**Functions to Import**:
- `dcisionai_graph.orchestration.dame_workflow.create_dame_supervisor_workflow` - Full optimization workflow
- `dcisionai_graph.core.tools.nlp.query_tool.answer_nlp_query` - NLP queries
- `dcisionai_graph.core.tools.data.schema_mapping.map_concepts_to_schema` - Concept mapping
- `dcisionai_graph.core.tools.optimization.adhoc_optimize.solve_adhoc_optimization` - Ad-hoc optimization
- `dcisionai_graph.core.models.model_registry.get_all_models` - Model list
- `dcisionai_graph.core.solvers.solver_registry.get_all_solvers` - Solver list

#### Task 1.3: HTTP JSON-RPC 2.0 Transport
- [ ] Implement HTTP JSON-RPC 2.0 endpoint (`/mcp/tools/call`)
- [ ] Implement resource endpoint (`/mcp/resources/{uri}`)
- [ ] Test with Salesforce client
- [ ] Ensure backward compatibility

#### Task 1.4: Tool Implementations
- [ ] `dcisionai_solve` - Direct workflow import
- [x] `dcisionai_solve_with_model` - **Direct model execution** ⭐ **KEY FEATURE**
  - Direct import from `api.models_endpoint.run_deployed_model`
  - Supports all 4 deployed models
  - No HTTP calls - instant execution
- [ ] `dcisionai_nlp_query` - Direct NLP tool import
- [ ] `dcisionai_map_concepts` - Direct mapping tool import
- [ ] `dcisionai_adhoc_optimize` - Direct ad-hoc tool import

#### Task 1.5: Resource Implementations
- [x] `dcisionai://models/list` - **Direct model registry import** ⭐ **KEY FEATURE**
  - Direct import from `api.models_endpoint.list_deployed_models`
  - Full model metadata
  - Domain filtering support
- [ ] `dcisionai://solvers/list` - Direct solver registry import

---

## Phase 2: WebSocket Support for React UI

### Goal
Add WebSocket transport for React UI real-time streaming.

### Tasks

#### Task 2.1: WebSocket Transport
- [ ] Implement WebSocket endpoint (`/ws/{session_id}`)
- [ ] Handle WebSocket connections
- [ ] Stream optimization progress
- [ ] Handle thinking/step updates

#### Task 2.2: Session Management
- [ ] Create session management system
- [ ] Track active sessions
- [ ] Handle session cleanup
- [ ] Support multiple concurrent sessions

#### Task 2.3: Streaming Integration
- [ ] Integrate with dcisionai_graph streaming
- [ ] Stream thinking steps
- [ ] Stream optimization progress
- [ ] Stream final results

---

## Phase 3: React MCP Client (in dcisionai_mcp_clients/)

### Goal
Create React MCP client library in `dcisionai_mcp_clients/react-mcp-client/` directory.

### Tasks

#### Task 3.1: Create React Client Directory
- [ ] Create `dcisionai_mcp_clients/react-mcp-client/` directory
- [ ] Set up npm package structure
- [ ] Create README and docs

#### Task 3.2: Core Client Library
- [ ] Implement `useMCPTool` hook
- [ ] Implement `useMCPResource` hook
- [ ] Implement `useMCPWebSocket` hook
- [ ] Create MCP client utilities

#### Task 3.3: Migration Utilities
- [ ] Create migration helpers
- [ ] Provide examples
- [ ] Create migration guide

---

## Phase 4: Testing & Migration

### Goal
Test thoroughly and migrate clients.

### Tasks

#### Task 4.1: Testing
- [ ] Unit tests for all tools
- [ ] Integration tests with Salesforce
- [ ] Integration tests with React UI
- [ ] Performance benchmarking

#### Task 4.2: Migration
- [ ] Migrate React UI to MCP client
- [ ] Test Salesforce client (should work as-is)
- [ ] Update documentation
- [ ] Deploy to production

---

## Key Design Decisions

### 1. Direct Imports vs HTTP Calls
**Decision**: Direct imports for better performance
**Rationale**: Eliminates HTTP overhead, simpler code, lower latency

### 2. Multi-Transport Support
**Decision**: Support HTTP, WebSocket, and SSE
**Rationale**: Different clients need different transports

### 3. Backward Compatibility
**Decision**: Maintain protocol compatibility
**Rationale**: Existing clients (Salesforce) should work without changes

### 4. Anthropic Compliance
**Decision**: Follow all Anthropic MCP best practices
**Rationale**: Prepare for directory submission

---

## Success Criteria

- ✅ All tools work with direct dcisionai_graph imports
- ✅ Salesforce client works without changes
- ✅ React UI works with MCP client library
- ✅ Performance improved (lower latency)
- ✅ Code simpler (one service instead of two)
- ✅ Anthropic MCP compliant

---

**Last Updated**: 2025-11-25

