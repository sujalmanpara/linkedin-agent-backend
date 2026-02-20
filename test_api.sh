#!/bin/bash

# Wait for server
sleep 3

echo "=== Testing LinkedIn Agent Backend API ==="
echo ""

# 1. Health check
echo "1. Health check:"
curl -s http://127.0.0.1:8300/health
echo -e "\n"

# 2. Create user
echo "2. Creating user:"
USER_RESP=$(curl -s -X POST http://127.0.0.1:8300/api/users/configure \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "linkedin_credentials": {"email": "test@linkedin.com", "password": "pass123"},
    "llm_config": {"type": "anthropic", "model": "claude-sonnet-4-5", "api_key": "sk-test-key"},
    "daily_limits": {"connections": 50, "messages": 30}
  }')
echo "$USER_RESP" | python3 -m json.tool
echo ""

# 3. Create campaign
echo "3. Creating campaign:"
CAMPAIGN_RESP=$(curl -s -X POST http://127.0.0.1:8300/api/campaigns/create \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "name": "SaaS Founders Q1",
    "target_filters": {"title": ["Founder", "CEO"], "industry": "SaaS"},
    "sequence": [
      {"day": 0, "action": "connect", "template": "Hi {{name}}!"},
      {"day": 1, "action": "message", "template": "Thanks!", "condition": "if_accepted"}
    ]
  }')
echo "$CAMPAIGN_RESP" | python3 -m json.tool
CAMPAIGN_ID=$(echo "$CAMPAIGN_RESP" | python3 -c "import sys, json; print(json.load(sys.stdin).get('campaign_id', ''))" 2>/dev/null)
echo "Campaign ID: $CAMPAIGN_ID"
echo ""

# 4. List campaigns
echo "4. Listing campaigns:"
curl -s "http://127.0.0.1:8300/api/campaigns/user/test_user/list" | python3 -m json.tool
echo ""

# 5. Get campaign details
if [ -n "$CAMPAIGN_ID" ]; then
  echo "5. Getting campaign details:"
  curl -s "http://127.0.0.1:8300/api/campaigns/$CAMPAIGN_ID" | python3 -m json.tool
  echo ""
fi

echo "=== Tests complete! ==="
