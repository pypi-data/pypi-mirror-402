"""
Checkpoint API Endpoints (Phase 5)

REST API endpoints for checkpoint management.
Following MCP protocol where possible, but providing REST convenience endpoints.
"""

import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional

from ..tools.checkpointing import (
    create_checkpoint,
    restore_checkpoint,
    list_checkpoints,
    delete_checkpoint
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/checkpoints", tags=["checkpoints"])


@router.post("/create")
async def create_checkpoint_endpoint(
    state: Dict[str, Any],
    session_id: Optional[str] = None
) -> JSONResponse:
    """
    Create a checkpoint of current workflow state.
    
    Request Body:
        state: Current workflow state
        session_id: Optional session ID
    """
    try:
        result = create_checkpoint(state, session_id)
        return JSONResponse(result)
    except Exception as e:
        logger.error(f"Error creating checkpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restore/{checkpoint_id}")
async def restore_checkpoint_endpoint(checkpoint_id: str) -> JSONResponse:
    """
    Restore state from checkpoint.
    
    Path Parameters:
        checkpoint_id: Checkpoint ID to restore
    """
    try:
        restored_state = restore_checkpoint(checkpoint_id)
        if restored_state is None:
            raise HTTPException(status_code=404, detail=f"Checkpoint not found: {checkpoint_id}")
        return JSONResponse({"state": restored_state})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring checkpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_checkpoints_endpoint(session_id: Optional[str] = None) -> JSONResponse:
    """
    List all checkpoints, optionally filtered by session_id.
    
    Query Parameters:
        session_id: Optional session ID to filter by
    """
    try:
        checkpoints = list_checkpoints(session_id)
        return JSONResponse({"checkpoints": checkpoints})
    except Exception as e:
        logger.error(f"Error listing checkpoints: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{checkpoint_id}")
async def delete_checkpoint_endpoint(checkpoint_id: str) -> JSONResponse:
    """
    Delete a checkpoint.
    
    Path Parameters:
        checkpoint_id: Checkpoint ID to delete
    """
    try:
        success = delete_checkpoint(checkpoint_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Checkpoint not found: {checkpoint_id}")
        return JSONResponse({"success": True, "checkpoint_id": checkpoint_id})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting checkpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

