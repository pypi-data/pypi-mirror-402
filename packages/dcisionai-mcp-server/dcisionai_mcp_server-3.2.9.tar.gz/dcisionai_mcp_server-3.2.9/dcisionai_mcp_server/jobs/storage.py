"""
Job Storage Layer with Supabase Database and Redis Cache

Following MCP Protocol:
- Jobs stored in Supabase for persistence
- Jobs cached in Redis for fast access (24h TTL)
- Job results exposed as MCP resources (job://job_id/*)
- HATEOAS links for REST API navigation

Following LangGraph Patterns:
- JobState persisted as JSON (TypedDict serialization)
- Checkpoint support for resumable workflows
- Progress updates persisted for recovery
"""

import os
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from pathlib import Path

from supabase import create_client, Client

from dcisionai_mcp_server.jobs.schemas import (
    JobState,
    JobMetadata,
    JobInput,
    JobProgress,
    JobResult,
    JobStatus,
    JobPriority,
    JobRecord,
)

logger = logging.getLogger(__name__)

# ========== DATABASE CONFIGURATION ==========

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")

# Redis configuration
# Railway provides both REDIS_URL (internal) and REDIS_PUBLIC_URL (external)
# Use REDIS_PUBLIC_URL if available (for external access), otherwise fall back to REDIS_URL
# Note: On Railway, services in the same project can use REDIS_URL (internal)
#       For external access or cross-service access, use REDIS_PUBLIC_URL
REDIS_URL = os.getenv("REDIS_PUBLIC_URL") or os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_TTL_SECONDS = 24 * 60 * 60  # 24 hours

# Initialize Supabase client
supabase_client: Optional[Client] = None
try:
    if SUPABASE_URL and SUPABASE_API_KEY:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_API_KEY)
        logger.info(f"✅ Supabase client initialized: {SUPABASE_URL}")
    else:
        logger.warning("⚠️ Supabase credentials not found. Set SUPABASE_URL and SUPABASE_API_KEY environment variables.")
except Exception as e:
    logger.error(f"❌ Supabase client initialization failed: {e}")
    supabase_client = None

# Initialize Redis client
try:
    import redis
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    # Test connection
    redis_client.ping()
    logger.info(f"✅ Redis cache initialized: {REDIS_URL[:50]}...")
except Exception as e:
    logger.warning(f"⚠️ Redis cache initialization failed: {e}. Using database only.")
    logger.warning(f"   REDIS_URL: {REDIS_URL[:50] if REDIS_URL else 'Not set'}...")
    logger.warning(f"   REDIS_PUBLIC_URL: {'Set' if os.getenv('REDIS_PUBLIC_URL') else 'Not set'}")
    redis_client = None


# ========== DATABASE INITIALIZATION ==========

def init_database() -> None:
    """
    Verify Supabase tables exist.

    Tables should be created via Supabase Dashboard or setup script:
    - async_jobs: Main job records with metadata and state
    - async_job_checkpoints: LangGraph checkpoints for resumable workflows
    """
    if not supabase_client:
        logger.warning("⚠️ Supabase client not initialized. Skipping table verification.")
        return

    try:
        # Verify async_jobs table exists by attempting a simple query
        supabase_client.table("async_jobs").select("job_id").limit(1).execute()
        logger.info("✅ Supabase table 'async_jobs' verified")
    except Exception as e:
        logger.error(f"❌ Supabase table 'async_jobs' not found: {e}")
        logger.error("Please create tables using docs/implementation/SUPABASE_ASYNC_JOBS_SETUP.md")
        raise

    try:
        # Verify async_job_checkpoints table exists
        supabase_client.table("async_job_checkpoints").select("checkpoint_id").limit(1).execute()
        logger.info("✅ Supabase table 'async_job_checkpoints' verified")
    except Exception as e:
        logger.error(f"❌ Supabase table 'async_job_checkpoints' not found: {e}")
        logger.error("Please create tables using docs/implementation/SUPABASE_ASYNC_JOBS_SETUP.md")
        raise


# Initialize database on module import
init_database()


# ========== REDIS CACHE LAYER ==========

def cache_get(key: str) -> Optional[Dict[str, Any]]:
    """Get job from Redis cache"""
    if not redis_client:
        return None

    try:
        cached = redis_client.get(key)
        if cached:
            logger.debug(f"Cache HIT: {key}")
            return json.loads(cached)
        logger.debug(f"Cache MISS: {key}")
        return None
    except Exception as e:
        logger.error(f"Cache get error for {key}: {e}")
        return None


def cache_set(key: str, value: Dict[str, Any], ttl: int = REDIS_TTL_SECONDS) -> None:
    """
    Store job in Redis cache with TTL.
    
    Non-blocking: If Redis is unavailable, logs warning but doesn't raise exception.
    This ensures job creation/updates succeed even if Redis cache is down.
    """
    if not redis_client:
        return

    try:
        redis_client.setex(key, ttl, json.dumps(value))
        logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
    except Exception as e:
        logger.error(f"Cache set error for {key}: {e}")


def cache_delete(key: str) -> None:
    """Remove job from Redis cache"""
    if not redis_client:
        return

    try:
        redis_client.delete(key)
        logger.debug(f"Cache DELETE: {key}")
    except Exception as e:
        logger.error(f"Cache delete error for {key}: {e}")


def cache_key(job_id: str) -> str:
    """Generate cache key for job"""
    return f"job:{job_id}"


# ========== JOB CRUD OPERATIONS ==========

def create_job_record(
    job_id: str,
    session_id: str,
    user_query: str,
    priority: JobPriority = JobPriority.NORMAL,
    use_case: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None,
) -> JobRecord:
    """
    Create a new job record in database.

    Args:
        job_id: Unique job identifier (same as Celery task ID)
        session_id: Session identifier for context
        user_query: Natural language query from user
        priority: Job priority (low, normal, high, urgent)
        use_case: Optional use case hint
        parameters: Optional additional parameters

    Returns:
        JobRecord TypedDict with initial state
    """
    logger.info(f"Creating job record: {job_id}")

    # Create job record
    job_data = {
        "job_id": job_id,
        "session_id": session_id,
        "status": JobStatus.QUEUED.value,
        "priority": priority.value,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "started_at": None,
        "completed_at": None,
        "user_query": user_query,
        "use_case": use_case,
        "parameters": parameters,  # Supabase stores as JSONB
        "progress": None,
        "result": None,
        "error": None,
        "checkpoint_id": None,
    }

    # Insert into Supabase
    if supabase_client:
        try:
            supabase_client.table("async_jobs").insert(job_data).execute()
        except Exception as e:
            logger.error(f"❌ Failed to insert job into Supabase: {e}")
            raise

    # Convert to JobRecord format (parameters as JSON string for compatibility)
    job_record: JobRecord = {
        **job_data,
        "parameters": json.dumps(parameters) if parameters else None,
    }

    # Cache the job record
    cache_set(cache_key(job_id), job_record)

    logger.info(f"✅ Job record created: {job_id}")
    return job_record


def get_job(job_id: str) -> Optional[JobRecord]:
    """
    Get job record by ID.

    First checks Redis cache, then falls back to database.

    Args:
        job_id: Job identifier

    Returns:
        JobRecord if found, None otherwise
    """
    # Try cache first
    cached = cache_get(cache_key(job_id))
    if cached:
        return cached

    # Fall back to Supabase
    if not supabase_client:
        logger.error("Supabase client not initialized")
        return None

    try:
        response = supabase_client.table("async_jobs").select("*").eq("job_id", job_id).execute()

        if not response.data or len(response.data) == 0:
            logger.warning(f"Job not found: {job_id}")
            return None

        row = response.data[0]

        # Convert Supabase row to JobRecord
        job_record: JobRecord = {
            "job_id": row["job_id"],
            "session_id": row["session_id"],
            "status": row["status"],
            "priority": row["priority"],
            "created_at": row["created_at"],
            "started_at": row["started_at"],
            "completed_at": row["completed_at"],
            "user_query": row["user_query"],
            "use_case": row["use_case"],
            "parameters": json.dumps(row["parameters"]) if row["parameters"] else None,
            "progress": json.dumps(row["progress"]) if row["progress"] else None,
            "result": json.dumps(row["result"]) if row["result"] else None,
            "error": row["error"],
            "checkpoint_id": row["checkpoint_id"],
            "llm_metrics": row.get("llm_metrics"),  # Include llm_metrics if present (stored as JSONB)
        }

        # Cache for next time
        cache_set(cache_key(job_id), job_record)

        return job_record

    except Exception as e:
        logger.error(f"❌ Failed to get job from Supabase: {e}")
        return None


def delete_job(job_id: str) -> None:
    """
    Delete a job from the database and cache.

    Args:
        job_id: Unique job identifier
    """
    logger.info(f"Deleting job: {job_id}")

    if not supabase_client:
        logger.error("Supabase client not initialized")
        raise RuntimeError("Database not available")

    try:
        # Delete from Supabase
        supabase_client.table("async_jobs").delete().eq("job_id", job_id).execute()

        # Invalidate cache
        cache_delete(cache_key(job_id))

        logger.info(f"✅ Deleted job: {job_id}")
    except Exception as e:
        logger.error(f"❌ Failed to delete job {job_id}: {e}")
        raise


def update_job_status(
    job_id: str,
    status: JobStatus,
    started_at: Optional[str] = None,
    completed_at: Optional[str] = None,
    error: Optional[str] = None,
) -> None:
    """
    Update job status in database and cache.

    Args:
        job_id: Job identifier
        status: New status
        started_at: Optional start timestamp
        completed_at: Optional completion timestamp
        error: Optional error message
    """
    logger.info(f"Updating job {job_id} status: {status.value}")

    if not supabase_client:
        logger.error("Supabase client not initialized")
        return

    # Build update data
    update_data = {"status": status.value}

    if started_at:
        update_data["started_at"] = started_at

    if completed_at:
        update_data["completed_at"] = completed_at

    if error:
        update_data["error"] = error

    try:
        supabase_client.table("async_jobs").update(update_data).eq("job_id", job_id).execute()
    except Exception as e:
        logger.error(f"❌ Failed to update job status in Supabase: {e}")
        raise

    # Invalidate cache
    cache_delete(cache_key(job_id))

    logger.info(f"✅ Job status updated: {job_id} -> {status.value}")


def update_job_progress(job_id: str, progress: JobProgress) -> None:
    """
    Update job progress in database and cache.

    Args:
        job_id: Job identifier
        progress: JobProgress TypedDict with current step and percentage
    """
    logger.debug(f"Updating job {job_id} progress: {progress['current_step']} ({progress['progress_percentage']}%)")

    if not supabase_client:
        logger.error("Supabase client not initialized")
        return

    try:
        from datetime import datetime
        
        # Helper to serialize Pydantic models and datetime objects
        def serialize_for_db(obj):
            """Recursively serialize objects for database storage."""
            if hasattr(obj, 'model_dump'):  # Pydantic v2
                return serialize_for_db(obj.model_dump())
            elif hasattr(obj, 'dict'):  # Pydantic v1
                return serialize_for_db(obj.dict())
            elif isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: serialize_for_db(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [serialize_for_db(item) for item in obj]
            else:
                return obj
        
        # Serialize progress before storing (handles ReasoningTrail and datetime objects)
        serialized_progress = serialize_for_db(progress)
        
        supabase_client.table("async_jobs").update({"progress": serialized_progress}).eq("job_id", job_id).execute()
    except Exception as e:
        logger.error(f"❌ Failed to update job progress in Supabase: {e}")
        raise

    # Invalidate cache (progress updates frequently, so we don't cache)
    cache_delete(cache_key(job_id))


def upload_files_to_supabase_storage(
    job_id: str,
    file_contents: Dict[str, str],
    bucket_name: str = "solver-files"
) -> Dict[str, str]:
    """
    Upload files to Supabase Storage using hybrid strategy.
    
    Small files (<100KB) are stored in JSONB, large files are uploaded to Storage.
    
    Args:
        job_id: Job identifier (used as folder path)
        file_contents: Dict mapping filename to file content
        bucket_name: Supabase Storage bucket name (default: "solver-files")
    
    Returns:
        Dict mapping filename to storage URL (for large files) or None (for small files stored in JSONB)
    """
    if not supabase_client:
        logger.warning("Supabase client not initialized, skipping file upload")
        return {}
    
    LARGE_FILE_THRESHOLD = 100 * 1024  # 100KB
    file_urls = {}
    
    try:
        # Ensure bucket exists (create if needed)
        try:
            supabase_client.storage.from_(bucket_name).list()
        except Exception as e:
            logger.warning(f"Bucket {bucket_name} may not exist: {e}")
            logger.info(f"⚠️ Please create bucket '{bucket_name}' in Supabase Storage dashboard")
            return {}
        
        for filename, content in file_contents.items():
            content_size = len(content.encode('utf-8'))
            
            if content_size > LARGE_FILE_THRESHOLD:
                # Upload large files to Supabase Storage
                storage_path = f"{job_id}/{filename}"
                
                try:
                    # Upload file content
                    supabase_client.storage.from_(bucket_name).upload(
                        storage_path,
                        content.encode('utf-8'),
                        file_options={"content-type": "text/plain", "upsert": "true"}
                    )
                    
                    # Store storage path instead of public URL (bucket is private)
                    # Signed URLs will be generated on-demand when files are retrieved
                    file_urls[filename] = storage_path  # Store path, not URL
                    logger.info(f"✅ Uploaded {filename} to Supabase Storage ({content_size} bytes): {storage_path}")
                except Exception as e:
                    logger.error(f"❌ Failed to upload {filename} to Supabase Storage: {e}")
                    # Continue with other files
            else:
                # Small files will be stored in JSONB (no URL needed)
                logger.debug(f"📄 {filename} ({content_size} bytes) will be stored in JSONB")
        
        return file_urls
    
    except Exception as e:
        logger.error(f"❌ Failed to upload files to Supabase Storage: {e}")
        return {}


def save_job_result(job_id: str, result: JobResult) -> None:
    """
    Save job result to database and cache.
    
    Files are persisted using hybrid strategy:
    - Small files (<100KB): Stored in JSONB (file_contents)
    - Large files (>=100KB): Uploaded to Supabase Storage (file_urls)

    Args:
        job_id: Job identifier
        result: JobResult TypedDict with final workflow state and MCP resource URIs
    """
    logger.info(f"Saving job result: {job_id}")

    if not supabase_client:
        logger.error("Supabase client not initialized")
        return

    # Check if model_code exists in workflow_state for deployment support
    workflow_state = result.get("workflow_state", {})
    solver_result = workflow_state.get("solver_result", {})
    if isinstance(solver_result, dict):
        model_code = solver_result.get("model_code")
        if model_code:
            logger.info(f"✅ Model code present in result for job {job_id}: {len(model_code)} characters")
        else:
            logger.warning(f"⚠️ Model code NOT in solver_result for job {job_id}")
            logger.warning(f"⚠️ Solver result keys: {list(solver_result.keys())}")
            # Check work_dir
            work_dir = workflow_state.get("claude_agent_work_dir")
            if work_dir:
                logger.info(f"⚠️ Work dir available: {work_dir} - model may be in file")
        
        # Upload files to Supabase Storage if file_contents exist and not already uploaded
        # Note: Files may have already been uploaded in the solver node (_upload_files_to_supabase)
        # Only upload if file_urls is empty (indicating files weren't uploaded yet)
        file_contents = solver_result.get("file_contents", {})
        existing_file_urls = solver_result.get("file_urls", {})
        
        if file_contents and not existing_file_urls:
            # Files haven't been uploaded yet, upload them now
            logger.info(f"📤 Uploading {len(file_contents)} files to Supabase Storage...")
            file_urls = upload_files_to_supabase_storage(job_id, file_contents)
            
            # Update solver_result with file_urls
            solver_result["file_urls"] = file_urls
            workflow_state["solver_result"] = solver_result
            result["workflow_state"] = workflow_state
            
            logger.info(f"✅ Uploaded {len(file_urls)} large files to Supabase Storage")
        elif existing_file_urls:
            # Files were already uploaded in solver node
            logger.info(f"✅ Files already uploaded to Supabase Storage ({len(existing_file_urls)} files)")
        elif file_contents:
            # Files exist but are all small (<100KB), stored in JSONB
            logger.info(f"✅ {len(file_contents)} small files stored in JSONB (no Storage upload needed)")

    # Supabase stores JSONB, so we can pass dict directly
    # But ensure it's serializable
    update_data = {
        "result": result,  # Pass as dict - Supabase will handle JSONB conversion
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        supabase_client.table("async_jobs").update(update_data).eq("job_id", job_id).execute()
        logger.info(f"✅ Job result saved to database: {job_id}")
    except Exception as e:
        logger.error(f"❌ Failed to save job result in Supabase: {e}", exc_info=True)
        # Log result size to check if it's too large
        try:
            import json
            result_size = len(json.dumps(result, default=str))
            logger.error(f"Result size: {result_size} bytes")
            if result_size > 1000000:  # 1MB
                logger.warning(f"⚠️ Large result size ({result_size} bytes) - may be truncated by database")
            
            # Log structure to help debug
            workflow_state = result.get("workflow_state", {})
            logger.error(f"Workflow state keys: {list(workflow_state.keys())[:20]}")
            logger.error(f"Has solver_result: {'solver_result' in workflow_state}")
            logger.error(f"Has business_explanation: {'business_explanation' in workflow_state}")
            logger.error(f"Has decision_traces: {'decision_traces' in workflow_state}")
        except Exception as log_error:
            logger.error(f"Failed to log result details: {log_error}")
        raise

    # Invalidate cache
    cache_delete(cache_key(job_id))

    logger.info(f"✅ Job result saved: {job_id}")


def update_job_metrics(job_id: str, metrics: Dict[str, Any]) -> None:
    """
    Update LLM metrics for a job.

    Metrics are stored separately from the workflow result to prevent
    serialization issues. They can be retrieved independently.

    Args:
        job_id: Job identifier
        metrics: LLM metrics dictionary (LLMMetrics TypedDict)
    """
    logger.info(f"Updating LLM metrics for job: {job_id}")

    if not supabase_client:
        logger.error("Supabase client not initialized")
        return

    try:
        # Update job record with metrics
        # Store metrics as JSON in a separate field or in the result
        update_data = {
            "llm_metrics": json.dumps(metrics),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        supabase_client.table("async_jobs").update(update_data).eq("job_id", job_id).execute()

        # Invalidate cache
        cache_delete(cache_key(job_id))

        logger.info(f"✅ LLM metrics updated for job: {job_id}")
    except Exception as e:
        logger.error(f"❌ Failed to update LLM metrics in Supabase: {e}")
        raise


# ========== CHECKPOINT SUPPORT (LANGGRAPH RESUMABILITY) ==========

def save_checkpoint(job_id: str, checkpoint_id: str, checkpoint_data: Dict[str, Any]) -> None:
    """
    Save LangGraph checkpoint for resumable workflows.

    This allows workflows to be paused and resumed later.

    Args:
        job_id: Job identifier
        checkpoint_id: Unique checkpoint identifier
        checkpoint_data: LangGraph StateGraph checkpoint data
    """
    logger.info(f"Saving checkpoint {checkpoint_id} for job {job_id}")

    if not supabase_client:
        logger.error("Supabase client not initialized")
        return

    # Insert checkpoint
    checkpoint_record = {
        "checkpoint_id": checkpoint_id,
        "job_id": job_id,
        "checkpoint_data": checkpoint_data,  # Supabase stores as JSONB
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        supabase_client.table("async_job_checkpoints").insert(checkpoint_record).execute()

        # Update job record with latest checkpoint
        supabase_client.table("async_jobs").update({"checkpoint_id": checkpoint_id}).eq("job_id", job_id).execute()
    except Exception as e:
        logger.error(f"❌ Failed to save checkpoint in Supabase: {e}")
        raise

    logger.info(f"✅ Checkpoint saved: {checkpoint_id}")


def get_checkpoint(checkpoint_id: str) -> Optional[Dict[str, Any]]:
    """
    Get LangGraph checkpoint by ID.

    Args:
        checkpoint_id: Checkpoint identifier

    Returns:
        Checkpoint data if found, None otherwise
    """
    if not supabase_client:
        logger.error("Supabase client not initialized")
        return None

    try:
        response = supabase_client.table("async_job_checkpoints").select("*").eq("checkpoint_id", checkpoint_id).execute()

        if not response.data or len(response.data) == 0:
            logger.warning(f"Checkpoint not found: {checkpoint_id}")
            return None

        row = response.data[0]
        return row["checkpoint_data"]

    except Exception as e:
        logger.error(f"❌ Failed to get checkpoint from Supabase: {e}")
        return None


# ========== QUERY OPERATIONS ==========

def get_jobs_by_session(session_id: str, limit: int = 100, offset: int = 0) -> List[JobRecord]:
    """
    Get all jobs for a session.

    Args:
        session_id: Session identifier
        limit: Maximum number of jobs to return

    Returns:
        List of JobRecord Typedicts
    """
    if not supabase_client:
        logger.error("Supabase client not initialized")
        return []

    try:
        response = supabase_client.table("async_jobs").select("*").eq("session_id", session_id).order("created_at", desc=True).range(offset, offset + limit - 1).execute()

        return [
            {
                "job_id": row["job_id"],
                "session_id": row["session_id"],
                "status": row["status"],
                "priority": row["priority"],
                "created_at": row["created_at"],
                "started_at": row["started_at"],
                "completed_at": row["completed_at"],
                "user_query": row["user_query"],
                "use_case": row["use_case"],
                "parameters": json.dumps(row["parameters"]) if row["parameters"] else None,
                "progress": json.dumps(row["progress"]) if row["progress"] else None,
                "result": json.dumps(row["result"]) if row["result"] else None,
                "error": row["error"],
                "checkpoint_id": row["checkpoint_id"],
            }
            for row in response.data
        ]

    except Exception as e:
        logger.error(f"❌ Failed to get jobs by session from Supabase: {e}")
        return []


def get_jobs_by_status(status: JobStatus, limit: int = 100, offset: int = 0) -> List[JobRecord]:
    """
    Get all jobs with a specific status.

    Args:
        status: Job status to filter by
        limit: Maximum number of jobs to return

    Returns:
        List of JobRecord Typedicts
    """
    if not supabase_client:
        logger.error("Supabase client not initialized")
        return []

    try:
        response = supabase_client.table("async_jobs").select("*").eq("status", status.value).order("created_at", desc=True).range(offset, offset + limit - 1).execute()

        return [
            {
                "job_id": row["job_id"],
                "session_id": row["session_id"],
                "status": row["status"],
                "priority": row["priority"],
                "created_at": row["created_at"],
                "started_at": row["started_at"],
                "completed_at": row["completed_at"],
                "user_query": row["user_query"],
                "use_case": row["use_case"],
                "parameters": json.dumps(row["parameters"]) if row["parameters"] else None,
                "progress": json.dumps(row["progress"]) if row["progress"] else None,
                "result": json.dumps(row["result"]) if row["result"] else None,
                "error": row["error"],
                "checkpoint_id": row["checkpoint_id"],
            }
            for row in response.data
        ]

    except Exception as e:
        logger.error(f"❌ Failed to get jobs by status from Supabase: {e}")
        return []


def get_all_jobs(limit: int = 100, offset: int = 0, tenant_id: Optional[str] = None) -> List[JobRecord]:
    """
    Get all jobs (no filtering) with database-level pagination.

    Args:
        limit: Maximum number of jobs to return
        offset: Number of jobs to skip (for pagination)
        tenant_id: Optional tenant ID for multi-tenancy filtering

    Returns:
        List of JobRecord Typedicts
    """
    if not supabase_client:
        logger.error("Supabase client not initialized")
        return []

    try:
        query = supabase_client.table("async_jobs").select("*").order("created_at", desc=True)
        
        # Apply tenant filtering if provided
        if tenant_id:
            query = query.eq("tenant_id", tenant_id)
        
        # Apply pagination at database level
        response = query.range(offset, offset + limit - 1).execute()

        return [
            {
                "job_id": row["job_id"],
                "session_id": row["session_id"],
                "status": row["status"],
                "priority": row["priority"],
                "created_at": row["created_at"],
                "started_at": row["started_at"],
                "completed_at": row["completed_at"],
                "user_query": row["user_query"],
                "use_case": row["use_case"],
                "parameters": json.dumps(row["parameters"]) if row["parameters"] else None,
                "progress": json.dumps(row["progress"]) if row["progress"] else None,
                "result": json.dumps(row["result"]) if row["result"] else None,
                "error": row["error"],
                "checkpoint_id": row["checkpoint_id"],
            }
            for row in response.data
        ]

    except Exception as e:
        logger.error(f"❌ Failed to get all jobs from Supabase: {e}")
        return []


def count_jobs(session_id: Optional[str] = None, status: Optional[str] = None, tenant_id: Optional[str] = None) -> int:
    """
    Get total count of jobs matching filters (for pagination).
    
    Args:
        session_id: Optional session ID filter
        status: Optional status filter
        tenant_id: Optional tenant ID filter
        
    Returns:
        Total count of matching jobs
    """
    if not supabase_client:
        logger.error("Supabase client not initialized")
        return 0
    
    try:
        query = supabase_client.table("async_jobs").select("job_id", count="exact")
        
        if session_id:
            query = query.eq("session_id", session_id)
        if status:
            query = query.eq("status", status)
        if tenant_id:
            query = query.eq("tenant_id", tenant_id)
        
        response = query.execute()
        # Supabase returns count in response.count
        return response.count if hasattr(response, 'count') and response.count is not None else len(response.data)
    except Exception as e:
        logger.error(f"❌ Failed to count jobs from Supabase: {e}")
        return 0


def get_active_jobs() -> List[JobRecord]:
    """
    Get all active jobs (queued or running).

    Returns:
        List of JobRecord Typedicts
    """
    if not supabase_client:
        logger.error("Supabase client not initialized")
        return []

    try:
        response = supabase_client.table("async_jobs").select("*").in_("status", [JobStatus.QUEUED.value, JobStatus.RUNNING.value]).order("created_at", desc=True).execute()

        return [
            {
                "job_id": row["job_id"],
                "session_id": row["session_id"],
                "status": row["status"],
                "priority": row["priority"],
                "created_at": row["created_at"],
                "started_at": row["started_at"],
                "completed_at": row["completed_at"],
                "user_query": row["user_query"],
                "use_case": row["use_case"],
                "parameters": json.dumps(row["parameters"]) if row["parameters"] else None,
                "progress": json.dumps(row["progress"]) if row["progress"] else None,
                "result": json.dumps(row["result"]) if row["result"] else None,
                "error": row["error"],
                "checkpoint_id": row["checkpoint_id"],
            }
            for row in response.data
        ]

    except Exception as e:
        logger.error(f"❌ Failed to get active jobs from Supabase: {e}")
        return []


# ========== CLEANUP OPERATIONS ==========

def cleanup_old_jobs(days: int = 7) -> Dict[str, int]:
    """
    Clean up old job records from database and cache.

    Deletes jobs older than specified days (excluding RUNNING jobs).

    Args:
        days: Number of days to retain job records

    Returns:
        Cleanup statistics
    """
    logger.info(f"Cleaning up jobs older than {days} days")

    if not supabase_client:
        logger.error("Supabase client not initialized")
        return {"jobs_deleted": 0, "checkpoints_deleted": 0}

    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    try:
        # Get old job IDs first (excluding RUNNING jobs)
        old_jobs_response = supabase_client.table("async_jobs").select("job_id").lt("created_at", cutoff_date).neq("status", JobStatus.RUNNING.value).execute()
        old_job_ids = [row["job_id"] for row in old_jobs_response.data]

        if not old_job_ids:
            logger.info("No old jobs to clean up")
            return {"jobs_deleted": 0, "checkpoints_deleted": 0}

        # Delete old checkpoints first (foreign key constraint)
        checkpoints_response = supabase_client.table("async_job_checkpoints").delete().in_("job_id", old_job_ids).execute()
        checkpoints_deleted = len(checkpoints_response.data) if checkpoints_response.data else 0

        # Delete old jobs
        jobs_response = supabase_client.table("async_jobs").delete().in_("job_id", old_job_ids).execute()
        jobs_deleted = len(jobs_response.data) if jobs_response.data else 0

        logger.info(f"✅ Cleanup complete: {jobs_deleted} jobs, {checkpoints_deleted} checkpoints")

        return {
            "jobs_deleted": jobs_deleted,
            "checkpoints_deleted": checkpoints_deleted,
        }

    except Exception as e:
        logger.error(f"❌ Failed to cleanup old jobs in Supabase: {e}")
        return {"jobs_deleted": 0, "checkpoints_deleted": 0}


def cleanup_failed_jobs(days: int = 3) -> int:
    """
    Clean up failed job records.

    Deletes failed jobs older than specified days.

    Args:
        days: Number of days to retain failed job records

    Returns:
        Number of jobs deleted
    """
    logger.info(f"Cleaning up failed jobs older than {days} days")

    if not supabase_client:
        logger.error("Supabase client not initialized")
        return 0

    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    try:
        response = supabase_client.table("async_jobs").delete().lt("created_at", cutoff_date).eq("status", JobStatus.FAILED.value).execute()
        deleted = len(response.data) if response.data else 0

        logger.info(f"✅ Deleted {deleted} failed jobs")
        return deleted

    except Exception as e:
        logger.error(f"❌ Failed to cleanup failed jobs in Supabase: {e}")
        return 0


# ========== STATISTICS ==========

def create_signed_url(storage_path: str, bucket_name: str = "solver-files", expires_in: int = 3600) -> Optional[str]:
    """
    Create a signed URL for a private bucket file.
    
    Args:
        storage_path: Path to file in bucket (e.g., "job_id/filename.json")
        bucket_name: Supabase Storage bucket name
        expires_in: URL expiration time in seconds (default: 1 hour)
    
    Returns:
        Signed URL if successful, None otherwise
    """
    if not supabase_client:
        logger.warning("Supabase client not initialized")
        return None
    
    try:
        # Generate signed URL for private bucket
        response = supabase_client.storage.from_(bucket_name).create_signed_url(
            storage_path,
            expires_in
        )
        
        if response and 'signedURL' in response:
            return response['signedURL']
        elif isinstance(response, str):
            # Some Supabase client versions return URL directly
            return response
        else:
            logger.warning(f"Unexpected signed URL response format: {response}")
            return None
    
    except Exception as e:
        logger.error(f"Failed to create signed URL for {storage_path}: {e}")
        return None


def get_job_files(job_id: str, include_signed_urls: bool = True) -> Dict[str, Any]:
    """
    Get all files for a job (contents and URLs).
    
    Args:
        job_id: Job identifier
        include_signed_urls: If True, generate signed URLs for private bucket files
    
    Returns:
        Dict with:
        - file_contents: Dict mapping filename to content (small files from JSONB)
        - file_urls: Dict mapping filename to Supabase Storage path or signed URL (large files)
        - signed_urls: Dict mapping filename to signed URL (if include_signed_urls=True)
        - saved_files_path: Local filesystem path (if available)
    """
    logger.info(f"Getting files for job: {job_id}")
    
    job = get_job(job_id)
    if not job:
        logger.warning(f"Job not found: {job_id}")
        return {}
    
    result = json.loads(job['result']) if job.get('result') else {}
    workflow_state = result.get('workflow_state', {})
    solver_result = workflow_state.get('solver_result', {})
    
    # Get file contents from result (small files stored in JSONB)
    file_contents = solver_result.get('file_contents', {})
    
    # Get file paths from result (large files stored in Supabase Storage)
    # These are storage paths, not URLs (bucket is private)
    file_paths = solver_result.get('file_urls', {})
    
    # Generate signed URLs if requested
    signed_urls = {}
    if include_signed_urls and file_paths:
        logger.info(f"Generating signed URLs for {len(file_paths)} files...")
        for filename, storage_path in file_paths.items():
            # storage_path might be a path or already a URL
            if storage_path.startswith('http'):
                # Already a URL (from old public bucket)
                signed_urls[filename] = storage_path
            else:
                # Generate signed URL for private bucket
                signed_url = create_signed_url(storage_path)
                if signed_url:
                    signed_urls[filename] = signed_url
                else:
                    logger.warning(f"Failed to generate signed URL for {filename}")
                    signed_urls[filename] = None
    
    # Get local filesystem path (if available)
    saved_files_path = solver_result.get('saved_files_path')
    
    return {
        'file_contents': file_contents,
        'file_urls': file_paths,  # Storage paths
        'signed_urls': signed_urls if include_signed_urls else {},  # Signed URLs for private bucket
        'saved_files_path': saved_files_path,
        'total_files': len(file_contents) + len(file_paths),
        'bucket_is_private': True  # Indicate bucket is private
    }


def get_job_statistics() -> Dict[str, Any]:
    """
    Get job statistics across all statuses.

    Returns:
        Statistics dictionary with counts by status
    """
    if not supabase_client:
        logger.error("Supabase client not initialized")
        return {
            "total_jobs": 0,
            "by_status": {},
            "avg_completion_time_seconds": None,
        }

    try:
        # Get all jobs for statistics
        all_jobs_response = supabase_client.table("async_jobs").select("status, started_at, completed_at").execute()
        all_jobs = all_jobs_response.data

        # Count by status
        status_counts = {}
        for job in all_jobs:
            status = job["status"]
            status_counts[status] = status_counts.get(status, 0) + 1

        # Calculate average completion time
        completed_jobs = [
            job for job in all_jobs
            if job["status"] == JobStatus.COMPLETED.value
            and job["started_at"]
            and job["completed_at"]
        ]

        avg_duration = None
        if completed_jobs:
            total_duration = 0
            for job in completed_jobs:
                started = datetime.fromisoformat(job["started_at"].replace("Z", "+00:00"))
                completed = datetime.fromisoformat(job["completed_at"].replace("Z", "+00:00"))
                duration = (completed - started).total_seconds()
                total_duration += duration
            avg_duration = total_duration / len(completed_jobs)

        return {
            "total_jobs": len(all_jobs),
            "by_status": status_counts,
            "avg_completion_time_seconds": avg_duration,
        }

    except Exception as e:
        logger.error(f"❌ Failed to get job statistics from Supabase: {e}")
        return {
            "total_jobs": 0,
            "by_status": {},
            "avg_completion_time_seconds": None,
        }


if __name__ == "__main__":
    # Test storage layer
    logger.info("Testing storage layer...")

    # Create test job
    test_job_id = "test_job_123"
    job = create_job_record(
        job_id=test_job_id,
        session_id="test_session",
        user_query="Test query",
        priority=JobPriority.NORMAL,
    )
    print(f"Created job: {job}")

    # Get job
    retrieved = get_job(test_job_id)
    print(f"Retrieved job: {retrieved}")

    # Update progress
    update_job_progress(test_job_id, {
        "current_step": "data_generation",
        "progress_percentage": 50,
        "step_details": {"tables": 3},
        "updated_at": datetime.now(timezone.utc).isoformat(),
    })

    # Get statistics
    stats = get_job_statistics()
    print(f"Statistics: {stats}")

    logger.info("✅ Storage layer test complete")
