# Next Steps for MCP Server 2.0 Architecture

**Date**: 2025-11-25  
**Status**: Phase 1 & 2 Complete ✅ | Phase 3 & 4 Pending ⏳

---

## 📊 Current Status

### ✅ Completed

**Phase 1: Core MCP Server** ✅
- ✅ Directory structure created
- ✅ Direct `dcisionai_graph` imports (all tools)
- ✅ HTTP JSON-RPC 2.0 transport
- ✅ All 5 tools implemented
- ✅ All 2 resources implemented
- ✅ FastMCP server integration
- ✅ Configuration management

**Phase 2: WebSocket Support** ✅
- ✅ WebSocket transport implemented
- ✅ Real-time streaming (`step_complete`, `workflow_complete`)
- ✅ JSON serialization (datetime, AIMessage)
- ✅ Error handling
- ✅ **TESTED AND WORKING** ✅

---

## 🎯 Next Steps (Prioritized)

### Priority 1: React MCP Client Library (Phase 3)

**Goal**: Create React client library so React UI can migrate to MCP Server 2.0

**Strategy**: **Extract and adapt** existing code from `dcisionai_graph/ui/` (see `REACT_CLIENT_STRATEGY.md`)

**Tasks**:

#### Task 3.1: Create React Client Directory Structure
- [ ] Create `dcisionai_mcp_clients/react-mcp-client/` directory
- [ ] Set up npm package (`package.json`)
- [ ] Create basic directory structure:
  ```
  react-mcp-client/
  ├── package.json
  ├── README.md
  ├── src/
  │   ├── index.js              # Main exports
  │   ├── hooks/
  │   │   ├── useMCPTool.js     # Extract from mcp-client.js
  │   │   ├── useMCPResource.js  # New (for resource reading)
  │   │   └── useMCPWebSocket.js # Extract from useDAME.js
  │   └── utils/
  │       ├── mcpClient.js      # Extract from mcp-client.js
  │       └── websocket.js      # Extract from useDAME.js
  └── examples/
      └── WorkspaceDetailDAME.js # Copy from dcisionai_graph/ui
  ```

**Estimated Time**: 2-4 hours

---

#### Task 3.2: Extract & Adapt Core MCP Client
- [ ] **Copy** `dcisionai_graph/ui/src/mcp-client.js` → `react-mcp-client/src/utils/mcpClient.js`
- [ ] **Update** endpoints:
  - Change from `/mcp` to `/mcp/tools/call`
  - Update base URL to MCP Server 2.0 (`http://localhost:8080`)
  - Update tool names (`dcisionai_solve`, `dcisionai_solve_with_model`, etc.)
- [ ] **Copy** `dcisionai_graph/ui/src/hooks/useDAME.js` → `react-mcp-client/src/utils/websocket.js`
- [ ] **Update** WebSocket URL:
  - Change from FastAPI (`ws://localhost:8001`) to MCP Server 2.0 (`ws://localhost:8080`)
  - Keep message parsing logic (already compatible)
- [ ] Add resource reading utilities

**Estimated Time**: 3-4 hours (extract & adapt vs build from scratch)

---

#### Task 3.3: Create React Hooks
- [ ] `useMCPTool` hook:
  - Wrap `mcpClient.js` `callMCPTool` function
  - Add loading/error state management
  ```javascript
  const { callTool, loading, error } = useMCPTool();
  const result = await callTool('dcisionai_solve', {
    problem_description: '...'
  });
  ```
- [ ] `useMCPResource` hook (new):
  - Implement resource reading via HTTP GET
  ```javascript
  const { readResource, data, loading } = useMCPResource();
  const models = await readResource('dcisionai://models/list');
  ```
- [ ] `useMCPWebSocket` hook:
  - Extract from `useDAME.js` WebSocket logic
  - Generalize (remove DAME-specific code)
  - Keep message parsing (already handles `step_complete`, `workflow_complete`)
  ```javascript
  const { connect, disconnect, stream } = useMCPWebSocket();
  connect('ws://localhost:8080/ws/session123');
  stream.on('step_complete', (data) => { ... });
  stream.on('workflow_complete', (data) => { ... });
  ```

**Estimated Time**: 4-6 hours (extract & adapt vs build from scratch)

---

#### Task 3.4: Create Migration Examples
- [ ] **Copy** `dcisionai_graph/ui/src/components/WorkspaceDetailDAME.js` → `examples/WorkspaceDetailDAME.js`
- [ ] **Update** example to use new hooks:
  - Replace `useDAME` with `useMCPWebSocket`
  - Replace direct `callMCPTool` with `useMCPTool`
  - Update imports
- [ ] Create migration guide with before/after code
- [ ] Test example with MCP Server 2.0

**Estimated Time**: 3-4 hours (copy & adapt vs build from scratch)

**Total Phase 3 Estimated Time**: 12-18 hours (1.5-2 days)** ⚡ **Faster due to code reuse**

---

### Priority 2: React UI Migration (Phase 4.2)

**Goal**: Migrate existing React UI to use MCP client library

**Tasks**:

#### Task 4.2.1: Identify Components to Migrate
- [ ] Audit current React UI components
- [ ] List all FastAPI endpoint calls
- [ ] Map to MCP tools/resources:
  - `/api/optimize` → `dcisionai_solve` tool
  - `/api/models` → `dcisionai://models/list` resource
  - `/api/optimize/{model_id}` → `dcisionai_solve_with_model` tool
  - WebSocket `/ws/{session_id}` → MCP WebSocket `/ws/{session_id}`

**Estimated Time**: 2-4 hours

---

#### Task 4.2.2: Migrate Core Components
- [ ] Migrate `WorkspaceDetailDAME` component:
  - Replace FastAPI fetch with `useMCPTool`
  - Replace WebSocket with `useMCPWebSocket`
  - Update state management
- [ ] Migrate model selection component:
  - Replace `/api/models` with `useMCPResource('dcisionai://models/list')`
- [ ] Migrate optimization form:
  - Replace FastAPI calls with MCP tool calls

**Estimated Time**: 8-12 hours

---

#### Task 4.2.3: Update Configuration
- [ ] Update environment variables:
  - `REACT_APP_MCP_SERVER_URL` (instead of `REACT_APP_API_URL`)
- [ ] Update WebSocket URLs:
  - `ws://localhost:8080/ws/{session_id}` (instead of `ws://localhost:8001/ws/{session_id}`)
- [ ] Remove FastAPI dependencies

**Estimated Time**: 2-4 hours

---

#### Task 4.2.4: Testing & Validation
- [ ] Test all migrated components
- [ ] Verify WebSocket streaming works
- [ ] Verify tool calls work
- [ ] Verify resource reads work
- [ ] Performance comparison (before/after)

**Estimated Time**: 4-6 hours

**Total Phase 4.2 Estimated Time**: 16-26 hours (2-3 days)

---

### Priority 3: Production Deployment (Phase 4.3)

**Goal**: Deploy MCP Server 2.0 to production

**Tasks**:

#### Task 4.3.1: Railway Deployment
- [ ] Create new Railway service for MCP Server 2.0
- [ ] Configure environment variables:
  - `PORT=8080`
  - `DCISIONAI_DOMAIN_FILTER=all`
  - `ANTHROPIC_API_KEY=...`
- [ ] Set up health check endpoint
- [ ] Configure CORS for React UI domain
- [ ] Test deployment

**Estimated Time**: 2-4 hours

---

#### Task 4.3.2: Update Client Configurations
- [ ] Update React UI to point to production MCP Server 2.0
- [ ] Update Salesforce client endpoint URL (if needed)
- [ ] Test production connections

**Estimated Time**: 2-4 hours

---

#### Task 4.3.3: Monitoring & Observability
- [ ] Set up logging (structured logs)
- [ ] Set up metrics (tool call counts, latency, errors)
- [ ] Set up alerts (error rates, latency spikes)
- [ ] Create dashboard (optional)

**Estimated Time**: 4-6 hours

**Total Phase 4.3 Estimated Time**: 8-14 hours (1-2 days)

---

### Priority 4: Testing & Quality Assurance (Phase 4.1)

**Goal**: Comprehensive testing before production migration

**Tasks**:

#### Task 4.1.1: Unit Tests
- [ ] Test all MCP tools (`dcisionai_solve`, `dcisionai_solve_with_model`, etc.)
- [ ] Test all MCP resources (`dcisionai://models/list`, `dcisionai://solvers/list`)
- [ ] Test error handling
- [ ] Test input validation

**Estimated Time**: 8-12 hours

---

#### Task 4.1.2: Integration Tests
- [ ] Test Salesforce client with MCP Server 2.0
- [ ] Test React UI with MCP client library
- [ ] Test WebSocket streaming end-to-end
- [ ] Test concurrent sessions

**Estimated Time**: 6-8 hours

---

#### Task 4.1.3: Performance Benchmarking
- [ ] Compare latency (MCP Server 1.0 vs 2.0)
- [ ] Compare throughput
- [ ] Compare memory usage
- [ ] Document performance improvements

**Estimated Time**: 4-6 hours

**Total Phase 4.1 Estimated Time**: 18-26 hours (2-3 days)

---

### Priority 5: Documentation & Cleanup (Phase 4.4)

**Goal**: Complete documentation and deprecate old services

**Tasks**:

#### Task 4.4.1: Update Documentation
- [ ] Update main README with MCP Server 2.0 info
- [ ] Create migration guide for customers
- [ ] Update API documentation
- [ ] Create troubleshooting guide

**Estimated Time**: 4-6 hours

---

#### Task 4.4.2: Deprecate Old Services
- [ ] Mark FastAPI backend as deprecated
- [ ] Mark MCP Server 1.0 as deprecated
- [ ] Create deprecation timeline
- [ ] Notify customers

**Estimated Time**: 2-4 hours

---

#### Task 4.4.3: Code Cleanup
- [ ] Remove unused code
- [ ] Clean up old deployment configs
- [ ] Archive old services (don't delete yet)

**Estimated Time**: 2-4 hours

**Total Phase 4.4 Estimated Time**: 8-14 hours (1-2 days)

---

## 📅 Recommended Timeline

### Week 1: React MCP Client Library
- **Days 1-2**: Create directory structure and core client
- **Days 3-4**: Implement React hooks
- **Day 5**: Create examples and migration guide

### Week 2: React UI Migration
- **Days 1-2**: Identify and migrate core components
- **Days 3-4**: Update configuration and test
- **Day 5**: Performance validation

### Week 3: Testing & Deployment
- **Days 1-2**: Comprehensive testing
- **Days 3-4**: Production deployment
- **Day 5**: Monitoring setup

### Week 4: Documentation & Cleanup
- **Days 1-2**: Documentation updates
- **Days 3-4**: Deprecation process
- **Day 5**: Final validation

**Total Estimated Time**: 4 weeks

---

## 🎯 Success Criteria

### Phase 3: React MCP Client
- ✅ React hooks work correctly
- ✅ WebSocket streaming works
- ✅ Examples provided
- ✅ Migration guide complete

### Phase 4: Migration & Deployment
- ✅ React UI fully migrated
- ✅ Salesforce client works (no changes needed)
- ✅ Production deployment successful
- ✅ Performance improved (lower latency)
- ✅ All tests passing

### Final State
- ✅ Single service (MCP Server 2.0)
- ✅ All clients use MCP protocol
- ✅ Old services deprecated
- ✅ Documentation complete

---

## 🚨 Risks & Mitigations

### Risk 1: React UI Migration Complexity
**Mitigation**: 
- Create comprehensive examples
- Test incrementally
- Keep FastAPI running during migration

### Risk 2: Breaking Changes
**Mitigation**:
- Maintain backward compatibility
- Gradual migration
- Rollback plan ready

### Risk 3: Performance Regression
**Mitigation**:
- Benchmark before/after
- Monitor production metrics
- Optimize as needed

---

## 📚 Related Documentation

- **`IMPLEMENTATION_PLAN.md`** - Detailed implementation plan
- **`PROGRESS.md`** - Current progress tracking
- **`MIGRATION.md`** - Migration guide
- **`DEPLOYMENT_ARCHITECTURE.md`** - Deployment scenarios
- **`CUSTOMER_DEPLOYMENT_GUIDE.md`** - Customer-facing guide

---

## 🔄 Quick Start Checklist

### Immediate Next Steps (This Week)

- [ ] **Day 1**: Create `dcisionai_mcp_clients/react-mcp-client/` directory
- [ ] **Day 1**: Set up npm package structure
- [ ] **Day 2**: Implement core MCP client (`mcpClient.js`)
- [ ] **Day 2**: Implement WebSocket utilities (`websocket.js`)
- [ ] **Day 3**: Implement `useMCPTool` hook
- [ ] **Day 3**: Implement `useMCPResource` hook
- [ ] **Day 4**: Implement `useMCPWebSocket` hook
- [ ] **Day 5**: Create migration examples

### Next Week

- [ ] Audit React UI components
- [ ] Migrate `WorkspaceDetailDAME` component
- [ ] Test WebSocket streaming
- [ ] Update configuration

---

**Last Updated**: 2025-11-25

