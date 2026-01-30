# DcisionAI Architecture Summary - MCP Server 2.0

**Date**: 2025-11-25  
**Audience**: PE, Engineering, Product, Customers

---

## 🎯 Executive Summary

**MCP Server 2.0** transforms DcisionAI from a **multi-service architecture** to a **single-service architecture**, making MCP the primary interface for all clients.

### Before vs After

| Aspect | Before (MCP Server 1.0) | After (MCP Server 2.0) |
|--------|------------------------|------------------------|
| **Services** | 2 (FastAPI + MCP Server) | 1 (MCP Server only) |
| **Protocol** | Mixed (HTTP REST + MCP) | Unified (MCP only) |
| **Latency** | ~150-300ms (HTTP hop) | ~0-50ms (direct call) |
| **Deployment** | Complex (2 services) | Simple (1 service) |
| **Maintenance** | Update 2 codebases | Update 1 codebase |

---

## 🏗️ Architecture Evolution

### Current Architecture (Pre-2.0)

```
┌─────────────────────────────────────────────────────────────┐
│                    DcisionAI Platform                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐         ┌──────────────────┐            │
│  │  React UI    │────────▶│  FastAPI Backend  │            │
│  │              │  HTTP   │  (api/)           │            │
│  └──────────────┘         └────────┬──────────┘            │
│                                     │                        │
│                                     │ Import                 │
│                                     ▼                        │
│                              ┌──────────────┐                │
│                              │ dcisionai_   │                │
│                              │   graph/     │                │
│                              │ (Core Engine)│                │
│                              └──────────────┘                │
│                                     ▲                        │
│                                     │ HTTP                   │
│  ┌──────────────┐         ┌────────┴──────────┐            │
│  │  Salesforce  │────────▶│  MCP Server 1.0  │            │
│  │              │  MCP    │  (Thin Adapter)   │            │
│  └──────────────┘         └──────────────────┘            │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

**Issues**:
- ❌ Two services to maintain
- ❌ HTTP overhead between services
- ❌ Mixed protocols (HTTP REST + MCP)
- ❌ Complex deployment

---

### New Architecture (MCP Server 2.0)

```
┌─────────────────────────────────────────────────────────────┐
│                    DcisionAI Platform                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐         ┌──────────────────┐            │
│  │  React UI    │────────▶│                  │            │
│  │  (MCP Client)│  MCP    │                  │            │
│  └──────────────┘         │                  │            │
│                            │   MCP Server 2.0  │            │
│  ┌──────────────┐         │   (Primary)       │            │
│  │  Salesforce  │────────▶│                  │            │
│  │  (MCP Client)│  MCP    │                  │            │
│  └──────────────┘         └────────┬──────────┘            │
│                                     │                        │
│                                     │ Direct Import         │
│                                     ▼                        │
│                              ┌──────────────┐                │
│                              │ dcisionai_   │                │
│                              │   graph/     │                │
│                              │ (Core Engine)│                │
│                              └──────────────┘                │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

**Benefits**:
- ✅ Single service
- ✅ Direct imports (no HTTP overhead)
- ✅ Unified protocol (MCP only)
- ✅ Simple deployment

---

## 📦 Component Status

### ✅ Kept Components

#### 1. `dcisionai_graph/` - Core Engine
**Status**: ✅ **NO CHANGES**

**What It Is**:
- Core optimization engine
- LangGraph workflows
- DAME solver
- Deployed models
- Domain configurations

**Why Kept**:
- Working production code
- Reusable across all clients
- No changes needed

**Deployment**:
- Python package/library
- Imported by MCP Server 2.0
- Can be used independently

---

#### 2. `dcisionai_mcp_clients/` - Platform Clients
**Status**: ✅ **UPDATED FOR 2.0**

**What It Is**:
- Salesforce MCP client (Apex/LWC)
- React MCP client (new, to be built)
- Platform-specific integrations

**Updates Needed**:
- ✅ Salesforce: Already compatible (HTTP JSON-RPC 2.0)
- ⏳ React: Needs MCP client library
- ⏳ Update endpoint URLs

---

### ⚠️ Deprecated Components

#### 1. `api/` (FastAPI Backend)
**Status**: ⚠️ **DEPRECATED** (Phased Out)

**What It Was**:
- HTTP REST API backend
- Served React UI
- Called by MCP Server 1.0

**Migration Path**:
- **Phase 1**: Keep running (backward compatibility)
- **Phase 2**: Migrate React UI to MCP client
- **Phase 3**: Retire FastAPI backend

**Timeline**: After React UI migration complete

---

#### 2. `dcisionai_mcp_server/` (MCP Server 1.0)
**Status**: ⚠️ **DEPRECATED** (Replaced by 2.0)

**What It Was**:
- Thin MCP protocol adapter
- Called FastAPI backend via HTTP
- Protocol translation layer

**Migration Path**:
- **Immediate**: New deployments use MCP Server 2.0
- **Existing**: Migrate to MCP Server 2.0
- **Timeline**: After all clients migrated

---

## 🚀 Customer Deployment Scenarios

### Scenario 1: Cloud SaaS (Recommended)

**Deployment**:
```
┌─────────────────────────────────────────┐
│  Railway/Cloud Platform                │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  MCP Server 2.0                 │  │
│  │  - HTTP JSON-RPC 2.0            │  │
│  │  - WebSocket                    │  │
│  │  - SSE                          │  │
│  └──────────────┬───────────────────┘  │
│                 │                       │
│                 │ Import                │
│                 ▼                       │
│  ┌──────────────────────────────────┐  │
│  │  dcisionai_graph (Package)      │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
         ▲                    ▲
         │                    │
    ┌────┴────┐         ┌─────┴─────┐
    │React UI │         │ Salesforce │
    │(MCP)    │         │ (MCP)     │
    └─────────┘         └───────────┘
```

**Characteristics**:
- ✅ Single service deployment
- ✅ All clients connect via MCP
- ✅ Scalable, cloud-native
- ✅ Easy to maintain

**Use Case**: Most customers

---

### Scenario 2: On-Premise Enterprise

**Deployment**:
```
┌─────────────────────────────────────────┐
│  Customer Infrastructure                │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  MCP Server 2.0                  │  │
│  │  (Docker Container)              │  │
│  └──────────────┬───────────────────┘  │
│                 │                       │
│                 │ Import                │
│                 ▼                       │
│  ┌──────────────────────────────────┐  │
│  │  dcisionai_graph (Package)      │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
         ▲                    ▲
         │                    │
    ┌────┴────┐         ┌─────┴─────┐
    │Internal │         │ Salesforce │
    │React UI │         │ (MCP)     │
    │(MCP)    │         │           │
    └─────────┘         └───────────┘
```

**Characteristics**:
- ✅ Self-hosted deployment
- ✅ Customer controls infrastructure
- ✅ Same MCP protocol
- ✅ Can integrate with customer systems

**Use Case**: Enterprise, regulated industries

---

### Scenario 3: Hybrid (Cloud + On-Premise)

**Deployment**:
```
┌──────────────────┐         ┌──────────────────┐
│  Cloud (SaaS)    │         │  On-Premise     │
│                  │         │                  │
│  ┌────────────┐ │         │  ┌────────────┐ │
│  │MCP Server  │ │         │  │MCP Server  │ │
│  │2.0 (Cloud) │ │         │  │2.0 (Local) │ │
│  └─────┬──────┘ │         │  └─────┬──────┘ │
│        │         │         │        │        │
│        │         │         │        │        │
│        ▼         │         │        ▼        │
│  ┌────────────┐ │         │  ┌────────────┐ │
│  │dcisionai_  │ │         │  │dcisionai_  │ │
│  │graph       │ │         │  │graph       │ │
│  └────────────┘ │         │  └────────────┘ │
└──────────────────┘         └──────────────────┘
```

**Characteristics**:
- ✅ Cloud for public-facing
- ✅ On-premise for sensitive data
- ✅ Same MCP protocol
- ✅ Customer chooses deployment

**Use Case**: Large enterprises with data sovereignty requirements

---

## 🔄 Migration Timeline

### Phase 1: Parallel Operation (Current) ✅

**Duration**: 1-2 months

**What Happens**:
- ✅ MCP Server 2.0 deployed alongside existing services
- ✅ Both MCP Server 1.0 and 2.0 available
- ✅ FastAPI backend continues running
- ✅ React UI continues using FastAPI
- ✅ Salesforce can use either MCP Server

**Goal**: Zero downtime migration

---

### Phase 2: Client Migration ⏳

**Duration**: 1-2 months

**What Happens**:
- ✅ Salesforce migrates to MCP Server 2.0
- ⏳ React UI migrates to MCP client (WebSocket)
- ✅ New customers onboard to MCP Server 2.0
- ⚠️ FastAPI backend marked deprecated

**Goal**: All clients on MCP Server 2.0

---

### Phase 3: Retirement 📅

**Duration**: 1 month

**What Happens**:
- ❌ FastAPI backend retired
- ❌ MCP Server 1.0 retired
- ✅ Only MCP Server 2.0 remains
- ✅ Simplified architecture

**Goal**: Clean, single-service architecture

---

## 📊 What Gets Retired

### ❌ Retired Components

1. **`api/` (FastAPI Backend)**
   - **Why**: React UI migrates to MCP client
   - **When**: After React UI migration complete
   - **Impact**: No HTTP REST API (use MCP instead)

2. **`dcisionai_mcp_server/` (MCP Server 1.0)**
   - **Why**: Replaced by MCP Server 2.0
   - **When**: After all clients migrated
   - **Impact**: Thin adapter no longer needed

### ✅ Kept Components

1. **`dcisionai_graph/`**
   - **Why**: Core engine, reusable
   - **Status**: No changes, continues as-is

2. **`dcisionai_mcp_clients/`**
   - **Why**: Platform integrations needed
   - **Status**: Updated for MCP Server 2.0

---

## 🎯 Customer Impact

### For Existing Customers

**Migration Required**: ✅ **YES** (Gradual, Non-Breaking)

**Steps**:
1. Update endpoint URLs to MCP Server 2.0
2. Test compatibility
3. Migrate React UI (if applicable)
4. Decommission old services

**Timeline**: 2-3 months (gradual migration)

**Benefits After Migration**:
- ✅ Better performance (lower latency)
- ✅ Simpler architecture
- ✅ Unified protocol
- ✅ Easier maintenance

---

### For New Customers

**Deployment**: ✅ **MCP Server 2.0 Only**

**No Legacy Services**: New customers start with clean architecture

**Benefits**:
- ✅ Simpler deployment
- ✅ Better performance
- ✅ Modern architecture
- ✅ Full MCP support

---

## 📈 Benefits Summary

### 1. **Simplified Deployment**
- ✅ Single service (vs 2 services)
- ✅ Fewer moving parts
- ✅ Easier to maintain

### 2. **Better Performance**
- ✅ Direct imports (no HTTP overhead)
- ✅ Lower latency (~0-50ms vs ~150-300ms)
- ✅ More efficient

### 3. **Unified Protocol**
- ✅ All clients use MCP
- ✅ Consistent interface
- ✅ Easier to support

### 4. **Future-Proof**
- ✅ MCP is standard protocol
- ✅ Easy to add new clients
- ✅ Scalable architecture

---

## 📝 Summary

### Architecture Evolution

**Before (MCP Server 1.0)**:
- 3 services: FastAPI + MCP Server + `dcisionai_graph`
- Mixed protocols: HTTP REST + MCP
- Complex deployment

**After (MCP Server 2.0)**:
- 1 service: MCP Server 2.0 + `dcisionai_graph`
- Unified protocol: MCP only
- Simple deployment

### What Stays
- ✅ `dcisionai_graph` (core engine)
- ✅ `dcisionai_mcp_clients` (platform clients)

### What Goes
- ❌ `api/` (FastAPI backend)
- ❌ `dcisionai_mcp_server/` (MCP Server 1.0)

### Customer Impact
- ✅ Simpler deployments
- ✅ Better performance
- ✅ Unified interface
- ⚠️ Migration required (gradual, non-breaking)

---

## 📚 Related Documentation

- **`DEPLOYMENT_ARCHITECTURE.md`** - Detailed deployment scenarios
- **`CUSTOMER_DEPLOYMENT_GUIDE.md`** - Customer-facing guide
- **`MIGRATION.md`** - Migration guide from v1.0 to v2.0
- **`ARCHITECTURE.md`** - Detailed architecture documentation

---

**Last Updated**: 2025-11-25

