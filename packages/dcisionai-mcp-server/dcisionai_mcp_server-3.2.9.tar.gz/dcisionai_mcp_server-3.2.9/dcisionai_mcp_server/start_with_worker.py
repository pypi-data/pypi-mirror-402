"""
Railway startup script that runs both FastAPI server and Celery worker.

This script starts:
1. FastAPI server (main process)
2. Celery worker (background process)

Both processes share the same environment and can access Redis/Supabase.
"""

import os
import sys
import subprocess
import signal
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=os.getenv("DCISIONAI_LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Track child processes for cleanup
child_processes = []


def signal_handler(sig, frame):
    """Handle shutdown signals gracefully."""
    logger.info("Received shutdown signal, terminating child processes...")
    for proc in child_processes:
        try:
            proc.terminate()
        except Exception as e:
            logger.error(f"Error terminating process {proc.pid}: {e}")
    
    # Wait for processes to terminate
    for proc in child_processes:
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            logger.warning(f"Process {proc.pid} did not terminate, killing...")
            proc.kill()
    
    sys.exit(0)


def main():
    """Start both FastAPI server and Celery worker."""
    logger.info("=" * 60)
    logger.info("🚀 Starting DcisionAI MCP Server with Celery Worker")
    logger.info("=" * 60)
    
    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Get project root
    project_root = Path(__file__).parent.parent
    
    # Verify Redis URL is set (warn but don't exit - server can still start)
    # Railway provides both REDIS_URL (internal) and REDIS_PUBLIC_URL (external)
    # Use REDIS_PUBLIC_URL if available (for external access), otherwise fall back to REDIS_URL
    redis_url = os.getenv("REDIS_PUBLIC_URL") or os.getenv("REDIS_URL")
    celery_proc = None
    
    if not redis_url:
        logger.warning("⚠️ REDIS_URL and REDIS_PUBLIC_URL environment variables not set!")
        logger.warning("   Celery worker will not start. Set REDIS_URL or REDIS_PUBLIC_URL in Railway Dashboard → Variables")
        logger.warning("   Or link a Redis service in Railway")
        logger.warning("   Server will start but async jobs will fail")
    else:
        logger.info(f"✅ Redis URL configured: {redis_url[:50]}...")
        if os.getenv("REDIS_PUBLIC_URL"):
            logger.info("   Using REDIS_PUBLIC_URL (external access)")
        else:
            logger.info("   Using REDIS_URL (internal)")
        
        # Verify Supabase credentials (warn but don't exit)
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_API_KEY")
        if not supabase_url or not supabase_key:
            logger.warning("⚠️ SUPABASE_URL or SUPABASE_API_KEY not set!")
            logger.warning("   Set them in Railway Dashboard → Variables")
            logger.warning("   Server will start but job storage will fail")
        else:
            logger.info(f"✅ Supabase URL configured: {supabase_url[:30]}...")
        
        # Start Celery worker in background (only if Redis is configured)
        logger.info("Starting Celery worker...")
        
        # Set PYTHONPATH to ensure imports work
        env = os.environ.copy()
        project_root_str = str(project_root)
        if 'PYTHONPATH' in env:
            env['PYTHONPATH'] = f"{project_root_str}:{env['PYTHONPATH']}"
        else:
            env['PYTHONPATH'] = project_root_str
        
        celery_cmd = [
            sys.executable, "-m", "celery",
            "-A", "dcisionai_mcp_server.jobs.tasks",
            "worker",
            "--loglevel=info",
            "--concurrency=4",
            "--hostname=worker@%h"
        ]
        
        # On Linux (Railway), use prefork pool (default)
        # On macOS, use threads pool (fork-safe)
        import platform
        if platform.system() == "Darwin":
            celery_cmd.extend(["--pool=threads", "--concurrency=4"])
            logger.info("Using threads pool (macOS)")
        else:
            logger.info("Using prefork pool (Linux)")
        
        try:
            celery_proc = subprocess.Popen(
                celery_cmd,
                cwd=str(project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
                bufsize=1,
                universal_newlines=True
            )
            child_processes.append(celery_proc)
            logger.info(f"✅ Celery worker started (PID: {celery_proc.pid})")
            
            # Start a thread to log Celery output
            import threading
            def log_celery_output():
                for line in iter(celery_proc.stdout.readline, ''):
                    if line:
                        logger.info(f"[Celery] {line.rstrip()}")
                celery_proc.stdout.close()
            
            celery_log_thread = threading.Thread(target=log_celery_output, daemon=True)
            celery_log_thread.start()
            
            # Wait a moment for Celery to initialize
            import time
            time.sleep(2)
            
            # Check if Celery worker is still running (warn but don't exit)
            if celery_proc.poll() is not None:
                logger.warning(f"⚠️ Celery worker exited immediately (exit code: {celery_proc.returncode})")
                logger.warning("   Server will continue but async jobs will fail")
                celery_proc = None  # Mark as not running
            else:
                logger.info("✅ Celery worker is running")
                
        except Exception as e:
            logger.warning(f"⚠️ Failed to start Celery worker: {e}")
            logger.warning("   Server will continue but async jobs will fail")
            celery_proc = None
    
    # Start FastAPI server (main process - blocks)
    logger.info("Starting FastAPI server...")
    print("🚀 Starting FastAPI server...", file=sys.stdout)
    sys.stdout.flush()
    try:
        # Import and run the start script
        sys.path.insert(0, str(project_root))
        print(f"✅ Project root added to sys.path: {project_root}", file=sys.stdout)
        print(f"✅ PYTHONPATH: {os.environ.get('PYTHONPATH', 'not set')}", file=sys.stdout)
        sys.stdout.flush()
        
        # CRITICAL: Use module import for proper package structure
        import importlib.util
        start_mcp_server_path = project_root / "dcisionai_mcp_server" / "start_mcp_server.py"
        if not start_mcp_server_path.exists():
            error_msg = f"❌ start_mcp_server.py not found at {start_mcp_server_path}"
            logger.error(error_msg)
            print(error_msg, file=sys.stderr)
            sys.exit(1)
        
        print(f"✅ Found start_mcp_server.py at {start_mcp_server_path}", file=sys.stdout)
        sys.stdout.flush()
        
        # Try module import first
        try:
            from dcisionai_mcp_server.start_mcp_server import main as start_server
            print("✅ Successfully imported start_mcp_server module", file=sys.stdout)
            sys.stdout.flush()
        except ImportError as import_err:
            error_msg = f"❌ Failed to import start_mcp_server: {import_err}"
            logger.error(error_msg, exc_info=True)
            print(error_msg, file=sys.stderr)
            import traceback
            print(traceback.format_exc(), file=sys.stderr)
            sys.exit(1)
        
        start_server()
    except KeyboardInterrupt:
        logger.info("FastAPI server stopped by user")
    except Exception as e:
        logger.error(f"❌ FastAPI server failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        # Cleanup: terminate Celery worker (if it was started)
        if celery_proc:
            logger.info("Terminating Celery worker...")
            try:
                celery_proc.terminate()
                celery_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("Celery worker did not terminate, killing...")
                celery_proc.kill()
            except Exception as e:
                logger.error(f"Error terminating Celery worker: {e}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
        signal_handler(signal.SIGINT, None)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

