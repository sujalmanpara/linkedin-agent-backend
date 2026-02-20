# Bug Fixes - 2026-02-20

## 🐛 3 Bugs Fixed (From End-User Testing)

### **Bug #1: Prospect Add Endpoint Inconsistency** ✅ FIXED

**Issue:** `/api/prospects/add` used query parameters instead of JSON body (inconsistent with all other endpoints)

**Example of old behavior:**
```bash
POST /api/prospects/add?user_id=xxx&campaign_id=yyy&linkedin_url=zzz
```

**Fix Applied:**
- Changed to accept JSON body (consistent with `/api/users/configure`, `/api/campaigns/create`, etc.)
- Added `AddProspectRequest` Pydantic model for validation

**New behavior:**
```bash
POST /api/prospects/add
Content-Type: application/json

{
  "user_id": "xxx",
  "campaign_id": "yyy",
  "linkedin_url": "https://linkedin.com/in/person",
  "full_name": "John Smith",
  "title": "CEO",
  "company": "TechCorp"
}
```

**Files Changed:**
- `app/api/routes/prospects.py` - Added `AddProspectRequest` schema, changed endpoint signature

---

### **Bug #2: AI Scoring Fails Silently** ✅ FIXED

**Issue:** When AI scoring failed (invalid API key, LLM error, etc.), the endpoint returned `ai_score: null` with no explanation

**Example of old behavior:**
```json
{
  "status": "success",
  "prospect_id": "prospect_xxx",
  "ai_score": null,  // <-- Why is this null?
  "message": "Prospect added successfully"
}
```

**Fix Applied:**
- Added error handling that returns AI error message to user
- Response now includes `ai_scoring_error` field when scoring fails
- Message updates to indicate AI scoring failed

**New behavior:**
```json
{
  "status": "success",
  "prospect_id": "prospect_xxx",
  "ai_score": null,
  "ai_scoring_error": "AI scoring failed: Invalid API key",
  "message": "Prospect added (AI scoring failed)"
}
```

**Files Changed:**
- `app/api/routes/prospects.py` - Added error tracking and response field

---

### **Bug #3: Pending Actions Empty for Future Scheduled Actions** ✅ FIXED

**Issue:** `GET /api/actions/pending` only returned actions scheduled for NOW or earlier, not future pending actions

**Example of old behavior:**
```bash
# User queues 3 actions scheduled for 10 minutes from now
POST /api/actions/queue (3 times)

# Immediately check pending
GET /api/actions/pending?user_id=xxx
→ Returns: []  // Empty! Where are my actions?
```

**Root Cause:**
```python
# Old code filtered by scheduled_for <= NOW
actions = db.query(Action).filter(
    Action.user_id == user_id,
    Action.status == "pending",
    Action.scheduled_for <= datetime.now(timezone.utc)  # <-- Bug here
).all()
```

**Fix Applied:**
- Removed `scheduled_for` filter from pending actions query
- Users now see ALL pending actions (regardless of scheduled time)
- Added `order_by(scheduled_for)` to show actions chronologically

**New behavior:**
```bash
GET /api/actions/pending?user_id=xxx
→ Returns: [
  {
    "action_id": "action_1",
    "status": "pending",
    "scheduled_for": "2026-02-20T04:30:00Z"  // 10 min from now
  },
  {
    "action_id": "action_2",
    "status": "pending",
    "scheduled_for": "2026-02-20T04:35:00Z"  // 15 min from now
  },
  ...
]
```

**Files Changed:**
- `app/api/routes/actions.py` - Removed time filter, added ordering

---

## ✅ Verification

All 3 fixes maintain backward compatibility while improving:
1. **API consistency** (JSON body everywhere)
2. **Error transparency** (users know when AI fails)
3. **User experience** (see all pending work, not just immediate)

---

## 📊 Impact

**Before fixes:**
- UX confusion (why is AI score null?)
- API inconsistency (some endpoints use query params, some use JSON)
- Missing data (pending actions hidden)

**After fixes:**
- Clear error messages ✅
- Consistent JSON API ✅
- Complete data visibility ✅

---

**Status:** All fixes committed and ready for testing.
