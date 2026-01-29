#!/bin/bash

echo "================================================================================"
echo "JOB SUBMIT 500 ERROR DIAGNOSTIC"
echo "================================================================================"
echo ""

# Check if Railway CLI is available
if ! command -v railway &> /dev/null; then
    echo "⚠️  Railway CLI not found. Install with: npm i -g @railway/cli"
    echo ""
    echo "Checking environment variables locally..."
    echo ""
    
    # Check local .env files
    if [ -f ".env.production" ]; then
        echo "📄 Found .env.production:"
        grep -E "SUPABASE_URL|SUPABASE_API_KEY|REDIS_URL|CELERY" .env.production | sed 's/=.*/=***HIDDEN***/'
    fi
    
    if [ -f ".env.staging" ]; then
        echo "📄 Found .env.staging:"
        grep -E "SUPABASE_URL|SUPABASE_API_KEY|REDIS_URL|CELERY" .env.staging | sed 's/=.*/=***HIDDEN***/'
    fi
    
    echo ""
    echo "To check Railway logs:"
    echo "  1. Install Railway CLI: npm i -g @railway/cli"
    echo "  2. Login: railway login"
    echo "  3. Link project: railway link"
    echo "  4. View logs: railway logs | grep -i 'error\|500\|failed'"
    exit 0
fi

echo "✅ Railway CLI found"
echo ""

# Check if linked to a project
if ! railway status &> /dev/null; then
    echo "⚠️  Not linked to a Railway project"
    echo "  Run: railway link"
    exit 1
fi

echo "✅ Linked to Railway project"
echo ""

echo "================================================================================"
echo "STEP 1: Check Recent Errors in Railway Logs"
echo "================================================================================"
echo ""
echo "Fetching last 50 error lines..."
railway logs | grep -i "error\|500\|failed\|exception" | tail -50
echo ""

echo "================================================================================"
echo "STEP 2: Check Job Submit Endpoint Errors"
echo "================================================================================"
echo ""
echo "Searching for /api/jobs/submit errors..."
railway logs | grep -i "/api/jobs/submit\|job submission\|Failed to create job\|Failed to dispatch" | tail -20
echo ""

echo "================================================================================"
echo "STEP 3: Check Supabase Connection Errors"
echo "================================================================================"
echo ""
echo "Searching for Supabase errors..."
railway logs | grep -i "supabase\|Failed to insert job\|Failed to create job record" | tail -20
echo ""

echo "================================================================================"
echo "STEP 4: Check Redis/Celery Connection Errors"
echo "================================================================================"
echo ""
echo "Searching for Redis/Celery errors..."
railway logs | grep -i "redis\|celery\|broker\|Failed to dispatch job to Celery" | tail -20
echo ""

echo "================================================================================"
echo "STEP 5: Check Environment Variables"
echo "================================================================================"
echo ""
echo "Checking Railway environment variables..."
railway variables | grep -E "SUPABASE|REDIS|CELERY" || echo "⚠️  No matching environment variables found"
echo ""

echo "================================================================================"
echo "STEP 6: Check Celery Worker Status"
echo "================================================================================"
echo ""
echo "Searching for Celery worker logs..."
railway logs | grep -i "celery.*worker\|worker.*started\|celery.*ready" | tail -10
echo ""

echo "================================================================================"
echo "DIAGNOSIS SUMMARY"
echo "================================================================================"
echo ""
echo "Common causes of 500 errors on /api/jobs/submit:"
echo ""
echo "1. ❌ Supabase Connection Failure"
echo "   - Missing SUPABASE_URL or SUPABASE_API_KEY"
echo "   - Invalid Supabase credentials"
echo "   - Network connectivity issue"
echo "   - Fix: Check Railway environment variables"
echo ""
echo "2. ❌ Redis Connection Failure"
echo "   - Missing REDIS_URL environment variable"
echo "   - Redis service not accessible from MCP server"
echo "   - Redis project not linked/shared"
echo "   - Fix: Set REDIS_URL in Railway environment variables"
echo ""
echo "3. ❌ Celery Worker Not Running"
echo "   - No Celery worker process started"
echo "   - Worker crashed or not deployed"
echo "   - Fix: Ensure Celery worker is running in Railway"
echo ""
echo "4. ❌ Database Schema Issue"
echo "   - async_jobs table doesn't exist"
echo "   - Missing required columns"
echo "   - Fix: Run database migrations"
echo ""
echo "================================================================================"
echo "NEXT STEPS"
echo "================================================================================"
echo ""
echo "1. Check Railway Dashboard → MCP Server → Variables"
echo "   - Verify SUPABASE_URL and SUPABASE_API_KEY are set"
echo "   - Verify REDIS_URL points to your Redis project"
echo ""
echo "2. Check Railway Dashboard → MCP Server → Logs"
echo "   - Look for startup errors"
echo "   - Check for connection failures"
echo ""
echo "3. Verify Redis Project is Accessible"
echo "   - Railway Dashboard → Redis Project → Settings → Networking"
echo "   - Ensure MCP Server can connect to Redis"
echo ""
echo "4. Check Celery Worker"
echo "   - Railway Dashboard → MCP Server → Deployments"
echo "   - Verify worker process is running"
echo "   - Check worker logs for errors"
echo ""
echo "================================================================================"

