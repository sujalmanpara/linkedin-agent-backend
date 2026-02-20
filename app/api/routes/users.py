from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db_models import User
from app.models.schemas import ConfigureUserRequest, ConfigureUserResponse
from app.utils.encryption import encrypt_data, decrypt_data

router = APIRouter()


@router.post("/configure", response_model=ConfigureUserResponse)
async def configure_user(req: ConfigureUserRequest, db: Session = Depends(get_db)):
    """
    Store user's LinkedIn credentials + LLM config (encrypted)
    """
    
    try:
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
            user.linkedin_credentials_encrypted = linkedin_encrypted
            user.llm_config_encrypted = llm_encrypted
            user.daily_limits = req.daily_limits
        else:
            # Create new
            user = User(
                user_id=req.user_id,
                linkedin_email=linkedin_creds["email"],
                linkedin_credentials_encrypted=linkedin_encrypted,
                llm_config_encrypted=llm_encrypted,
                daily_limits=req.daily_limits
            )
            db.add(user)
    except ValueError as e:
        raise HTTPException(400, f"Encryption error: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Database error: {str(e)}")
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Database commit error: {str(e)}")
    
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
    
    # Verify we can decrypt config (validation)
    try:
        llm_config = decrypt_data(user.llm_config_encrypted)
        llm_provider = llm_config.get("type", "unknown")
    except Exception:
        llm_provider = "error_decrypting"
    
    return {
        "user_id": user.user_id,
        "linkedin_email": user.linkedin_email,
        "automation_enabled": user.automation_enabled,
        "daily_limits": user.daily_limits,
        "llm_provider": llm_provider,
        "created_at": user.created_at
    }


@router.get("/{user_id}/credentials")
async def get_user_credentials(user_id: str, db: Session = Depends(get_db)):
    """Get decrypted credentials (for testing only - should be protected in production)"""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    try:
        linkedin_creds = decrypt_data(user.linkedin_credentials_encrypted)
        llm_config = decrypt_data(user.llm_config_encrypted)
        
        # Mask sensitive data
        return {
            "user_id": user.user_id,
            "linkedin_email": linkedin_creds["email"],
            "linkedin_password": "****" + linkedin_creds["password"][-4:] if len(linkedin_creds["password"]) > 4 else "****",
            "llm_provider": llm_config["type"],
            "llm_model": llm_config["model"],
            "llm_api_key": "****" + llm_config["api_key"][-4:] if len(llm_config["api_key"]) > 4 else "****"
        }
    except Exception as e:
        raise HTTPException(500, f"Decryption error: {str(e)}")
