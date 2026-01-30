"""
Configuration API Endpoints

Exposes server configuration and feature flags to frontend clients.
"""

import logging
from fastapi import APIRouter
from pydantic import BaseModel

from dcisionai_mcp_server.config import MCPConfig

logger = logging.getLogger(__name__)

# Create FastAPI router
router = APIRouter(prefix="/api/config", tags=["config"])


class FeatureFlags(BaseModel):
    """Feature flags configuration"""
    enable_business_explanation: bool
    enable_llm_metrics: bool
    enable_llm_decision_traces: bool
    enable_dame: bool


class ConfigResponse(BaseModel):
    """Server configuration response"""
    feature_flags: FeatureFlags


@router.get("", response_model=ConfigResponse)
async def get_config():
    """
    Get server configuration and feature flags.
    
    This endpoint allows frontend clients to check which features are enabled
    and adjust UI accordingly.
    
    **Response:**
    ```json
    {
        "feature_flags": {
            "enable_business_explanation": false,
            "enable_llm_metrics": false
        }
    }
    ```
    """
    return ConfigResponse(
        feature_flags=FeatureFlags(
            enable_business_explanation=MCPConfig.ENABLE_BUSINESS_EXPLANATION,
            enable_llm_metrics=MCPConfig.ENABLE_LLM_METRICS,
            enable_llm_decision_traces=MCPConfig.ENABLE_LLM_DECISION_TRACES,
            enable_dame=MCPConfig.ENABLE_DAME,
        )
    )

