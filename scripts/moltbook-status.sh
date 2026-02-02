#!/bin/bash
# Moltbook API Status Checker
# Quick diagnostic to see which endpoints are working

AUSTN_HOME="${AUSTN_HOME:-$HOME/.austnomaton}"
source "$AUSTN_HOME/.env" 2>/dev/null

if [ -z "$MOLTBOOK_API_KEY" ]; then
    echo "ERROR: MOLTBOOK_API_KEY not set"
    exit 1
fi

BASE="https://www.moltbook.com/api/v1"
AUTH="Authorization: Bearer $MOLTBOOK_API_KEY"

echo "=== Moltbook API Status Check ==="
echo "Time: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# Test /agents/me (GET)
echo -n "GET /agents/me: "
BODY=$(curl -s "$BASE/agents/me" -H "$AUTH")
CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/agents/me" -H "$AUTH")
if [ "$CODE" = "200" ]; then
    KARMA=$(echo "$BODY" | grep -o '"karma":[0-9]*' | cut -d: -f2)
    echo "OK (karma: $KARMA)"
else
    echo "FAIL ($CODE)"
fi

# Test /posts (GET) - should list posts
echo -n "GET /posts: "
BODY=$(curl -s "$BASE/posts?limit=1" -H "$AUTH")
CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/posts?limit=1" -H "$AUTH")
if echo "$BODY" | grep -q '"success":true'; then
    echo "OK"
elif echo "$BODY" | grep -q '"error"'; then
    ERR=$(echo "$BODY" | grep -o '"error":"[^"]*"' | cut -d'"' -f4)
    echo "FAIL ($ERR)"
else
    echo "FAIL ($CODE)"
fi

# Test /posts create (dry run - don't actually post)
echo -n "POST /posts (auth check only): "
# We check if the auth is accepted by looking at error type
RESULT=$(curl -s "$BASE/posts" -H "$AUTH" -H "Content-Type: application/json" -d '{}')
if echo "$RESULT" | grep -q '"error":"Invalid API key"'; then
    echo "FAIL (key rejected)"
elif echo "$RESULT" | grep -q '"error":"Missing required'; then
    echo "OK (auth works, validation error expected)"
elif echo "$RESULT" | grep -q 'TimeoutError'; then
    echo "DEGRADED (backend timeout)"
else
    echo "UNKNOWN: $RESULT"
fi

# Summary
echo ""
echo "=== Summary ==="
echo "If /agents/me works but others fail: Backend issue"
echo "If all fail with 'Invalid API key': Regenerate key"
echo "If 'TimeoutError': Moltbook backend degraded"
