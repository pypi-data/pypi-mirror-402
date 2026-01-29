"""
Railway start script for DcisionAI MCP Server 2.0

This script initializes logging and starts the FastMCP server
with Railway-specific configuration (PORT, HOST, etc.)
"""

import os
import sys
import logging
from pathlib import Path

# Load environment variables from .env.staging if available
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env.staging'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass  # dotenv not available, use system env vars
except Exception:
    pass  # Ignore errors loading .env.staging

# Configure logging - ensure it goes to stdout for Railway
# Use single handler to avoid duplicate logs
# CRITICAL: Also log to stderr for Railway error visibility
logging.basicConfig(
    level=os.getenv("DCISIONAI_LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # stdout for normal logs
        logging.StreamHandler(sys.stderr)    # stderr for errors (Railway highlights these)
    ],
    force=True  # Override any existing configuration
)
logger = logging.getLogger(__name__)

# CRITICAL: Redirect uncaught exceptions to stderr for Railway visibility
def handle_exception(exc_type, exc_value, exc_traceback):
    """Handle uncaught exceptions - log to stderr for Railway"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    print(f"❌ FATAL ERROR: {exc_type.__name__}: {exc_value}", file=sys.stderr)
    import traceback
    traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)

sys.excepthook = handle_exception

# Print immediately to ensure Railway sees output
print("=" * 60, file=sys.stdout)
print("🚀 DcisionAI MCP Server Startup Script", file=sys.stdout)
print("=" * 60, file=sys.stdout)
sys.stdout.flush()


def main():
    """Start the MCP Server 2.0"""
    # Print to stdout immediately for Railway visibility
    # CRITICAL: Use print() directly (not logger) for Railway to see startup immediately
    print("=" * 80, file=sys.stdout)
    print("🚀 Starting DcisionAI MCP Server 2.0 on Railway", file=sys.stdout)
    print("=" * 80, file=sys.stdout)
    print(f"Python version: {sys.version}", file=sys.stdout)
    print(f"Working directory: {os.getcwd()}", file=sys.stdout)
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'not set')}", file=sys.stdout)
    print(f"PORT env var: {os.environ.get('PORT', 'not set')}", file=sys.stdout)
    print(f"HOST env var: {os.environ.get('HOST', 'not set')}", file=sys.stdout)
    sys.stdout.flush()
    
    logger.info("🚀 Starting DcisionAI MCP Server 2.0 on Railway")
    logger.info(f"Domain Filter: {os.getenv('DCISIONAI_DOMAIN_FILTER', 'all')}")
    
    # REQUIRED: Verify Claude Agent SDK is available before starting
    # Migration guide: https://platform.claude.com/docs/en/agent-sdk/migration-guide
    try:
        from claude_agent_sdk.client import ClaudeSDKClient
        logger.info("✅ Claude Agent SDK verified - required dependency available")
        print("✅ Claude Agent SDK verified - required dependency available", file=sys.stdout)
    except ImportError as e:
        error_msg = (
            f"❌ CRITICAL: Claude Agent SDK REQUIRED but not available: {e}\n"
            "Install with: pip install claude-agent-sdk\n"
            "Migration guide: https://platform.claude.com/docs/en/agent-sdk/migration-guide\n"
            "This is a hard requirement - server cannot start without it."
        )
        logger.error(error_msg)
        print(error_msg, file=sys.stderr)
        sys.exit(1)
    
    # REQUIRED: Verify SCIP solver is available (mandatory for mathematical optimization)
    try:
        import pyscipopt
        logger.info("✅ SCIP solver verified - required dependency available")
        print("✅ SCIP solver verified - required dependency available", file=sys.stdout)
    except ImportError as e:
        error_msg = (
            f"❌ CRITICAL: SCIP solver REQUIRED but not available: {e}\n"
            "Install with: pip install 'pyscipopt>=4.3.0'\n"
            "Note: SCIP binary must also be installed separately (see pyscipopt docs)\n"
            "This is a hard requirement - server cannot start without it."
        )
        logger.error(error_msg)
        print(error_msg, file=sys.stderr)
        sys.exit(1)
    
    # REQUIRED: Verify SDV is available (central to data strategy per ADR-037)
    try:
        from dcisionai_workflow.tools.data.sdv_generator import is_sdv_available
        if is_sdv_available():
            logger.info("✅ SDV (Synthetic Data Vault) verified - required for Tier 3 data generation")
            print("✅ SDV (Synthetic Data Vault) verified - required for Tier 3 data generation", file=sys.stdout)
        else:
            warning_msg = (
                "⚠️ WARNING: SDV not available! SDV is central to data strategy per ADR-037.\n"
                "Install with: pip install 'sdv>=1.29.0' 'sdmetrics>=0.10.0'\n"
                "Tier 3 data generation will fall back to programmatic generation (lower quality)."
            )
            logger.warning(warning_msg)
            print(warning_msg, file=sys.stdout)
    except ImportError as e:
        warning_msg = (
            f"⚠️ WARNING: Could not verify SDV availability: {e}\n"
            "Install with: pip install 'sdv>=1.29.0' 'sdmetrics>=0.10.0'\n"
            "Tier 3 data generation will fall back to programmatic generation (lower quality)."
        )
        logger.warning(warning_msg)
        print(warning_msg, file=sys.stdout)
    
    # Add project root to sys.path so api module can be imported
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        logger.info(f"✅ Added project root to sys.path: {project_root}")
    
    # Use importlib to load modules directly (handles dots in directory name)
    import importlib.util
    
    # Load config module
    config_path = os.path.join(os.path.dirname(__file__), 'config.py')
    config_spec = importlib.util.spec_from_file_location('config', config_path)
    config_module = importlib.util.module_from_spec(config_spec)
    config_spec.loader.exec_module(config_module)
    MCPConfig = config_module.MCPConfig
    
    logger.info(f"Server Host: {MCPConfig.SERVER_HOST}")
    logger.info(f"Server Port: {MCPConfig.SERVER_PORT}")
    logger.info(f"HTTP Transport: {MCPConfig.ENABLE_HTTP}")
    logger.info(f"WebSocket Transport: {MCPConfig.ENABLE_WEBSOCKET}")
    logger.info(f"SSE Transport: {MCPConfig.ENABLE_SSE}")
    
    # Railway provides PORT env var, but locally use MCP_SERVER_PORT to avoid conflict with frontend
    port = int(os.getenv("MCP_SERVER_PORT", os.getenv("PORT", str(MCPConfig.SERVER_PORT))))
    
    # CRITICAL: Railway requires binding to 0.0.0.0, not localhost
    # Always use 0.0.0.0 for Railway compatibility (allows external connections)
    host = os.getenv("HOST", "0.0.0.0")
    # Force 0.0.0.0 if Railway environment detected or if host is localhost
    is_railway = os.getenv("PORT") is not None or os.getenv("RAILWAY_ENVIRONMENT") is not None
    if is_railway or host == "localhost" or host == "127.0.0.1":
        host = "0.0.0.0"
        if host != "0.0.0.0":
            logger.warning(f"⚠️ Changed host to 0.0.0.0 for Railway compatibility (was: {host})")
    
    logger.info(f"Starting server on {host}:{port}")
    print(f"🚀 Server will bind to {host}:{port}", file=sys.stdout)
    print(f"📍 Railway environment detected: {is_railway}", file=sys.stdout)
    sys.stdout.flush()
    
    # Set PYTHONPATH to ensure dcisionai_workflow can be imported
    if '/app' not in os.environ.get('PYTHONPATH', ''):
        current_pythonpath = os.environ.get('PYTHONPATH', '')
        new_pythonpath = f"/app:{current_pythonpath}" if current_pythonpath else "/app"
        os.environ['PYTHONPATH'] = new_pythonpath
        logger.info(f"✅ Set PYTHONPATH: {os.environ['PYTHONPATH']}")
    
    try:
        # Load fastmcp_server module
        logger.info("Step 1: Loading fastmcp_server module...")
        server_path = os.path.join(os.path.dirname(__file__), 'fastmcp_server.py')
        logger.info(f"Server path: {server_path}")
        logger.info(f"Server path exists: {os.path.exists(server_path)}")
        
        # CRITICAL: Set up package structure BEFORE loading module
        # This allows relative imports (from .api.jobs) to work correctly
        server_dir = os.path.dirname(server_path)
        package_dir = os.path.dirname(server_dir)
        if package_dir not in sys.path:
            sys.path.insert(0, package_dir)
            logger.info(f"✅ Added package root to sys.path: {package_dir}")
        
        # Use package-relative import instead of importlib to preserve package structure
        # This allows 'from .api.jobs import router' to work
        logger.info("Step 2: Importing fastmcp_server module as package...")
        print("Step 2: Importing fastmcp_server module...", file=sys.stdout)
        sys.stdout.flush()
        try:
            import dcisionai_mcp_server.fastmcp_server as server_module
            logger.info("✅ Server module imported successfully as package")
            print("✅ Server module imported successfully", file=sys.stdout)
            sys.stdout.flush()
        except ImportError as import_err:
            logger.warning(f"Package import failed ({import_err}), trying importlib fallback...")
            print(f"⚠️ Package import failed, trying fallback...", file=sys.stdout)
            sys.stdout.flush()
            # Fallback to importlib if package import fails
            server_spec = importlib.util.spec_from_file_location('dcisionai_mcp_server.fastmcp_server', server_path)
            server_module = importlib.util.module_from_spec(server_spec)
            server_spec.loader.exec_module(server_module)
            logger.info("✅ Server module loaded via importlib fallback")
            print("✅ Server module loaded via fallback", file=sys.stdout)
            sys.stdout.flush()
        except Exception as module_err:
            logger.error(f"❌ Failed to execute server module: {module_err}", exc_info=True)
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"Full traceback:\n{error_trace}")
            print(f"❌ CRITICAL: Failed to import server module: {module_err}", file=sys.stderr)
            print(error_trace, file=sys.stderr)
            sys.stderr.flush()
            raise
        
        logger.info("Step 3: Extracting mcp and app objects...")
        try:
            mcp = server_module.mcp
            app = server_module.app
            logger.info(f"✅ mcp: {type(mcp)}")
            logger.info(f"✅ app: {type(app) if app else 'None'}")
            
            # Verify app has health endpoint
            if app:
                routes = [route.path for route in app.routes]
                logger.info(f"✅ App routes: {routes[:10]}...")  # Log first 10 routes
                if "/health" not in routes:
                    logger.warning("⚠️ /health endpoint not found in app routes!")
        except AttributeError as attr_err:
            logger.error(f"❌ Failed to extract mcp/app objects: {attr_err}")
            logger.error(f"   Available attributes: {[a for a in dir(server_module) if not a.startswith('_')]}")
            raise
        
        import uvicorn
        logger.info("✅ uvicorn imported successfully")
        
        # If we have a FastAPI app with health endpoint, use uvicorn directly
        if app:
            logger.info("✅ Using FastAPI app with health endpoint and HTTP JSON-RPC endpoints")
            logger.info(f"🚀 Starting server on {host}:{port}")
            # CRITICAL: Print to stdout for Railway visibility
            print(f"✅ FastAPI app ready", file=sys.stdout)
            print(f"🚀 Starting uvicorn server on {host}:{port}", file=sys.stdout)
            print(f"📋 Health endpoint: http://{host}:{port}/health", file=sys.stdout)
            print(f"✅ Server starting - health endpoint should be available immediately", file=sys.stdout)
            sys.stdout.flush()
            # Configure uvicorn with increased timeouts for long-running tool calls
            # Railway has a 60s HTTP timeout, but we can handle longer operations internally
            # CRITICAL: Use access_log=True so Railway can see requests
            uvicorn.run(
                app,
                host=host,
                port=port,
                log_level="info",
                access_log=True,  # Enable access logs for Railway debugging
                timeout_keep_alive=75,  # Keep connections alive longer
                timeout_graceful_shutdown=10  # Graceful shutdown timeout
            )
        else:
            logger.info("⚠️  No FastAPI app wrapper, using FastMCP.run()")
            logger.info(f"🚀 Starting FastMCP server on {host}:{port}")
            # FastMCP.run() may not accept host/port, so we'll let it use defaults
            # Railway's PORT env var should be picked up automatically
            mcp.run()
    except Exception as e:
        logger.error(f"❌ Failed to start MCP Server 2.0: {e}")
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Full traceback:\n{error_trace}")
        # Print to stderr as well for Railway logs
        print(f"❌ CRITICAL ERROR: {e}", file=sys.stderr)
        print(error_trace, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Fatal error in main(): {e}")
        import traceback
        print(f"❌ FATAL ERROR: {e}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        sys.exit(1)

