"""
REST API Endpoints for Async Job Queue

This module provides FastAPI endpoints for:
- Job submission (POST /api/jobs/optimize)
- Job status polling (GET /api/jobs/{job_id}/status)
- Job result retrieval (GET /api/jobs/{job_id}/result)
- Job listing (GET /api/jobs)
- Job cancellation (POST /api/jobs/{job_id}/cancel)

Following MCP Protocol:
- HATEOAS links for navigation
- Job resources exposed via job:// URIs
- Compatible with existing MCP tools

Following LangGraph Best Practices:
- Jobs execute Dame Workflow with TypedDict state
- Progress callbacks update JobState
- Checkpointing supports resumable workflows
"""

import json
import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, Request, Depends
from fastapi.responses import Response
from pydantic import BaseModel, Field

# Import API key middleware for multi-tenancy
try:
    from dcisionai_mcp_server.middleware.api_key_auth import verify_api_key_optional
except ImportError:
    # Fallback if middleware not available
    async def verify_api_key_optional():
        from dcisionai_mcp_server.config import MCPConfig
        return {"tenant_id": MCPConfig.DEFAULT_TENANT_ID, "is_admin": False}

from dcisionai_mcp_server.jobs import (
    # Schemas
    JobStatus,
    JobPriority,
    # Tasks
    run_optimization_job,
    cancel_job,
    get_task_status,
    # Storage
    create_job_record,
    get_job,
    get_all_jobs,
    get_jobs_by_session,
    get_jobs_by_status,
    get_job_statistics,
    get_job_files,
    count_jobs,
)

from dcisionai_mcp_server.resources.jobs import (
    read_job_resource,
    list_job_resources,
)

logger = logging.getLogger(__name__)

# Create FastAPI router
router = APIRouter(prefix="/api/jobs", tags=["jobs"])


# ========== REQUEST/RESPONSE MODELS ==========

class JobSubmitRequest(BaseModel):
    """Request body for job submission"""
    problem_description: Optional[str] = Field(None, description="Natural language optimization query (preferred)")
    user_query: Optional[str] = Field(None, description="Natural language optimization query (backward compatibility)")
    session_id: str = Field(..., description="Session identifier for context")
    priority: str = Field(default="normal", description="Job priority: low, normal, high, urgent")
    use_case: Optional[str] = Field(None, description="Optional use case hint (e.g., 'VRP', 'client_advisor_matching')")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Optional additional parameters")
    hitl_enabled: bool = Field(default=False, description="Enable HITL mode (True=user interaction, False=auto-pilot with synthetic data)")
    
    def get_problem_description(self) -> str:
        """Get problem description from either field (backward compatibility)"""
        return self.problem_description or self.user_query or ""


class JobSubmitResponse(BaseModel):
    """Response for job submission"""
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Current job status")
    priority: str = Field(..., description="Job priority")
    created_at: str = Field(..., description="Job creation timestamp (ISO 8601)")
    links: Dict[str, str] = Field(..., description="HATEOAS navigation links")


class JobStatusResponse(BaseModel):
    """Response for job status polling"""
    job_id: str
    session_id: str
    status: str
    priority: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    user_query: str
    use_case: Optional[str] = None
    progress: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    links: Dict[str, str]


class JobResultResponse(BaseModel):
    """Response for job result retrieval"""
    job_id: str
    status: str
    completed_at: str
    result: Dict[str, Any]
    links: Dict[str, str]


class JobListResponse(BaseModel):
    """Response for job listing"""
    jobs: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    links: Dict[str, str]


class JobCancelResponse(BaseModel):
    """Response for job cancellation"""
    job_id: str
    status: str
    cancelled_at: str
    message: str


# ========== ENDPOINTS ==========

@router.post("/submit", response_model=JobSubmitResponse, status_code=202)
async def submit_workflow_job(request: Request):
    """
    Submit a new optimization job (simplified endpoint for React client).

    This endpoint accepts workflow parameters from the React MCP client and dispatches
    them to the async job queue for background processing.

    **Expected Request Body from React Client:**
    ```json
    {
        "problem_description": "Optimize delivery routes...",
        "enabled_features": ["vagueness_detection", "template_matching"],
        "enabled_tools": ["intent_discovery", "data_preparation", "solver"],
        "reasoning_model": "claude-haiku-4-5-20251001",
        "code_model": "claude-sonnet-4-5-20250929",
        "enable_validation": false,
        "enable_templates": true,
        "use_claude_sdk_for_pyomo": true,
        "use_parallel_execution": false,
        "template_hint": null,
        "priority": "normal",
        "use_case": null
    }
    ```

    **Response (202 Accepted):**
    ```json
    {
        "job_id": "550e8400-e29b-41d4-a716-446655440000",
        "status": "queued",
        "priority": "normal",
        "created_at": "2025-12-08T12:00:00Z",
        "links": {
            "self": "/api/jobs/550e8400-e29b-41d4-a716-446655440000",
            "status": "/api/jobs/550e8400-e29b-41d4-a716-446655440000/status",
            "progress": "/api/jobs/550e8400-e29b-41d4-a716-446655440000/progress",
            "result": "/api/jobs/550e8400-e29b-41d4-a716-446655440000/result"
        }
    }
    ```
    """
    import json
    body = await request.json()

    logger.info(f"Received workflow job submission: {body.get('problem_description', '')[:100]}...")

    # Extract fields from request body
    problem_description = body.get("problem_description", "")
    if not problem_description:
        raise HTTPException(status_code=400, detail="problem_description is required")

    # Generate unique job ID
    job_id = str(uuid.uuid4())

    # Use a default session ID if not provided (React client doesn't send this)
    # Format: session_{job_id} so we can extract full job_id later
    session_id = body.get("session_id", f"session_{job_id}")

    # Validate priority
    priority_str = body.get("priority", "normal")
    try:
        priority = JobPriority[priority_str.upper()]
    except KeyError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid priority: {priority_str}. Must be one of: low, normal, high, urgent"
        )

    # Prepare workflow parameters
    parameters = {
        "enabled_features": body.get("enabled_features", []),
        "enabled_tools": body.get("enabled_tools", []),
        "reasoning_model": body.get("reasoning_model", "claude-haiku-4-5-20251001"),
        "code_model": body.get("code_model", "claude-sonnet-4-5-20250929"),
        "enable_validation": body.get("enable_validation", False),
        "enable_templates": body.get("enable_templates", True),
        "use_claude_sdk_for_pyomo": body.get("use_claude_sdk_for_pyomo", True),
        "use_parallel_execution": body.get("use_parallel_execution", False),
        "template_hint": body.get("template_hint"),
    }

    use_case = body.get("use_case")
    hitl_enabled = body.get("hitl_enabled", False)  # Default to Auto-Pilot mode

    # Create job record in database
    try:
        job_record = create_job_record(
            job_id=job_id,
            session_id=session_id,
            user_query=problem_description,
            priority=priority,
            use_case=use_case,
            parameters=parameters,
        )
        logger.info(f"Job record created: {job_id}")
    except Exception as e:
        logger.error(f"Failed to create job record: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create job record: {str(e)}")

    # Dispatch to Celery (use job_id as task_id for consistency)
    try:
        task = run_optimization_job.apply_async(
            args=(job_id, problem_description, session_id),
            kwargs={
                "use_case": use_case,
                "parameters": parameters,
                "hitl_enabled": hitl_enabled,
            },
            task_id=job_id,  # Use job_id as Celery task_id
            priority=priority.value,
        )
        logger.info(f"Job dispatched to Celery: {job_id} (task_id: {task.id})")
    except Exception as e:
        logger.error(f"Failed to dispatch job to Celery: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to dispatch job: {str(e)}")

    # Build HATEOAS links
    base_url = str(request.base_url).rstrip("/")
    links = {
        "self": f"{base_url}/api/jobs/{job_id}",
        "status": f"{base_url}/api/jobs/{job_id}/status",
        "progress": f"{base_url}/api/jobs/{job_id}/progress",
        "result": f"{base_url}/api/jobs/{job_id}/result",
    }

    return JobSubmitResponse(
        job_id=job_id,
        status=JobStatus.QUEUED.value,
        priority=priority.value,
        created_at=job_record["created_at"],
        links=links,
    )


@router.post("/optimize", response_model=JobSubmitResponse, status_code=202)
async def submit_optimization_job(request: JobSubmitRequest, http_request: Request):
    """
    Submit a new optimization job to the async queue.

    This endpoint accepts a natural language query and dispatches it to Celery
    for background processing. The job executes the Dame Workflow asynchronously,
    allowing the client to poll for status or subscribe to WebSocket updates.

    **Request Body:**
    ```json
    {
        "user_query": "Optimize delivery routes for 150 packages",
        "session_id": "user_session_123",
        "priority": "normal",
        "use_case": "VRP",
        "parameters": {}
    }
    ```

    **Response (202 Accepted):**
    ```json
    {
        "job_id": "550e8400-e29b-41d4-a716-446655440000",
        "status": "queued",
        "priority": "normal",
        "created_at": "2025-12-08T12:00:00Z",
        "links": {
            "self": "/api/jobs/550e8400-e29b-41d4-a716-446655440000",
            "status": "/api/jobs/550e8400-e29b-41d4-a716-446655440000/status",
            "stream": "/api/jobs/550e8400-e29b-41d4-a716-446655440000/stream",
            "cancel": "/api/jobs/550e8400-e29b-41d4-a716-446655440000/cancel"
        }
    }
    ```

    **HATEOAS Links:**
    - `self`: Job details endpoint
    - `status`: Job status polling endpoint
    - `stream`: WebSocket streaming endpoint
    - `cancel`: Job cancellation endpoint
    """
    logger.info(f"Received job submission: {request.user_query[:100]}...")

    # Generate unique job ID
    job_id = str(uuid.uuid4())

    # Validate priority
    try:
        priority = JobPriority[request.priority.upper()]
    except KeyError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid priority: {request.priority}. Must be one of: low, normal, high, urgent"
        )

    # Create job record in database
    try:
        job_record = create_job_record(
            job_id=job_id,
            session_id=request.session_id,
            user_query=problem_description,  # Use extracted problem_description
            priority=priority,
            use_case=request.use_case,
            parameters=request.parameters,
        )
        logger.info(f"Job record created: {job_id}")
    except Exception as e:
        logger.error(f"Failed to create job record: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create job record: {str(e)}")

    # Dispatch to Celery (use job_id as task_id for consistency)
    try:
        # Extract problem_description (support both fields for backward compatibility)
        problem_description = request.get_problem_description()
        if not problem_description:
            raise HTTPException(status_code=400, detail="Either 'problem_description' or 'user_query' must be provided")
        
        task = run_optimization_job.apply_async(
            args=(job_id, problem_description, request.session_id),
            kwargs={
                "use_case": request.use_case,
                "parameters": request.parameters,
                "hitl_enabled": request.hitl_enabled,
            },
            task_id=job_id,  # Use job_id as Celery task_id
            priority=priority.value,
        )
        logger.info(f"Job dispatched to Celery: {job_id} (task_id: {task.id})")
    except Exception as e:
        logger.error(f"Failed to dispatch job to Celery: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to dispatch job: {str(e)}")

    # Build HATEOAS links
    base_url = str(http_request.base_url).rstrip("/")
    links = {
        "self": f"{base_url}/api/jobs/{job_id}",
        "status": f"{base_url}/api/jobs/{job_id}/status",
        "stream": f"{base_url}/api/jobs/{job_id}/stream",
        "cancel": f"{base_url}/api/jobs/{job_id}/cancel",
    }

    return JobSubmitResponse(
        job_id=job_id,
        status=JobStatus.QUEUED.value,
        priority=priority.value,
        created_at=job_record["created_at"],
        links=links,
    )


@router.get("", response_model=JobListResponse)
async def list_jobs(
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of jobs per page"),
    http_request: Request = None,
    tenant_info: dict = Depends(verify_api_key_optional),
):
    """
    List jobs with optional filtering and pagination.

    **Query Parameters:**
    - `session_id`: Filter jobs by session ID
    - `status`: Filter jobs by status (queued, running, completed, failed, cancelled)
    - `page`: Page number (1-indexed)
    - `page_size`: Number of jobs per page (max 100)

    **Example Request:**
    ```
    GET /api/jobs?session_id=user_session_123&status=completed&page=1&page_size=20
    ```

    **Response:**
    ```json
    {
        "jobs": [
            {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "completed",
                "priority": "normal",
                "created_at": "2025-12-08T12:00:00Z",
                "completed_at": "2025-12-08T12:05:00Z",
                "user_query": "Optimize delivery routes..."
            },
            ...
        ],
        "total": 45,
        "page": 1,
        "page_size": 20,
        "links": {
            "self": "/api/jobs?session_id=user_session_123&page=1&page_size=20",
            "next": "/api/jobs?session_id=user_session_123&page=2&page_size=20"
        }
    }
    ```
    """
    tenant_id = tenant_info.get("tenant_id")
    is_admin = tenant_info.get("is_admin", False)
    
    logger.info(f"Listing jobs: session_id={session_id}, status={status}, page={page}, page_size={page_size}, tenant_id={tenant_id}, is_admin={is_admin}")

    # Calculate offset for database-level pagination
    offset = (page - 1) * page_size
    
    # Get total count first (for pagination metadata)
    total = count_jobs(session_id=session_id, status=status, tenant_id=tenant_id if not is_admin else None)
    
    # Get jobs with database-level pagination
    try:
        if session_id and status:
            # Filter by both session and status
            status_enum = JobStatus[status.upper()]
            # Get jobs by session with status filter (need to filter in Python for now)
            # TODO: Add combined filter support to storage layer
            all_session_jobs = get_jobs_by_session(session_id, limit=1000, offset=0)
            filtered_jobs = [j for j in all_session_jobs if j["status"] == status]
            # Recalculate total for filtered results
            total = len(filtered_jobs)
            page_jobs = filtered_jobs[offset:offset + page_size]
        elif session_id:
            # Filter by session only
            page_jobs = get_jobs_by_session(session_id, limit=page_size, offset=offset)
        elif status:
            # Filter by status only
            status_enum = JobStatus[status.upper()]
            page_jobs = get_jobs_by_status(status_enum, limit=page_size, offset=offset)
        else:
            # No filters - get all jobs with pagination
            page_jobs = get_all_jobs(limit=page_size, offset=offset, tenant_id=tenant_id if not is_admin else None)
        
        # Apply tenant filtering if multi-tenancy is enabled and not admin (for session+status case)
        from dcisionai_mcp_server.config import MCPConfig
        if MCPConfig.MULTI_TENANT_ENABLED and not is_admin and tenant_id and session_id and status:
            page_jobs = [j for j in page_jobs if j.get('tenant_id') == tenant_id]
            logger.debug(f"Filtered to {len(page_jobs)} jobs for tenant {tenant_id}")
    except KeyError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status: {status}. Must be one of: queued, running, completed, failed, cancelled"
        )

    # Simplify job records for list response
    simplified_jobs = []
    for job in page_jobs:
        simplified_jobs.append({
            "job_id": job["job_id"],
            "status": job["status"],
            "priority": job["priority"],
            "created_at": job["created_at"],
            "started_at": job["started_at"],
            "completed_at": job["completed_at"],
            "user_query": job["user_query"],
            "use_case": job["use_case"],
            "progress": job.get("progress"),  # Include progress for progress bar display
        })

    # Build HATEOAS links
    base_url = str(http_request.base_url).rstrip("/")
    query_params = []
    if session_id:
        query_params.append(f"session_id={session_id}")
    if status:
        query_params.append(f"status={status}")

    query_string = "&".join(query_params)
    links = {
        "self": f"{base_url}/api/jobs?{query_string}&page={page}&page_size={page_size}",
    }

    # Add next/prev links
    if offset + page_size < total:
        links["next"] = f"{base_url}/api/jobs?{query_string}&page={page + 1}&page_size={page_size}"
    if page > 1:
        links["prev"] = f"{base_url}/api/jobs?{query_string}&page={page - 1}&page_size={page_size}"

    return JobListResponse(
        jobs=simplified_jobs,
        total=total,
        page=page,
        page_size=page_size,
        links=links,
    )


@router.get("/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: str, http_request: Request):
    """
    Get current job status (polling endpoint).

    This endpoint returns the current status, progress, and metadata for a job.
    Clients can poll this endpoint periodically to check job progress, or use
    the WebSocket endpoint for real-time updates.

    **Response:**
    ```json
    {
        "job_id": "550e8400-e29b-41d4-a716-446655440000",
        "session_id": "user_session_123",
        "status": "running",
        "priority": "normal",
        "created_at": "2025-12-08T12:00:00Z",
        "started_at": "2025-12-08T12:00:05Z",
        "completed_at": null,
        "user_query": "Optimize delivery routes...",
        "progress": {
            "current_step": "data_generation",
            "progress_percentage": 45,
            "step_details": {"tables": 3},
            "updated_at": "2025-12-08T12:00:30Z"
        },
        "error": null,
        "links": {
            "self": "/api/jobs/550e8400-e29b-41d4-a716-446655440000/status",
            "stream": "/api/jobs/550e8400-e29b-41d4-a716-446655440000/stream",
            "cancel": "/api/jobs/550e8400-e29b-41d4-a716-446655440000/cancel"
        }
    }
    ```

    **Status Values:**
    - `queued`: Job is waiting to be processed
    - `running`: Job is currently executing
    - `completed`: Job finished successfully
    - `failed`: Job encountered an error
    - `cancelled`: Job was cancelled by user
    """
    logger.info(f"Getting status for job: {job_id}")

    # Get job from storage
    job_record = get_job(job_id)
    if not job_record:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    # Parse progress if available
    import json
    progress = None
    if job_record["progress"]:
        progress = json.loads(job_record["progress"])

    # Build HATEOAS links
    base_url = str(http_request.base_url).rstrip("/")
    links = {
        "self": f"{base_url}/api/jobs/{job_id}/status",
        "stream": f"{base_url}/api/jobs/{job_id}/stream",
    }

    # Add result link if completed
    if job_record["status"] == JobStatus.COMPLETED.value:
        links["result"] = f"{base_url}/api/jobs/{job_id}/result"
    elif job_record["status"] in [JobStatus.QUEUED.value, JobStatus.RUNNING.value]:
        links["cancel"] = f"{base_url}/api/jobs/{job_id}/cancel"

    return JobStatusResponse(
        job_id=job_id,
        session_id=job_record["session_id"],
        status=job_record["status"],
        priority=job_record["priority"],
        created_at=job_record["created_at"],
        started_at=job_record["started_at"],
        completed_at=job_record["completed_at"],
        user_query=job_record["user_query"],
        use_case=job_record["use_case"],
        progress=progress,
        error=job_record["error"],
        links=links,
    )


@router.get("/{job_id}/progress")
async def get_job_progress(job_id: str):
    """
    Get job progress for real-time updates (simplified endpoint for React client).

    Returns the progress field from the job record, if available.

    **Response:**
    ```json
    {
        "job_id": "550e8400-e29b-41d4-a716-446655440000",
        "progress_percentage": 45,
        "current_step": "data_generation",
        "step_details": {"tables": 3},
        "updated_at": "2025-12-08T12:00:30Z"
    }
    ```
    """
    logger.info(f"Getting progress for job: {job_id}")

    # Get job from storage
    job_record = get_job(job_id)
    if not job_record:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    # Parse progress if available
    import json
    progress = None
    if job_record["progress"]:
        progress = json.loads(job_record["progress"])

    if not progress:
        # Return minimal progress if none available
        return {
            "job_id": job_id,
            "progress_percentage": 0,
            "current_step": None,
            "step_details": None,
            "updated_at": job_record["created_at"]
        }

    # Add job_id to progress response
    progress["job_id"] = job_id
    return progress


@router.get("/{job_id}/result", response_model=JobResultResponse)
async def get_job_result(job_id: str, http_request: Request):
    """
    Get final job result (only available for completed jobs).

    This endpoint returns the complete workflow result including intent discovery,
    data generation, solver optimization, and business explanation.

    **Response:**
    ```json
    {
        "job_id": "550e8400-e29b-41d4-a716-446655440000",
        "status": "completed",
        "completed_at": "2025-12-08T12:05:00Z",
        "result": {
            "status": "completed",
            "workflow_state": {
                "intent": {...},
                "data_pack": {...},
                "solver_output": {...},
                "explanation": {...}
            },
            "mcp_resources": {
                "status": "job://550e8400-e29b-41d4-a716-446655440000/status",
                "result": "job://550e8400-e29b-41d4-a716-446655440000/result",
                "intent": "job://550e8400-e29b-41d4-a716-446655440000/intent",
                "data": "job://550e8400-e29b-41d4-a716-446655440000/data",
                "solver": "job://550e8400-e29b-41d4-a716-446655440000/solver",
                "explanation": "job://550e8400-e29b-41d4-a716-446655440000/explanation"
            }
        },
        "links": {
            "self": "/api/jobs/550e8400-e29b-41d4-a716-446655440000/result",
            "status": "/api/jobs/550e8400-e29b-41d4-a716-446655440000/status"
        }
    }
    ```

    **MCP Resources:**
    All job artifacts are exposed as MCP resources using the `job://` URI scheme.
    """
    logger.info(f"Getting result for job: {job_id}")

    # Get job from storage
    job_record = get_job(job_id)
    if not job_record:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    # Check if job is completed
    if job_record["status"] != JobStatus.COMPLETED.value:
        raise HTTPException(
            status_code=409,
            detail=f"Job not completed (status: {job_record['status']}). Result not available."
        )

    # Parse result
    import json
    if not job_record["result"]:
        # CRITICAL FIX: Try to retrieve result from Celery backend as fallback
        # This handles cases where save_job_result() failed but result exists in Celery
        logger.warning(f"Job {job_id} marked as completed but has no result in database. Attempting to retrieve from Celery backend...")
        
        try:
            from dcisionai_mcp_server.jobs.tasks import celery_app
            from celery.result import AsyncResult
            
            # Try to get result from Celery backend
            celery_result = AsyncResult(job_id, app=celery_app)
            
            if celery_result.ready() and celery_result.successful():
                celery_data = celery_result.result
                if celery_data and isinstance(celery_data, dict):
                    # Found result in Celery backend - save it to database
                    logger.info(f"✅ Found result in Celery backend for job {job_id}, saving to database...")
                    from dcisionai_mcp_server.jobs.storage import save_job_result
                    try:
                        save_job_result(job_id=job_id, result=celery_data)
                        logger.info(f"✅ Successfully saved result from Celery backend to database")
                        # Re-fetch job record to get the newly saved result
                        job_record = get_job(job_id)
                        if job_record and job_record["result"]:
                            result = json.loads(job_record["result"])
                        else:
                            # Use Celery result directly
                            result = celery_data
                    except Exception as save_error:
                        logger.error(f"❌ Failed to save result from Celery backend: {save_error}")
                        # Use Celery result directly as fallback
                        result = celery_data
                else:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Job marked as completed but has no result. Celery backend also has no valid result."
                    )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Job marked as completed but has no result. Celery task status: {celery_result.state if celery_result else 'unknown'}"
                )
        except ImportError:
            logger.error("Celery not available for result fallback")
            raise HTTPException(
                status_code=500,
                detail=f"Job marked as completed but has no result. Unable to retrieve from Celery backend."
            )
        except Exception as celery_error:
            logger.error(f"Failed to retrieve result from Celery backend: {celery_error}")
            raise HTTPException(
                status_code=500,
                detail=f"Job marked as completed but has no result. Error retrieving from Celery: {str(celery_error)}"
            )
    else:
        result = json.loads(job_record["result"])
    
    # CRITICAL: Include thinking_history from progress if not already in workflow_state
    # This ensures CoT is restored on page reload (same logic as MCP resource handler)
    workflow_state = result.get("workflow_state", {})
    if not workflow_state.get("thinking_history"):
        # Try to get thinking_history from progress field
        progress_data = job_record.get("progress")
        if progress_data:
            # Progress might be stored as JSON string or dict
            if isinstance(progress_data, str):
                try:
                    progress = json.loads(progress_data)
                except (json.JSONDecodeError, TypeError):
                    progress = None
            else:
                progress = progress_data
            
            if progress and isinstance(progress, dict):
                thinking_history = progress.get("thinking_history", {})
                if thinking_history:
                    # Add thinking_history to workflow_state
                    workflow_state["thinking_history"] = thinking_history
                    result["workflow_state"] = workflow_state
                    logger.debug(f"✅ Added thinking_history to REST API result for job {job_id} ({len(thinking_history)} steps)")
    
    # CRITICAL: Include llm_metrics from database if not already in result
    # Metrics are stored separately in llm_metrics column
    if not result.get("llm_metrics") and job_record.get("llm_metrics"):
        try:
            llm_metrics_data = job_record.get("llm_metrics")
            if isinstance(llm_metrics_data, str):
                llm_metrics = json.loads(llm_metrics_data)
            else:
                llm_metrics = llm_metrics_data
            if llm_metrics:
                result["llm_metrics"] = llm_metrics
                logger.debug(f"✅ Added llm_metrics to REST API result for job {job_id}: {llm_metrics.get('total_calls', 0)} calls")
        except (json.JSONDecodeError, TypeError) as metrics_error:
            logger.warning(f"⚠️ Failed to parse llm_metrics for job {job_id}: {metrics_error}")

    # Build HATEOAS links
    base_url = str(http_request.base_url).rstrip("/")
    links = {
        "self": f"{base_url}/api/jobs/{job_id}/result",
        "status": f"{base_url}/api/jobs/{job_id}/status",
    }

    return JobResultResponse(
        job_id=job_id,
        status=job_record["status"],
        completed_at=job_record["completed_at"],
        result=result,
        links=links,
    )


@router.post("/{job_id}/summarize-executive-summary")
async def summarize_executive_summary(
    job_id: str,
    tenant_info: dict = Depends(verify_api_key_optional)
):
    """
    Extract Executive_Summary.md from solver results and generate a structured summary.
    
    Uses LLM to convert the markdown file into a structured executive summary format.
    
    **Response:**
    ```json
    {
        "job_id": "550e8400-e29b-41d4-a716-446655440000",
        "executive_summary": {
            "problem_statement": "...",
            "optimal_solution": "...",
            "objective_value": {...},
            "key_metrics": {...},
            "confidence_level": "high|medium|low"
        }
    }
    ```
    """
    logger.info(f"Summarizing Executive_Summary.md for job: {job_id}")
    
    # Get job from storage
    job_record = get_job(job_id)
    if not job_record:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    
    # Check if job is completed
    if job_record["status"] != JobStatus.COMPLETED.value:
        raise HTTPException(
            status_code=409,
            detail=f"Executive summary is only available for completed jobs. Current status: {job_record['status']}"
        )
    
    # Get workflow state
    result = job_record.get("result")
    if not result:
        raise HTTPException(status_code=500, detail="Job is completed but has no result data")
    
    # Parse result if it's a string
    if isinstance(result, str):
        try:
            import json
            result = json.loads(result)
        except Exception as e:
            logger.error(f"Failed to parse job result: {e}")
            raise HTTPException(status_code=500, detail="Invalid result data format")
    
    workflow_state = result.get("workflow_state", {})
    solver_result = workflow_state.get("solver_result", {})
    
    # Extract Executive_Summary.md from file_contents
    file_contents = solver_result.get("file_contents", {})
    executive_summary_md = (
        file_contents.get("Executive_Summary.md") or
        file_contents.get("executive_summary.md") or
        file_contents.get("EXECUTIVE_SUMMARY.md")
    )
    
    if not executive_summary_md:
        raise HTTPException(
            status_code=404,
            detail="Executive_Summary.md not found in solver results"
        )
    
    # Parse markdown into sections
    try:
        sections = _parse_markdown_sections(executive_summary_md)
        
        # Filter out any sections with empty or whitespace-only content
        sections = [s for s in sections if s.get("content") and s["content"].strip()]
        
        # Filter out "Questions?" and "Questions" sections (customer's own teams handle this)
        sections = [s for s in sections if s.get("title", "").lower() not in ["questions?", "questions"]]
        
        # Log for debugging
        logger.info(f"Parsed {len(sections)} sections from Executive_Summary.md")
        for section in sections:
            logger.debug(f"Section '{section['title']}': {len(section.get('content', ''))} chars")
        
        return {
            "job_id": job_id,
            "sections": sections,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to parse Executive_Summary.md: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse Executive_Summary.md: {str(e)}"
        )


def _parse_markdown_sections(markdown_content: str) -> List[Dict[str, Any]]:
    """
    Parse markdown content into sections based on ## headings.
    Each section becomes a tab in the frontend.
    
    Returns a list of sections with:
    - title: Section heading (## text)
    - content: Markdown content for that section
    - order: Display order
    """
    import re
    
    sections = []
    
    # Split by ## headings (level 2 headings)
    # Pattern matches: ## Title (with optional leading whitespace)
    pattern = r'^##\s+(.+)$'
    
    lines = markdown_content.split('\n')
    current_section = None
    current_content = []
    has_seen_first_heading = False
    pre_heading_content = []  # Collect content before first heading
    
    for line in lines:
        # Check if this line is a ## heading
        match = re.match(pattern, line.strip())
        if match:
            heading_title = match.group(1).strip()
            
            # Skip "Overview" and "Questions?" sections entirely
            heading_lower = heading_title.lower()
            is_skipped_section = heading_lower == "overview" or heading_lower == "questions?" or heading_lower == "questions"
            
            # If this is the first heading and we have pre-heading content
            if not has_seen_first_heading:
                if pre_heading_content:
                    # Skip "Overview" and "Questions?" sections - don't create them
                    if is_skipped_section:
                        # Skip section, discard pre-heading content
                        current_section = None
                        current_content = []
                        pre_heading_content = []
                    else:
                        # First heading is not skipped, start with the actual first heading
                        current_section = heading_title
                        current_content = []
                        pre_heading_content = []
                else:
                    # No pre-heading content
                    # Skip "Overview" and "Questions?" sections entirely
                    if is_skipped_section:
                        current_section = None
                        current_content = []
                    else:
                        current_section = heading_title
                        current_content = []
            else:
                # Save previous section if it exists (this is not the first heading)
                if current_section is not None:
                    # Skip "Overview" and "Questions?" sections entirely
                    current_section_lower = current_section.lower()
                    if current_section_lower != "overview" and current_section_lower != "questions?" and current_section_lower != "questions":
                        content = '\n'.join(current_content).strip()
                        # Only add section if it has meaningful content (not just whitespace)
                        if content and len(content) > 0:
                            # Check if a section with this title already exists (prevent duplicates)
                            existing_titles = [s["title"] for s in sections]
                            if current_section in existing_titles:
                                # Merge content into existing section
                                existing_index = existing_titles.index(current_section)
                                sections[existing_index]["content"] += "\n\n" + content
                            else:
                                sections.append({
                                    "title": current_section,
                                    "content": content,
                                    "order": len(sections)
                                })
                    # If it's Overview/Questions? or content is empty, skip this section (don't add it)
                
                # Start new section (skip if it's Overview or Questions?)
                if is_skipped_section:
                    current_section = None
                    current_content = []
                else:
                    current_section = heading_title
                    current_content = []
            
            has_seen_first_heading = True
        else:
            # Add line to current section content
            if current_section is not None:
                current_content.append(line)
            elif line.strip() and not has_seen_first_heading:
                # Content before first section - collect it
                pre_heading_content.append(line)
    
    # Add the last section (skip if it's Overview or Questions?)
    if current_section:
        current_section_lower = current_section.lower()
        if current_section_lower != "overview" and current_section_lower != "questions?" and current_section_lower != "questions":
            content = '\n'.join(current_content).strip()
            # Only add section if it has meaningful content (not just whitespace)
            if content and len(content) > 0:
                # Check if a section with this title already exists (prevent duplicates)
                existing_titles = [s["title"] for s in sections]
                if current_section in existing_titles:
                    # Merge content into existing section
                    existing_index = existing_titles.index(current_section)
                    sections[existing_index]["content"] += "\n\n" + content
                else:
                    sections.append({
                        "title": current_section,
                        "content": content,
                        "order": len(sections)
                    })
    
    # If no sections were found, create a single "Summary" section with all content
    # (but skip if the only content was an Overview section)
    if not sections:
        content = markdown_content.strip()
        if content:
            # Check if content is just an Overview section
            overview_pattern = r'^##\s+Overview\s*$'
            import re
            if not re.match(overview_pattern, content, re.IGNORECASE | re.MULTILINE):
                sections.append({
                    "title": "Summary",
                    "content": content,
                    "order": 0
                })
    
    return sections


@router.get("/{job_id}/business-summary")
async def get_business_summary(job_id: str, tenant_info: dict = Depends(verify_api_key_optional)):
    """
    Generate or retrieve business-facing solution summary for a completed job.
    
    Uses Claude Sonnet 4.5 to analyze solver results and generate
    document-ready business insights.
    
    **Response:**
    ```json
    {
        "job_id": "550e8400-e29b-41d4-a716-446655440000",
        "summary": "# Business-Facing Solution Analysis\n\n## Executive Summary\n...",
        "generated_at": "2025-12-08T12:05:00Z"
    }
    ```
    """
    logger.info(f"Getting business summary for job: {job_id}")
    
    # Get job from storage
    job_record = get_job(job_id)
    if not job_record:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    
    # Check if job is completed
    if job_record["status"] != JobStatus.COMPLETED.value:
        raise HTTPException(
            status_code=409,
            detail=f"Business summary is only available for completed jobs. Current status: {job_record['status']}"
        )
    
    # Check if result exists
    if not job_record.get("result"):
        raise HTTPException(
            status_code=500,
            detail="Job is completed but has no result data"
        )
    
    # Import business summary generator
    try:
        import sys
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir))
        scripts_dir = os.path.join(project_root, "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        
        from generate_business_summary import generate_business_summary
        
        # Generate business summary (handles different file naming conventions internally)
        summary_text = generate_business_summary(job_id, output_file=None)
        
        return {
            "job_id": job_id,
            "summary": summary_text,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    except ImportError as e:
        logger.error(f"Failed to import business summary generator: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Business summary generation not available: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to generate business summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate business summary: {str(e)}"
        )


class DeployModelRequest(BaseModel):
    """Request body for model deployment"""
    name: str = Field(..., description="Model name (e.g., 'Portfolio Optimization')")
    description: str = Field(..., description="Model description")
    domain: str = Field(default="general", description="Domain (e.g., 'private_equity', 'ria', 'logistics')")


class DeployModelResponse(BaseModel):
    """Response for model deployment"""
    status: str = Field(..., description="Deployment status")
    model_id: str = Field(..., description="Deployed model ID")
    message: str = Field(..., description="Deployment message")
    file_path: Optional[str] = Field(None, description="Path to deployed model file (internal)")
    endpoint_url: Optional[str] = Field(None, description="HTTP endpoint URL for executing the model")
    version: Optional[str] = Field(None, description="Model version number")
    all_versions: Optional[list[str]] = Field(None, description="All versions of this model")


@router.get("/{job_id}/files")
async def get_job_files_endpoint(job_id: str):
    """
    Get all files for a job.
    
    Returns:
        Dict with:
        - file_contents: Dict mapping filename to content (small files <100KB stored in JSONB)
        - file_urls: Dict mapping filename to Supabase Storage URL (large files >=100KB)
        - saved_files_path: Local filesystem path (if available)
        - total_files: Total number of files
    """
    try:
        files = get_job_files(job_id)
        
        if not files or files.get('total_files', 0) == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No files found for job {job_id}"
            )
        
        return {
            "job_id": job_id,
            "file_contents": files.get('file_contents', {}),
            "file_urls": files.get('file_urls', {}),
            "signed_urls": files.get('signed_urls', {}),  # Include signed URLs for private bucket files
            "saved_files_path": files.get('saved_files_path'),
            "total_files": files.get('total_files', 0),
            "files_in_jsonb": len(files.get('file_contents', {})),
            "files_in_storage": len(files.get('file_urls', {})),
            "bucket_is_private": files.get('bucket_is_private', True)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get files for job {job_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve files: {str(e)}"
        )


@router.post("/{job_id}/deploy", response_model=DeployModelResponse)
async def deploy_job_model(
    job_id: str, 
    request: DeployModelRequest, 
    http_request: Request,
    tenant_info: dict = Depends(verify_api_key_optional)
):
    """
    Deploy a model from a completed job as a reusable model endpoint.
    
    This endpoint extracts the Pyomo model code from a completed job and registers it
    as a deployed model that can be invoked directly via the model registry.
    
    **Request Body:**
    ```json
    {
        "name": "Portfolio Optimization",
        "description": "Optimize multi-asset portfolio allocation",
        "domain": "private_equity"
    }
    ```
    
    **Response:**
    ```json
    {
        "status": "success",
        "model_id": "portfolio_optimization_v1",
        "message": "Model deployed successfully",
        "file_path": "dcisionai_workflow/models/portfolio_optimization_model.py"
    }
    ```
    """
    import json
    import os
    import tempfile
    from pathlib import Path
    from datetime import datetime
    
    logger.info(f"🔍 Deploying model from job: {job_id}")
    
    # Query database directly to get fresh data and avoid cache issues
    from dcisionai_mcp_server.jobs.storage import supabase_client
    
    if not supabase_client:
        logger.error("❌ Supabase client not initialized")
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        # Query database directly - use job_id column (primary key)
        # The async_jobs table uses 'job_id' as the primary key, not 'id'
        response = supabase_client.table("async_jobs").select("*").eq("job_id", job_id).execute()
        
        if not response.data or len(response.data) == 0:
            logger.error(f"❌ Job not found in database: {job_id}")
            raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
        
        row = response.data[0]
        logger.info(f"✅ Job found in database: {job_id}, status: {row.get('status')}")
        
        # Check if job is completed
        if row["status"] != JobStatus.COMPLETED.value:
            logger.warning(f"⚠️ Job {job_id} not completed (status: {row['status']})")
            raise HTTPException(
                status_code=409,
                detail=f"Job not completed (status: {row['status']}). Only completed jobs can be deployed."
            )
        
        # Get result from database (Supabase returns JSONB as dict)
        result = row.get("result")
        if not result:
            logger.error(f"❌ Job {job_id} marked as completed but has no result field")
            raise HTTPException(
                status_code=500,
                detail=f"Job marked as completed but has no result. The job may have completed with an error."
            )
        
        # Supabase returns JSONB as dict, but handle both cases
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except (json.JSONDecodeError, TypeError) as e:
                logger.error(f"❌ Failed to parse job result JSON: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to parse job result: {str(e)}")
        elif not isinstance(result, dict):
            logger.error(f"❌ Job result is not a dict or string: {type(result)}")
            raise HTTPException(status_code=500, detail=f"Job result has unexpected type: {type(result)}")
        
        logger.info(f"✅ Retrieved job result from database, type: {type(result)}, keys: {list(result.keys())}")
        workflow_state = result.get("workflow_state", {})
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to query database for job {job_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve job from database: {str(e)}")
    
    if not workflow_state:
        logger.error(f"❌ No workflow_state in job result for {job_id}")
        logger.error(f"Result keys: {list(result.keys())}")
        raise HTTPException(
            status_code=500,
            detail=f"Job result does not contain workflow_state. Result keys: {list(result.keys())}"
        )
    
    # Log full structure for debugging
    logger.info(f"🔍 Deploying model from job {job_id}")
    logger.debug(f"Workflow state keys: {list(workflow_state.keys())}")
    
    # Extract model code from DB-stored workflow_state (prioritize DB over filesystem)
    # This allows deploying old jobs even if local files are gone
    model_code = None
    
    # Get solver_result (most common location)
    solver_result = workflow_state.get("solver_result") or workflow_state.get("claude_sdk_solver") or {}
    logger.info(f"Checking solver_result: type={type(solver_result)}, is_dict={isinstance(solver_result, dict)}")
    
    # PRIORITY 1: Check DB-stored model_code (supports old jobs)
    if isinstance(solver_result, dict):
        solver_keys = list(solver_result.keys())
        logger.info(f"Solver result keys: {solver_keys}")
        
        # Check solver status first
        solver_status = solver_result.get("status", "unknown")
        logger.info(f"🔍 Solver status: {solver_status}")
        
        # Check for model_code in mathematical solver result (most common)
        mathematical = solver_result.get("mathematical", {})
        if isinstance(mathematical, dict):
            model_code = mathematical.get("model_code")
            if model_code:
                logger.info(f"✅ Found model_code in solver_result.mathematical.model_code: length={len(model_code)}")
        
        # Check top-level model_code
        if not model_code:
            model_code = solver_result.get("model_code")
            if model_code:
                logger.info(f"✅ Found model_code in solver_result.model_code: length={len(model_code)}")
        
        # Check nested structures
        if not model_code:
            for key in ['result', 'output', 'data', 'claude_agent_result', 'execution_result']:
                nested = solver_result.get(key, {})
                if isinstance(nested, dict):
                    nested_model_code = nested.get("model_code")
                    if nested_model_code:
                        model_code = nested_model_code
                        logger.info(f"✅ Found model_code in solver_result.{key}.model_code: length={len(model_code)}")
                        break
    
    # PRIORITY 2: Check solver_output (alternative DB location)
    if not model_code:
        solver_output = workflow_state.get("solver_output", {})
        logger.info(f"Checking solver_output: type={type(solver_output)}")
        if isinstance(solver_output, dict):
            model_code = solver_output.get("model_code")
            if model_code:
                logger.info(f"✅ Found model_code in solver_output.model_code: length={len(model_code)}")
    
    # PRIORITY 3: Check workflow_state directly
    if not model_code:
        model_code = workflow_state.get("model_code")
        if model_code:
            logger.info(f"✅ Found model_code directly in workflow_state: length={len(model_code)}")
    
    # PRIORITY 4: Check file_contents (if stored in DB)
    # Extract original model and relaxed versions
    model_code_relaxed = None
    model_code_relaxed_v2 = None
    
    if not model_code and isinstance(solver_result, dict):
        file_contents = solver_result.get("file_contents", {})
        if isinstance(file_contents, dict):
            # Try common model file names (prioritize original model)
            for filename in ["model.py", "solve.py", "model_relaxed.py", "model_bounded.py"]:
                if filename in file_contents:
                    model_code = file_contents[filename]
                    logger.info(f"✅ Found model_code in solver_result.file_contents.{filename}: length={len(model_code)}")
                    break
            
            # Extract relaxed model versions (for retry logic)
            if "model_relaxed.py" in file_contents:
                model_code_relaxed = file_contents["model_relaxed.py"]
                logger.info(f"✅ Found model_relaxed.py: length={len(model_code_relaxed)}")
            
            if "model_relaxed_v2.py" in file_contents:
                model_code_relaxed_v2 = file_contents["model_relaxed_v2.py"]
                logger.info(f"✅ Found model_relaxed_v2.py: length={len(model_code_relaxed_v2)}")
    
    # FALLBACK: Only check filesystem if DB doesn't have it (for backward compatibility)
    # This allows deploying very old jobs that might not have model_code in DB
    if not model_code:
        logger.warning("⚠️ Model code not found in DB, checking filesystem as fallback (may fail for old jobs)")
        work_dir = workflow_state.get("claude_agent_work_dir")
        if work_dir:
            try:
                from pathlib import Path
                work_path = Path(work_dir)
                if work_path.exists():
                    model_file = work_path / "model.py"
                    if model_file.exists():
                        model_code = model_file.read_text()
                        logger.info(f"✅ Read model code from filesystem fallback: {model_file}, length={len(model_code)}")
            except Exception as file_error:
                logger.warning(f"⚠️ Filesystem fallback failed: {file_error}")
    
    # Final check - log what we found
    if not model_code:
        logger.error(f"❌ No model_code found in job {job_id}")
        logger.error(f"Workflow state keys: {list(workflow_state.keys())}")
        if solver_result:
            solver_keys = list(solver_result.keys()) if isinstance(solver_result, dict) else []
            logger.error(f"Solver result keys: {solver_keys}")
            # Log a sample of solver_result to see structure
            if isinstance(solver_result, dict):
                logger.error(f"Solver result sample (first 3 keys): {dict(list(solver_result.items())[:3])}")
        
        raise HTTPException(
            status_code=400,
            detail=(
                f"No model code found in job result. "
                f"The job may not have generated a Pyomo model. "
                f"Solver result keys: {list(solver_result.keys()) if isinstance(solver_result, dict) else 'N/A'}"
            )
        )
    
    logger.info(f"✅ Model code extracted successfully: {len(model_code)} characters")
    
    # Extract default data/parameters from the successful job run
    default_data = {}
    try:
        # Look for data in various locations in workflow_state
        # 1. Check solver_result for fitted_data or data_pack
        if isinstance(solver_result, dict):
            default_data = solver_result.get("fitted_data") or solver_result.get("data_pack") or solver_result.get("data") or {}
        
        # 2. Check workflow_state for generated_data or data_pack
        if not default_data:
            default_data = workflow_state.get("generated_data") or workflow_state.get("data_pack") or workflow_state.get("data") or {}
        
        # 3. Check claude_agent_work_dir for problem_data.json (Claude SDK solver saves data here)
        if not default_data:
            work_dir = workflow_state.get("claude_agent_work_dir")
            if work_dir:
                try:
                    from pathlib import Path
                    work_path = Path(work_dir)
                    data_file = work_path / "problem_data.json"
                    if data_file.exists():
                        with open(data_file, 'r') as f:
                            default_data = json.load(f)
                        logger.info(f"✅ Read default data from problem_data.json in work_dir: {len(default_data)} keys")
                except Exception as file_error:
                    logger.warning(f"⚠️ Could not read problem_data.json from work_dir: {file_error}")
        
        # 4. Check for parameters in workflow_state
        if not default_data:
            params = workflow_state.get("parameters") or {}
            if params:
                default_data = {"parameters": params}
        
        # 5. Check data_pack in workflow_state (may be nested)
        if not default_data:
            # Check nested locations
            if isinstance(workflow_state.get("data_pack"), dict):
                default_data = workflow_state["data_pack"]
            # Check in entities or other nested structures
            entities = workflow_state.get("entities", {})
            if isinstance(entities, dict) and entities:
                # Entities might contain data
                default_data = entities
        
        # Ensure default_data has the expected structure
        # Don't wrap in 'parameters' if it's already structured or if model expects direct access
        if default_data and isinstance(default_data, dict):
            # Check if it's already wrapped
            if "parameters" not in default_data and len(default_data) > 0:
                # Check if keys look like they should be wrapped (scalars, indexed, etc.)
                has_structured_keys = any(key in default_data for key in ['scalars', 'indexed', 'sets', 'matrices'])
                if not has_structured_keys:
                    # For models that expect data['parameters'], wrap it
                    # But we'll detect this in _prepare_data_for_model based on model code
                    # So keep it as-is for now
                    pass
        
        logger.info(f"✅ Extracted default data with keys: {list(default_data.keys())[:10] if isinstance(default_data, dict) else 'N/A'}")
        if isinstance(default_data, dict) and "parameters" in default_data:
            params = default_data["parameters"]
            logger.info(f"   Parameters keys: {list(params.keys())[:10] if isinstance(params, dict) else 'N/A'}")
        elif isinstance(default_data, dict):
            logger.info(f"   Direct data keys (first 10): {list(default_data.keys())[:10]}")
    except Exception as e:
        logger.warning(f"⚠️ Failed to extract default data from job result: {e}", exc_info=True)
        default_data = {}
    
    # Generate model ID from name with versioning support
    base_name = request.name.lower().replace(' ', '_').replace('-', '_')
    
    # Check for existing versions and determine next version number
    from dcisionai_workflow.models.model_registry import MODEL_REGISTRY
    
    # Find all existing versions of this model
    existing_versions = []
    for existing_id in MODEL_REGISTRY.keys():
        if existing_id.startswith(f"{base_name}_v"):
            try:
                # Extract version number
                version_part = existing_id.rsplit('_v', 1)[1]
                version_num = int(version_part)
                existing_versions.append(version_num)
            except (ValueError, IndexError):
                # If version parsing fails, treat as v1
                if existing_id == f"{base_name}_v1":
                    existing_versions.append(1)
    
    # Determine next version number
    if existing_versions:
        next_version = max(existing_versions) + 1
    else:
        next_version = 1
    
    model_id = f"{base_name}_v{next_version}"
    
    logger.info(f"Deploying model as {model_id} (existing versions: {sorted(existing_versions) if existing_versions else 'none'})")
    
    # Generate file path (include version in filename to avoid conflicts)
    base_name = model_id.rsplit('_v', 1)[0]
    version = model_id.rsplit('_v', 1)[1] if '_v' in model_id else '1'
    model_filename = f"{base_name}_v{version}_model.py"
    model_file_path = f"dcisionai_workflow/models/{model_filename}"
    
    # Get project root (go up from dcisionai_mcp_server/api to project root)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent
    full_model_path = project_root / model_file_path
    
    # Ensure models directory exists
    full_model_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create model class wrapper
    class_name = "".join(word.capitalize() for word in model_id.rsplit('_v', 1)[0].split('_'))
    
    # Clean up model code - extract Python code if it's in markdown
    cleaned_code = model_code
    if "```python" in cleaned_code:
        start = cleaned_code.find("```python") + 9
        end = cleaned_code.find("```", start)
        if end > start:
            cleaned_code = cleaned_code[start:end].strip()
    elif "```" in cleaned_code:
        start = cleaned_code.find("```") + 3
        end = cleaned_code.find("```", start)
        if end > start:
            cleaned_code = cleaned_code[start:end].strip()
    
    # Store cleaned code as a class variable for retrieval
    # We'll embed it in the class definition
    model_code_repr = repr(cleaned_code)
    
    # Strip leading indentation from all lines to ensure code can be executed directly
    # This prevents IndentationError when exec() is called
    lines = cleaned_code.split("\n")
    if lines:
        # Find minimum indentation (excluding empty lines)
        min_indent = min(
            len(line) - len(line.lstrip())
            for line in lines
            if line.strip()  # Only consider non-empty lines
        ) if any(line.strip() for line in lines) else 0
        
        # Strip minimum indentation from all lines
        unindented_lines = [
            line[min_indent:] if len(line) > min_indent else line
            for line in lines
        ]
        unindented_code = "\n".join(unindented_lines)
    else:
        unindented_code = cleaned_code
    
    # Store indented version (for display in template if needed)
    indented_code = "\n".join("        " + line if line.strip() else line for line in unindented_code.split("\n"))
    
    # Use base64 encoding to safely embed code without quote issues
    # This avoids all problems with quotes, triple quotes, and special characters
    import base64
    encoded_code = base64.b64encode(unindented_code.encode('utf-8')).decode('utf-8')
    
    # Wrap model code in a class using .format() to avoid f-string brace issues
    model_class_template = '''"""
{description}

Deployed from job: {job_id}
Domain: {domain}
"""

import pyomo.environ as pyo
from typing import Dict, Any, Optional


class {class_name}:
    """
    {description}
    
    This model was deployed from job {job_id}.
    """
    
    def __init__(self, solver: str = "scip", **kwargs):
        """
        Initialize the model.
        
        Args:
            solver: Solver to use (default: scip)
            **kwargs: Additional model parameters (stored for use in build_model)
        """
        self.solver = solver
        self.model = None
        self.kwargs = kwargs
        self.is_ortools_model = False
        self.model_code_str = None
        self._cached_create_model = None  # Cache create_model function to avoid re-executing code
    
    def get_model_code(self) -> str:
        """
        Get the raw model code (Pyomo or OR-Tools).
        
        Returns:
            The original model code string (unindented, ready for execution)
        """
        if self.model_code_str is None:
            # Decode base64-encoded code to get original code string
            import base64
            encoded_str = {encoded_code}
            try:
                # Try to decode base64 string (new format)
                raw_code = base64.b64decode(encoded_str.encode('utf-8')).decode('utf-8')
            except Exception:
                # Fallback: if decoding fails, encoded_str might already be the code (old format)
                # This should not happen with new deployments, but handles edge cases
                raw_code = encoded_str
            # Strip leading indentation to ensure code can be executed directly
            # This handles cases where code might have been stored with indentation
            # Use chr(10) instead of \\n to avoid template formatting issues
            lines = raw_code.split(chr(10))
            if lines:
                # Find minimum indentation (excluding empty lines)
                non_empty_lines = [line for line in lines if line.strip()]
                if non_empty_lines:
                    min_indent = min(len(line) - len(line.lstrip()) for line in non_empty_lines)
                    # Strip minimum indentation from all lines
                    # Use chr(10) instead of \\n to avoid template formatting issues
                    self.model_code_str = chr(10).join(
                        line[min_indent:] if len(line) > min_indent else line
                        for line in lines
                    )
                else:
                    self.model_code_str = raw_code
            else:
                self.model_code_str = raw_code
        return self.model_code_str
    
    def solve(self, data: Optional[Dict[str, Any]] = None, verbose: bool = False, time_limit: int = 60) -> Dict[str, Any]:
        """
        Solve the optimization model directly with data.
        
        For deployed models, this combines model building and solving in one step.
        The model code is executed with the provided data, then solved.
        
        Args:
            data: Input data dictionary for model parameters (required)
            verbose: Print solver output
            time_limit: Time limit in seconds
            
        Returns:
            Dictionary with solution status and results
        """
        if data is None:
            data = dict()
        
        # Import pyomo - use a different name to avoid local variable shadowing
        import pyomo.environ as _pyomo_module
        
        # Execute the original model code with data
        # Make all Pyomo classes available directly (for code that uses "from pyomo.environ import *")
        # Also provide pyo module for code that uses "import pyomo.environ as pyo"
        exec_globals = dict(
            pyo=_pyomo_module,
            data=data,
            # Import all common Pyomo classes directly
            ConcreteModel=_pyomo_module.ConcreteModel,
            AbstractModel=_pyomo_module.AbstractModel,
            Var=_pyomo_module.Var,
            Param=_pyomo_module.Param,
            Constraint=_pyomo_module.Constraint,
            Objective=_pyomo_module.Objective,
            Set=_pyomo_module.Set,
            RangeSet=_pyomo_module.RangeSet,
            Binary=_pyomo_module.Binary,
            NonNegativeReals=_pyomo_module.NonNegativeReals,
            NonNegativeIntegers=_pyomo_module.NonNegativeIntegers,
            Reals=_pyomo_module.Reals,
            Integers=_pyomo_module.Integers,
            SolverFactory=_pyomo_module.SolverFactory,
            value=_pyomo_module.value,
            # Objective sense constants
            minimize=_pyomo_module.minimize,
            maximize=_pyomo_module.maximize,
            # Also import common functions
            sum=sum,
            min=min,
            max=max,
            range=range,
            len=len,
            dict=dict,
            list=list,
            tuple=tuple,
            str=str,
            int=int,
            float=float,
            bool=bool,
        )
        exec_globals.update(self.kwargs)
        
        # Check if we've already cached the create_model function (avoid re-executing code)
        if self._cached_create_model is None:
            # Execute the model code ONCE to extract create_model function
            model_code_to_execute = self.get_model_code()
            exec_locals = dict()
            exec(
                model_code_to_execute,
                exec_globals,
                exec_locals
            )
            
            # Cache create_model function if it exists
            if 'create_model' in exec_locals:
                self._cached_create_model = exec_locals['create_model']
            elif 'model' in exec_locals:
                # Model was created directly (not via function) - wrap it
                direct_model = exec_locals['model']
                self._cached_create_model = lambda d: direct_model
        
        # Extract model using cached function or execute code
        if self._cached_create_model is not None:
            # Use cached create_model function - much faster! No re-execution needed.
            model = self._cached_create_model(data if data is not None else dict())
            if model is None:
                raise RuntimeError("create_model() did not return a model")
            is_ortools_model = False
        else:
            # Fallback: execute code again (shouldn't happen if caching works)
            model_code_to_execute = self.get_model_code()
            exec_locals = dict()
            exec(
                model_code_to_execute,
                exec_globals,
                exec_locals
            )
            
            if 'model' in exec_locals:
                model = exec_locals['model']
                is_ortools_model = False
            elif 'create_model' in exec_locals:
                create_model_func = exec_locals['create_model']
                model = create_model_func(data if data is not None else dict())
                if model is None:
                    raise RuntimeError("create_model() did not return a model")
                is_ortools_model = False
        else:
            # Check if code uses OR-Tools (ortools imports)
            model_code_str = self.get_model_code()
            if 'ortools' in model_code_str.lower() or 'from ortools' in model_code_str or 'main' in exec_locals:
                # OR-Tools model - execute main function directly
                is_ortools_model = True
                if 'main' in exec_locals:
                    result = exec_locals['main']()
                    if isinstance(result, dict):
                        return dict(
                            status=result.get('status', 'optimal').lower(),
                            objective_value=result.get('objective_value'),
                            solution=result.get('routes') or result.get('solution', dict()),
                            solve_time=result.get('solve_time', 0),
                            solver_used="ortools"
                        )
                    else:
                        return dict(
                            status="error",
                            message="OR-Tools main() did not return a dict",
                            solve_time=0,
                            solver_used="ortools"
                        )
                else:
                    return dict(
                        status="error",
                        message="OR-Tools model did not define main() function",
                        solve_time=0,
                        solver_used="ortools"
                    )
            else:
                raise RuntimeError("Model code did not create a 'model' variable, 'create_model' function, or OR-Tools 'main' function")
        
        # Pyomo model execution
        if is_ortools_model:
            # Already handled above - should not reach here
            return dict(
                status="error",
                message="OR-Tools execution path error",
                solve_time=0,
                solver_used="ortools"
            )
        else:
            # Pyomo model execution
            solver = pyo.SolverFactory(self.solver)
            if not solver.available():
                # Use .format() instead of f-string to avoid self reference issues
                # Escape braces to prevent outer template formatting from interpreting them
                raise RuntimeError("Solver {{solver_name}} not available".format(solver_name=self.solver))
            
            solver.options['time_limit'] = time_limit
            
            result = solver.solve(model, tee=verbose)
            
            status = str(result.solver.status)
            termination_condition = str(result.solver.termination_condition)
            
            if status == "ok" and termination_condition in ["optimal", "feasible"]:
                # Use dict() constructor to avoid f-string parsing issues with curly braces
                return dict(
                    status="optimal" if termination_condition == "optimal" else "feasible",
                    objective_value=pyo.value(model.objective) if hasattr(model, 'objective') else None,
                    solution=dict(),
                    solve_time=result.solver.time if hasattr(result.solver, 'time') else 0,
                    solver_used=self.solver
                )
            else:
                # Use .format() instead of f-string to avoid self reference issues
                # Escape braces to prevent outer template formatting from interpreting them
                error_msg = "Solver status: {{status}}, termination: {{termination_condition}}".format(
                    status=status, termination_condition=termination_condition
                )
                return dict(
                    status="error",
                    message=error_msg,
                    solve_time=result.solver.time if hasattr(result.solver, 'time') else 0,
                    solver_used=self.solver
                )
'''
    
    # Format the template with actual values
    model_class_code = model_class_template.format(
        description=request.description,
        job_id=job_id,
        domain=request.domain,
        class_name=class_name,
        encoded_code=repr(encoded_code)  # repr() to safely embed base64 string in Python code
    )
    
    # Write model file to filesystem (for fast loading, but DB is source of truth)
    # If this fails, we can still use DB-stored model_code to reconstruct later
    try:
        with open(full_model_path, 'w') as f:
            f.write(model_class_code)
        logger.info(f"✅ Model file written: {full_model_path}")
    except Exception as e:
        logger.warning(f"⚠️ Failed to write model file to filesystem: {e}")
        logger.info("⚠️ Model code is stored in DB, file can be reconstructed later if needed")
        # Don't fail deployment - DB storage is sufficient
    
    # Extract problem signature and optimization plan for simulation
    problem_signature = None
    optimization_plan = None
    try:
        # Extract problem signature from workflow state
        classification = workflow_state.get("classification", {})
        classification_result = classification.get("result") if isinstance(classification, dict) else classification
        entities = workflow_state.get("entities", {})
        entities_result = entities.get("result") if isinstance(entities, dict) else entities
        constraints = workflow_state.get("constraints", [])
        objectives = workflow_state.get("objectives", [])
        
        problem_signature = {
            "problem_type": classification_result.get("problem_type", "") if isinstance(classification_result, dict) else "",
            "entity_structure": {
                "decision_variables": entities_result.get("decision_variables", []) if isinstance(entities_result, dict) else [],
                "parameters": entities_result.get("parameters", []) if isinstance(entities_result, dict) else [],
                "indices": entities_result.get("indices", {}) if isinstance(entities_result, dict) else {}
            },
            "constraint_patterns": [c.get("type") or c.get("constraint_type", "") for c in constraints if isinstance(c, dict)],
            "objective_structure": {
                "count": len(objectives),
                "types": [obj.get("direction", "") for obj in objectives if isinstance(obj, dict)]
            },
            "domain_context": classification_result.get("domain", "") if isinstance(classification_result, dict) else workflow_state.get("domain_context", "")
        }
        
        # Build optimization plan
        optimization_plan = {
            "problem_description": result.get("user_query") or workflow_state.get("problem_description", ""),
            "problem_type": problem_signature.get("problem_type", ""),
            "entities": entities_result if isinstance(entities_result, dict) else {},
            "constraints": constraints,
            "objectives": objectives
        }
        
        logger.info(f"✅ Extracted problem signature and optimization plan for simulation")
    except Exception as e:
        logger.warning(f"⚠️ Failed to extract problem signature/optimization plan: {e}", exc_info=True)
    
    # Get tenant_id from middleware
    tenant_id = tenant_info.get('tenant_id', 'default')
    
    # Register model in registry with metadata and default data
    try:
        from dcisionai_workflow.models.model_registry import register_model
        register_model(
            model_id=model_id,
            file_path=model_file_path,
            class_name=class_name,
            module_name=model_filename.replace('.py', ''),
            name=request.name,
            description=request.description,
            domain=request.domain,
            default_data=default_data,
            problem_signature=problem_signature,
            optimization_plan=optimization_plan,
            solver_result=solver_result,
            source_job_id=job_id
        )
        logger.info(f"✅ Model registered: {model_id} (with metadata and default data)")
    except Exception as e:
        logger.error(f"❌ Failed to register model in registry: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to register model: {str(e)}")
    
    # Persist to Supabase
    try:
        base_name = model_id.rsplit('_v', 1)[0] if '_v' in model_id else model_id
        version = int(model_id.rsplit('_v', 1)[1]) if '_v' in model_id else 1
        
        # Generate relaxed model class code if relaxed versions exist
        model_class_code_relaxed = None
        model_class_code_relaxed_v2 = None
        
        if model_code_relaxed:
            # Generate relaxed model class (same template, different code)
            model_class_code_relaxed = model_class_template.format(
                description=request.description,
                job_id=job_id,
                domain=request.domain,
                class_name=f"{class_name}Relaxed",
                encoded_code=base64.b64encode(model_code_relaxed.encode('utf-8')).decode('utf-8'),
                solver_name="{solver_name}",
                status="{status}",
                termination_condition="{termination_condition}"
            )
            logger.info(f"✅ Generated relaxed model class code: {len(model_class_code_relaxed)} chars")
        
        if model_code_relaxed_v2:
            # Generate relaxed v2 model class
            model_class_code_relaxed_v2 = model_class_template.format(
                description=request.description,
                job_id=job_id,
                domain=request.domain,
                class_name=f"{class_name}RelaxedV2",
                encoded_code=base64.b64encode(model_code_relaxed_v2.encode('utf-8')).decode('utf-8'),
                solver_name="{solver_name}",
                status="{status}",
                termination_condition="{termination_condition}"
            )
            logger.info(f"✅ Generated relaxed v2 model class code: {len(model_class_code_relaxed_v2)} chars")
        
        deployed_model_data = {
            'model_id': model_id,
            'tenant_id': tenant_id,
            'name': request.name,
            'description': request.description,
            'domain': request.domain,
            'version': version,
            'base_name': base_name,
            'file_path': model_file_path,
            'model_code': model_class_code,  # Store original model code in DB
            'model_code_relaxed': model_class_code_relaxed,  # Store relaxed model code
            'model_code_relaxed_v2': model_class_code_relaxed_v2,  # Store relaxed v2 model code
            'class_name': class_name,
            'module_name': model_filename.replace('.py', ''),
            'default_data': default_data or {},
            'problem_signature': problem_signature,
            'optimization_plan': optimization_plan,
            'solver_result': solver_result,
            'source_job_id': job_id,
            'variables': 0,  # Can be extracted from entities if needed
            'constraints': len(optimization_plan.get('constraints', [])) if optimization_plan else 0,
            'avg_solve_time': 0.0,
            'solver': 'scip',
            'problem_type': problem_signature.get('problem_type', 'linear_programming') if problem_signature else 'linear_programming',
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Upsert to Supabase (insert or update if exists)
        # Check if table exists first
        try:
            # Try to query the table to see if it exists
            test_query = supabase_client.table("deployed_models").select("model_id").limit(1).execute()
            table_exists = True
        except Exception as table_check_error:
            # Table might not exist - log warning but don't fail
            logger.warning(f"⚠️ deployed_models table may not exist: {table_check_error}. Run migration: scripts/run_deployed_models_migration.py")
            table_exists = False
        
        if table_exists:
            try:
                # Set tenant context for RLS before inserting
                # RLS policies require app.current_tenant_id to be set
                try:
                    # Try using the RPC function if it exists
                    supabase_client.rpc('set_tenant_context', {'tenant_id_value': tenant_id}).execute()
                    logger.info(f"✅ Set tenant context for insert: {tenant_id}")
                except Exception as rpc_error:
                    # Fallback: Try setting via raw SQL if RPC doesn't work
                    logger.warning(f"⚠️ RPC set_tenant_context failed: {rpc_error}, trying direct SQL")
                    try:
                        # Use raw SQL to set session variable via Supabase connection
                        import psycopg2
                        from urllib.parse import urlparse
                        db_url = os.getenv('SUPABASE_DB_URL')
                        if db_url:
                            conn = psycopg2.connect(db_url)
                            cur = conn.cursor()
                            cur.execute("SELECT set_config('app.current_tenant_id', %s, false)", (tenant_id,))
                            conn.commit()
                            cur.close()
                            conn.close()
                            logger.info(f"✅ Set tenant context via SQL: {tenant_id}")
                    except Exception as sql_error:
                        logger.warning(f"⚠️ SQL set_tenant_context also failed: {sql_error}")
                        # Continue anyway - explicit tenant_id in WHERE clause might work
                
                # Now insert/update with explicit tenant_id (RLS should allow it)
                supabase_response = supabase_client.table("deployed_models").upsert(
                    deployed_model_data,
                    on_conflict="model_id"
                ).execute()
                
                logger.info(f"✅ Model persisted to Supabase: {model_id} (tenant: {tenant_id})")
                logger.info(f"✅ Upsert response: {len(supabase_response.data) if supabase_response.data else 0} rows affected")
                
                # Verify the model was actually saved by querying it back
                try:
                    verify_response = supabase_client.table("deployed_models").select("model_id").eq("model_id", model_id).execute()
                    if verify_response.data:
                        logger.info(f"✅ Verified model exists in database: {model_id}")
                    else:
                        logger.warning(f"⚠️ Model upserted but not found on verification query (RLS may be blocking)")
                except Exception as verify_error:
                    logger.warning(f"⚠️ Could not verify model persistence: {verify_error}")
            except Exception as upsert_error:
                logger.error(f"⚠️ Failed to upsert model to Supabase: {upsert_error}", exc_info=True)
                # Don't fail the deployment if Supabase persistence fails - model is already registered locally
        else:
            logger.warning(f"⚠️ Skipping Supabase persistence - table does not exist. Model registered locally only.")
    except Exception as e:
        logger.error(f"⚠️ Failed to persist model to Supabase: {e}", exc_info=True)
        # Don't fail the deployment if Supabase persistence fails - model is already registered locally
        # But log the error for debugging
    
    # Get version info from Supabase (since we're only using DB now)
    all_versions = [model_id]  # Default to current model
    try:
        if supabase_client and table_exists:
            versions_response = supabase_client.table("deployed_models").select("model_id").eq("base_name", base_name).order("version", desc=False).execute()
            if versions_response.data:
                all_versions = [v.get('model_id') for v in versions_response.data]
    except Exception as e:
        logger.warning(f"Failed to get model versions from Supabase: {e}")
        all_versions = [model_id]  # Fallback to current model only
    
    # Generate HTTP endpoint URL
    # Get base URL from request
    base_url = str(http_request.base_url).rstrip('/')
    endpoint_url = f"{base_url}/api/models/{model_id}/solve"
    
    # Reload dynamic model tools to include the newly deployed model
    try:
        from dcisionai_mcp_server.tools.registry import reload_dynamic_model_tools, initialize_dynamic_model_tools
        reload_dynamic_model_tools()
        # Re-initialize to include the new model
        await initialize_dynamic_model_tools()
        logger.info(f"✅ Dynamic tools reloaded after deploying {model_id}")
    except Exception as tool_reload_error:
        logger.warning(f"⚠️ Failed to reload dynamic tools after deployment: {tool_reload_error}")
        # Don't fail deployment if tool reload fails
    
    return DeployModelResponse(
        status="success",
        model_id=model_id,
        message=f"Model '{request.name}' deployed successfully as {model_id} (version {version} of {len(all_versions)} total versions)",
        file_path=model_file_path,
        endpoint_url=endpoint_url,
        version=str(version),  # Convert to string for Pydantic validation
        all_versions=all_versions
    )


@router.post("/models/{model_id}/solve")
async def solve_with_deployed_model(
    model_id: str,
    request: Request,
    tenant_info: dict = Depends(verify_api_key_optional)
):
    """
    Execute a deployed model with provided data.
    
    This is the HTTP endpoint for integrating deployed models into external tools.
    Customers can call this endpoint directly from their applications.
    
    **Request Body:**
    ```json
    {
        "data": {
            "parameters": {...},
            "indices": {...}
        },
        "options": {
            "solver": "scip",
            "time_limit": 60,
            "verbose": false
        }
    }
    ```
    
    **Response:**
    ```json
    {
        "status": "success",
        "model_id": "portfolio_optimization_v1",
        "result": {
            "status": "optimal",
            "objective_value": 12345.67,
            "solution": {...},
            "solve_time": 2.5
        }
    }
    ```
    """
    import json
    
    try:
        # Parse request body
        body = await request.json()
        data = body.get("data", {})
        options = body.get("options", {})
        
        logger.info(f"🔧 Executing deployed model {model_id} via HTTP endpoint")
        logger.info(f"   Data keys: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")
        
        # Import model registry
        from dcisionai_workflow.models.model_registry import run_deployed_model, MODEL_REGISTRY
        
        # Validate model exists
        if model_id not in MODEL_REGISTRY:
            raise HTTPException(
                status_code=404,
                detail=f"Model '{model_id}' not found. Available models: {list(MODEL_REGISTRY.keys())[:10]}"
            )
        
        # Execute model
        result = await run_deployed_model(model_id, data, options)
        
        # Format response
        return {
            "status": "success",
            "model_id": model_id,
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to execute model {model_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute model: {str(e)}"
        )


@router.get("/models/{model_id}/csv-template")
async def download_model_csv_template(model_id: str):
    """
    Download CSV template for a deployed model.
    
    Returns a CSV file showing the required data format with example values
    from the successful job run that created the model.
    
    Args:
        model_id: Model identifier (e.g., 'pharma_v1')
        
    Returns:
        CSV file download
    """
    try:
        from dcisionai_workflow.models.csv_template_generator import generate_csv_template_from_model_id
        
        csv_content = generate_csv_template_from_model_id(model_id)
        
        if not csv_content:
            raise HTTPException(
                status_code=404,
                detail=f"Model {model_id} not found or CSV template generation failed"
            )
        
        # Get model name for filename
        from dcisionai_workflow.models.model_registry import MODEL_METADATA
        metadata = MODEL_METADATA.get(model_id, {})
        model_name = metadata.get('name', model_id).replace(' ', '_').lower()
        
        filename = f"{model_name}_data_template.csv"
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate CSV template for {model_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate CSV template: {str(e)}"
        )


@router.post("/{job_id}/cancel", response_model=JobCancelResponse)
async def cancel_optimization_job(job_id: str):
    """
    Cancel a running or queued job.

    This endpoint terminates the Celery task and updates the job status to cancelled.
    Only jobs in `queued` or `running` status can be cancelled.

    **Response:**
    ```json
    {
        "job_id": "550e8400-e29b-41d4-a716-446655440000",
        "status": "cancelled",
        "cancelled_at": "2025-12-08T12:02:30Z",
        "message": "Job cancelled successfully"
    }
    ```
    """
    logger.info(f"Cancelling job: {job_id}")

    # Get job from storage
    job_record = get_job(job_id)
    if not job_record:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    # Check if job can be cancelled
    if job_record["status"] not in [JobStatus.QUEUED.value, JobStatus.RUNNING.value]:
        raise HTTPException(
            status_code=409,
            detail=f"Job cannot be cancelled (status: {job_record['status']}). Only queued/running jobs can be cancelled."
        )

    # Revoke Celery task immediately
    try:
        from dcisionai_mcp_server.jobs.tasks import celery_app
        celery_app.control.revoke(job_id, terminate=False)
        logger.info(f"Revoked Celery task: {job_id}")
    except Exception as e:
        logger.warning(f"Failed to revoke Celery task (may not exist): {e}")

    # Update job status in database immediately
    try:
        from dcisionai_mcp_server.jobs.storage import update_job_status
        update_job_status(
            job_id=job_id,
            status=JobStatus.CANCELLED
        )
        logger.info(f"Job status updated to cancelled: {job_id}")
    except Exception as e:
        logger.error(f"Failed to update job status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel job: {str(e)}")

    # CRITICAL FIX: Signal metrics completion so metrics aggregator doesn't block
    try:
        from dcisionai_workflow.shared.utils.metrics_publisher import publish_job_metrics_complete
        session_id = job_record.get("session_id", "unknown")
        publish_job_metrics_complete(job_id, session_id)
        logger.debug(f"✅ Published metrics completion signal for cancelled job {job_id}")
    except Exception as metrics_signal_error:
        logger.warning(f"⚠️ Failed to publish metrics completion signal for cancelled job: {metrics_signal_error}")

    # Also dispatch cancel task for cleanup (non-blocking)
    try:
        cancel_job.apply_async(args=(job_id,))
        logger.info(f"Cancel cleanup task dispatched: {job_id}")
    except Exception as e:
        logger.warning(f"Failed to dispatch cancel cleanup task: {e}")

    return JobCancelResponse(
        job_id=job_id,
        status=JobStatus.CANCELLED.value,
        cancelled_at=datetime.now(timezone.utc).isoformat(),
        message="Job cancelled successfully",
    )


@router.get("/workers/status")
async def get_worker_status():
    """
    Get Celery worker status for debugging.
    
    Returns information about active Celery workers and their status.
    """
    logger.info("Getting Celery worker status")
    
    try:
        from dcisionai_mcp_server.jobs.tasks import celery_app, get_active_jobs
        
        inspect = celery_app.control.inspect()
        
        # Get worker information
        active_workers = inspect.active() or {}
        registered_workers = inspect.registered() or {}
        scheduled_tasks = inspect.scheduled() or {}
        reserved_tasks = inspect.reserved() or {}
        
        # Get active jobs from our helper
        active_jobs_info = get_active_jobs()
        
        return {
            "workers": {
                "active_count": len(active_workers),
                "registered_count": len(registered_workers),
                "active_worker_names": list(active_workers.keys()),
                "registered_worker_names": list(registered_workers.keys()),
            },
            "tasks": {
                "active": {worker: len(tasks) for worker, tasks in active_workers.items()},
                "scheduled": {worker: len(tasks) for worker, tasks in scheduled_tasks.items()},
                "reserved": {worker: len(tasks) for worker, tasks in reserved_tasks.items()},
            },
            "active_jobs": active_jobs_info,
        }
    except Exception as e:
        logger.error(f"Failed to get worker status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get worker status: {str(e)}")


@router.get("/statistics")
async def get_statistics():
    """
    Get job queue statistics.

    Returns aggregated statistics about jobs across all statuses.

    **Response:**
    ```json
    {
        "total_jobs": 145,
        "by_status": {
            "queued": 5,
            "running": 3,
            "completed": 120,
            "failed": 15,
            "cancelled": 2
        },
        "avg_completion_time_seconds": 285.5
    }
    ```
    """
    logger.info("Getting job statistics")

    try:
        stats = get_job_statistics()
        return stats
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


# ========== MCP RESOURCE ENDPOINTS ==========

@router.get("/{job_id}/resources")
async def get_job_mcp_resources(job_id: str):
    """
    List all available MCP resources for a job.

    Returns a list of MCP resource URIs (`job://job_id/resource_type`) that
    can be used to access job artifacts.

    **Response:**
    ```json
    {
        "job_id": "550e8400-e29b-41d4-a716-446655440000",
        "status": "completed",
        "resources": {
            "status": "job://550e8400-e29b-41d4-a716-446655440000/status",
            "progress": "job://550e8400-e29b-41d4-a716-446655440000/progress",
            "result": "job://550e8400-e29b-41d4-a716-446655440000/result",
            "intent": "job://550e8400-e29b-41d4-a716-446655440000/intent",
            "data": "job://550e8400-e29b-41d4-a716-446655440000/data",
            "solver": "job://550e8400-e29b-41d4-a716-446655440000/solver",
            "explanation": "job://550e8400-e29b-41d4-a716-446655440000/explanation"
        }
    }
    ```
    """
    logger.info(f"Getting MCP resources for job: {job_id}")

    try:
        resources = list_job_resources(job_id)
        return resources
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get resources: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get resources: {str(e)}")


if __name__ == "__main__":
    # For testing the router independently
    import uvicorn
    from fastapi import FastAPI

    app = FastAPI(title="DcisionAI Job Queue API")
    app.include_router(router)

    logger.info("Starting job API test server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
