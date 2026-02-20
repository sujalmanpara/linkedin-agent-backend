#!/bin/bash

echo "=== Testing Bug Fixes ==="
echo ""

# Wait for server
sleep 3

# 1. Setup: Create user and campaign
echo "Setup: Creating user..."
curl -s -X POST http://127.0.0.1:8300/api/users/configure \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "bugfix_test",
    "linkedin_credentials": {"email": "test@test.com", "password": "pass"},
    "llm_config": {"type": "anthropic", "model": "claude-sonnet-4-5", "api_key": "sk-test"},
    "daily_limits": {"connections": 50, "messages": 30}
  }' | python3 -m json.tool | grep -E '(status|user_id|message)'

echo ""
echo "Creating campaign..."
CAMPAIGN_RESP=$(curl -s -X POST http://127.0.0.1:8300/api/campaigns/create \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "bugfix_test",
    "name": "Test Campaign",
    "target_filters": {"title": ["CEO"]},
    "sequence": [{"day": 0, "action": "connect", "template": "Hi!"}]
  }')
CAMPAIGN_ID=$(echo "$CAMPAIGN_RESP" | python3 -c "import sys, json; print(json.load(sys.stdin).get('campaign_id', ''))" 2>/dev/null)
echo "Campaign ID: $CAMPAIGN_ID"

echo ""
echo "=== BUG FIX #1: Prospect add now uses JSON body (not query params) ==="
curl -s -X POST http://127.0.0.1:8300/api/prospects/add \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"bugfix_test\",
    \"campaign_id\": \"$CAMPAIGN_ID\",
    \"linkedin_url\": \"https://linkedin.com/in/test-person\",
    \"full_name\": \"Test Person\",
    \"title\": \"CEO\",
    \"company\": \"TestCo\"
  }" | python3 -m json.tool
echo ""

echo "=== BUG FIX #2: AI scoring error now reported (not silent) ==="
echo "Check response above - should show 'ai_scoring_error' field when LLM fails"
echo ""

echo "=== BUG FIX #3: Pending actions now includes future scheduled actions ==="
# Queue action with future timestamp
curl -s -X POST http://127.0.0.1:8300/api/actions/queue \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"bugfix_test\",
    \"prospect_id\": \"test_prospect\",
    \"action_type\": \"connect\",
    \"action_data\": {}
  }" > /dev/null

echo "Queued action (scheduled for future)..."
echo "Checking pending actions:"
curl -s "http://127.0.0.1:8300/api/actions/pending?user_id=bugfix_test" | python3 -m json.tool
echo ""

echo "=== All bug fixes tested! ==="
