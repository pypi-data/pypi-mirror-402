"""
API Key Authentication Middleware

FastAPI dependencies for API key verification and tenant isolation.
Supports both required and optional API key authentication.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.requests import Request as StarletteRequest

from dcisionai_mcp_server.config import MCPConfig

logger = logging.getLogger(__name__)

# Optional import: dcisionai_onboarding may not be available
APIKeyService = None
try:
    from dcisionai_onboarding.api_keys import APIKeyService
    _onboarding_available = True
except ImportError:
    _onboarding_available = False
    logger.warning("⚠️ dcisionai_onboarding not available - API key verification will use default tenant only")

# HTTP Bearer security scheme
# auto_error=False means it won't raise 403 if no credentials provided
security = HTTPBearer(auto_error=False)


def _get_credentials_from_request(request: StarletteRequest) -> Optional[str]:
    """Extract API key from request headers."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.replace("Bearer ", "")
    return None


async def verify_api_key_optional(
    request: Request
) -> Dict[str, Any]:
    """
    Verify API key if provided, otherwise return default tenant.
    
    This is used for endpoints that work with or without API keys.
    If no API key is provided, returns default tenant info.
    
    Returns:
        Dict with tenant_id, api_key_id, metadata, and is_admin flag
    """
    from dcisionai_mcp_server.config import MCPConfig
    
    # Get API key from request headers
    api_key = _get_credentials_from_request(request)
    
    # Check for Admin API Key (DEV ONLY)
    if MCPConfig.ADMIN_API_KEY and api_key == MCPConfig.ADMIN_API_KEY:
        logger.warning("⚠️ Admin API Key detected. Bypassing tenant isolation.")
        return {
            "tenant_id": "admin",
            "api_key_id": None,
            "metadata": {"is_admin": True},
            "is_admin": True
        }
    
    # If no API key provided, return default tenant
    if not api_key:
        return {
            "tenant_id": MCPConfig.DEFAULT_TENANT_ID,
            "api_key_id": None,
            "metadata": {"is_admin": False},
            "is_admin": False
        }
    
    # Verify API key (if dcisionai_onboarding is available)
    if not _onboarding_available or APIKeyService is None:
        # Onboarding module not available - return default tenant
        logger.debug(f"API key provided but dcisionai_onboarding not available, using default tenant")
        return {
            "tenant_id": MCPConfig.DEFAULT_TENANT_ID,
            "api_key_id": None,
            "metadata": {"is_admin": False},
            "is_admin": False
        }
    
    api_key_service = APIKeyService()
    
    try:
        tenant_info = api_key_service.verify_api_key(api_key)
        
        if not tenant_info:
            # API key not found or invalid - return default tenant
            logger.warning(f"Invalid API key provided, using default tenant")
            return {
                "tenant_id": MCPConfig.DEFAULT_TENANT_ID,
                "api_key_id": None,
                "metadata": {"is_admin": False},
                "is_admin": False
            }
        
        return {
            "tenant_id": tenant_info.get("tenant_id"),
            "api_key_id": tenant_info.get("api_key_id"),
            "metadata": tenant_info.get("metadata", {}),
            "is_admin": tenant_info.get("metadata", {}).get("is_admin", False)
        }
    except Exception as e:
        logger.error(f"Error verifying API key: {e}")
        # On error, return default tenant
        return {
            "tenant_id": MCPConfig.DEFAULT_TENANT_ID,
            "api_key_id": None,
            "metadata": {"is_admin": False},
            "is_admin": False
        }


async def verify_api_key_required(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """
    Verify API key - required for this endpoint.
    
    Raises HTTPException if API key is missing or invalid.
    
    Returns:
        Dict with tenant_id, api_key_id, and metadata
    """
    from dcisionai_mcp_server.config import MCPConfig
    
    # Check for Admin API Key (DEV ONLY)
    if MCPConfig.ADMIN_API_KEY and credentials and credentials.credentials == MCPConfig.ADMIN_API_KEY:
        logger.warning("⚠️ Admin API Key detected. Bypassing tenant isolation.")
        return {
            "tenant_id": "admin",
            "api_key_id": None,
            "metadata": {"is_admin": True},
            "is_admin": True
        }
    
    # Require credentials
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=401,
            detail="API key required. Provide Authorization: Bearer <api_key> header."
        )
    
    # Verify API key (if dcisionai_onboarding is available)
    if not _onboarding_available or APIKeyService is None:
        # Onboarding module not available - reject API key requirement
        raise HTTPException(
            status_code=503,
            detail="API key verification service not available. dcisionai_onboarding module is required."
        )
    
    api_key = credentials.credentials
    api_key_service = APIKeyService()
    
    try:
        tenant_info = api_key_service.verify_api_key(api_key)
        
        if not tenant_info:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired API key"
            )
        
        return {
            "tenant_id": tenant_info.get("tenant_id"),
            "api_key_id": tenant_info.get("api_key_id"),
            "metadata": tenant_info.get("metadata", {}),
            "is_admin": tenant_info.get("metadata", {}).get("is_admin", False)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying API key: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to verify API key: {str(e)}"
        )

