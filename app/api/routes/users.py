from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.models.schemas import ConfigureUserRequest, ConfigureUserResponse
from app.utils.encryption import encrypt_data

router = APIRouter()


@router.post("/configure", response_model=ConfigureUserResponse)
async def configure_user(req: ConfigureUserRequest, db: Session = Depends(get_db)):
    """
    Store user's LinkedIn credentials + LLM config (encrypted)
    """
    
    # Encrypt LinkedIn credentials
    linkedin_creds = {
        "email": req.linkedin_credentials.email,
        "password": req.linkedin_credentials.password
    }
    linkedin_encrypted = encrypt_data(linkedin_creds)
    
    # Encrypt LLM config
    llm_config = req.llm_config.model_dump()
    llm_encrypted = encrypt_data(llm_config)
    
    # Check if user exists
    user = db.query(User).filter(User.user_id == req.user_id).first()
    
    if user:
        # Update existing
        user.linkedin_email = linkedin_creds["email"]  # Store email in plain for display
        user.linkedin_password = linkedin_encrypted  # Encrypted password
        user.llm_config_encrypted = llm_encrypted
        user.daily_limits = req.daily_limits
    else:
        # Create new
        user = User(
            user_id=req.user_id,
            linkedin_email=linkedin_creds["email"],
            linkedin_password=linkedin_encrypted,
            llm_config_encrypted=llm_encrypted,
            daily_limits=req.daily_limits
        )
        db.add(user)
    
    db.commit()
    
    return ConfigureUserResponse(
        status="success",
        user_id=req.user_id,
        message="User configured successfully"
    )


@router.get("/{user_id}")
async def get_user_info(user_id: str, db: Session = Depends(get_db)):
    """Get user info (without sensitive data)"""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    return {
        "user_id": user.user_id,
        "linkedin_email": user.linkedin_email,
        "automation_enabled": user.automation_enabled,
        "daily_limits": user.daily_limits,
        "created_at": user.created_at
    }
