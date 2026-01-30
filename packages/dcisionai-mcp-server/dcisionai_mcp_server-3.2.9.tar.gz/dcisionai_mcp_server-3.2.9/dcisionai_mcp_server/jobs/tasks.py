"""
Celery Tasks for Async Job Queue

Following LangGraph Best Practices:
- TypedDict state management (no dict or dataclass)
- Progress callbacks for state updates
- Checkpointing support for resumable workflows
- StateGraph-compatible state structure

Following MCP Protocol:
- Job results exposed as MCP resources
- Reuses existing Dame Workflow (no changes)
- Compatible with existing MCP tool patterns
"""

import os
import sys
import logging
import traceback
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timezone
from platform import system

from celery import Celery, Task
from celery.exceptions import SoftTimeLimitExceeded, TaskRevokedError

from dcisionai_mcp_server.jobs.schemas import (
    JobState,
    JobMetadata,
    JobInput,
    JobProgress,
    JobResult,
    JobStatus,
    JobPriority,
    CeleryTaskInput,
)

logger = logging.getLogger(__name__)

# ========== CELERY APP INITIALIZATION ==========

# Redis URL from environment (Railway will provide this)
# Railway provides both REDIS_URL (internal) and REDIS_PUBLIC_URL (external)
# Use REDIS_PUBLIC_URL if available (for external access), otherwise fall back to REDIS_URL
REDIS_URL = os.getenv("REDIS_PUBLIC_URL") or os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "dcisionai_jobs",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["dcisionai_mcp_server.jobs.tasks", "dcisionai_mcp_server.jobs.metrics_aggregator"],
)

# CRITICAL FIX: Use 'threads' pool on macOS to prevent segfaults while allowing concurrency
# macOS has strict restrictions on forking multi-threaded processes.
# Arrow/libcurl initialization is not fork-safe, causing crashes when Celery forks.
# Using 'threads' pool avoids forking while allowing multiple concurrent tasks.
if system() == "Darwin":  # macOS
    celery_app.conf.worker_pool = "threads"  # Use threads pool on macOS (fork-safe + concurrent)
    celery_app.conf.worker_threads = 4  # Allow 4 concurrent tasks per worker
    logger.info("✅ Configured Celery to use 'threads' worker pool on macOS (fork-safe + concurrent)")
else:
    # On Linux, we can use prefork (default) or threads
    celery_app.conf.worker_pool = "prefork"  # Default for Linux
    logger.info("✅ Configured Celery to use 'prefork' worker pool on Linux")

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3300,  # 55 minutes soft limit
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks
    task_acks_late=True,  # Acknowledge after task completion
    task_reject_on_worker_lost=True,  # Requeue if worker dies
)

logger.info(f"✅ Celery app initialized with Redis broker: {REDIS_URL}")


# ========== REDIS PUB/SUB FOR REAL-TIME UPDATES ==========

try:
    import redis
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    # Test connection
    redis_client.ping()
    logger.info(f"✅ Redis client initialized for pub/sub: {REDIS_URL[:50]}...")
except Exception as e:
    logger.warning(f"⚠️ Redis client initialization failed: {e}. Real-time updates disabled.")
    logger.warning(f"   REDIS_URL: {REDIS_URL[:50] if REDIS_URL else 'Not set'}...")
    logger.warning(f"   REDIS_PUBLIC_URL: {'Set' if os.getenv('REDIS_PUBLIC_URL') else 'Not set'}")
    redis_client = None


def publish_job_update(job_id: str, update: Dict[str, Any]) -> None:
    """
    Publish job update to Redis pub/sub channel.

    WebSocket subscribers listen to: job_updates:{job_id}
    This enables real-time streaming to frontend.
    """
    if not redis_client:
        logger.debug(f"[RedisPubSub] Redis not available, skipping update for job {job_id}")
        return

    try:
        import json
        from datetime import datetime
        
        # Helper to serialize Pydantic models and datetime objects
        def serialize_for_json(obj):
            """Recursively serialize objects for JSON."""
            if hasattr(obj, 'model_dump'):  # Pydantic v2
                return serialize_for_json(obj.model_dump())
            elif hasattr(obj, 'dict'):  # Pydantic v1
                return serialize_for_json(obj.dict())
            elif isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: serialize_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [serialize_for_json(item) for item in obj]
            else:
                return obj
        
        # Serialize update before JSON encoding
        serialized_update = serialize_for_json(update)
        
        channel = f"job_updates:{job_id}"
        message = json.dumps(serialized_update)
        redis_client.publish(channel, message)
        logger.info(f"[RedisPubSub] Published to {channel}: type={update.get('type')}, step={update.get('step', update.get('current_step', 'N/A'))}")
    except Exception as e:
        logger.error(f"[RedisPubSub] Failed to publish job update for {job_id}: {e}", exc_info=True)


# ========== CUSTOM TASK BASE CLASS ==========

class JobTask(Task):
    """
    Base class for all job tasks with error handling and state management.

    LangGraph Pattern:
    - Maintains JobState throughout execution
    - Updates progress via callbacks
    - Supports checkpointing for resumability
    """

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure with detailed error tracking"""
        logger.error(f"Task {task_id} failed: {exc}")
        logger.error(f"Traceback: {einfo}")

        # Extract job_id from args
        job_id = args[0] if args else kwargs.get("job_id")

        if job_id:
            # CRITICAL FIX: Update database status first, then publish to Redis
            from dcisionai_mcp_server.jobs.storage import update_job_status
            
            try:
                update_job_status(
                    job_id=job_id,
                    status=JobStatus.FAILED,
                    completed_at=datetime.now(timezone.utc).isoformat(),
                    error=str(exc)
                )
                logger.info(f"✅ Job {job_id} status updated to FAILED in database")
            except Exception as db_error:
                logger.error(f"❌ Failed to update job {job_id} status in database: {db_error}")
                # Continue anyway - still publish to Redis
            
            # CRITICAL FIX: Signal metrics completion so metrics aggregator doesn't block (only if metrics enabled)
            from dcisionai_mcp_server.config import MCPConfig
            if MCPConfig.ENABLE_LLM_METRICS:
                try:
                    from dcisionai_workflow.shared.utils.metrics_publisher import publish_job_metrics_complete
                    session_id = args[1] if len(args) > 1 else kwargs.get("session_id", "unknown")
                    publish_job_metrics_complete(job_id, session_id)
                    logger.debug(f"✅ Published metrics completion signal for failed job {job_id}")
                except Exception as metrics_signal_error:
                    logger.warning(f"⚠️ Failed to publish metrics completion signal for failed job: {metrics_signal_error}")
            
            # Publish failure notification to Redis
            error_update = {
                "type": "error",  # Add type field for WebSocket protocol
                "job_id": job_id,
                "status": JobStatus.FAILED.value,
                "error": {
                    "message": str(exc),
                    "type": type(exc).__name__,
                    "traceback": str(einfo),
                },
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }
            publish_job_update(job_id, error_update)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handle task retry with progress notification"""
        logger.warning(f"Task {task_id} retrying: {exc}")

        job_id = args[0] if args else kwargs.get("job_id")

        if job_id:
            retry_update = {
                "type": "status",  # Add type field for WebSocket protocol
                "job_id": job_id,
                "status": "retrying",
                "retry_count": self.request.retries,
                "error": str(exc),
            }
            publish_job_update(job_id, retry_update)

    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success with final result notification"""
        logger.info(f"Task {task_id} completed successfully")

        job_id = args[0] if args else kwargs.get("job_id")

        if job_id:
            # CRITICAL FIX: Update database status if not already updated
            # (The task itself updates the database, but this ensures it happens even if task code fails)
            from dcisionai_mcp_server.jobs.storage import update_job_status, get_job
            
            try:
                # Check current status to avoid duplicate updates
                job = get_job(job_id)
                current_status = job.get("status") if job else None
                
                # Only update if status is still RUNNING (task might have already updated it)
                # This is a safety net in case the task's database update failed
                if current_status == JobStatus.RUNNING.value:
                    update_job_status(
                        job_id=job_id,
                        status=JobStatus.COMPLETED,
                        completed_at=datetime.now(timezone.utc).isoformat()
                    )
                    logger.info(f"✅ Job {job_id} status updated to COMPLETED in database (on_success callback)")
                else:
                    logger.debug(f"Job {job_id} already has status {current_status}, skipping database update")
            except Exception as db_error:
                logger.error(f"❌ Failed to update job {job_id} status in database: {db_error}")
                # Continue anyway - still publish to Redis
            
            # Publish success notification to Redis (only if not already published by task)
            # The task now publishes completion before returning, so this is a backup
            success_update = {
                "type": "completed",  # Add type field for WebSocket protocol
                "job_id": job_id,
                "status": JobStatus.COMPLETED.value,
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }
            publish_job_update(job_id, success_update)
            logger.debug(f"Published completion message from on_success callback for job {job_id}")


# ========== DAME WORKFLOW INTEGRATION ==========

def run_dame_workflow(
    user_query: str,
    session_id: str,
    use_case: Optional[str] = None,
    progress_callback: Optional[Callable[[str, int, Dict[str, Any]], None]] = None,
    job_id: Optional[str] = None,
    hitl_enabled: bool = False,
) -> Dict[str, Any]:
    """
    Execute existing Dame Workflow (LangGraph StateGraph).

    CRITICAL: This function does NOT change the workflow itself.
    It simply calls the existing workflow with progress callbacks.

    LangGraph Integration:
    - Passes TypedDict state through workflow
    - Receives progress updates via callbacks
    - Returns final workflow state

    Args:
        user_query: Natural language query from user
        session_id: Session identifier for context
        use_case: Optional use case hint (e.g., "VRP", "client_advisor_matching")
        progress_callback: Optional callback for progress updates

    Returns:
        Final Dame Workflow state (TypedDict)
    """
    import asyncio
    from dcisionai_workflow.workflow import run_workflow

    logger.info(f"Starting DcisionAI Workflow for session {session_id}")
    logger.info(f"Query: {user_query}")

    try:
        # Run the clean workflow from dcisionai_workflow
        # This workflow includes: HITL Router → Intent Discovery (9 steps) → Claude SDK Solver → Business Explanation
        # Pass job_id if available so metrics can be published correctly
        workflow_kwargs = {
            "problem_description": user_query,
            "session_id": session_id,
            "hitl_enabled": hitl_enabled,  # Use provided hitl_enabled flag
            "progress_callback": progress_callback  # Pass progress callback to workflow
        }
        if job_id:
            workflow_kwargs["job_id"] = job_id  # Pass job_id for metrics publishing
        
        result = asyncio.run(
            run_workflow(**workflow_kwargs)
        )
        logger.info(f"DcisionAI Workflow completed for session {session_id}")
        return result

    except TypeError as e:
        error_msg = str(e)
        # Check if it's a serialization error (workflow completed but checkpointing failed)
        if 'msgpack serializable' in error_msg.lower() or 'function' in error_msg.lower():
            logger.warning(f"⚠️ Serialization error after workflow completion: {error_msg}")
            logger.info("Workflow likely completed successfully but checkpointing failed - attempting recovery...")
            
            # Try to get the result from the workflow by running it again without checkpointing
            # OR: The workflow might have completed, so we can try to extract state from memory
            # For now, create a minimal result indicating completion
            try:
                # Import cleaning function
                from dcisionai_mcp_server.jobs.tasks import make_serializable
                # Try to get partial result - if workflow completed, we might have state in memory
                # For now, return a result indicating the workflow completed but had serialization issues
                result = {
                    'workflow_stage': 'completed',
                    'errors': [f"Workflow completed but serialization error: {error_msg[:200]}"],
                    'warnings': ['Workflow completed but checkpointing failed due to serialization'],
                    '_serialization_error': True
                }
                logger.warning("Returning minimal result due to serialization error")
                return result
            except Exception as recovery_error:
                logger.error(f"Recovery attempt failed: {recovery_error}")
                raise
        else:
            # Re-raise if it's not a serialization error
            logger.error(f"DcisionAI Workflow failed for session {session_id}: {e}")
            logger.error(traceback.format_exc())
            raise
    except Exception as e:
        logger.error(f"DcisionAI Workflow failed for session {session_id}: {e}")
        logger.error(traceback.format_exc())
        raise


# ========== CELERY TASKS ==========

# Set timeout to 2 hours (7200 seconds) to prevent jobs from running indefinitely
@celery_app.task(base=JobTask, bind=True, max_retries=3, default_retry_delay=60, soft_time_limit=7200, time_limit=7500)
def run_optimization_job(
    self,
    job_id: str,
    user_query: str,
    session_id: str,
    use_case: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None,
    hitl_enabled: bool = False,
) -> Dict[str, Any]:
    """
    Execute optimization workflow as background job.

    LangGraph Integration:
    - Maintains JobState throughout execution
    - Updates progress via callbacks
    - Supports resumable workflows via checkpointing

    MCP Integration:
    - Job results stored and exposed as MCP resources
    - Compatible with existing MCP tool patterns

    Args:
        job_id: Unique job identifier
        user_query: Natural language query
        session_id: Session identifier
        use_case: Optional use case hint
        parameters: Optional additional parameters

    Returns:
        JobResult TypedDict with final state and MCP resource URIs
    """
    logger.info(f"Starting optimization job {job_id}")

    # Track job start time for metrics
    job_start_time = datetime.now(timezone.utc)

    # CRITICAL FIX: Update job status to RUNNING in database
    # Import here to avoid circular imports
    from dcisionai_mcp_server.jobs.storage import update_job_status

    try:
        # Update job status in database with started timestamp
        update_job_status(
            job_id=job_id,
            status=JobStatus.RUNNING,
            started_at=job_start_time.isoformat()
        )
        logger.info(f"✅ Job {job_id} status updated to RUNNING in database")
    except Exception as db_error:
        logger.error(f"❌ Failed to update job {job_id} status in database: {db_error}")
        # Continue anyway - job will still run

    # Update job status to RUNNING (for Redis pub/sub)
    running_update = {
        "type": "status",
        "job_id": job_id,
        "status": JobStatus.RUNNING.value,
        "progress": 0,
        "current_step": "initializing",
        "started_at": job_start_time.isoformat(),
    }
    publish_job_update(job_id, running_update)
    logger.info(f"[JobProgress] Published RUNNING status for job {job_id}")

    # Also update Celery task state (for polling clients)
    self.update_state(
        state="PROGRESS",
        meta={
            "job_id": job_id,
            "status": JobStatus.RUNNING.value,
            "progress": {
                "current_step": "initializing",
                "progress_percentage": 0,
                "step_details": {},
            },
        },
    )

    # Define progress callback for Dame Workflow
    def progress_callback(step: str, progress: int, details: Dict[str, Any]) -> None:
        """
        Progress callback invoked by Dame Workflow.

        LangGraph Pattern:
        - Called after each StateGraph node completion
        - Receives current step, progress %, and step details
        - Updates JobState progress field
        - Extracts and streams thinking content if available
        """
        # Extract thinking content from current step
        thinking_content = details.get("_thinking_content") or details.get("thinking_content")
        
        # CRITICAL: Get current progress to accumulate thinking content BEFORE publishing
        # This ensures thinking_history is available in WebSocket messages
        thinking_history = {}
        try:
            import json
            from dcisionai_mcp_server.jobs.storage import get_job
            current_job = get_job(job_id)
            if current_job:
                # Progress is stored as JSON string in JobRecord
                progress_data = current_job.get('progress')
                if progress_data:
                    # Parse JSON string to dict
                    if isinstance(progress_data, str):
                        try:
                            current_progress = json.loads(progress_data)
                        except (json.JSONDecodeError, TypeError):
                            current_progress = {}
                    else:
                        current_progress = progress_data
                    
                    if isinstance(current_progress, dict):
                        thinking_history = current_progress.get('thinking_history', {})
            
            # Always add current step to history (even if no thinking content)
            # This ensures all workflow steps appear in the CoT UI
            if thinking_content and isinstance(thinking_content, str) and thinking_content.strip():
                thinking_history[step] = {
                    "content": thinking_content,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                logger.debug(f"[JobProgress] ✅ Accumulated thinking for step {step} (total steps with thinking: {len(thinking_history)})")
            else:
                # Add step even without thinking content (for UI completeness)
                # Generate minimal thinking content dynamically from step details
                step_display_name = step.replace('_', ' ').title()
                minimal_content = f"**{step_display_name}**\n\n"
                
                if details and isinstance(details, dict):
                    status = details.get("status", "complete")
                    
                    # Dynamically extract meaningful information from details
                    # Build a summary from any numeric/count fields, status, or other relevant info
                    summary_parts = []
                    
                    # Check for count fields (any field ending with _count or containing 'count')
                    for key, value in details.items():
                        if key == "_thinking_content" or key == "thinking_content":
                            continue  # Skip thinking content field itself
                        if isinstance(value, (int, float)) and ("count" in key.lower() or "score" in key.lower() or "match" in key.lower()):
                            if "count" in key.lower():
                                entity_name = key.replace("_count", "").replace("count", "").replace("_", " ")
                                summary_parts.append(f"Extracted {value} {entity_name}")
                            elif "score" in key.lower() or "match" in key.lower():
                                if isinstance(value, float) and 0 <= value <= 1:
                                    summary_parts.append(f"Match score: {value:.1%}")
                                else:
                                    summary_parts.append(f"{key.replace('_', ' ').title()}: {value}")
                    
                    # Check for domain/type fields
                    if "domain" in details:
                        summary_parts.append(f"Domain: {details['domain']}")
                    if "type" in details:
                        summary_parts.append(f"Type: {details['type']}")
                    
                    # Add status if not complete
                    if status != "complete":
                        summary_parts.append(f"Status: {status}")
                    
                    # Build final content
                    if summary_parts:
                        minimal_content += " ".join(summary_parts) + ".\n"
                    elif status == "complete":
                        minimal_content += "Step completed successfully.\n"
                    else:
                        minimal_content += f"Status: {status}.\n"
                else:
                    minimal_content += "Step completed.\n"
                
                thinking_history[step] = {
                    "content": minimal_content,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                logger.debug(f"[JobProgress] ✅ Added step {step} to history (minimal content: {len(minimal_content)} chars)")
        except Exception as hist_error:
            logger.debug(f"[JobProgress] Could not get thinking_history for WebSocket message: {hist_error}")
            # Initialize history with current step
            if thinking_content and isinstance(thinking_content, str) and thinking_content.strip():
                thinking_history = {step: {"content": thinking_content, "timestamp": datetime.now(timezone.utc).isoformat()}}
            else:
                # Even without thinking content, add the step
                thinking_history = {step: {"content": f"**{step.replace('_', ' ').title()}**\n\nStep completed.", "timestamp": datetime.now(timezone.utc).isoformat()}}

        # Format progress update for WebSocket clients
        # Client expects: { type: 'progress', step: '...', progress: 45, current_step: '...' }
        progress_update = {
            "type": "progress",
            "job_id": job_id,
            "status": JobStatus.RUNNING.value,
            # Flat fields for client compatibility
            "step": step,
            "progress": progress,
            "current_step": step,  # Alias for compatibility
            "progress_percentage": progress,  # Alias for compatibility
            # Nested structure for detailed information
            "step_details": details,
            "thinking_history": thinking_history,  # Cumulative thinking from all steps
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Publish to Redis (for WebSocket subscribers)
        publish_job_update(job_id, progress_update)
        logger.info(f"[JobProgress] Published progress update for job {job_id}: {step} ({progress}%)")

        # Extract and publish thinking content if available (for streaming CoT display)
        if thinking_content and isinstance(thinking_content, str) and thinking_content.strip():
            # Publish thinking message separately for streaming display
            thinking_update = {
                "type": "thinking",
                "job_id": job_id,
                "step": step,
                "content": thinking_content,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            publish_job_update(job_id, thinking_update)
            logger.info(f"[JobProgress] ✅ Published thinking content for job {job_id}: {step} ({len(thinking_content)} chars)")
        else:
            # Debug: Log when thinking content is missing
            logger.debug(f"[JobProgress] ⚠️ No thinking content for job {job_id}, step {step}. Details keys: {list(details.keys())}")
            if details:
                logger.debug(f"[JobProgress] Details preview: {str(details)[:200]}")

        # CRITICAL: Persist progress to database (including thinking content in step_details)
        # This ensures progress is restored on page reload
        # IMPORTANT: Accumulate thinking content from all steps (not just current step)
        try:
            from dcisionai_mcp_server.jobs.storage import update_job_progress
            
            # Update progress with both current step_details and cumulative thinking_history
            update_job_progress(job_id, {
                "current_step": step,
                "progress_percentage": progress,
                "step_details": details,  # Includes _thinking_content if present (for current step)
                "thinking_history": thinking_history,  # Cumulative thinking from all steps
                "updated_at": datetime.now(timezone.utc).isoformat(),
            })
            logger.debug(f"[JobProgress] ✅ Persisted progress to database for job {job_id}: {step} ({progress}%)")
        except Exception as db_error:
            logger.error(f"[JobProgress] ❌ Failed to persist progress to database for job {job_id}: {db_error}")
            # Don't fail the workflow if database update fails

        # Update Celery task state (for polling clients) - keep nested format for API
        celery_progress_update = {
            "type": "progress",
            "job_id": job_id,
            "status": JobStatus.RUNNING.value,
            "progress": {
                "current_step": step,
                "progress_percentage": progress,
                "thinking_history": thinking_history,  # Include cumulative thinking history
                "step_details": details,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
        }
        self.update_state(state="PROGRESS", meta=celery_progress_update)

    try:
        # Feature flag: Conditionally start metrics aggregator task
        from dcisionai_mcp_server.config import MCPConfig
        enable_llm_metrics = MCPConfig.ENABLE_LLM_METRICS
        
        if enable_llm_metrics:
            # Start metrics aggregator task (separate process)
            # This task subscribes to Redis pub/sub and aggregates metrics independently
            from dcisionai_mcp_server.jobs.metrics_aggregator import aggregate_llm_metrics
            metrics_task = aggregate_llm_metrics.delay(job_id, session_id)
            logger.info(f"✅ Started metrics aggregator task for job {job_id}")
        else:
            logger.info(f"⚠️ LLM metrics aggregation disabled (ENABLE_LLM_METRICS=false) for job {job_id}")
            metrics_task = None

        # CRITICAL: Execute existing Dame Workflow (NO changes to workflow)
        # Metrics are now published separately via Redis pub/sub, not stored in workflow state
        # Pass job_id to workflow so metrics can be published correctly
        workflow_result = run_dame_workflow(
            user_query=user_query,
            session_id=session_id,
            use_case=use_case,
            progress_callback=progress_callback,
            job_id=job_id,  # Pass job_id for metrics publishing
            hitl_enabled=hitl_enabled,  # Pass hitl_enabled flag
        )
        
        # Clean workflow result immediately after receiving it to prevent serialization issues
        # This catches any function objects that might have slipped through
        # Note: make_serializable is defined later in this function, so we'll clean it there
        # workflow_result = make_serializable(workflow_result, path="workflow_result")

        # Signal metrics completion (all metrics have been published) - only if metrics enabled
        if enable_llm_metrics:
            try:
                from dcisionai_workflow.shared.utils.metrics_publisher import publish_job_metrics_complete
                publish_job_metrics_complete(job_id, session_id)
                logger.debug(f"✅ Published metrics completion signal for job {job_id}")
            except Exception as metrics_signal_error:
                logger.warning(f"⚠️ Failed to publish metrics completion signal: {metrics_signal_error}")

        # Wait for metrics aggregation to complete (with timeout) - only if metrics enabled
        llm_metrics: LLMMetrics = {}
        if enable_llm_metrics:
            try:
                # Wait up to 30 seconds for metrics aggregation
                metrics_result = metrics_task.get(timeout=30)
                if metrics_result:
                    llm_metrics = metrics_result
                    logger.info(f"📊 Job {job_id} LLM Metrics aggregated: {llm_metrics.get('total_calls', 0)} calls, "
                               f"{llm_metrics.get('total_tokens_in', 0):,} tokens in, "
                               f"{llm_metrics.get('total_tokens_out', 0):,} tokens out, "
                               f"${llm_metrics.get('total_cost_usd', 0):.4f} USD")
            except Exception as metrics_wait_error:
                logger.warning(f"⚠️ Metrics aggregation not yet complete or failed: {metrics_wait_error}")
                # Try to get metrics from database as fallback
                try:
                    from dcisionai_mcp_server.jobs.storage import get_job
                    import json
                    current_job = get_job(job_id)
                    if current_job and current_job.get('llm_metrics'):
                        llm_metrics_str = current_job.get('llm_metrics')
                        if isinstance(llm_metrics_str, str):
                            llm_metrics = json.loads(llm_metrics_str)
                        else:
                            llm_metrics = llm_metrics_str
                        logger.info(f"📊 Retrieved LLM metrics from database for job {job_id}: {llm_metrics.get('total_calls', 0)} calls")
                except Exception as db_metrics_error:
                    logger.debug(f"Could not retrieve metrics from database: {db_metrics_error}")
                # Continue without metrics if both fail - they'll be available later via database
        else:
            logger.info(f"⚠️ LLM metrics skipped (ENABLE_LLM_METRICS=false) for job {job_id}")

        # Convert workflow_result to JSON-serializable format
        # LangChain Message objects (HumanMessage, AIMessage, etc.) are not JSON serializable
        def is_callable_object(obj) -> bool:
            """
            Comprehensive check for callable objects that cannot be serialized.
            
            Checks for:
            - Function types (FunctionType, BuiltinFunctionType, LambdaType)
            - Method types (MethodType, BuiltinMethodType)
            - Partial functions (functools.partial, functools.partialmethod)
            - Callable classes and instances
            - Wrapper descriptors
            - Any object with __call__ that isn't a type
            
            Returns:
                True if object is a callable that cannot be serialized, False otherwise
            """
            import types
            from functools import partial, partialmethod
            
            # Quick check: if it's a basic serializable type, it's not a callable problem
            if isinstance(obj, (str, int, float, bool, type(None), bytes)):
                return False
            
            # Check for function/method types (most common case)
            if isinstance(obj, (
                types.FunctionType,
                types.MethodType,
                types.BuiltinFunctionType,
                types.BuiltinMethodType,
            )):
                return True
            
            # Check for lambda functions (subclass of FunctionType but explicit check)
            if type(obj).__name__ == 'function' and hasattr(obj, '__code__'):
                return True
            
            # Check for wrapper types (less common but possible)
            try:
                if isinstance(obj, (
                    types.WrapperDescriptorType,
                    types.MethodWrapperType,
                    types.MethodDescriptorType,
                )):
                    return True
            except AttributeError:
                # These types might not exist in all Python versions
                pass
            
            # Check for functools partial objects
            try:
                if isinstance(obj, (partial, partialmethod)):
                    return True
            except (NameError, TypeError):
                pass
            
            # Check if it's a callable (but exclude types and classes)
            if callable(obj):
                # Exclude types and classes (they're callable but serializable as strings)
                if isinstance(obj, type):
                    return False
                
                # Exclude certain built-in types that are callable but serializable
                builtin_callables = (str, int, float, bool, list, dict, tuple, set, bytes, bytearray)
                if obj in builtin_callables:
                    return False
                
                # Check if it has __call__ method
                if hasattr(obj, '__call__'):
                    # If it's a class instance with __call__, it's callable
                    # But we need to be careful - some objects are callable but serializable
                    
                    # Check if it's a Pydantic model (has model_dump, which means it's serializable)
                    if hasattr(obj, 'model_dump') or hasattr(obj, 'dict'):
                        return False
                    
                    # Check if it's a dataclass (has __dataclass_fields__)
                    if hasattr(obj, '__dataclass_fields__'):
                        return False
                    
                    # Check if it's a namedtuple (has _fields)
                    if hasattr(obj, '_fields') and isinstance(obj._fields, tuple):
                        return False
                    
                    # Check if it's an enum (has _name_ and _value_)
                    import enum
                    if isinstance(obj, enum.Enum):
                        return False
                    
                    # Everything else with __call__ is likely a function/callable
                    return True
            
            return False
        
        def make_serializable(obj, path: str = "root"):
            """
            Recursively convert non-serializable objects to serializable format.
            
            Args:
                obj: Object to serialize
                path: Current path in the object tree (for debugging)
            """
            import types
            
            # Check for callable objects first (before other checks)
            if is_callable_object(obj):
                obj_type_name = type(obj).__name__
                obj_repr = str(obj)[:100] if hasattr(obj, '__name__') else repr(obj)[:100]
                logger.warning(f"⚠️ Found callable object at path '{path}': {obj_type_name} (repr: {obj_repr})")
                return {"_type": "function", "_message": f"{obj_type_name} object (cannot be serialized)", "_path": path}
            
            # Check for LLMMetricsTracker instances (can be nested anywhere)
            if obj.__class__.__name__ == 'LLMMetricsTracker':
                # Extract summary and return as dict
                if hasattr(obj, 'get_summary'):
                    return obj.get_summary()
                return {"_type": "LLMMetricsTracker", "_message": "Metrics extracted separately"}
            
            if hasattr(obj, "type") and hasattr(obj, "content"):
                # LangChain message object
                return {
                    "role": obj.type,
                    "content": obj.content,
                }
            elif isinstance(obj, dict):
                # Skip non-serializable tracker object (extracted separately)
                # CRITICAL: Preserve _thinking_content fields for CoT restoration
                result = {}
                for k, v in obj.items():
                    # Skip function/callable objects (cannot be serialized)
                    # Use comprehensive callable detection
                    if is_callable_object(v):
                        obj_repr = str(v)[:100] if hasattr(v, '__name__') else repr(v)[:100]
                        logger.debug(f"Skipping non-serializable callable: {k} (type: {type(v).__name__}, repr: {obj_repr})")
                        continue
                    
                    if k == 'llm_metrics_tracker':
                        # Handle LLMMetricsTracker - extract summary if it's a tracker instance
                        if hasattr(v, 'get_summary'):
                            result[k] = v.get_summary()
                        else:
                            continue  # Skip if not a tracker instance
                    # Skip progress_callback and other callable fields
                    elif k == 'progress_callback' or k == '_websocket_manager' or k == '_progress_callback':
                        logger.debug(f"Skipping non-serializable callback: {k}")
                        continue
                    # Preserve _thinking_content fields (they're strings, so serializable)
                    elif k == '_thinking_content' or k == 'thinking_content':
                        result[k] = v  # Keep as-is (already string)
                    else:
                        try:
                            serialized_value = make_serializable(v, path=f"{path}.{k}")
                            # Double-check the serialized value isn't a function
                            if isinstance(serialized_value, dict) and serialized_value.get('_type') == 'function':
                                logger.debug(f"Skipping key '{k}' at path '{path}.{k}' - serialized to function placeholder")
                                continue
                            result[k] = serialized_value
                        except Exception as e:
                            # If serialization fails, skip this key and log
                            logger.warning(f"Skipping non-serializable value for key '{k}' at path '{path}.{k}': {e}")
                            continue
                return result
            elif isinstance(obj, (list, tuple)):
                serialized_list = []
                for idx, item in enumerate(obj):
                    try:
                        serialized_item = make_serializable(item, path=f"{path}[{idx}]")
                        # Skip function placeholders
                        if isinstance(serialized_item, dict) and serialized_item.get('_type') == 'function':
                            logger.debug(f"Skipping list item at path '{path}[{idx}]' - function placeholder")
                            continue
                        serialized_list.append(serialized_item)
                    except Exception as e:
                        logger.debug(f"Skipping non-serializable list item at path '{path}[{idx}]': {e}")
                        continue
                return serialized_list
            elif isinstance(obj, (str, int, float, bool, type(None))):
                return obj
            else:
                # Check for callable/function objects using comprehensive detection
                if is_callable_object(obj):
                    logger.debug(f"Skipping non-serializable callable object: {type(obj).__name__}")
                    return {"_type": "callable", "_message": f"{type(obj).__name__} object (cannot be serialized)"}
                
                # Check if it's LLMMetricsTracker
                if obj.__class__.__name__ == 'LLMMetricsTracker':
                    if hasattr(obj, 'get_summary'):
                        return obj.get_summary()
                    return {"_type": "LLMMetricsTracker", "_message": "Metrics extracted separately"}
                # For other non-serializable objects, convert to string
                try:
                    return str(obj)
                except Exception as e:
                    logger.warning(f"Failed to convert object to string: {e}")
                    return {"_type": "non_serializable", "_message": f"{type(obj).__name__} object (conversion failed)"}

        # Clean workflow result before serialization (moved here so make_serializable is defined)
        # This catches any function objects that might have slipped through
        workflow_result = make_serializable(workflow_result, path="workflow_result")
        
        # Serialize workflow result, catching any serialization errors
        try:
            serializable_workflow_state = make_serializable(workflow_result)
            
            # Test serialization with msgpack to catch any remaining function objects
            try:
                import msgpack
                # Test with a small sample first to catch errors early
                test_sample = {}
                for key in list(serializable_workflow_state.keys())[:10]:
                    test_sample[key] = serializable_workflow_state[key]
                msgpack.packb(test_sample, default=str, strict_types=False)
                
                # If sample works, test full object
                msgpack.packb(serializable_workflow_state, default=str, strict_types=False)
            except Exception as msgpack_error:
                error_msg = str(msgpack_error)
                logger.warning(f"Msgpack serialization test failed: {error_msg}")
                
                # If error mentions "function", try more aggressive filtering
                if 'function' in error_msg.lower() or 'callable' in error_msg.lower():
                    logger.info("Detected function in serialization error, attempting deeper cleanup...")
                    # Try one more pass with more aggressive filtering
                    serializable_workflow_state = make_serializable(serializable_workflow_state)
                    
                    # Try serialization again
                    try:
                        msgpack.packb(serializable_workflow_state, default=str, strict_types=False)
                        logger.info("✅ Second pass serialization successful")
                    except Exception as retry_error:
                        logger.error(f"Second pass also failed: {retry_error}")
                        # Extract only essential fields (avoiding callable objects)
                        # CRITICAL: Include trace_id for graph-native traces
                        essential_fields = [
                            'workflow_stage', 'current_step', 'completed_steps', 'trace_id',
                            'errors', 'warnings', '_thinking_content', 'thinking_content',
                            # CRITICAL: Preserve solver_result for model deployment
                            'solver_result', 'solver_output', 'claude_agent_work_dir',
                            'claude_agent_status', 'claude_agent_execution_summary'
                        ]
                        filtered_state = {}
                        for k, v in serializable_workflow_state.items():
                            if k in essential_fields:
                                filtered_state[k] = v
                            elif not is_callable_object(v):
                                # Only include non-callable fields
                                try:
                                    # Test if it's serializable
                                    import msgpack
                                    msgpack.packb({k: v}, default=str, strict_types=False)
                                    filtered_state[k] = v
                                except:
                                    logger.debug(f"Skipping non-serializable field: {k}")
                        
                        # CRITICAL: Ensure solver_result is preserved even if not in essential_fields
                        # This is needed for model deployment
                        if 'solver_result' in serializable_workflow_state and 'solver_result' not in filtered_state:
                            solver_result = serializable_workflow_state.get('solver_result')
                            if isinstance(solver_result, dict) and not is_callable_object(solver_result):
                                # Try to preserve solver_result, especially model_code
                                try:
                                    filtered_solver_result = {}
                                    for sk, sv in solver_result.items():
                                        if not is_callable_object(sv):
                                            filtered_solver_result[sk] = sv
                                    filtered_state['solver_result'] = filtered_solver_result
                                    logger.info(f"✅ Preserved solver_result in filtered state (keys: {list(filtered_solver_result.keys())})")
                                except Exception as e:
                                    logger.warning(f"⚠️ Could not preserve solver_result: {e}")
                        
                        serializable_workflow_state = filtered_state
                        logger.warning("Using minimal workflow state due to serialization issues")
        except Exception as serialization_error:
            logger.error(f"Failed to serialize workflow result: {serialization_error}")
            # Create a minimal serializable result with just essential fields
            # CRITICAL: Preserve solver_result for model deployment even on serialization error
            minimal_state = {
                'workflow_stage': workflow_result.get('workflow_stage', 'error'),
                'errors': workflow_result.get('errors', []) + [f"Serialization error: {str(serialization_error)}"],
                'warnings': workflow_result.get('warnings', []) + ["Workflow completed but result serialization failed"],
                '_serialization_error': True
            }
            
            # Try to preserve solver_result if it exists (needed for deployment)
            solver_result = workflow_result.get('solver_result')
            if solver_result and isinstance(solver_result, dict):
                try:
                    # Only preserve serializable parts of solver_result
                    preserved_solver_result = {}
                    for k, v in solver_result.items():
                        if not is_callable_object(v) and isinstance(v, (str, int, float, bool, type(None), dict, list)):
                            preserved_solver_result[k] = v
                    if preserved_solver_result:
                        minimal_state['solver_result'] = preserved_solver_result
                        logger.info(f"✅ Preserved solver_result in minimal state (keys: {list(preserved_solver_result.keys())})")
                except Exception as e:
                    logger.warning(f"⚠️ Could not preserve solver_result in minimal state: {e}")
            
            # Also preserve work_dir for file-based model retrieval
            work_dir = workflow_result.get('claude_agent_work_dir')
            if work_dir:
                minimal_state['claude_agent_work_dir'] = work_dir
            
            serializable_workflow_state = minimal_state
        
        # LLM metrics are now aggregated separately and stored in database
        # They're retrieved above from the aggregator task or will be available via database query

        # Calculate timing metrics
        step_timings = workflow_result.get('step_timings', {})
        job_end_time = datetime.now(timezone.utc)
        total_duration = (job_end_time - job_start_time).total_seconds()

        # Calculate intent discovery total (all intent steps)
        intent_steps = ['decomposition', 'context_building', 'classification', 'assumptions',
                       'entities', 'objectives', 'constraints', 'synthesis']
        intent_discovery_seconds = sum(step_timings.get(step, 0) for step in intent_steps)

        timing_metrics: TimingMetrics = {
            "job_started_at": job_start_time.isoformat(),
            "job_completed_at": job_end_time.isoformat(),
            "total_duration_seconds": total_duration,
            "by_step": step_timings,
            "intent_discovery_seconds": intent_discovery_seconds,
            "solver_seconds": step_timings.get('claude_sdk_solver', 0),
            "explanation_seconds": step_timings.get('business_explanation', 0),
        }

        logger.info(f"⏱️ Job {job_id} Timing: {total_duration:.1f}s total "
                   f"(Intent: {intent_discovery_seconds:.1f}s, "
                   f"Solver: {timing_metrics['solver_seconds']:.1f}s, "
                   f"Explanation: {timing_metrics['explanation_seconds']:.1f}s)")

        # CRITICAL: Get thinking_history from progress before saving result
        # This ensures thinking content is preserved in the final result
        thinking_history = {}
        try:
            import json
            from dcisionai_mcp_server.jobs.storage import get_job
            current_job = get_job(job_id)
            if current_job:
                # Progress is stored as JSON string in JobRecord
                progress_data = current_job.get('progress')
                if progress_data:
                    # Parse JSON string to dict
                    if isinstance(progress_data, str):
                        try:
                            current_progress = json.loads(progress_data)
                        except (json.JSONDecodeError, TypeError):
                            current_progress = {}
                    else:
                        current_progress = progress_data
                    
                    if isinstance(current_progress, dict):
                        thinking_history = current_progress.get('thinking_history', {})
                        logger.debug(f"[JobResult] ✅ Retrieved thinking_history with {len(thinking_history)} steps for job {job_id}")
        except Exception as hist_error:
            logger.warning(f"[JobResult] ⚠️ Could not retrieve thinking_history for final result: {hist_error}")
        
        # Extract key results from workflow state
        # Dame Workflow returns TypedDict with intent, data, solver, explanation
        # CRITICAL: Include thinking_history in workflow_state so frontend can restore CoT
        workflow_state_with_thinking = serializable_workflow_state.copy()
        if thinking_history:
            workflow_state_with_thinking['thinking_history'] = thinking_history
            logger.debug(f"[JobResult] ✅ Added thinking_history to workflow_state for job {job_id}")
        
        # Check if model_code exists in solver_result for deployment support
        solver_result = workflow_state_with_thinking.get("solver_result", {})
        if isinstance(solver_result, dict):
            model_code = solver_result.get("model_code")
            if model_code:
                logger.info(f"✅ Model code found in solver_result for job {job_id}: {len(model_code)} characters")
            else:
                logger.warning(f"⚠️ No model_code in solver_result for job {job_id}. Keys: {list(solver_result.keys())}")
                # Check if work_dir exists - model might be in file
                work_dir = workflow_state_with_thinking.get("claude_agent_work_dir")
                if work_dir:
                    logger.info(f"⚠️ Work dir available: {work_dir} - model_code may be in file")
        
        job_result: JobResult = {
            "status": JobStatus.COMPLETED.value,
            "workflow_state": workflow_state_with_thinking,  # Includes thinking_history
            "llm_metrics": llm_metrics,  # LLM usage and cost tracking
            "timing_metrics": timing_metrics,  # Execution timing
            "mcp_resources": {
                "status": f"job://{job_id}/status",
                "result": f"job://{job_id}/result",
                "intent": f"job://{job_id}/intent",
                "data": f"job://{job_id}/data",
                "solver": f"job://{job_id}/solver",
                "explanation": f"job://{job_id}/explanation",
            },
            "summary": {
                "query": user_query,
                "use_case": serializable_workflow_state.get("use_case", use_case),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            },
        }
        
        logger.info(f"Job {job_id} completed successfully")

        # CRITICAL FIX: Update job status in database with completion timestamp
        # Import here to avoid circular imports
        from dcisionai_mcp_server.jobs.storage import update_job_status, save_job_result, update_job_progress

        try:
            # Update job status to COMPLETED with timestamp
            update_job_status(
                job_id=job_id,
                status=JobStatus.COMPLETED,
                completed_at=datetime.now(timezone.utc).isoformat()
            )

            # CRITICAL FIX: Ensure progress is set to 100% when job completes
            # This ensures UI always shows 100% for completed jobs, even if final progress update was missed
            update_job_progress(job_id, {
                "current_step": "completed",
                "progress_percentage": 100,
                "step_details": {"status": "complete", "workflow_stage": workflow_result.get('workflow_stage', 'completed')},
                "updated_at": datetime.now(timezone.utc).isoformat(),
            })
            logger.info(f"✅ Updated job {job_id} progress to 100% (completed)")

            # Save job result to database
            # CRITICAL: If this fails, we should NOT mark job as completed
            # The result will be available in Celery backend, but we need to ensure
            # it can be retrieved via the API endpoint fallback mechanism
            try:
                # Use serializable_job_result (not job_result) to ensure it's serializable
                save_job_result(job_id=job_id, result=serializable_job_result)
                logger.info(f"✅ Job {job_id} status and result saved to database")
            except Exception as save_error:
                logger.error(f"❌ Failed to save job result for {job_id}: {save_error}", exc_info=True)
                # Log detailed error but don't fail the job
                # The result is still being returned and stored in Celery backend
                # The API endpoint will attempt to retrieve it from Celery as fallback
                logger.warning(f"⚠️ Job {job_id} completed but result not saved. Result available in Celery backend.")
                
                # CRITICAL FIX: Try to save a minimal result with critical components
                # This ensures at least some data is available even if full result fails
                try:
                    minimal_result = {
                        "status": JobStatus.COMPLETED.value,
                        "workflow_state": {
                            "workflow_stage": "completed",
                            "errors": serializable_job_result.get("workflow_state", {}).get("errors", []) + [f"Database save failed: {str(save_error)[:200]}"],
                            "warnings": serializable_job_result.get("workflow_state", {}).get("warnings", []) + ["Full result save failed, minimal result saved"],
                            # Preserve critical components if they exist
                            "solver_result": serializable_job_result.get("workflow_state", {}).get("solver_result"),
                            "business_explanation": serializable_job_result.get("workflow_state", {}).get("business_explanation"),
                            "decision_traces": serializable_job_result.get("workflow_state", {}).get("decision_traces"),
                            "decision_traces_text": serializable_job_result.get("workflow_state", {}).get("decision_traces_text"),
                        },
                        "summary": serializable_job_result.get("summary", {}),
                        "_minimal_result": True
                    }
                    save_job_result(job_id=job_id, result=minimal_result)
                    logger.info(f"✅ Saved minimal result for job {job_id} as fallback")
                except Exception as minimal_save_error:
                    logger.error(f"❌ Failed to save even minimal result: {minimal_save_error}")
        except Exception as db_error:
            logger.error(f"❌ Failed to update job {job_id} in database: {db_error}", exc_info=True)
            # Don't fail the entire job if database update fails
            # The result is still being returned and stored in Celery backend

        # Decision Trace Collection (Phase 4: Casevo Simulation Integration)
        # Automatically collect traces from completed workflows for simulation
        try:
            from dcisionai_workflow.tools.simulation.trace_collector import TraceCollector
            
            logger.info(f"🔄 Starting trace collection for job {job_id}")
            logger.debug(f"   Workflow result keys: {list(workflow_result.keys()) if isinstance(workflow_result, dict) else 'Not a dict'}")
            
            trace_collector = TraceCollector()
            
            # Collect trace from workflow state
            trace = trace_collector.collect_trace_from_job(
                job_id=job_id,
                workflow_state=workflow_result,
                job_metadata={
                    'user_query': user_query,
                    'use_case': use_case,
                    'session_id': session_id
                }
            )
            
            if trace:
                logger.info(f"✅ Decision trace collected for job {job_id}")
                logger.info(f"   Problem Type: {trace.problem_signature.problem_type}")
                logger.info(f"   Domain: {trace.problem_signature.domain_context}")
                logger.info(f"   Trajectory Steps: {len(trace.trajectory)}")
                logger.info(f"   Decisions: {len(trace.decisions)}")
                logger.info(f"   Decision Variables: {len(trace.problem_signature.entity_structure.get('decision_variables', []))}")
                logger.info(f"   Constraints: {len(trace.problem_signature.constraint_patterns)}")
            else:
                logger.warning(f"⚠️ Failed to collect trace for job {job_id} - trace_collector returned None")
        except ImportError as import_error:
            logger.error(f"❌ Trace collection import failed for job {job_id}: {import_error}")
            logger.debug(f"Import error details: {import_error}", exc_info=True)
        except Exception as trace_error:
            # Don't fail the job if trace collection fails
            logger.error(f"❌ Trace collection failed for job {job_id}: {trace_error}")
            logger.error(f"   Error type: {type(trace_error).__name__}")
            logger.error(f"   Error message: {str(trace_error)}")
            logger.debug(f"Trace collection error details: {trace_error}", exc_info=True)

        # Training Data Collection (Phase 1: ADR-040)
        # Opt-in, disabled by default - does not affect workflow execution
        try:
            enable_training_collection = os.getenv("ENABLE_TRAINING_DATA_COLLECTION", "false").lower() == "true"
            
            if enable_training_collection:
                from dcisionai_workflow.training import TrainingDataExtractor, TrainingDataStorage
                
                extractor = TrainingDataExtractor()
                # CRITICAL: Use workflow_state_with_thinking which includes thinking_history
                # This ensures all 7 thinking steps are captured for training
                # ADR-043: Pass job_id for decision trace extraction (will be removed during anonymization)
                training_record = extractor.extract_training_data(
                    workflow_state=workflow_state_with_thinking,  # Includes thinking_history
                    job_result=job_result,
                    enable_training_collection=True,
                    job_id=job_id  # Pass job_id for decision trace extraction (ADR-043)
                )
                
                if training_record:
                    storage = TrainingDataStorage()
                    storage.save_training_record(training_record)
                    logger.info(f"✅ Training data collected for job {job_id}: quality_score={training_record.get('quality_score', 0):.2f}")
                else:
                    logger.debug(f"Training data not collected for job {job_id}: quality_score below threshold or extraction failed")
            else:
                logger.debug(f"Training data collection disabled for job {job_id}")
                
        except Exception as training_error:
            logger.warning(f"⚠️ Training data collection failed for job {job_id}: {training_error}")
            # Don't fail the workflow if training data collection fails
            # This is a non-critical operation

        # CRITICAL FIX: Ensure job_result is fully serializable before returning
        # Celery uses msgpack to serialize return values, so we need to ensure
        # all objects are JSON-serializable (msgpack-compatible)
        try:
            # Double-check serialization - recursively serialize job_result
            serializable_job_result = make_serializable(job_result)
            logger.debug(f"✅ Verified job_result is serializable for job {job_id}")
        except Exception as serialize_error:
            logger.error(f"❌ Failed to serialize job_result for job {job_id}: {serialize_error}")
            # Fallback: create minimal serializable result
            serializable_job_result = {
                "status": JobStatus.COMPLETED.value,
                "workflow_state": serializable_workflow_state,
                "llm_metrics": llm_metrics,
                "timing_metrics": timing_metrics,
                "mcp_resources": job_result.get("mcp_resources", {}),
                "summary": job_result.get("summary", {}),
            }

        # CRITICAL FIX: Publish completion message BEFORE returning
        # This ensures WebSocket clients receive completion notification immediately
        # The on_success callback also publishes, but this ensures it happens synchronously
        completion_update = {
            "type": "completed",
            "job_id": job_id,
            "status": JobStatus.COMPLETED.value,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "result": serializable_job_result,  # Use serialized result
        }
        publish_job_update(job_id, completion_update)
        logger.info(f"✅ Published completion message for job {job_id}")

        # Final check: ensure return value is JSON serializable (Celery uses JSON serializer)
        # Also test with msgpack since LangGraph uses it for checkpointing
        def json_default_handler(obj):
            """Default handler for JSON to catch any non-serializable objects."""
            if is_callable_object(obj):
                obj_type = type(obj).__name__
                logger.warning(f"⚠️ JSON default handler caught callable at final check: {obj_type}")
                return {"_type": "function", "_message": f"{obj_type} (filtered by JSON default)"}
            # For other non-serializable types, convert to string
            try:
                return str(obj)
            except:
                return {"_type": "non_serializable", "_message": "Object could not be serialized"}
        
        def msgpack_default_handler(obj):
            """Default handler for msgpack to catch any non-serializable objects."""
            if is_callable_object(obj):
                obj_type = type(obj).__name__
                logger.warning(f"⚠️ Msgpack default handler caught callable: {obj_type}")
                return {"_type": "function", "_message": f"{obj_type} (filtered by msgpack default)"}
            # For other non-serializable types, convert to string
            try:
                return str(obj)
            except:
                return {"_type": "non_serializable", "_message": "Object could not be serialized"}
        
        # Test with both JSON (Celery) and msgpack (LangGraph checkpointing)
        serialization_failed = False
        error_msg = None
        
        # Test JSON serialization (what Celery actually uses)
        try:
            import json
            json.dumps(serializable_job_result, default=json_default_handler)
            logger.debug(f"✅ JSON serialization check passed for job {job_id}")
        except Exception as json_error:
            error_msg = str(json_error)
            logger.error(f"JSON serialization check failed: {error_msg}")
            serialization_failed = True
        
        # Also test msgpack (used by LangGraph checkpointing)
        try:
            import msgpack
            msgpack.packb(serializable_job_result, default=msgpack_default_handler, strict_types=False)
            logger.debug(f"✅ Msgpack serialization check passed for job {job_id}")
        except Exception as msgpack_error:
            error_msg = str(msgpack_error)
            logger.error(f"Msgpack serialization check failed: {error_msg}")
            serialization_failed = True
        
        if serialization_failed:
            # If error mentions function, do one more aggressive pass
            if error_msg and ('function' in error_msg.lower() or 'callable' in error_msg.lower()):
                logger.warning("Function detected in final check, doing aggressive cleanup...")
                # Recursively clean the result one more time with path tracking
                serializable_job_result = make_serializable(serializable_job_result, path="final_cleanup")
                
                # Try again with both serializers
                try:
                    import json
                    json.dumps(serializable_job_result, default=json_default_handler)
                    import msgpack
                    msgpack.packb(serializable_job_result, default=msgpack_default_handler, strict_types=False)
                    logger.info("✅ Aggressive cleanup successful")
                except Exception as retry_error:
                    logger.error(f"Aggressive cleanup also failed: {retry_error}")
                    # CRITICAL FIX: Preserve critical components even when serialization fails
                    # Extract solver_result, business_explanation, decision_traces from original
                    original_workflow_state = job_result.get("workflow_state", {})
                    preserved_components = {}
                    
                    # Preserve solver_result (critical for model deployment)
                    if 'solver_result' in original_workflow_state:
                        solver_result = original_workflow_state.get('solver_result')
                        if isinstance(solver_result, dict):
                            # Try to serialize just the solver_result
                            try:
                                import json
                                json.dumps(solver_result, default=str)
                                preserved_components['solver_result'] = solver_result
                                logger.info(f"✅ Preserved solver_result despite serialization failure")
                            except Exception as e:
                                logger.warning(f"⚠️ Could not preserve solver_result: {e}")
                    
                    # Preserve business_explanation (critical for user understanding)
                    if 'business_explanation' in original_workflow_state:
                        business_explanation = original_workflow_state.get('business_explanation')
                        if isinstance(business_explanation, str):
                            preserved_components['business_explanation'] = business_explanation
                            logger.info(f"✅ Preserved business_explanation despite serialization failure")
                    
                    # Preserve decision_traces (critical for decision tracking)
                    if 'decision_traces' in original_workflow_state:
                        decision_traces = original_workflow_state.get('decision_traces')
                        if isinstance(decision_traces, dict):
                            try:
                                import json
                                json.dumps(decision_traces, default=str)
                                preserved_components['decision_traces'] = decision_traces
                                logger.info(f"✅ Preserved decision_traces despite serialization failure")
                            except Exception as e:
                                logger.warning(f"⚠️ Could not preserve decision_traces: {e}")
                    
                    # Preserve decision_traces_text
                    if 'decision_traces_text' in original_workflow_state:
                        preserved_components['decision_traces_text'] = original_workflow_state.get('decision_traces_text')
                    
                    # Create result with preserved components
                    workflow_state_with_preserved = {
                        "workflow_stage": "completed",
                        "errors": serializable_job_result.get("workflow_state", {}).get("errors", []) + [f"Serialization error: {error_msg[:200]}"],
                        "warnings": serializable_job_result.get("workflow_state", {}).get("warnings", []) + ["Result serialization simplified due to non-serializable objects"],
                        **preserved_components  # Merge preserved components
                    }
                    
                    serializable_job_result = {
                        "status": JobStatus.COMPLETED.value,
                        "workflow_state": workflow_state_with_preserved,
                        "llm_metrics": job_result.get("llm_metrics", {}),
                        "timing_metrics": job_result.get("timing_metrics", {}),
                        "mcp_resources": job_result.get("mcp_resources", {}),
                        "summary": serializable_job_result.get("summary", {}),
                        "_serialization_simplified": True
                    }
                    logger.warning(f"Returning simplified result for job {job_id} with preserved critical components: {list(preserved_components.keys())}")
            else:
                # CRITICAL FIX: Preserve critical components for other errors too
                original_workflow_state = job_result.get("workflow_state", {})
                preserved_components = {}
                
                # Preserve solver_result
                if 'solver_result' in original_workflow_state:
                    solver_result = original_workflow_state.get('solver_result')
                    if isinstance(solver_result, dict):
                        try:
                            import json
                            json.dumps(solver_result, default=str)
                            preserved_components['solver_result'] = solver_result
                        except:
                            pass
                
                # Preserve business_explanation
                if 'business_explanation' in original_workflow_state:
                    business_explanation = original_workflow_state.get('business_explanation')
                    if isinstance(business_explanation, str):
                        preserved_components['business_explanation'] = business_explanation
                
                # Preserve decision_traces
                if 'decision_traces' in original_workflow_state:
                    decision_traces = original_workflow_state.get('decision_traces')
                    if isinstance(decision_traces, dict):
                        try:
                            import json
                            json.dumps(decision_traces, default=str)
                            preserved_components['decision_traces'] = decision_traces
                        except:
                            pass
                
                if 'decision_traces_text' in original_workflow_state:
                    preserved_components['decision_traces_text'] = original_workflow_state.get('decision_traces_text')
                
                workflow_state_with_preserved = {
                    "workflow_stage": "completed",
                    "errors": serializable_job_result.get("workflow_state", {}).get("errors", []),
                    "warnings": serializable_job_result.get("workflow_state", {}).get("warnings", []) + ["Result serialization simplified due to non-serializable objects"],
                    **preserved_components
                }
                
                serializable_job_result = {
                    "status": JobStatus.COMPLETED.value,
                    "workflow_state": workflow_state_with_preserved,
                    "llm_metrics": job_result.get("llm_metrics", {}),
                    "timing_metrics": job_result.get("timing_metrics", {}),
                    "mcp_resources": job_result.get("mcp_resources", {}),
                    "summary": serializable_job_result.get("summary", {}),
                    "_serialization_simplified": True
                }
                logger.warning(f"Returning simplified result for job {job_id} with preserved critical components: {list(preserved_components.keys())}")

        return serializable_job_result

    except SoftTimeLimitExceeded:
        logger.error(f"Job {job_id} exceeded time limit")
        
        # CRITICAL FIX: Signal metrics completion BEFORE updating status (only if metrics enabled)
        from dcisionai_mcp_server.config import MCPConfig
        if MCPConfig.ENABLE_LLM_METRICS:
            try:
                from dcisionai_workflow.shared.utils.metrics_publisher import publish_job_metrics_complete
                publish_job_metrics_complete(job_id, session_id)
                logger.debug(f"✅ Published metrics completion signal for timed-out job {job_id}")
            except Exception as metrics_signal_error:
                logger.warning(f"⚠️ Failed to publish metrics completion signal for timed-out job: {metrics_signal_error}")
        
        # CRITICAL FIX: Update database status BEFORE publishing to Redis
        from dcisionai_mcp_server.jobs.storage import update_job_status
        try:
            update_job_status(
                job_id=job_id,
                status=JobStatus.FAILED,
                completed_at=datetime.now(timezone.utc).isoformat(),
                error="Job exceeded time limit"
            )
            logger.info(f"✅ Job {job_id} status updated to FAILED (timeout) in database")
        except Exception as db_error:
            logger.error(f"❌ Failed to update job {job_id} status in database: {db_error}")
        
        # CRITICAL FIX: Publish timeout error message BEFORE raising
        timeout_update = {
            "type": "error",
            "job_id": job_id,
            "status": JobStatus.FAILED.value,
            "error": {
                "message": "Job exceeded time limit",
                "type": "SoftTimeLimitExceeded",
            },
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
        publish_job_update(job_id, timeout_update)
        logger.info(f"✅ Published timeout error message for job {job_id}")
        raise

    except TaskRevokedError:
        logger.error(f"Job {job_id} was cancelled")
        raise

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        logger.error(traceback.format_exc())

        # CRITICAL FIX: Signal metrics completion BEFORE publishing error
        # This ensures metrics aggregator doesn't block waiting for completion signal (only if metrics enabled)
        from dcisionai_mcp_server.config import MCPConfig
        if MCPConfig.ENABLE_LLM_METRICS:
            try:
                from dcisionai_workflow.shared.utils.metrics_publisher import publish_job_metrics_complete
                publish_job_metrics_complete(job_id, session_id)
                logger.debug(f"✅ Published metrics completion signal for failed job {job_id}")
            except Exception as metrics_signal_error:
                logger.warning(f"⚠️ Failed to publish metrics completion signal for failed job: {metrics_signal_error}")

        # CRITICAL FIX: Publish error message BEFORE retry/failure
        # This ensures WebSocket clients receive error notification immediately
        error_update = {
            "type": "error",
            "job_id": job_id,
            "status": JobStatus.FAILED.value,
            "error": {
                "message": str(e),
                "type": type(e).__name__,
            },
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
        publish_job_update(job_id, error_update)
        logger.info(f"✅ Published error message for job {job_id}")

        # Retry on recoverable errors
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying job {job_id} (attempt {self.request.retries + 1})")
            raise self.retry(exc=e)
        else:
            # Max retries exceeded, mark as failed
            raise


@celery_app.task(base=JobTask, bind=True, max_retries=3)
def cancel_job(self, job_id: str) -> Dict[str, str]:
    """
    Cancel a running job (cleanup task).

    This terminates the Celery task if running and publishes cancellation update.
    Note: Database status should already be updated by the API endpoint.

    Args:
        job_id: Job identifier to cancel

    Returns:
        Status dictionary
    """
    logger.info(f"Cancel cleanup task for job {job_id}")

    try:
        # Revoke the task (terminate if running)
        celery_app.control.revoke(job_id, terminate=True, signal="SIGKILL")

        # Ensure database status is cancelled (in case API update failed)
        try:
            from dcisionai_mcp_server.jobs.storage import update_job_status, get_job
            update_job_status(
                job_id=job_id,
                status=JobStatus.CANCELLED
            )
            logger.info(f"✅ Job status confirmed as cancelled: {job_id}")
        except Exception as db_error:
            logger.warning(f"⚠️ Failed to update job status in database: {db_error}")

        # CRITICAL FIX: Signal metrics completion so metrics aggregator doesn't block (only if metrics enabled)
        from dcisionai_mcp_server.config import MCPConfig
        if MCPConfig.ENABLE_LLM_METRICS:
            try:
                from dcisionai_workflow.shared.utils.metrics_publisher import publish_job_metrics_complete
                job = get_job(job_id)
                session_id = job.get("session_id", "unknown") if job else "unknown"
                publish_job_metrics_complete(job_id, session_id)
                logger.debug(f"✅ Published metrics completion signal for cancelled job {job_id}")
            except Exception as metrics_signal_error:
                logger.warning(f"⚠️ Failed to publish metrics completion signal for cancelled job: {metrics_signal_error}")

        # Publish cancellation update via Redis
        cancel_update = {
            "job_id": job_id,
            "status": JobStatus.CANCELLED.value,
            "cancelled_at": datetime.now(timezone.utc).isoformat(),
        }
        publish_job_update(job_id, cancel_update)

        return {"status": "cancelled", "job_id": job_id}

    except Exception as e:
        logger.error(f"Failed to cancel job {job_id}: {e}")
        raise


# ========== TASK INSPECTION UTILITIES ==========

def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Get current status of a Celery task.

    This is used by the polling API to check job progress.

    Args:
        task_id: Celery task identifier (same as job_id)

    Returns:
        Task status dictionary with state and progress
    """
    from celery.result import AsyncResult

    result = AsyncResult(task_id, app=celery_app)

    status = {
        "task_id": task_id,
        "state": result.state,
        "ready": result.ready(),
        "successful": result.successful() if result.ready() else None,
        "failed": result.failed() if result.ready() else None,
    }

    # Include progress metadata if available
    if result.state == "PROGRESS" and result.info:
        status["progress"] = result.info.get("progress", {})

    # Include result if completed
    if result.ready() and result.successful():
        status["result"] = result.result

    # Include error if failed
    if result.failed():
        status["error"] = str(result.info)

    return status


def get_active_jobs() -> Dict[str, Any]:
    """
    Get list of currently active jobs.

    Returns:
        Dictionary with active, scheduled, and reserved tasks
    """
    inspect = celery_app.control.inspect()

    active = inspect.active() or {}
    scheduled = inspect.scheduled() or {}
    reserved = inspect.reserved() or {}

    return {
        "active": active,
        "scheduled": scheduled,
        "reserved": reserved,
    }


# ========== PERIODIC TASKS (OPTIONAL) ==========

@celery_app.task(name="cleanup_old_jobs")
def cleanup_old_jobs(days: int = 7) -> Dict[str, int]:
    """
    Clean up old job records from database and Redis cache.

    This task runs periodically to prevent unbounded storage growth.

    Args:
        days: Number of days to retain job records

    Returns:
        Cleanup statistics
    """
    logger.info(f"Cleaning up jobs older than {days} days")

    # TODO: Implement when storage layer is ready
    # from dcisionai_mcp_server.jobs.storage import cleanup_old_jobs
    # return cleanup_old_jobs(days)

    return {"deleted": 0, "message": "Cleanup not yet implemented"}


# ========== HEALTH CHECK ==========

@celery_app.task(name="health_check")
def health_check() -> Dict[str, str]:
    """
    Health check task to verify Celery workers are running.

    This can be called from the /health endpoint.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "worker": "celery",
    }


if __name__ == "__main__":
    # For local testing
    logger.info("Starting Celery worker...")
    celery_app.worker_main(["worker", "--loglevel=info", "--concurrency=2"])
