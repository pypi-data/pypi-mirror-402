# Architecture Decision: Should dcisionai_graph be Bundled?

**Date**: 2025-11-25  
**Decision Maker**: PE Review  
**Status**: Under Review

---

## Question

Should `dcisionai_graph` be bundled inside `dcisionai_mcp_server_2.0`, or remain as an independent package?

---

## Current Architecture

```
dcisionai_graph/          # Core optimization engine (independent)
dcisionai_mcp_server_2.0/ # MCP protocol adapter (imports dcisionai_graph)
dcisionai_mcp_clients/    # Platform clients (React, Salesforce)
```

**Current Approach**: `mcp_server_2.0` imports `dcisionai_graph` as external dependency

---

## Analysis: PE Perspective

### Option 1: Keep Separate (Current)

**Pros**:
- ✅ **Separation of Concerns**: Core engine is independent of protocol
- ✅ **Reusability**: `dcisionai_graph` can be used by other clients (CLI, direct Python, future protocols)
- ✅ **Independent Evolution**: Can version/deploy independently
- ✅ **Testing**: Can test core engine without MCP infrastructure
- ✅ **Clear Boundaries**: Each package has single responsibility
- ✅ **Future-Proof**: If we add gRPC, REST, or other protocols, they can all use `dcisionai_graph`

**Cons**:
- ❌ **Import Complexity**: Need to manage Python paths (current pain point)
- ❌ **Deployment Complexity**: Two packages to deploy/version
- ❌ **Dependency Management**: Need to ensure versions are compatible

### Option 2: Bundle Inside MCP Server 2.0

**Pros**:
- ✅ **Simpler Imports**: No path management needed
- ✅ **Single Deployment**: One package to deploy
- ✅ **No Version Conflicts**: Everything in sync
- ✅ **Easier Development**: Everything in one place

**Cons**:
- ❌ **Tight Coupling**: MCP server becomes monolithic
- ❌ **No Reusability**: Can't use core engine without MCP
- ❌ **Violates SRP**: MCP server becomes both protocol adapter AND core engine
- ❌ **Future Limitations**: If we need gRPC or REST, we'd duplicate the core engine

---

## PE Recommendation: **Keep Separate** ✅

### Reasoning:

1. **Single Responsibility Principle**
   - `dcisionai_graph` = Core optimization engine
   - `dcisionai_mcp_server_2.0` = MCP protocol adapter
   - These are distinct concerns

2. **Future-Proofing**
   - If we add gRPC adapter, REST adapter, or CLI tool, they can all use `dcisionai_graph`
   - Bundling would force duplication

3. **Reusability**
   - Core engine should be usable independently
   - Example: Direct Python scripts, Jupyter notebooks, other frameworks

4. **Testing & Development**
   - Can test core engine without MCP overhead
   - Can develop/debug independently

5. **Industry Best Practice**
   - Core libraries are typically separate from protocol adapters
   - Examples: `requests` (core) vs `flask` (HTTP adapter), `sqlalchemy` (core) vs `flask-sqlalchemy` (adapter)

---

## Mitigation for Current Pain Points

The import complexity can be solved:

### Solution 1: Proper Package Installation
```bash
pip install -e .  # Install dcisionai_graph as package
```

### Solution 2: PYTHONPATH Management
```python
# In start_mcp_server.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

### Solution 3: Use setup.py/pyproject.toml
```python
# setup.py
install_requires=[
    'dcisionai-graph @ file:///${PROJECT_ROOT}/dcisionai_graph',
]
```

---

## Alternative: Hybrid Approach

If deployment simplicity is critical:

**Option 3: Bundle for Deployment, Separate for Development**

- Keep `dcisionai_graph` separate in source
- Bundle into `mcp_server_2.0` during build/deployment
- Use build tools (setuptools, poetry) to create single distributable

**Trade-off**: More complex build process, but simpler runtime

---

## Decision Matrix

| Criteria | Separate | Bundled | Hybrid |
|----------|----------|---------|--------|
| **Reusability** | ✅ High | ❌ None | ⚠️ Limited |
| **Simplicity** | ⚠️ Medium | ✅ High | ⚠️ Medium |
| **Future-Proof** | ✅ Yes | ❌ No | ⚠️ Partial |
| **Maintainability** | ✅ High | ⚠️ Medium | ⚠️ Medium |
| **Deployment** | ⚠️ Complex | ✅ Simple | ✅ Simple |

---

## Recommendation

**Keep `dcisionai_graph` separate**, but:

1. ✅ Fix import paths properly (use proper package installation)
2. ✅ Add `setup.py`/`pyproject.toml` for proper dependency management
3. ✅ Document installation process clearly
4. ✅ Consider hybrid approach if deployment becomes blocker

**Rationale**: The architectural benefits (reusability, separation of concerns, future-proofing) outweigh the current import complexity, which is solvable with proper tooling.

---

## Action Items

1. [ ] Create proper `setup.py` for `dcisionai_graph`
2. [ ] Update `mcp_server_2.0` to use proper package imports
3. [ ] Document installation process
4. [ ] Consider build-time bundling if needed for deployment

---

**Last Updated**: 2025-11-25

