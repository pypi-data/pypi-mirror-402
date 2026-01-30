#!/bin/bash

# Production Health Check Script
# Checks if Railway MCP server is accessible and endpoints are working

MCP_SERVER_URL="${MCP_SERVER_URL:-https://dcisionai-mcp-server-production.up.railway.app}"

echo "================================================================================"
echo "PRODUCTION MCP SERVER HEALTH CHECK"
echo "================================================================================"
echo ""
echo "Server URL: $MCP_SERVER_URL"
echo ""

# Test 1: Health Check
echo "1. Testing Health Endpoint..."
HEALTH_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" "$MCP_SERVER_URL/health")
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
HEALTH_BODY=$(echo "$HEALTH_RESPONSE" | sed '/HTTP_CODE/d')

if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ Health check passed (HTTP $HTTP_CODE)"
    echo "   Response: $HEALTH_BODY"
else
    echo "   ❌ Health check failed (HTTP $HTTP_CODE)"
    echo "   Response: $HEALTH_BODY"
fi
echo ""

# Test 2: CORS Preflight
echo "2. Testing CORS Preflight (OPTIONS)..."
CORS_RESPONSE=$(curl -s -X OPTIONS \
    -H "Origin: https://platform.dcisionai.com" \
    -H "Access-Control-Request-Method: POST" \
    -H "Access-Control-Request-Headers: content-type" \
    -w "\nHTTP_CODE:%{http_code}" \
    "$MCP_SERVER_URL/api/jobs/submit")
CORS_HTTP_CODE=$(echo "$CORS_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
CORS_HEADERS=$(curl -s -I -X OPTIONS \
    -H "Origin: https://platform.dcisionai.com" \
    -H "Access-Control-Request-Method: POST" \
    "$MCP_SERVER_URL/api/jobs/submit" | grep -i "access-control")

if [ "$CORS_HTTP_CODE" = "200" ] || [ "$CORS_HTTP_CODE" = "204" ]; then
    echo "   ✅ CORS preflight passed (HTTP $CORS_HTTP_CODE)"
    echo "   CORS Headers:"
    echo "$CORS_HEADERS" | sed 's/^/      /'
else
    echo "   ❌ CORS preflight failed (HTTP $CORS_HTTP_CODE)"
fi
echo ""

# Test 3: Job Submit Endpoint (should return 400 for empty body, but endpoint should exist)
echo "3. Testing Job Submit Endpoint..."
JOB_SUBMIT_RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -H "Origin: https://platform.dcisionai.com" \
    -d '{}' \
    -w "\nHTTP_CODE:%{http_code}" \
    "$MCP_SERVER_URL/api/jobs/submit")
JOB_HTTP_CODE=$(echo "$JOB_SUBMIT_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
JOB_BODY=$(echo "$JOB_SUBMIT_RESPONSE" | sed '/HTTP_CODE/d')

if [ "$JOB_HTTP_CODE" = "400" ]; then
    echo "   ✅ Job submit endpoint exists (HTTP 400 - expected for empty body)"
    echo "   Response: $JOB_BODY"
elif [ "$JOB_HTTP_CODE" = "202" ]; then
    echo "   ⚠️  Job submit accepted (unexpected - should require problem_description)"
elif [ "$JOB_HTTP_CODE" = "401" ]; then
    echo "   ❌ Authentication required (HTTP 401)"
    echo "   Response: $JOB_BODY"
elif [ "$JOB_HTTP_CODE" = "404" ]; then
    echo "   ❌ Endpoint not found (HTTP 404)"
    echo "   Response: $JOB_BODY"
else
    echo "   ⚠️  Unexpected response (HTTP $JOB_HTTP_CODE)"
    echo "   Response: $JOB_BODY"
fi
echo ""

# Test 4: Resource Endpoint
echo "4. Testing Resource Endpoint..."
RESOURCE_RESPONSE=$(curl -s -X GET \
    -H "Origin: https://platform.dcisionai.com" \
    -w "\nHTTP_CODE:%{http_code}" \
    "$MCP_SERVER_URL/mcp/resources/dcisionai://models/list")
RESOURCE_HTTP_CODE=$(echo "$RESOURCE_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
RESOURCE_BODY=$(echo "$RESOURCE_RESPONSE" | sed '/HTTP_CODE/d' | head -c 200)

if [ "$RESOURCE_HTTP_CODE" = "200" ]; then
    echo "   ✅ Resource endpoint works (HTTP 200)"
    echo "   Response preview: ${RESOURCE_BODY:0:100}..."
elif [ "$RESOURCE_HTTP_CODE" = "404" ]; then
    echo "   ❌ Resource endpoint not found (HTTP 404)"
    echo "   Response: $RESOURCE_BODY"
else
    echo "   ⚠️  Unexpected response (HTTP $RESOURCE_HTTP_CODE)"
    echo "   Response: $RESOURCE_BODY"
fi
echo ""

# Test 5: Tools List Endpoint
echo "5. Testing Tools List Endpoint..."
TOOLS_RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -H "Origin: https://platform.dcisionai.com" \
    -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' \
    -w "\nHTTP_CODE:%{http_code}" \
    "$MCP_SERVER_URL/mcp/tools/list")
TOOLS_HTTP_CODE=$(echo "$TOOLS_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
TOOLS_BODY=$(echo "$TOOLS_RESPONSE" | sed '/HTTP_CODE/d' | head -c 200)

if [ "$TOOLS_HTTP_CODE" = "200" ]; then
    echo "   ✅ Tools list endpoint works (HTTP 200)"
    echo "   Response preview: ${TOOLS_BODY:0:100}..."
else
    echo "   ⚠️  Unexpected response (HTTP $TOOLS_HTTP_CODE)"
    echo "   Response: $TOOLS_BODY"
fi
echo ""

echo "================================================================================"
echo "SUMMARY"
echo "================================================================================"
echo ""
echo "If all tests pass, the issue is likely:"
echo "  1. React app not configured with correct MCP_SERVER_URL"
echo "  2. Browser CORS policy blocking requests"
echo "  3. Network connectivity issue"
echo ""
echo "Check Railway logs for:"
echo "  - CORS errors"
echo "  - 401 authentication errors"
echo "  - 404 not found errors"
echo "  - 500 server errors"
echo ""

