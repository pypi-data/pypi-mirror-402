"""
WebSocket Handler for Real-Time Job Progress Streaming

Provides WebSocket endpoint for streaming job progress updates in real-time.

Architecture:
- Subscribes to Redis pub/sub channel: job_updates:{job_id}
- Streams progress updates as they happen
- Sends completion/failure notifications
- Reuses existing WebSocket transport patterns

Following MCP Protocol:
- WebSocket endpoint: /api/jobs/{job_id}/stream
- Message format compatible with existing MCP WebSocket transport
- Real-time updates for optimal UX
"""

import json
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect, HTTPException
from redis import Redis

from dcisionai_mcp_server.jobs.storage import get_job
from dcisionai_mcp_server.jobs.schemas import JobStatus

logger = logging.getLogger(__name__)

# Redis client for pub/sub
redis_client: Optional[Redis] = None


def get_redis_client() -> Redis:
    """
    Get Redis client for pub/sub.

    Returns:
        Redis client instance
    """
    global redis_client
    if redis_client is None:
        import os
        # Railway provides both REDIS_URL (internal) and REDIS_PUBLIC_URL (external)
        # Use REDIS_PUBLIC_URL if available (for external access), otherwise fall back to REDIS_URL
        redis_url = os.getenv("REDIS_PUBLIC_URL") or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        redis_client = Redis.from_url(redis_url, decode_responses=True)
        # Test connection
        try:
            redis_client.ping()
            logger.info(f"✅ Redis WebSocket client initialized: {redis_url[:50]}...")
        except Exception as e:
            logger.warning(f"⚠️ Redis WebSocket client connection test failed: {e}")
            logger.warning(f"   REDIS_URL: {redis_url[:50] if redis_url else 'Not set'}...")
            logger.warning(f"   REDIS_PUBLIC_URL: {'Set' if os.getenv('REDIS_PUBLIC_URL') else 'Not set'}")
    return redis_client


async def stream_job_progress(websocket: WebSocket, job_id: str):
    """
    Stream job progress updates via WebSocket.

    This endpoint provides real-time progress updates for a running job.
    It subscribes to the Redis pub/sub channel for the job and forwards
    all updates to the WebSocket client.

    Message Types Sent:
    - connection_ack: Initial connection acknowledgment
    - job_status: Current job status
    - progress_update: Progress updates during execution
    - job_completed: Final completion notification
    - job_failed: Failure notification
    - error: Error messages

    Args:
        websocket: FastAPI WebSocket connection
        job_id: Job identifier

    Raises:
        HTTPException: If job not found
    """
    # Accept WebSocket connection
    await websocket.accept()
    logger.info(f"WebSocket connected for job: {job_id}")

    try:
        # Verify job exists
        job_record = get_job(job_id)
        if not job_record:
            await websocket.send_json({
                "type": "error",
                "error": f"Job not found: {job_id}",
                "timestamp": datetime.utcnow().isoformat(),
            })
            await websocket.close(code=1008, reason="Job not found")
            return

        # Send connection acknowledgment
        await websocket.send_json({
            "type": "connection_ack",
            "job_id": job_id,
            "timestamp": datetime.utcnow().isoformat(),
        })

        # Send current job status
        progress = None
        if job_record["progress"]:
            progress = json.loads(job_record["progress"])

        await websocket.send_json({
            "type": "job_status",
            "job_id": job_id,
            "status": job_record["status"],
            "progress": progress,
            "timestamp": datetime.utcnow().isoformat(),
        })

        # If job is already completed/failed, send final notification and close
        if job_record["status"] in [JobStatus.COMPLETED.value, JobStatus.FAILED.value]:
            if job_record["status"] == JobStatus.COMPLETED.value:
                result = json.loads(job_record["result"]) if job_record["result"] else None
                await websocket.send_json({
                    "type": "job_completed",
                    "job_id": job_id,
                    "result": result,
                    "completed_at": job_record["completed_at"],
                    "timestamp": datetime.utcnow().isoformat(),
                })
            else:
                await websocket.send_json({
                    "type": "job_failed",
                    "job_id": job_id,
                    "error": job_record["error"],
                    "completed_at": job_record["completed_at"],
                    "timestamp": datetime.utcnow().isoformat(),
                })

            logger.info(f"Job {job_id} already {job_record['status']}, closing WebSocket")
            await websocket.close(code=1000, reason="Job already completed")
            return

        # Subscribe to Redis pub/sub channel for job updates
        redis = get_redis_client()
        pubsub = redis.pubsub()
        channel_name = f"job_updates:{job_id}"
        pubsub.subscribe(channel_name)

        logger.info(f"Subscribed to Redis channel: {channel_name}")

        # Stream updates from Redis pub/sub
        try:
            # Create a task to listen for pub/sub messages
            async def listen_for_updates():
                """Listen for Redis pub/sub messages and forward to WebSocket"""
                for message in pubsub.listen():
                    if message["type"] == "message":
                        try:
                            # Parse update from Redis
                            update = json.loads(message["data"])

                            # Determine message type based on status
                            status = update.get("status")
                            message_type = "progress_update"

                            if status == JobStatus.COMPLETED.value:
                                message_type = "job_completed"
                                # Fetch final result from storage
                                final_job = get_job(job_id)
                                if final_job and final_job["result"]:
                                    update["result"] = json.loads(final_job["result"])
                            elif status == JobStatus.FAILED.value:
                                message_type = "job_failed"

                            # Add message type and timestamp
                            update["type"] = message_type
                            update["timestamp"] = datetime.utcnow().isoformat()

                            # Send to WebSocket client
                            await websocket.send_json(update)

                            logger.debug(f"Sent {message_type} to WebSocket for job {job_id}")

                            # If job is completed/failed, close connection
                            if message_type in ["job_completed", "job_failed"]:
                                logger.info(f"Job {job_id} finished, closing WebSocket")
                                await websocket.close(code=1000, reason="Job completed")
                                break

                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse Redis message: {e}")
                            await websocket.send_json({
                                "type": "error",
                                "error": "Failed to parse update",
                                "timestamp": datetime.utcnow().isoformat(),
                            })
                        except Exception as e:
                            logger.error(f"Error processing update: {e}", exc_info=True)
                            await websocket.send_json({
                                "type": "error",
                                "error": str(e),
                                "timestamp": datetime.utcnow().isoformat(),
                            })

            # Run listener in background
            listener_task = asyncio.create_task(listen_for_updates())

            # Keep connection alive and handle client disconnects
            try:
                while True:
                    # Wait for messages from client (heartbeat or close)
                    data = await websocket.receive_text()

                    # Handle ping/pong for keepalive
                    if data == "ping":
                        await websocket.send_text("pong")

            except WebSocketDisconnect:
                logger.info(f"WebSocket client disconnected for job {job_id}")
                listener_task.cancel()

        finally:
            # Cleanup: unsubscribe from Redis
            pubsub.unsubscribe(channel_name)
            pubsub.close()
            logger.info(f"Unsubscribed from Redis channel: {channel_name}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected during setup for job {job_id}")

    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            })
            await websocket.close(code=1011, reason="Internal server error")
        except Exception:
            pass  # Connection may already be closed


async def handle_job_stream_websocket(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint handler for job progress streaming.

    This is the main entry point for the WebSocket endpoint.
    It delegates to stream_job_progress for the actual streaming logic.

    Usage:
        @app.websocket("/api/jobs/{job_id}/stream")
        async def job_stream_endpoint(websocket: WebSocket, job_id: str):
            await handle_job_stream_websocket(websocket, job_id)

    Args:
        websocket: FastAPI WebSocket connection
        job_id: Job identifier
    """
    await stream_job_progress(websocket, job_id)


# Message format documentation
"""
WebSocket Message Formats:

1. Connection Acknowledgment (sent immediately after connection):
{
    "type": "connection_ack",
    "job_id": "uuid",
    "timestamp": "2025-12-08T10:30:00.000Z"
}

2. Job Status (sent after connection_ack):
{
    "type": "job_status",
    "job_id": "uuid",
    "status": "running",
    "progress": {
        "current_step": "generate_data",
        "progress_percentage": 45,
        "step_details": {...},
        "updated_at": "2025-12-08T10:30:00.000Z"
    },
    "timestamp": "2025-12-08T10:30:00.000Z"
}

3. Progress Update (sent during job execution):
{
    "type": "progress_update",
    "job_id": "uuid",
    "status": "running",
    "progress": {
        "current_step": "solve_optimization",
        "progress_percentage": 75,
        "step_details": {...},
        "updated_at": "2025-12-08T10:35:00.000Z"
    },
    "timestamp": "2025-12-08T10:35:00.000Z"
}

4. Job Completed (sent when job finishes successfully):
{
    "type": "job_completed",
    "job_id": "uuid",
    "result": {
        "workflow_state": {...},
        "intent": {...},
        "data_pack": {...},
        "solver_output": {...},
        "explanation": {...}
    },
    "completed_at": "2025-12-08T10:40:00.000Z",
    "timestamp": "2025-12-08T10:40:00.000Z"
}

5. Job Failed (sent when job fails):
{
    "type": "job_failed",
    "job_id": "uuid",
    "error": "Error message or stack trace",
    "completed_at": "2025-12-08T10:40:00.000Z",
    "timestamp": "2025-12-08T10:40:00.000Z"
}

6. Error (sent on error):
{
    "type": "error",
    "error": "Error message",
    "timestamp": "2025-12-08T10:30:00.000Z"
}

Client Heartbeat:
- Client can send "ping" text message
- Server responds with "pong" text message
- Keeps connection alive
"""


if __name__ == "__main__":
    # Test WebSocket handler
    print("WebSocket handler for job progress streaming")
    print("\nSupported message types:")
    print("  - connection_ack: Connection established")
    print("  - job_status: Current job status")
    print("  - progress_update: Progress updates during execution")
    print("  - job_completed: Job completed successfully")
    print("  - job_failed: Job failed with error")
    print("  - error: Error messages")
    print("\nUsage:")
    print("  WebSocket endpoint: ws://localhost:8000/api/jobs/{job_id}/stream")
    print("  Heartbeat: Send 'ping' to receive 'pong'")
