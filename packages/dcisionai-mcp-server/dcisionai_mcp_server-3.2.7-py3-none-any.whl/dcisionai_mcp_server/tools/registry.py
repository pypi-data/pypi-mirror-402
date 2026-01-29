"""
MCP Tool Registry

Centralized registry for all MCP tools. Eliminates code duplication
by providing a single source of truth for tool discovery and execution.
"""

import logging
from typing import List, Callable, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Tool registry - populated on module load
_TOOL_REGISTRY: Dict[str, Callable] = {}
_TOOL_METADATA: Dict[str, Dict[str, Any]] = {}

# Dynamic model tools registry (populated asynchronously)
_DYNAMIC_MODEL_TOOLS: List[Callable] = []
_DYNAMIC_TOOLS_INITIALIZED: bool = False


def register_tool(tool_func: Callable) -> None:
    """
    Register a tool function in the registry.
    
    Args:
        tool_func: Tool function decorated with @mcp_tool
    """
    from dcisionai_workflow.tools.mcp_decorator import is_mcp_tool, get_mcp_tool_metadata
    
    if not is_mcp_tool(tool_func):
        logger.warning(f"Attempted to register non-MCP tool: {tool_func.__name__}")
        return
    
    metadata = get_mcp_tool_metadata(tool_func)
    if metadata:
        tool_name = metadata.get("name")
        if tool_name:
            _TOOL_REGISTRY[tool_name] = tool_func
            _TOOL_METADATA[tool_name] = metadata
            logger.debug(f"Registered MCP tool: {tool_name}")
        else:
            logger.warning(f"Tool {tool_func.__name__} has no name in metadata")
    else:
        logger.warning(f"Could not get metadata for tool: {tool_func.__name__}")


def get_all_mcp_tools() -> List[Callable]:
    """
    Get all registered MCP tools (static + dynamic).
    
    Returns:
        List of tool functions
    """
    all_tools = list(_TOOL_REGISTRY.values())
    all_tools.extend(_DYNAMIC_MODEL_TOOLS)
    return all_tools


def get_tool_by_name(tool_name: str) -> Optional[Callable]:
    """
    Get a tool function by name.
    
    Args:
        tool_name: Name of the tool
        
    Returns:
        Tool function or None if not found
    """
    return _TOOL_REGISTRY.get(tool_name)


def get_tool_metadata(tool_name: str) -> Optional[Dict[str, Any]]:
    """
    Get metadata for a tool by name.
    
    Args:
        tool_name: Name of the tool
        
    Returns:
        Tool metadata dict or None if not found
    """
    return _TOOL_METADATA.get(tool_name)


def get_all_tool_names() -> List[str]:
    """
    Get all registered tool names.
    
    Returns:
        List of tool names
    """
    return list(_TOOL_REGISTRY.keys())


def initialize_registry() -> None:
    """
    Initialize the tool registry by importing and registering all MCP tools.
    
    This should be called once at module load time.
    """
    logger.info("Initializing MCP tool registry...")
    
    try:
        # Import optimization tools
        from dcisionai_workflow.tools.optimization.mcp_tools import (
            dcisionai_solve,
            dcisionai_solve_with_model,
            dcisionai_adhoc_optimize
        )
        
        # Import NLP tools
        from dcisionai_workflow.tools.nlp.mcp_tools import dcisionai_nlp_query
        
        # Import data tools (excluding internal engineering tools)
        from dcisionai_workflow.tools.data.mcp_tools import (
            dcisionai_map_concepts,
            dcisionai_prepare_data,
            dcisionai_prepare_salesforce_data
            # NOTE: dcisionai_list_templates and dcisionai_register_template
            # are NOT imported - they are internal engineering tools
        )
        
        # Import intent tools (IDE-focused)
        from dcisionai_workflow.tools.intent.mcp_tools import (
            dcisionai_analyze_problem,
            dcisionai_validate_constraints,
            dcisionai_search_problem_types,
            dcisionai_get_problem_type_schema
        )
        
        # Import client tools (workflow management)
        from dcisionai_workflow.tools.optimization.mcp_tools import (
            dcisionai_get_workflow_status,
            dcisionai_cancel_workflow,
            dcisionai_get_result,
            dcisionai_export_result,
            dcisionai_deploy_model
        )
        
        # Import simulation tools (workflow execution simulation)
        try:
            from dcisionai_workflow.tools.simulation.mcp_tools import (
                dcisionai_simulate_scenario,
                dcisionai_assess_deployment_risk,
                dcisionai_compare_scenarios
            )
            simulation_tools_available = True
        except ImportError as e:
            logger.warning(f"Simulation tools not available: {e}")
            simulation_tools_available = False
        
        # Import optimization problem simulation tools (NEW - Phase 1-4)
        try:
            from dcisionai_workflow.tools.simulation.mcp_tools import (
                dcisionai_simulate_optimization_scenario,
                dcisionai_compare_optimization_scenarios,
                dcisionai_sensitivity_analysis,
                dcisionai_monte_carlo_simulation,
                dcisionai_initialize_mesa_model,
                dcisionai_update_mesa_parameter,
                dcisionai_get_mesa_model_state,
                dcisionai_check_model_deployment_status
            )
            optimization_simulation_tools_available = True
        except ImportError as e:
            logger.warning(f"Optimization simulation tools not available: {e}")
            optimization_simulation_tools_available = False
        
        # Register all public tools
        register_tool(dcisionai_solve)
        register_tool(dcisionai_solve_with_model)
        register_tool(dcisionai_adhoc_optimize)
        register_tool(dcisionai_nlp_query)
        register_tool(dcisionai_map_concepts)
        register_tool(dcisionai_prepare_data)
        register_tool(dcisionai_prepare_salesforce_data)
        # IDE tools
        register_tool(dcisionai_analyze_problem)
        register_tool(dcisionai_validate_constraints)
        register_tool(dcisionai_search_problem_types)
        register_tool(dcisionai_get_problem_type_schema)
        # Client tools
        register_tool(dcisionai_get_workflow_status)
        register_tool(dcisionai_cancel_workflow)
        register_tool(dcisionai_get_result)
        register_tool(dcisionai_export_result)
        register_tool(dcisionai_deploy_model)
        # Simulation tools (workflow execution simulation)
        if simulation_tools_available:
            register_tool(dcisionai_simulate_scenario)
            register_tool(dcisionai_assess_deployment_risk)
            register_tool(dcisionai_compare_scenarios)
        
        # Optimization problem simulation tools (NEW - Phase 1-4)
        if optimization_simulation_tools_available:
            register_tool(dcisionai_simulate_optimization_scenario)
            register_tool(dcisionai_compare_optimization_scenarios)
            register_tool(dcisionai_sensitivity_analysis)
            register_tool(dcisionai_monte_carlo_simulation)
            # Mesa interactive simulation tools
            register_tool(dcisionai_initialize_mesa_model)
            register_tool(dcisionai_update_mesa_parameter)
            register_tool(dcisionai_get_mesa_model_state)
            register_tool(dcisionai_check_model_deployment_status)
        
        logger.info(f"✅ Registered {len(_TOOL_REGISTRY)} MCP tools: {', '.join(_TOOL_REGISTRY.keys())}")
        
    except ImportError as e:
        logger.error(f"Failed to import MCP tools: {e}", exc_info=True)
        logger.error("Tool registry may be incomplete")
    except Exception as e:
        logger.error(f"Error initializing tool registry: {e}", exc_info=True)


async def initialize_dynamic_model_tools() -> None:
    """
    Initialize dynamic model tools asynchronously.
    
    This should be called after the server starts to ensure database is available.
    """
    global _DYNAMIC_MODEL_TOOLS, _DYNAMIC_TOOLS_INITIALIZED
    
    if _DYNAMIC_TOOLS_INITIALIZED:
        logger.debug("Dynamic model tools already initialized")
        return
    
    try:
        logger.info("Initializing dynamic model tools...")
        from dcisionai_mcp_server.tools.dynamic_model_tools import register_all_dynamic_model_tools
        
        # Generate tools for all deployed models
        dynamic_tools = await register_all_dynamic_model_tools()
        
        # Register each tool
        for tool_func in dynamic_tools:
            register_tool(tool_func)
        
        _DYNAMIC_MODEL_TOOLS = dynamic_tools
        _DYNAMIC_TOOLS_INITIALIZED = True
        
        logger.info(f"✅ Initialized {len(dynamic_tools)} dynamic model tools")
        
    except Exception as e:
        logger.error(f"Failed to initialize dynamic model tools: {e}", exc_info=True)
        logger.warning("Dynamic model tools will not be available")


def reload_dynamic_model_tools() -> None:
    """
    Reload dynamic model tools (call after model deployment).
    
    This resets the initialization flag so tools will be regenerated on next access.
    """
    global _DYNAMIC_TOOLS_INITIALIZED, _DYNAMIC_MODEL_TOOLS
    
    # Remove old dynamic tools from registry
    for tool_func in _DYNAMIC_MODEL_TOOLS:
        from dcisionai_workflow.tools.mcp_decorator import get_mcp_tool_metadata
        metadata = get_mcp_tool_metadata(tool_func)
        if metadata:
            tool_name = metadata.get("name")
            if tool_name and tool_name in _TOOL_REGISTRY:
                del _TOOL_REGISTRY[tool_name]
                if tool_name in _TOOL_METADATA:
                    del _TOOL_METADATA[tool_name]
    
    _DYNAMIC_MODEL_TOOLS = []
    _DYNAMIC_TOOLS_INITIALIZED = False
    
    logger.info("Dynamic model tools reset - will be regenerated on next access")


# Initialize registry on module load
initialize_registry()

