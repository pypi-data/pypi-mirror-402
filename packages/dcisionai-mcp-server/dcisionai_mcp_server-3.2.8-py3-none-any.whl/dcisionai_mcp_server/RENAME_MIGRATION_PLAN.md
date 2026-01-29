# Rename Migration Plan: dcisionai_mcp_server_2.0 → dcisionai_mcp_server

**Date**: 2025-11-25  
**Status**: ⚠️ **RISK ASSESSMENT** - Careful planning required

---

## 🎯 Goal

Move `dcisionai_mcp_server` → `deprecated/dcisionai_mcp_server`  
Rename `dcisionai_mcp_server_2.0` → `dcisionai_mcp_server`  
**Result**: Clean codebase with seamless production deployment

---

## ⚠️ Risk Assessment

### High Risk Areas

#### 1. **PyPI Package Name** (`pyproject.toml`) ⚠️ **CRITICAL**

**Current**:
```toml
name = "dcisionai-mcp-server"
packages = ["dcisionai_mcp_server"]
dcisionai-mcp-server = "dcisionai_mcp_server.mcp_server:entry_point"
```

**Risk**: 
- ⚠️ **PyPI package name conflicts** - If package is published, renaming breaks existing installs
- ⚠️ **Entry point changes** - External tools using `dcisionai-mcp-server` CLI will break
- ⚠️ **Version conflicts** - Old and new packages might conflict

**Mitigation**:
- Check if package is published to PyPI
- If published: Keep old package name OR publish new version with migration notice
- Update entry point to new location

#### 2. **Railway Deployment Configs** ⚠️ **CRITICAL**

**Files**:
- `railway.toml` ✅ Already updated to v2.0
- `railway.mcp.toml` ⚠️ Still references old server
- `Dockerfile.mcp` ✅ Already updated
- `nixpacks.mcp.toml` ✅ Already updated

**Risk**:
- ⚠️ **Active deployments** - Railway might be using old configs
- ⚠️ **Multiple config files** - `railway.mcp.toml` still references old server

**Mitigation**:
- Update `railway.mcp.toml` OR remove if unused
- Verify which config Railway actually uses
- Test deployment before renaming

#### 3. **Git History & Branches** ⚠️ **MEDIUM RISK**

**Current State**:
- Branch: `mcp-server` (active)
- Uncommitted changes present
- Multiple branches exist

**Risk**:
- ⚠️ **Git history** - Renaming directories loses history
- ⚠️ **Branch conflicts** - Other branches might reference old paths
- ⚠️ **Merge conflicts** - Future merges might conflict

**Mitigation**:
- Use `git mv` to preserve history
- Check all branches for references
- Create backup branch before renaming

#### 4. **Internal Imports** ✅ **LOW RISK**

**Current**:
- Uses relative imports (`.config`, `.tools`)
- Uses `importlib` with file paths
- No hardcoded `dcisionai_mcp_server_2.0` in imports

**Risk**: ✅ **LOW** - Relative imports will work fine

---

## 📋 Migration Checklist

### Pre-Migration (Risk Mitigation)

- [ ] **Check PyPI**: Is `dcisionai-mcp-server` published?
- [ ] **Check Railway**: Which config file is actually used?
- [ ] **Check Git**: Are there uncommitted changes?
- [ ] **Check Branches**: Do other branches reference old paths?
- [ ] **Backup**: Create backup branch
- [ ] **Test**: Verify current deployment works

### Migration Steps (If Safe)

1. **Update Deployment Configs**:
   - [ ] Update `railway.toml` (if not already done)
   - [ ] Update `railway.mcp.toml` OR remove
   - [ ] Update `Dockerfile.mcp` (if not already done)
   - [ ] Update `nixpacks.mcp.toml` (if not already done)

2. **Move Old Server**:
   - [ ] `git mv dcisionai_mcp_server deprecated/dcisionai_mcp_server`
   - [ ] Verify move preserved history

3. **Rename New Server**:
   - [ ] `git mv dcisionai_mcp_server_2.0 dcisionai_mcp_server`
   - [ ] Verify move preserved history

4. **Update All References**:
   - [ ] Update `railway.toml` paths
   - [ ] Update `Dockerfile.mcp` paths
   - [ ] Update `nixpacks.mcp.toml` paths
   - [ ] Update `start_all.sh` paths
   - [ ] Update `stop_all.sh` paths
   - [ ] Update `pyproject.toml` (if safe)
   - [ ] Update documentation references

5. **Test**:
   - [ ] Test local startup
   - [ ] Test Docker build
   - [ ] Test imports work
   - [ ] Test Railway deployment (staging first)

### Post-Migration

- [ ] Verify production deployment
- [ ] Monitor for 24-48 hours
- [ ] Update documentation
- [ ] Remove deprecated directory after verification

---

## 🚨 Alternative: Keep `_2.0` Suffix

### If Risks Are Too High

**Option**: Keep `dcisionai_mcp_server_2.0` name

**Pros**:
- ✅ **Zero risk** - No breaking changes
- ✅ **Clear versioning** - Explicitly shows it's v2.0
- ✅ **No deployment issues** - Current configs work

**Cons**:
- ❌ **Not ideal** - `_2.0` suffix is awkward
- ❌ **Confusing** - Two directories with similar names

**Recommendation**: ⚠️ **Consider keeping `_2.0` if PyPI package is published**

---

## 📊 Risk vs Benefit Analysis

| Aspect | Risk Level | Impact | Mitigation |
|--------|------------|--------|------------|
| **PyPI Package** | ⚠️ **HIGH** | Breaks external installs | Check if published, version bump |
| **Railway Deploy** | ⚠️ **MEDIUM** | Deployment breaks | Test staging first |
| **Git History** | ⚠️ **LOW** | History preserved | Use `git mv` |
| **Internal Code** | ✅ **LOW** | Should work fine | Relative imports |
| **Documentation** | ✅ **LOW** | Easy to update | Search and replace |

---

## 🎯 Recommendation

### **CONDITIONAL APPROVAL** ⚠️

**Proceed IF**:
1. ✅ PyPI package is NOT published (or we can handle version bump)
2. ✅ Railway configs are verified and updated
3. ✅ Git state is clean (commit current changes first)
4. ✅ Staging deployment tested successfully

**DO NOT Proceed IF**:
1. ❌ PyPI package is published and actively used
2. ❌ Railway production is using old configs
3. ❌ Git has uncommitted critical changes
4. ❌ Cannot test staging deployment

---

## 🔄 Safe Migration Path

### Phase 1: Preparation (Low Risk)

1. **Commit current changes**
2. **Check PyPI status**
3. **Verify Railway configs**
4. **Create backup branch**

### Phase 2: Staging Test (Medium Risk)

1. **Update configs to use new name**
2. **Test staging deployment**
3. **Verify everything works**

### Phase 3: Production (High Risk)

1. **Deploy to production**
2. **Monitor closely**
3. **Have rollback plan ready**

---

## 📝 Next Steps

1. **Check PyPI**: `pip search dcisionai-mcp-server` or check PyPI website
2. **Check Railway**: Which config file is actually used?
3. **Check Git**: Commit current changes
4. **Decide**: Proceed with rename OR keep `_2.0` suffix

---

**Last Updated**: 2025-11-25

