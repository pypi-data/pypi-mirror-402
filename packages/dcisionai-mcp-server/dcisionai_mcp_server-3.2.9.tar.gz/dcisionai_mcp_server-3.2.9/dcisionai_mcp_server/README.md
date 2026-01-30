# DcisionAI MCP Server 2.0

**Status**: 🚧 **In Development**  
**Architecture**: MCP as Primary Interface  
**Goal**: Unified MCP server that directly uses `dcisionai_graph`, serving both React UI and Salesforce clients

---

## 🎯 Vision

**MCP Server 2.0** is the next-generation MCP server that:
- ✅ **Directly imports `dcisionai_graph`** (no FastAPI dependency)
- ✅ **Serves React UI** as an MCP client (with WebSocket support)
- ✅ **Serves Salesforce** as an MCP client (HTTP JSON-RPC 2.0)
- ✅ **Follows Anthropic MCP best practices** (annotations, error handling, etc.)
- ✅ **Single service** instead of two (simpler architecture)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│              MCP Clients                              │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │  React UI    │  │  Salesforce  │  │  IDEs       │ │
│  │  (WebSocket) │  │  (HTTP RPC)  │  │  (SSE)      │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬──────┘ │
│         │                  │                  │        │
│         └──────────────────┴──────────────────┘        │
│                      │ MCP Protocol                     │
└──────────────────────┼──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│         MCP Server 2.0 (Primary Interface)             │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Tools: dcisionai_solve, dcisionai_solve_with_  │  │
│  │         model, dcisionai_map_concepts, etc.      │  │
│  │  Resources: dcisionai://models/list, etc.      │  │
│  │  Prompts: Optimization templates                │  │
│  └──────────────────┬───────────────────────────────┘  │
│                     │ Direct Import                    │
│                     ▼                                  │
│  ┌──────────────────────────────────────────────────┐ │
│  │         dcisionai_graph/                         │ │
│  │  (Core Optimization Engine)                      │ │
│  └──────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 Directory Structure

```
dcisionai_mcp_server_2.0/
├── README.md                    # This file
├── ARCHITECTURE.md              # Detailed architecture docs
├── requirements.txt             # Python dependencies
├── config.py                    # Configuration management
├── server.py                    # Main MCP server entry point
├── tools/                       # MCP Tools (direct dcisionai_graph imports)
│   ├── __init__.py
│   ├── optimization.py          # dcisionai_solve, dcisionai_solve_with_model
│   ├── nlp.py                   # dcisionai_nlp_query
│   ├── mapping.py               # dcisionai_map_concepts
│   └── adhoc.py                 # dcisionai_adhoc_optimize
├── resources/                   # MCP Resources
│   ├── __init__.py
│   ├── models.py                # dcisionai://models/list
│   └── solvers.py               # dcisionai://solvers/list
├── prompts/                     # MCP Prompts
│   ├── __init__.py
│   └── optimization.py
├── transports/                  # Transport implementations
│   ├── __init__.py
│   ├── http.py                  # HTTP JSON-RPC 2.0 (Salesforce)
│   ├── websocket.py              # WebSocket (React UI)
│   └── sse.py                    # Server-Sent Events (IDEs)
# Note: Client libraries are in dcisionai_mcp_clients/ directory
# - React client: dcisionai_mcp_clients/react-mcp-client/
# - Salesforce client: dcisionai_mcp_clients/salesforce-mcp-client/
└── tests/                       # Test suite
    ├── test_tools.py
    ├── test_resources.py
    └── test_transports.py
```

---

## 🚀 Key Features

### 1. **Direct dcisionai_graph Integration**
- No HTTP client wrapper
- Direct Python imports
- Lower latency
- Simpler code

### 2. **Deployed Models Support** ⭐ **KEY FEATURE**
- Direct access to `MODEL_REGISTRY` from `api.models_endpoint`
- Direct execution via `run_deployed_model()` (no HTTP calls)
- Full support for all 4 deployed models:
  - `portfolio_optimization_v1`
  - `portfolio_rebalancing_v1`
  - `capital_deployment_v1`
  - `fund_structure_v1`
- Model listing via `list_deployed_models()` (direct import)

### 2. **Multi-Transport Support**
- **HTTP JSON-RPC 2.0**: For Salesforce and other HTTP clients
- **WebSocket**: For React UI real-time streaming
- **SSE**: For IDE integrations (Cursor, VS Code, etc.)

### 3. **Anthropic MCP Best Practices**
- ✅ Tool annotations (`readOnlyHint`, `destructiveHint`, `title`)
- ✅ Clear error handling
- ✅ Token-efficient responses
- ✅ Proper tool descriptions
- ✅ Resource caching

### 4. **Client Libraries**
- React MCP client (hooks for easy integration)
- Salesforce MCP client (existing, compatible)
- IDE MCP client (standard MCP SDK)

---

## 📋 Implementation Phases

### Phase 1: Core MCP Server (Current)
- ✅ Create directory structure
- ⏳ Copy and adapt `dcisionai_graph` imports
- ⏳ Implement basic tools (optimization, NLP, mapping)
- ⏳ Implement resources (models, solvers)
- ⏳ HTTP JSON-RPC 2.0 transport

### Phase 2: WebSocket Support
- ⏳ WebSocket transport for React UI
- ⏳ Real-time streaming support
- ⏳ Session management

### Phase 3: React MCP Client (in dcisionai_mcp_clients/)
- ⏳ Create `dcisionai_mcp_clients/react-mcp-client/`
- ⏳ React hooks for MCP tools
- ⏳ React hooks for MCP resources
- ⏳ WebSocket hook for streaming
- ⏳ Migration guide for existing UI

### Phase 4: Testing & Migration
- ⏳ Test with Salesforce client
- ⏳ Test with React UI
- ⏳ Performance benchmarking
- ⏳ Migration guide

---

## 🔧 Development

### Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Run server
python server.py
```

### Environment Variables

```bash
# MCP Server Configuration
MCP_SERVER_PORT=8080
MCP_SERVER_HOST=0.0.0.0

# dcisionai_graph Configuration
DCISIONAI_DOMAIN_FILTER=all  # or "ria", "pe", "hf", etc.

# Anthropic Claude (for concept mapping)
ANTHROPIC_API_KEY=sk-ant-...

# Logging
DCISIONAI_LOG_LEVEL=INFO
```

---

## 📚 Documentation

- [Architecture](./ARCHITECTURE.md) - Detailed architecture documentation
- [Anthropic MCP Compliance](./ANTHROPIC_COMPLIANCE.md) - Compliance checklist
- [Migration Guide](./MIGRATION.md) - Migrating from v1.0 to v2.0

---

## 🎯 Goals

1. **Simplicity**: One service instead of two
2. **Performance**: Lower latency (direct imports)
3. **Consistency**: All clients use MCP protocol
4. **Maintainability**: Single codebase
5. **Standards**: Follow Anthropic MCP best practices

---

## 📝 Notes

- This is a **parallel development** - existing `dcisionai_mcp_server/` continues to work
- Migration will be gradual - both versions can coexist
- No changes to `dcisionai_graph/` - it remains unchanged
- No changes to `dcisionai_mcp_clients/` - they work with both versions

---

**Last Updated**: 2025-11-25

