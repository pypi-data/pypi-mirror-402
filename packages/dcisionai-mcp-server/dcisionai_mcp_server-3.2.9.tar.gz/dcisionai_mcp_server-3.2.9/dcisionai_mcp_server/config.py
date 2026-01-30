"""
Configuration management for DcisionAI MCP Server 2.0
"""

import os
from typing import Optional


class MCPConfig:
    """Configuration for MCP Server 2.0"""
    
    # Server Configuration
    SERVER_HOST: str = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
    SERVER_PORT: int = int(os.getenv("MCP_SERVER_PORT", "8080"))
    
    # dcisionai_graph Configuration
    DOMAIN_FILTER: str = os.getenv("DCISIONAI_DOMAIN_FILTER", "all").lower()
    
    # Anthropic Claude API Configuration
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY", None)
    CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
    
    # Logging
    LOG_LEVEL: str = os.getenv("DCISIONAI_LOG_LEVEL", "INFO")
    
    # Transport Configuration
    ENABLE_HTTP: bool = os.getenv("MCP_ENABLE_HTTP", "true").lower() == "true"
    ENABLE_WEBSOCKET: bool = os.getenv("MCP_ENABLE_WEBSOCKET", "true").lower() == "true"
    ENABLE_SSE: bool = os.getenv("MCP_ENABLE_SSE", "true").lower() == "true"
    
    # CORS Configuration (for web clients)
    # Production: Allow Vercel domains and platform domain
    # Development: Allow localhost
    _default_cors_origins = (
        "http://localhost:3000,"
        "http://localhost:8080,"
        "http://127.0.0.1:3000,"
        "http://127.0.0.1:8080,"
        "https://platform.dcisionai.com,"
        "https://*.vercel.app"  # Vercel preview and production deployments
    )
    CORS_ORIGINS: list[str] = os.getenv(
        "MCP_CORS_ORIGINS",
        _default_cors_origins
    ).split(",")
    
    # Authentication (for remote clients)
    API_KEY: Optional[str] = os.getenv("MCP_API_KEY", None)
    OAUTH_ENABLED: bool = os.getenv("MCP_OAUTH_ENABLED", "false").lower() == "true"
    
    # Multi-Tenancy Configuration
    MULTI_TENANT_ENABLED: bool = os.getenv("MULTI_TENANT_ENABLED", "false").lower() == "true"
    DEFAULT_TENANT_ID: str = os.getenv("DEFAULT_TENANT_ID", "default")
    ADMIN_API_KEY: Optional[str] = os.getenv("ADMIN_API_KEY", None)
    
    # Feature Flags
    # NOTE: These are read dynamically at runtime via getter methods
    # This ensures environment variable changes are picked up without server restart
    # Old class variables are kept for backward compatibility but should use getter methods
    @staticmethod
    def get_enable_business_explanation() -> bool:
        return os.getenv("ENABLE_BUSINESS_EXPLANATION", "false").lower() == "true"
    
    @staticmethod
    def get_enable_llm_metrics() -> bool:
        return os.getenv("ENABLE_LLM_METRICS", "false").lower() == "true"
    
    @staticmethod
    def get_enable_llm_decision_traces() -> bool:
        return os.getenv("ENABLE_LLM_DECISION_TRACES", "false").lower() == "true"
    
    @staticmethod
    def get_enable_dame() -> bool:
        return os.getenv("ENABLE_DAME", "true").lower() == "true"  # Default to true for backward compatibility
    
    @staticmethod
    def get_enable_graph_native_traces() -> bool:
        """Enable graph-native decision traces (Neo4j integration)."""
        return os.getenv("ENABLE_GRAPH_NATIVE_TRACES", "false").lower() == "true"
    
    @staticmethod
    def get_enable_shadow_price_analysis() -> bool:
        """Enable shadow price / sensitivity analysis for constraint economics."""
        return os.getenv("ENABLE_SHADOW_PRICE_ANALYSIS", "true").lower() == "true"
    
    @staticmethod
    def get_enable_rigor_domain_review() -> bool:
        """Enable post-completion review agent for mathematical rigor and domain accuracy."""
        return os.getenv("ENABLE_RIGOR_DOMAIN_REVIEW", "false").lower() == "true"
    
    @staticmethod
    def get_enable_auto_correct_markdown() -> bool:
        """Enable automatic markdown file correction."""
        return os.getenv("ENABLE_AUTO_CORRECT_MARKDOWN", "true").lower() == "true"
    
    @staticmethod
    def get_enable_auto_rerun_solver() -> bool:
        """Enable automatic solver re-run with corrections.
        
        When disabled, the review agent will only review and document issues
        without triggering automatic re-runs. Re-runs can be expensive and
        may not always be necessary.
        """
        return os.getenv("ENABLE_AUTO_RERUN_SOLVER", "false").lower() == "true"
    
    # Backward compatibility: Keep class variables for old code, but they're cached at import time
    # New code should use getter methods above for dynamic reading
    ENABLE_BUSINESS_EXPLANATION: bool = os.getenv("ENABLE_BUSINESS_EXPLANATION", "false").lower() == "true"
    ENABLE_LLM_METRICS: bool = os.getenv("ENABLE_LLM_METRICS", "false").lower() == "true"
    ENABLE_LLM_DECISION_TRACES: bool = os.getenv("ENABLE_LLM_DECISION_TRACES", "false").lower() == "true"
    ENABLE_DAME: bool = os.getenv("ENABLE_DAME", "true").lower() == "true"  # Default to true for backward compatibility
    ENABLE_GRAPH_NATIVE_TRACES: bool = os.getenv("ENABLE_GRAPH_NATIVE_TRACES", "false").lower() == "true"
    
    @classmethod
    def get_domain_filter(cls) -> str:
        """Get domain filter setting"""
        return cls.DOMAIN_FILTER
    
    @classmethod
    def get_anthropic_api_key(cls) -> Optional[str]:
        """Get Anthropic API key for Claude"""
        return cls.ANTHROPIC_API_KEY
    
    @classmethod
    def get_claude_model(cls) -> str:
        """Get Claude model name"""
        return cls.CLAUDE_MODEL

