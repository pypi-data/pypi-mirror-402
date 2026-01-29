"""
LLM Metrics Aggregator Task

Separate Celery task that aggregates LLM metrics from Redis pub/sub
and stores them independently of workflow execution.

This prevents serialization issues and allows metrics to be tracked
asynchronously without affecting workflow performance.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from dcisionai_mcp_server.jobs.tasks import celery_app
from dcisionai_mcp_server.jobs.storage import update_job_metrics
from dcisionai_mcp_server.jobs.schemas import LLMMetrics

logger = logging.getLogger(__name__)

# Redis configuration
# Railway provides both REDIS_URL (internal) and REDIS_PUBLIC_URL (external)
# Use REDIS_PUBLIC_URL if available (for external access), otherwise fall back to REDIS_URL
REDIS_URL = os.getenv("REDIS_PUBLIC_URL") or os.getenv("REDIS_URL", "redis://localhost:6379/0")


@celery_app.task(
    name="aggregate_llm_metrics",
    bind=True,
    soft_time_limit=1800,  # 30 minutes soft timeout (reduced to prevent blocking)
    time_limit=1900,  # 31 minutes hard timeout
    max_retries=0,  # Don't retry - metrics are best-effort
    ignore_result=True,  # Don't store result - reduces Redis memory
)
def aggregate_llm_metrics(self, job_id: str, session_id: str) -> Dict[str, Any]:
    """
    Aggregate LLM metrics for a job by subscribing to Redis pub/sub.

    This task:
    1. Subscribes to llm_metrics:{job_id} channel
    2. Collects all metric events until completion signal
    3. Aggregates metrics by step and model
    4. Stores aggregated metrics in database

    Args:
        job_id: Job identifier
        session_id: Session identifier

    Returns:
        Aggregated metrics dictionary
    """
    try:
        import redis
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        pubsub = redis_client.pubsub()
        
        channel = f"llm_metrics:{job_id}"
        pubsub.subscribe(channel)
        logger.info(f"[MetricsAggregator] Subscribed to {channel} for job {job_id}")

        # Initialize aggregation structures
        calls: list[Dict[str, Any]] = []
        by_step: Dict[str, Dict[str, Any]] = {}
        by_model: Dict[str, Dict[str, Any]] = {}

        # Collect metrics until completion signal
        metrics_complete = False
        timeout_seconds = 1800  # 30 minutes max (reduced from 1 hour to prevent blocking)
        start_time = datetime.utcnow()
        status_check_interval = 10  # Check job status every 10 seconds (more frequent)
        last_status_check = start_time
        message_timeout = 5  # Timeout for pubsub.get_message() in seconds

        # Use non-blocking pubsub.get_message() instead of blocking listen()
        # This allows us to check timeouts and job status more frequently
        while True:
            # Check timeout first
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            if elapsed > timeout_seconds:
                logger.warning(f"[MetricsAggregator] Timeout ({timeout_seconds}s) waiting for metrics completion for job {job_id}")
                break

            # Check job status frequently (every 10 seconds)
            check_elapsed = (datetime.utcnow() - last_status_check).total_seconds()
            if check_elapsed >= status_check_interval:
                last_status_check = datetime.utcnow()
                try:
                    from dcisionai_mcp_server.jobs.storage import get_job
                    from dcisionai_mcp_server.jobs.schemas import JobStatus
                    job = get_job(job_id)
                    if job:
                        job_status = job.get('status')
                        # Exit early if job is cancelled, failed, or completed
                        if job_status in [JobStatus.CANCELLED.value, JobStatus.FAILED.value, JobStatus.COMPLETED.value]:
                            logger.info(f"[MetricsAggregator] Job {job_id} is {job_status}, exiting metrics aggregation early")
                            # Send completion signal to unblock any waiting listeners
                            try:
                                redis_client.publish(channel, json.dumps({"type": "metrics_complete", "reason": f"job_{job_status}"}))
                            except:
                                pass
                            metrics_complete = True
                            break
                except Exception as status_check_error:
                    logger.debug(f"[MetricsAggregator] Failed to check job status: {status_check_error}")
                    # Continue - don't fail metrics aggregation due to status check errors

            # Use non-blocking get_message() with timeout instead of blocking listen()
            try:
                message = pubsub.get_message(timeout=message_timeout)
                if message is None:
                    # No message received, continue loop to check timeout/status
                    continue
            except Exception as get_msg_error:
                logger.debug(f"[MetricsAggregator] Error getting message: {get_msg_error}")
                # Continue loop - check timeout/status
                continue

            # Process message if received
            if message["type"] == "message":
                try:
                    event = json.loads(message["data"])
                    event_type = event.get("type")

                    if event_type == "llm_metric":
                        # Aggregate metric
                        calls.append(event)
                        
                        # Update by_step aggregation
                        step_name = event.get("step_name")
                        if step_name:
                            if step_name not in by_step:
                                by_step[step_name] = {
                                    "calls": 0,
                                    "tokens_in": 0,
                                    "tokens_out": 0,
                                    "cost_usd": 0.0,
                                    "duration_seconds": 0.0,
                                }
                            by_step[step_name]["calls"] += 1
                            by_step[step_name]["tokens_in"] += event.get("tokens_in", 0)
                            by_step[step_name]["tokens_out"] += event.get("tokens_out", 0)
                            by_step[step_name]["cost_usd"] += event.get("cost_usd", 0.0)
                            if event.get("duration_seconds"):
                                by_step[step_name]["duration_seconds"] += event.get("duration_seconds", 0.0)

                        # Update by_model aggregation
                        model = event.get("model")
                        if model:
                            if model not in by_model:
                                by_model[model] = {
                                    "calls": 0,
                                    "tokens_in": 0,
                                    "tokens_out": 0,
                                    "cost_usd": 0.0,
                                }
                            by_model[model]["calls"] += 1
                            by_model[model]["tokens_in"] += event.get("tokens_in", 0)
                            by_model[model]["tokens_out"] += event.get("tokens_out", 0)
                            by_model[model]["cost_usd"] += event.get("cost_usd", 0.0)

                    elif event_type == "metrics_complete":
                        metrics_complete = True
                        logger.info(f"[MetricsAggregator] Received completion signal for job {job_id}")
                        break

                except json.JSONDecodeError as e:
                    logger.error(f"[MetricsAggregator] Failed to decode metric event: {e}")
                    continue
                except Exception as e:
                    logger.error(f"[MetricsAggregator] Error processing metric event: {e}", exc_info=True)
                    continue
            
            # Exit loop if metrics are complete (from status check or message)
            if metrics_complete:
                break

        # Unsubscribe and close
        pubsub.unsubscribe(channel)
        pubsub.close()

        # Calculate totals
        total_calls = len(calls)
        total_tokens_in = sum(c.get("tokens_in", 0) for c in calls)
        total_tokens_out = sum(c.get("tokens_out", 0) for c in calls)
        total_cost_usd = round(sum(c.get("cost_usd", 0.0) for c in calls), 4)

        # Build aggregated metrics
        aggregated_metrics: LLMMetrics = {
            "total_calls": total_calls,
            "total_tokens_in": total_tokens_in,
            "total_tokens_out": total_tokens_out,
            "total_cost_usd": total_cost_usd,
            "by_step": by_step,
            "by_model": by_model,
        }

        # Store metrics in database
        try:
            update_job_metrics(job_id=job_id, metrics=aggregated_metrics)
            logger.info(
                f"[MetricsAggregator] ✅ Aggregated metrics for job {job_id}: "
                f"{total_calls} calls, {total_tokens_in:,} in, {total_tokens_out:,} out, "
                f"${total_cost_usd:.4f} USD"
            )
        except Exception as db_error:
            logger.error(f"[MetricsAggregator] ❌ Failed to store metrics for job {job_id}: {db_error}")

        return aggregated_metrics

    except Exception as e:
        logger.error(f"[MetricsAggregator] Failed to aggregate metrics for job {job_id}: {e}", exc_info=True)
        return {}

