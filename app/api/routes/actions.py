from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from typing import List
import uuid

from app.database import get_db
from app.models import User, Prospect, Action
from app.models.schemas import QueueActionRequest, ActionResponse

router = APIRouter()


@router.post("/queue", response_model=ActionResponse)
async def queue_action(req: QueueActionRequest, db: Session = Depends(get_db)):
    """
    Queue a LinkedIn action (connect, message, visit)
    """
    # Verify user and prospect exist
    user = db.query(User).filter(User.user_id == req.user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    prospect = db.query(Prospect).filter(Prospect.prospect_id == req.prospect_id).first()
    if not prospect:
        raise HTTPException(404, "Prospect not found")
    
    # Generate action ID
    action_id = f"action_{uuid.uuid4().hex[:12]}"
    
    # Schedule time (if not provided, use now + random delay for safety)
    if req.scheduled_for:
        scheduled_for = req.scheduled_for
    else:
        # Add random delay (5-15 minutes) to avoid spam detection
        import random
        delay_minutes = random.randint(5, 15)
        scheduled_for = datetime.now(timezone.utc) + timedelta(minutes=delay_minutes)
    
    # Create action
    action = Action(
        action_id=action_id,
        user_id=req.user_id,
        prospect_id=req.prospect_id,
        campaign_id=prospect.campaign_id,
        action_type=req.action_type,
        action_data=req.action_data,
        scheduled_for=scheduled_for,
        status="pending"
    )
    
    try:
        db.add(action)
        db.commit()
        db.refresh(action)
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Database error: {str(e)}")
    
    return ActionResponse(
        action_id=action.action_id,
        status=action.status,
        scheduled_for=action.scheduled_for
    )


@router.get("/pending", response_model=List[ActionResponse])
async def get_pending_actions(user_id: str, db: Session = Depends(get_db)):
    """Get all pending actions for a user"""
    actions = db.query(Action).filter(
        Action.user_id == user_id,
        Action.status == "pending",
        Action.scheduled_for <= datetime.now(timezone.utc)
    ).all()
    
    return [
        ActionResponse(
            action_id=a.action_id,
            status=a.status,
            scheduled_for=a.scheduled_for
        )
        for a in actions
    ]


@router.get("/{action_id}")
async def get_action(action_id: str, db: Session = Depends(get_db)):
    """Get action details"""
    action = db.query(Action).filter(Action.action_id == action_id).first()
    if not action:
        raise HTTPException(404, "Action not found")
    
    return {
        "action_id": action.action_id,
        "user_id": action.user_id,
        "prospect_id": action.prospect_id,
        "campaign_id": action.campaign_id,
        "action_type": action.action_type,
        "action_data": action.action_data,
        "scheduled_for": action.scheduled_for,
        "executed_at": action.executed_at,
        "status": action.status,
        "retry_count": action.retry_count,
        "error_message": action.error_message,
        "created_at": action.created_at
    }


@router.post("/{action_id}/cancel")
async def cancel_action(action_id: str, db: Session = Depends(get_db)):
    """Cancel a pending action"""
    action = db.query(Action).filter(Action.action_id == action_id).first()
    if not action:
        raise HTTPException(404, "Action not found")
    
    if action.status != "pending":
        raise HTTPException(400, f"Cannot cancel action with status: {action.status}")
    
    action.status = "cancelled"
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Database error: {str(e)}")
    
    return {"status": "success", "message": "Action cancelled"}


@router.get("/user/{user_id}/history")
async def get_action_history(
    user_id: str,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get action history for a user"""
    actions = db.query(Action).filter(
        Action.user_id == user_id
    ).order_by(Action.created_at.desc()).limit(limit).all()
    
    return [
        {
            "action_id": a.action_id,
            "action_type": a.action_type,
            "status": a.status,
            "scheduled_for": a.scheduled_for,
            "executed_at": a.executed_at,
            "error_message": a.error_message
        }
        for a in actions
    ]
