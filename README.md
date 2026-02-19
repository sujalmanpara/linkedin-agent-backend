# 🔗 LinkedIn AI Agent - Backend API

AI-powered LinkedIn automation backend. Users provide their LinkedIn credentials + LLM API key, backend handles all automation.

**Same architecture as `podcast-clip-agent-backend`** — proven, tested, production-ready.

---

## 🚀 Quick Start

```bash
# 1. Clone/navigate
cd linkedin-agent-backend

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
# Edit .env — set ENCRYPTION_KEY

# 4. Generate encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 5. Run (with SQLite fallback, no Postgres needed for testing)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 6. API docs
open http://localhost:8000/docs
```

---

## 📋 API Flow

### 1. Configure User

```bash
curl -X POST http://localhost:8000/api/users/configure \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "linkedin_credentials": {
      "email": "user@example.com",
      "password": "password"
    },
    "llm_config": {
      "type": "anthropic",
      "model": "claude-sonnet-4-5",
      "api_key": "sk-ant-xxx"
    },
    "daily_limits": {
      "connections": 50,
      "messages": 30
    }
  }'
```

### 2. Create Campaign

```bash
curl -X POST http://localhost:8000/api/campaigns/create \
  -d '{
    "user_id": "user_123",
    "name": "Q1 SaaS Founders",
    "target_filters": {
      "title": ["Founder", "CEO"],
      "company_size": [10, 500]
    },
    "sequence": [
      {
        "day": 0,
        "action": "connect",
        "template": "Hey {{first_name}}! {{ai_note}}"
      },
      {
        "day": 1,
        "action": "message",
        "condition": "if_accepted",
        "template": "Thanks for connecting! {{ai_intro}}"
      }
    ]
  }'
```

### 3. Add Prospects

```bash
curl -X POST http://localhost:8000/api/prospects/add \
  -d '{
    "user_id": "user_123",
    "campaign_id": "campaign_xxx",
    "linkedin_url": "https://linkedin.com/in/john-smith",
    "full_name": "John Smith",
    "title": "CEO",
    "company": "TechCorp"
  }'
```

### 4. Backend Automates

- AI scores prospects
- Generates personalized messages
- Schedules actions with safe delays
- Executes via Playwright (browser automation)
- Tracks results

### 5. Check Stats

```bash
curl http://localhost:8000/api/campaigns/{campaign_id}/stats
```

---

## 🏗️ Architecture

```
User provides:
├─ LinkedIn email + password (encrypted)
└─ LLM API key (encrypted)

Backend does:
├─ Campaign management
├─ Prospect scoring (AI)
├─ Message personalization (AI)
├─ LinkedIn automation (Playwright)
├─ Rate limiting (safety)
└─ Analytics
```

**Same pattern as podcast-clip-agent:**
- FastAPI (REST API)
- Celery (job queue)
- PostgreSQL (or SQLite fallback)
- Redis (or sync mode fallback)
- User's LLM (zero AI cost to us!)

---

## 💰 Economics

| Cost | Amount |
|------|--------|
| Infrastructure | ~$50/month |
| Per user | ~$0.50/month |
| LLM costs | **$0** (user's key!) |

**Profit margin:** ~98% 🚀

---

## 🔐 Security

- All credentials encrypted (Fernet)
- User's own LinkedIn account (not shared proxy)
- User's own LLM key (not our quota)
- Safe rate limits (50 connections/week, 30 messages/day)
- Human-like delays (random 2-6 sec)

---

## 📊 Tech Stack

- **FastAPI** — REST API
- **Celery + Redis** — async job queue
- **PostgreSQL** — database (SQLite fallback)
- **Playwright** — LinkedIn automation
- **User's LLM** — AI personalization

---

## 🚧 Status

**MVP In Progress** — Core features being built

**Ready:**
- ✅ Database schema
- ✅ User management
- ✅ LLM service
- ✅ LinkedIn automation (Playwright)

**TODO:**
- ⏳ Campaign routes
- ⏳ Prospect routes
- ⏳ Celery tasks
- ⏳ Analytics
- ⏳ Docker setup

---

## 📝 License

MIT
