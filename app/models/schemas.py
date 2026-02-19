from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# --- User Schemas ---

class LLMConfig(BaseModel):
    type: str = "anthropic"  # anthropic, openai
    model: str = "claude-sonnet-4-5"
    api_key: str


class LinkedInCredentials(BaseModel):
    email: str
    password: str


class ConfigureUserRequest(BaseModel):
    user_id: str
    linkedin_credentials: LinkedInCredentials
    llm_config: LLMConfig
    daily_limits: Optional[dict] = {"connections": 50, "messages": 30}


class ConfigureUserResponse(BaseModel):
    status: str
    user_id: str
    message: str


# --- Campaign Schemas ---

class CampaignSequenceStep(BaseModel):
    day: int
    action: str  # "connect", "message"
    template: str
    condition: Optional[str] = None  # "if_accepted", "if_no_reply"


class CreateCampaignRequest(BaseModel):
    user_id: str
    name: str
    target_filters: dict
    sequence: list[CampaignSequenceStep]


class CreateCampaignResponse(BaseModel):
    status: str
    campaign_id: str
    message: str


class CampaignStatsResponse(BaseModel):
    campaign_id: str
    name: str
    status: str
    stats: dict
    created_at: datetime


# --- Prospect Schemas ---

class ProspectDetail(BaseModel):
    prospect_id: str
    full_name: Optional[str]
    title: Optional[str]
    company: Optional[str]
    linkedin_url: str
    ai_score: Optional[int]
    stage: str
    connection_status: Optional[str]


class SearchProspectsRequest(BaseModel):
    user_id: str
    campaign_id: Optional[str] = None
    filters: Optional[dict] = {}
    limit: int = 50


# --- Action Schemas ---

class QueueActionRequest(BaseModel):
    user_id: str
    prospect_id: str
    action_type: str
    action_data: dict
    scheduled_for: Optional[datetime] = None


class ActionResponse(BaseModel):
    action_id: str
    status: str
    scheduled_for: datetime
