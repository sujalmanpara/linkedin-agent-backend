from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.database import get_db
from app.models import User, Campaign
from app.models.schemas import (
    CreateCampaignRequest, 
    CampaignResponse,
    CampaignStatsResponse
)

router = APIRouter()


@router.post("/create", response_model=CampaignResponse)
async def create_campaign(req: CreateCampaignRequest, db: Session = Depends(get_db)):
    """
    Create a new outreach campaign
    """
    # Verify user exists
    user = db.query(User).filter(User.user_id == req.user_id).first()
    if not user:
        raise HTTPException(404, "User not found. Configure user first.")
    
    # Generate campaign ID
    campaign_id = f"campaign_{uuid.uuid4().hex[:12]}"
    
    # Create campaign (convert Pydantic models to dicts for JSON serialization)
    campaign = Campaign(
        campaign_id=campaign_id,
        user_id=req.user_id,
        name=req.name,
        target_filters=req.target_filters,
        sequence=[step.model_dump() for step in req.sequence],  # Convert to dict
        status="active",
        stats={"sent": 0, "accepted": 0, "replied": 0, "views": 0}
    )
    
    try:
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Database error: {str(e)}")
    
    return CampaignResponse(
        campaign_id=campaign.campaign_id,
        user_id=campaign.user_id,
        name=campaign.name,
        status=campaign.status,
        target_filters=campaign.target_filters,
        sequence=campaign.sequence,
        stats=campaign.stats,
        created_at=campaign.created_at
    )


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(campaign_id: str, db: Session = Depends(get_db)):
    """Get campaign details"""
    campaign = db.query(Campaign).filter(Campaign.campaign_id == campaign_id).first()
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    
    return CampaignResponse(
        campaign_id=campaign.campaign_id,
        user_id=campaign.user_id,
        name=campaign.name,
        status=campaign.status,
        target_filters=campaign.target_filters,
        sequence=campaign.sequence,
        stats=campaign.stats,
        created_at=campaign.created_at
    )


@router.get("/user/{user_id}/list", response_model=List[CampaignResponse])
async def list_campaigns(user_id: str, db: Session = Depends(get_db)):
    """List all campaigns for a user"""
    campaigns = db.query(Campaign).filter(Campaign.user_id == user_id).all()
    
    return [
        CampaignResponse(
            campaign_id=c.campaign_id,
            user_id=c.user_id,
            name=c.name,
            status=c.status,
            target_filters=c.target_filters,
            sequence=c.sequence,
            stats=c.stats,
            created_at=c.created_at
        )
        for c in campaigns
    ]


@router.post("/{campaign_id}/pause")
async def pause_campaign(campaign_id: str, db: Session = Depends(get_db)):
    """Pause a running campaign"""
    campaign = db.query(Campaign).filter(Campaign.campaign_id == campaign_id).first()
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    
    campaign.status = "paused"
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Database error: {str(e)}")
    
    return {"status": "success", "message": "Campaign paused"}


@router.post("/{campaign_id}/resume")
async def resume_campaign(campaign_id: str, db: Session = Depends(get_db)):
    """Resume a paused campaign"""
    campaign = db.query(Campaign).filter(Campaign.campaign_id == campaign_id).first()
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    
    campaign.status = "active"
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Database error: {str(e)}")
    
    return {"status": "success", "message": "Campaign resumed"}


@router.get("/{campaign_id}/stats", response_model=CampaignStatsResponse)
async def get_campaign_stats(campaign_id: str, db: Session = Depends(get_db)):
    """Get detailed campaign statistics"""
    campaign = db.query(Campaign).filter(Campaign.campaign_id == campaign_id).first()
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    
    return CampaignStatsResponse(
        campaign_id=campaign.campaign_id,
        name=campaign.name,
        status=campaign.status,
        stats=campaign.stats,
        created_at=campaign.created_at
    )
