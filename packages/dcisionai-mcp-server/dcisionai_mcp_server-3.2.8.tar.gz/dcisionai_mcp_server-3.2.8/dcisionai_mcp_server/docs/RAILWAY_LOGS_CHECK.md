# How to Check Railway Logs

## Accessing Railway Logs

### Option 1: Railway Dashboard (Web UI)

1. Go to [Railway Dashboard](https://railway.app)
2. Navigate to your project → MCP Server service
3. Click on **"Logs"** tab
4. Filter by:
   - Time range (when errors occurred)
   - Search for: `error`, `401`, `404`, `CORS`, `NetworkError`

### Option 2: Railway CLI

```bash
# Install Railway CLI (if not installed)
npm i -g @railway/cli

# Login
railway login

# Link to project
railway link

# View logs
railway logs

# Follow logs in real-time
railway logs --follow

# Filter logs
railway logs | grep -i "error\|401\|cors"
```

### Option 3: Railway API

```bash
# Get service logs via API
curl -H "Authorization: Bearer $RAILWAY_TOKEN" \
  "https://api.railway.app/v1/services/{service_id}/logs"
```

## What to Look For

### Common Errors

1. **CORS Errors**
   ```
   CORS policy blocked origin: https://platform.dcisionai.com
   ```
   - **Fix**: Check `MCP_CORS_ORIGINS` environment variable

2. **401 Authentication Errors**
   ```
   401 - invalid x-api-key
   ```
   - **Fix**: Check if `MCP_API_KEY` is set and matches client

3. **404 Not Found**
   ```
   404 - /api/jobs/submit not found
   ```
   - **Fix**: Check if routes are registered correctly

4. **500 Server Errors**
   ```
   500 - Internal server error
   ```
   - **Fix**: Check full stack trace in logs

5. **Celery Connection Errors**
   ```
   Failed to connect to Redis/Celery broker
   ```
   - **Fix**: Check Redis/Celery configuration

## Log Analysis Commands

### Filter by Error Type
```bash
railway logs | grep -i "error"
railway logs | grep -i "401"
railway logs | grep -i "cors"
railway logs | grep -i "networkerror"
```

### Filter by Endpoint
```bash
railway logs | grep "/api/jobs/submit"
railway logs | grep "/mcp/resources"
railway logs | grep "/mcp/tools"
```

### Filter by Time
```bash
# Last 100 lines
railway logs | tail -100

# Last hour
railway logs --since 1h
```

## Debugging Production Issues

### Step 1: Check Recent Errors
```bash
railway logs | grep -i "error" | tail -50
```

### Step 2: Check CORS Headers
Look for logs showing CORS headers:
```
CORS origins configured: ['*'] (production: True)
access-control-allow-origin: https://platform.dcisionai.com
```

### Step 3: Check Job Submissions
```bash
railway logs | grep "job submission\|/api/jobs/submit"
```

### Step 4: Check Resource Requests
```bash
railway logs | grep "/mcp/resources"
```

## Common Issues and Solutions

### Issue: NetworkError in Browser

**Symptoms**: Browser console shows `NetworkError: Failed to fetch`

**Check Logs For**:
- CORS errors
- 401 authentication errors
- Connection refused errors

**Solutions**:
1. Verify CORS configuration
2. Check API key if required
3. Verify server is running
4. Check network connectivity

### Issue: Jobs Not Submitting

**Symptoms**: Job submission fails silently

**Check Logs For**:
- `/api/jobs/submit` endpoint errors
- Celery connection errors
- Database connection errors

**Solutions**:
1. Check Celery worker is running
2. Verify Redis connection
3. Check database connectivity
4. Verify job record creation

### Issue: Resource Fetch Fails

**Symptoms**: `NetworkError` when fetching resources

**Check Logs For**:
- `/mcp/resources` endpoint errors
- 404 not found errors
- CORS errors

**Solutions**:
1. Verify resource URI format
2. Check CORS configuration
3. Verify endpoint exists
4. Check authentication if required

## Exporting Logs

### Export to File
```bash
railway logs > railway_logs_$(date +%Y%m%d_%H%M%S).txt
```

### Export Filtered Logs
```bash
railway logs | grep -i "error\|401\|cors" > errors_$(date +%Y%m%d_%H%M%S).txt
```

## Monitoring

### Set Up Alerts
1. Railway Dashboard → Service → Settings → Alerts
2. Configure alerts for:
   - Error rate > threshold
   - Response time > threshold
   - 5xx errors

### Check Metrics
1. Railway Dashboard → Service → Metrics
2. Monitor:
   - Request rate
   - Error rate
   - Response time
   - CPU/Memory usage

