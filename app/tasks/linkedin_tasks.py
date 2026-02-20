"""
Celery tasks for LinkedIn automation
"""

from celery import Celery
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import User, Prospect, Action, Campaign
from app.services.linkedin_service import LinkedInService
from app.services.llm_service import LLMService
from app.utils.encryption import decrypt_data

# Initialize Celery (Redis broker)
celery_app = Celery('linkedin_agent', broker='redis://localhost:6379/0')


@celery_app.task
def execute_pending_actions():
    """
    Check for pending actions and execute them
    Run this task every 5 minutes via Celery Beat
    """
    db = SessionLocal()
    
    try:
        # Get all pending actions that are due
        pending = db.query(Action).filter(
            Action.status == "pending",
            Action.scheduled_for <= datetime.now(timezone.utc)
        ).limit(50).all()  # Process 50 at a time
        
        for action in pending:
            try:
                # Execute action
                execute_action.delay(action.action_id)
            except Exception as e:
                print(f"Failed to queue action {action.action_id}: {e}")
    
    finally:
        db.close()


@celery_app.task
def execute_action(action_id: str):
    """
    Execute a single LinkedIn action
    """
    db = SessionLocal()
    
    try:
        action = db.query(Action).filter(Action.action_id == action_id).first()
        if not action:
            return {"error": "Action not found"}
        
        # Update status
        action.status = "executing"
        db.commit()
        
        # Get user and decrypt credentials
        user = db.query(User).filter(User.user_id == action.user_id).first()
        linkedin_creds = decrypt_data(user.linkedin_credentials_encrypted)
        llm_config = decrypt_data(user.llm_config_encrypted)
        
        # Get prospect
        prospect = db.query(Prospect).filter(Prospect.prospect_id == action.prospect_id).first()
        
        # Execute based on action type
        linkedin_service = LinkedInService(linkedin_creds)
        
        try:
            await linkedin_service.login()
            
            if action.action_type == "connect":
                # Generate personalized note with LLM
                llm_service = LLMService(llm_config)
                note = await llm_service.generate_connection_note({
                    "full_name": prospect.full_name,
                    "title": prospect.title,
                    "company": prospect.company,
                    "headline": prospect.headline
                })
                
                # Send connection request
                result = await linkedin_service.send_connection_request(
                    prospect.linkedin_url,
                    note
                )
                
                if result["success"]:
                    action.status = "completed"
                    prospect.connection_status = "pending"
                    prospect.stage = "contacted"
                    
                    # Update campaign stats
                    campaign = db.query(Campaign).filter(
                        Campaign.campaign_id == action.campaign_id
                    ).first()
                    if campaign:
                        campaign.stats["sent"] = campaign.stats.get("sent", 0) + 1
                else:
                    raise Exception(result.get("error", "Unknown error"))
            
            elif action.action_type == "message":
                # Generate personalized message
                llm_service = LLMService(llm_config)
                message = await llm_service.generate_first_message({
                    "full_name": prospect.full_name,
                    "title": prospect.title,
                    "company": prospect.company
                })
                
                # Send message
                result = await linkedin_service.send_message(
                    prospect.linkedin_url,
                    message
                )
                
                if result["success"]:
                    action.status = "completed"
                    prospect.stage = "messaged"
                    
                    # Add to conversation history
                    if not prospect.conversation_history:
                        prospect.conversation_history = []
                    prospect.conversation_history.append({
                        "role": "assistant",
                        "message": message,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                else:
                    raise Exception(result.get("error", "Unknown error"))
            
            elif action.action_type == "visit_profile":
                # Just visit the profile (for engagement)
                result = await linkedin_service.visit_profile(prospect.linkedin_url)
                
                if result["success"]:
                    action.status = "completed"
                    
                    # Update campaign stats
                    campaign = db.query(Campaign).filter(
                        Campaign.campaign_id == action.campaign_id
                    ).first()
                    if campaign:
                        campaign.stats["views"] = campaign.stats.get("views", 0) + 1
                else:
                    raise Exception(result.get("error", "Unknown error"))
            
            action.executed_at = datetime.now(timezone.utc)
            prospect.last_interaction_at = datetime.now(timezone.utc)
            
            db.commit()
            
        except Exception as e:
            # Retry logic
            action.retry_count += 1
            action.error_message = str(e)
            
            if action.retry_count >= 3:
                action.status = "failed"
            else:
                action.status = "pending"  # Will retry
            
            db.commit()
            
        finally:
            await linkedin_service.close()
    
    except Exception as e:
        print(f"Task error: {e}")
        if action:
            action.status = "failed"
            action.error_message = str(e)
            db.commit()
    
    finally:
        db.close()


@celery_app.task
def process_campaign_sequence(campaign_id: str):
    """
    Process campaign sequence for all prospects
    Schedule next actions based on sequence configuration
    """
    db = SessionLocal()
    
    try:
        campaign = db.query(Campaign).filter(Campaign.campaign_id == campaign_id).first()
        if not campaign or campaign.status != "active":
            return
        
        # Get all prospects in campaign
        prospects = db.query(Prospect).filter(Prospect.campaign_id == campaign_id).all()
        
        for prospect in prospects:
            # Determine next step in sequence
            for step in campaign.sequence:
                # Check if this step should be executed
                # (based on prospect stage and conditions)
                # Queue the action
                pass  # TODO: Implement sequence logic
    
    finally:
        db.close()


# Celery Beat schedule (run every 5 minutes)
celery_app.conf.beat_schedule = {
    'execute-pending-actions': {
        'task': 'app.tasks.linkedin_tasks.execute_pending_actions',
        'schedule': 300.0,  # 5 minutes
    },
}
