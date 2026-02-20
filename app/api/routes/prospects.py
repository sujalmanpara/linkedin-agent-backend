from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from pydantic import BaseModel

from app.database import get_db
from app.models import User, Campaign, Prospect
from app.models.schemas import ProspectDetail
from app.services.llm_service import LLMService
from app.utils.encryption import decrypt_data

router = APIRouter()


class AddProspectRequest(BaseModel):
    user_id: str
    campaign_id: str
    linkedin_url: str
    full_name: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    headline: Optional[str] = None
    location: Optional[str] = None


@router.post("/add")
async def add_prospect(
    req: AddProspectRequest,
    db: Session = Depends(get_db)
):
    """
    Add a prospect to a campaign and score with AI
    """
    # Verify user and campaign exist
    user = db.query(User).filter(User.user_id == req.user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    campaign = db.query(Campaign).filter(Campaign.campaign_id == req.campaign_id).first()
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    
    # Generate prospect ID
    prospect_id = f"prospect_{uuid.uuid4().hex[:12]}"
    
    # Create prospect
    prospect = Prospect(
        prospect_id=prospect_id,
        user_id=req.user_id,
        campaign_id=req.campaign_id,
        linkedin_url=req.linkedin_url,
        full_name=req.full_name,
        title=req.title,
        company=req.company,
        headline=req.headline,
        location=req.location,
        stage="new",
        connection_status="not_sent"
    )
    
    try:
        db.add(prospect)
        db.commit()
        db.refresh(prospect)
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Database error: {str(e)}")
    
    # Score with AI (async task in production, sync for now)
    ai_error = None
    try:
        llm_config = decrypt_data(user.llm_config_encrypted)
        llm_service = LLMService(llm_config)
        
        prospect_data = {
            "full_name": req.full_name,
            "title": req.title,
            "company": req.company,
            "headline": req.headline
        }
        
        score_result = await llm_service.score_prospect(
            prospect_data,
            campaign.target_filters
        )
        
        prospect.ai_score = score_result.get("score", 5)
        prospect.score_reasoning = score_result.get("reasoning", "")
        
        db.commit()
    except Exception as e:
        # Don't fail if AI scoring fails, but inform user
        ai_error = str(e)
        print(f"AI scoring failed: {e}")
    
    response = {
        "status": "success",
        "prospect_id": prospect.prospect_id,
        "ai_score": prospect.ai_score,
        "message": "Prospect added successfully"
    }
    
    if ai_error:
        response["ai_scoring_error"] = f"AI scoring failed: {ai_error}"
        response["message"] = "Prospect added (AI scoring failed)"
    
    return response


@router.get("/campaign/{campaign_id}/list", response_model=List[ProspectDetail])
async def list_prospects(campaign_id: str, db: Session = Depends(get_db)):
    """List all prospects in a campaign"""
    prospects = db.query(Prospect).filter(Prospect.campaign_id == campaign_id).all()
    
    return [
        ProspectDetail(
            prospect_id=p.prospect_id,
            full_name=p.full_name,
            title=p.title,
            company=p.company,
            linkedin_url=p.linkedin_url,
            ai_score=p.ai_score,
            stage=p.stage,
            connection_status=p.connection_status
        )
        for p in prospects
    ]


@router.get("/{prospect_id}")
async def get_prospect(prospect_id: str, db: Session = Depends(get_db)):
    """Get detailed prospect info"""
    prospect = db.query(Prospect).filter(Prospect.prospect_id == prospect_id).first()
    if not prospect:
        raise HTTPException(404, "Prospect not found")
    
    return {
        "prospect_id": prospect.prospect_id,
        "linkedin_url": prospect.linkedin_url,
        "full_name": prospect.full_name,
        "title": prospect.title,
        "company": prospect.company,
        "headline": prospect.headline,
        "location": prospect.location,
        "ai_score": prospect.ai_score,
        "score_reasoning": prospect.score_reasoning,
        "stage": prospect.stage,
        "connection_status": prospect.connection_status,
        "conversation_history": prospect.conversation_history,
        "last_interaction_at": prospect.last_interaction_at,
        "created_at": prospect.created_at
    }


@router.post("/{prospect_id}/update-stage")
async def update_prospect_stage(
    prospect_id: str,
    stage: str,
    db: Session = Depends(get_db)
):
    """Update prospect stage (new, contacted, connected, replied, cold)"""
    prospect = db.query(Prospect).filter(Prospect.prospect_id == prospect_id).first()
    if not prospect:
        raise HTTPException(404, "Prospect not found")
    
    prospect.stage = stage
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Database error: {str(e)}")
    
    return {"status": "success", "stage": stage}
