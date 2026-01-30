"""
Onboarding API Endpoints

Handles Railway-per-tenant onboarding via web-based wizard.
"""

import os
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

# Optional imports: dcisionai_onboarding may not be available
OnboardingOrchestrator = None
APIKeyService = None
_onboarding_available = False
try:
    from dcisionai_onboarding.orchestrator import OnboardingOrchestrator
    from dcisionai_onboarding.api_keys import APIKeyService
    _onboarding_available = True
except ImportError:
    logger.warning("⚠️ dcisionai_onboarding not available - onboarding endpoints will be disabled")

logger = logging.getLogger(__name__)


class ResumeOnboardingRequest(BaseModel):
    """Request to resume onboarding from checkpoint."""
    session_id: str
    project_id: Optional[str] = None
    database_url: Optional[str] = None
    supabase_url: Optional[str] = None
    supabase_api_key: Optional[str] = None
    redis_url: Optional[str] = None

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])

# Store onboarding sessions
_onboarding_sessions: Dict[str, Dict[str, Any]] = {}


class OnboardingRequest(BaseModel):
    """Onboarding request model."""
    tenant_id: str = Field(..., description="Unique tenant identifier")
    customer_name: str = Field(..., description="Customer/company name")
    customer_email: Optional[str] = Field(None, description="Customer email")
    railway_token: Optional[str] = Field(None, description="Railway API token (optional)")


class OnboardingStatus(BaseModel):
    """Onboarding status model."""
    session_id: str
    tenant_id: str
    status: str  # "pending", "in_progress", "completed", "failed"
    current_step: str
    progress: float  # 0.0 to 1.0
    message: str
    project_id: Optional[str] = None
    api_key: Optional[str] = None
    error: Optional[str] = None
    checkpoint: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


@router.post("/start", response_model=Dict[str, Any])
async def start_onboarding(
    request: OnboardingRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Start Railway-per-tenant onboarding.
    
    Returns session_id for status polling.
    """
    if not _onboarding_available or OnboardingOrchestrator is None:
        raise HTTPException(
            status_code=503,
            detail="Onboarding service not available. dcisionai_onboarding module is required."
        )
    # Validate input
    if not request.tenant_id or not request.tenant_id.strip():
        raise HTTPException(
            status_code=400,
            detail="tenant_id is required"
        )
    
    if not request.customer_name or not request.customer_name.strip():
        raise HTTPException(
            status_code=400,
            detail="customer_name is required"
        )
    
    # Validate tenant_id format (alphanumeric, hyphens, underscores)
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', request.tenant_id):
        raise HTTPException(
            status_code=400,
            detail="tenant_id must contain only letters, numbers, hyphens, and underscores"
        )
    
    session_id = f"onboarding-{request.tenant_id}-{int(datetime.now().timestamp())}"
    
    # Initialize session
    _onboarding_sessions[session_id] = {
        "session_id": session_id,
        "tenant_id": request.tenant_id,
        "status": "pending",
        "current_step": "Initializing",
        "progress": 0.0,
        "message": "Starting onboarding...",
        "project_id": None,
        "api_key": None,
        "error": None,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    # Start onboarding in background
    background_tasks.add_task(
        run_onboarding,
        session_id,
        request.tenant_id,
        request.customer_name,
        request.customer_email,
        request.railway_token
    )
    
    return {
        "session_id": session_id,
        "status": "pending",
        "message": "Onboarding started. Poll /api/onboarding/status/{session_id} for progress."
    }


@router.get("/status/{session_id}", response_model=OnboardingStatus)
async def get_onboarding_status(session_id: str) -> OnboardingStatus:
    """Get onboarding status by session ID."""
    if session_id not in _onboarding_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = _onboarding_sessions[session_id]
    return OnboardingStatus(**session)


@router.post("/resume", response_model=Dict[str, Any])
async def resume_onboarding(
    request: ResumeOnboardingRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Resume onboarding from checkpoint after manual setup.
    
    Requires project_id and database_url at minimum.
    """
    if request.session_id not in _onboarding_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = _onboarding_sessions[request.session_id]
    
    # Validate required fields
    if not request.database_url:
        raise HTTPException(
            status_code=400,
            detail="database_url is required to resume onboarding"
        )
    
    # Update session with checkpoint data
    session["checkpoint"] = {
        "project_id": request.project_id,
        "database_url": request.database_url,
        "supabase_url": request.supabase_url,
        "supabase_api_key": request.supabase_api_key,
        "redis_url": request.redis_url
    }
    session["status"] = "pending"
    session["current_step"] = "Resuming"
    session["message"] = "Resuming onboarding from checkpoint..."
    session["updated_at"] = datetime.now()
    
    # Resume onboarding in background
    background_tasks.add_task(
        resume_onboarding_from_checkpoint,
        request.session_id,
        request.project_id,
        request.database_url,
        request.supabase_url,
        request.supabase_api_key,
        request.redis_url
    )
    
    return {
        "session_id": request.session_id,
        "status": "pending",
        "message": "Resuming onboarding. Poll /api/onboarding/status/{session_id} for progress."
    }


async def run_onboarding(
    session_id: str,
    tenant_id: str,
    customer_name: str,
    customer_email: Optional[str],
    railway_token: Optional[str]
):
    """Run onboarding process in background."""
    session = _onboarding_sessions.get(session_id)
    if not session:
        return
    
    try:
        # Update status helper
        def update_status(step: str, progress: float, message: str, **kwargs):
            session["current_step"] = step
            session["progress"] = progress
            session["message"] = message
            session["updated_at"] = datetime.now()
            session.update(kwargs)
            logger.info(f"[{session_id}] {step}: {message} ({progress*100:.1f}%)")
        
        update_status("Initializing", 0.1, "Setting up Railway client...")
        
        # Initialize orchestrator
        if not _onboarding_available or OnboardingOrchestrator is None:
            update_status(
                "Failed",
                0.0,
                "Onboarding service not available",
                status="failed",
                error="dcisionai_onboarding module is required"
            )
            return
        
        try:
            orchestrator = OnboardingOrchestrator(railway_token)
        except ValueError as e:
            # Railway token validation error
            update_status(
                "Failed",
                0.0,
                f"Railway token error: {str(e)}",
                status="failed",
                error=f"Invalid Railway token: {str(e)}. You can proceed without a token to use Railway CLI login."
            )
            return
        except Exception as e:
            logger.error(f"Orchestrator initialization error: {e}", exc_info=True)
            update_status(
                "Failed",
                0.0,
                f"Setup initialization failed: {str(e)}",
                status="failed",
                error=str(e)
            )
            return
        
        update_status("Creating Project", 0.2, "Creating Railway project...")
        
        # Run onboarding with progress updates
        customer_info = {
            "name": customer_name,
            "email": customer_email
        }
        
        # Update status before each major step
        update_status("Creating Project", 0.2, "Creating Railway project...")
        result = orchestrator.onboard_tenant(tenant_id, customer_info)
        
        # Update status based on result
        if result.get("status") == "in_progress":
            # If orchestrator provides progress updates, use them
            if "current_step" in result:
                update_status(
                    result.get("current_step", "In Progress"),
                    result.get("progress", 0.5),
                    result.get("message", "Onboarding in progress..."),
                    project_id=result.get("project_id")
                )
            return
        
        if result.get("status") == "success":
            update_status(
                "Completed",
                1.0,
                "Onboarding completed successfully!",
                status="completed",
                project_id=result.get("project_id"),
                api_key=result.get("api_key")
            )
        else:
            error_msg = result.get("error", "Unknown error")
            suggestion = result.get("suggestion", "")
            project_id = result.get("project_id")
            
            # Format error message with suggestion if available
            if suggestion:
                formatted_error = f"{error_msg}\n\n💡 Suggestion: {suggestion}"
            else:
                formatted_error = error_msg
            
            # Store checkpoint info for resume
            checkpoint = {
                "project_id": project_id,
                "can_resume": project_id is not None or "database_url" in error_msg.lower()
            }
            
            update_status(
                "Failed",
                0.0,
                formatted_error,
                status="failed",
                error=formatted_error,
                checkpoint=checkpoint,
                project_id=project_id
            )
    
    except Exception as e:
        logger.error(f"Onboarding error for {session_id}: {e}", exc_info=True)
        session["status"] = "failed"
        session["current_step"] = "Error"
        session["progress"] = 0.0
        session["message"] = f"Onboarding failed: {str(e)}"
        session["error"] = str(e)
        session["updated_at"] = datetime.now()


async def resume_onboarding_from_checkpoint(
    session_id: str,
    project_id: Optional[str],
    database_url: str,
    supabase_url: Optional[str],
    supabase_api_key: Optional[str],
    redis_url: Optional[str]
):
    """Resume onboarding from checkpoint after manual setup."""
    session = _onboarding_sessions.get(session_id)
    if not session:
        return
    
    tenant_id = session.get("tenant_id")
    if not tenant_id:
        logger.error(f"Session {session_id} missing tenant_id")
        return
    
    try:
        # Update status helper
        def update_status(step: str, progress: float, message: str, **kwargs):
            session["current_step"] = step
            session["progress"] = progress
            session["message"] = message
            session["updated_at"] = datetime.now()
            session.update(kwargs)
            logger.info(f"[{session_id}] {step}: {message} ({progress*100:.1f}%)")
        
        update_status("Resuming", 0.3, "Resuming from checkpoint...")
        
        # These imports are already handled at module level
        # If not available, OnboardingOrchestrator will be None and we'll handle it
        if not _onboarding_available:
            raise HTTPException(
                status_code=503,
                detail="Onboarding service not available. dcisionai_onboarding module is required."
            )
        
        from dcisionai_onboarding.migrations import TenantMigrationRunner
        
        # Step 1: Run database migrations
        update_status("Running Migrations", 0.4, "Running database migrations...")
        migration_runner = TenantMigrationRunner(database_url)
        migration_success = migration_runner.run_migrations(tenant_id)
        
        if not migration_success:
            update_status(
                "Failed",
                0.0,
                "Database migrations failed",
                status="failed",
                error="Database migrations failed. Please check your DATABASE_URL and try again."
            )
            return
        
        # Step 2: Generate API key
        update_status("Generating API Key", 0.7, "Generating API key...")
        api_key_service = APIKeyService()
        api_key = api_key_service.generate_api_key(tenant_id)
        api_key_service.store_api_key(tenant_id, api_key)
        
        # Step 3: Verify setup
        update_status("Verifying Setup", 0.9, "Verifying setup...")
        
        # Basic verification
        verification = {
            "database_accessible": False,
            "redis_accessible": False,
            "tables_created": False
        }
        
        try:
            import psycopg2
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'async_jobs')")
            verification["tables_created"] = cursor.fetchone()[0]
            verification["database_accessible"] = True
            cursor.close()
            conn.close()
        except Exception as e:
            logger.warning(f"Database verification failed: {e}")
        
        if redis_url:
            try:
                import redis
                r = redis.from_url(redis_url)
                r.ping()
                verification["redis_accessible"] = True
            except Exception as e:
                logger.warning(f"Redis verification failed: {e}")
        
        # Success!
        update_status(
            "Completed",
            1.0,
            "Onboarding completed successfully!",
            status="completed",
            project_id=project_id,
            api_key=api_key,
            verification=verification
        )
        
        logger.info(f"✅ Onboarding resumed and completed for tenant {tenant_id}")
        
    except Exception as e:
        logger.error(f"❌ Resume onboarding failed: {e}", exc_info=True)
        update_status(
            "Failed",
            0.0,
            f"Resume failed: {str(e)}",
            status="failed",
            error=str(e)
        )


@router.post("/verify-railway-token")
async def verify_railway_token(request: Dict[str, str]) -> Dict[str, Any]:
    """
    Verify Railway API token.
    
    Returns token validity and user info.
    """
    try:
        token = request.get("token")
        if not token:
            return {
                "valid": False,
                "message": "Token not provided",
                "can_proceed": True  # Can proceed without token (uses CLI)
            }
        
        # Check if token looks like a project ID (UUID format)
        if len(token) == 36 and token.count('-') == 4:
            return {
                "valid": False,
                "message": "This appears to be a project ID, not an API token. Railway API tokens are longer strings (100+ characters). You can proceed without a token to use Railway CLI login instead.",
                "can_proceed": True,
                "suggestion": "Leave token empty to use Railway CLI login, or get your API token from https://railway.app/account/tokens"
            }
        
        if not _onboarding_available:
            raise HTTPException(
                status_code=503,
                detail="Onboarding service not available. dcisionai_onboarding module is required."
            )
        
        from dcisionai_onboarding.railway_client import RailwayClient
        
        client = RailwayClient(token)
        
        # Try to get projects (test token)
        import requests
        try:
            response = requests.get(
                "https://api.railway.app/v1/projects",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                projects = response.json()
                return {
                    "valid": True,
                    "message": f"Token is valid! Found {len(projects)} project(s)",
                    "project_count": len(projects),
                    "can_proceed": True
                }
            elif response.status_code == 401:
                return {
                    "valid": False,
                    "message": "Token is invalid or expired. Please check your Railway API token.",
                    "can_proceed": True,
                    "suggestion": "Get a new token from https://railway.app/account/tokens or leave empty to use Railway CLI login"
                }
            elif response.status_code == 404:
                return {
                    "valid": False,
                    "message": "Railway API endpoint not found. Railway's REST API may not be publicly available. You can proceed without a token to use Railway CLI login instead.",
                    "can_proceed": True,
                    "suggestion": "Leave token empty and use Railway CLI login, or check Railway documentation for API access"
                }
            else:
                return {
                    "valid": False,
                    "message": f"Token validation failed (HTTP {response.status_code}). Railway API may not be accessible. You can proceed without a token to use Railway CLI login.",
                    "can_proceed": True,
                    "suggestion": "Leave token empty to use Railway CLI login"
                }
        except requests.exceptions.Timeout:
            return {
                "valid": False,
                "message": "Token verification timed out. Railway API may be slow or unavailable. You can proceed without a token to use Railway CLI login.",
                "can_proceed": True,
                "suggestion": "Leave token empty to use Railway CLI login"
            }
        except requests.exceptions.ConnectionError:
            return {
                "valid": False,
                "message": "Cannot connect to Railway API. Railway's REST API may not be publicly available. You can proceed without a token to use Railway CLI login.",
                "can_proceed": True,
                "suggestion": "Leave token empty to use Railway CLI login"
            }
    
    except ValueError as e:
        # RailwayClient initialization error
        return {
            "valid": False,
            "message": f"Invalid token format: {str(e)}",
            "can_proceed": True,
            "suggestion": "Get your Railway API token from https://railway.app/account/tokens or leave empty to use Railway CLI login"
        }
    except Exception as e:
        logger.error(f"Token verification error: {e}", exc_info=True)
        return {
            "valid": False,
            "message": f"Token verification error: {str(e)}. You can proceed without a token to use Railway CLI login.",
            "can_proceed": True,
            "suggestion": "Leave token empty to use Railway CLI login"
        }

