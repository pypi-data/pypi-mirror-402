"""
API Key Authentication Middleware for Multi-Tenancy

Provides FastAPI dependencies for API key verification and tenant isolation.
"""

from .api_key_auth import verify_api_key_optional, verify_api_key_required

__all__ = ["verify_api_key_optional", "verify_api_key_required"]
