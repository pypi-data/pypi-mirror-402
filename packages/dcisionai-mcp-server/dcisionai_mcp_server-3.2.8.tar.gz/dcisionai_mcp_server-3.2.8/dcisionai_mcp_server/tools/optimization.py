"""
Optimization Tools - Direct dcisionai_graph Integration

These tools directly import and call dcisionai_graph optimization functions,
including deployed model execution via direct imports from dcisionai_workflow.models.model_registry.
"""

import json
import logging
from typing import Dict, Any
from mcp.types import Tool, TextContent

logger = logging.getLogger(__name__)


def _make_json_schema(schema_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a schema dict to JSON-compatible format (Python False/True -> JSON false/true)."""
    # Serialize to JSON string and parse back to convert Python booleans to JSON booleans
    # This ensures Python False/True becomes JSON false/true before creating Tool objects
    json_str = json.dumps(schema_dict)
    return json.loads(json_str)


def get_tools() -> list[Tool]:
    """
    Get list of optimization tools.
    
    These tools directly import dcisionai_graph functions instead of
    making HTTP calls to FastAPI backend.
    """
    return [
        Tool(
            name="dcisionai_solve",
            description="Solve an optimization problem using DcisionAI. Provides full optimization workflow including problem classification, intent extraction, model generation, solving, and business explanation. All internal steps are included automatically.",
            inputSchema={
                "type": "object",
                "properties": {
                    "problem_description": {
                        "type": "string",
                        "description": "Natural language description of the optimization problem"
                    }
                },
                "required": ["problem_description"]
            }
        ),
        Tool(
            name="dcisionai_solve_with_model",
            description="Solve an optimization problem using a deployed DcisionAI model. Faster than full solve for known problem types. Supports portfolio optimization, capital deployment, portfolio rebalancing, and fund structure models.",
            inputSchema=_make_json_schema({
                "type": "object",
                "properties": {
                    "model_id": {
                        "type": "string",
                        "description": "ID of the deployed model to use (e.g., 'portfolio_optimization_v1', 'capital_deployment_v1', 'portfolio_rebalancing_v1', 'fund_structure_v1')"
                    },
                    "data": {
                        "type": "object",
                        "description": "Model-specific input data. See model documentation for required fields."
                    },
                    "options": {
                        "type": "object",
                        "description": "Optional solver options (solver, time_limit, verbose)",
                        "properties": {
                            "solver": {
                                "type": "string",
                                "description": "Solver to use (e.g., 'scip', 'ipopt', 'highs')",
                                "default": "scip"
                            },
                            "time_limit": {
                                "type": "integer",
                                "description": "Time limit in seconds",
                                "default": 60
                            },
                            "verbose": {
                                "type": "boolean",
                                "description": "Verbose solver output",
                                "default": False
                            }
                        }
                    }
                },
                "required": ["model_id", "data"]
            })
        ),
    ]


async def dcisionai_solve(problem_description: str, **kwargs) -> list[TextContent]:
    """
    Solve an optimization problem using DcisionAI.
    
    This function directly imports and calls dcisionai_graph DAME workflow,
    eliminating the HTTP client layer.
    
    Phase 2-4: Now supports Claude Agent SDK features:
    - Enhanced Pyomo generation with checkpointing
    - Parallel Pyomo + DAME execution
    - DAME strategy/config generation
    
    Args:
        problem_description: Natural language description of the optimization problem
        **kwargs: Additional options (use_claude_sdk_for_pyomo, use_parallel_execution, etc.)
        
    Returns:
        Optimization results as TextContent
    """
    try:
        # Direct import from dcisionai_graph orchestration (no HTTP call)
        # DAME workflow removed - use dcisionai_workflow instead
        raise NotImplementedError("DAME workflow has been removed. Use dcisionai_workflow instead.")
        from datetime import datetime
        
        logger.info(f"dcisionai_solve called with: {problem_description[:100]}...")
        
        # Check if Claude SDK is available
        try:
            from dcisionai_workflow.shared.agents.claude_sdk_adapter import CLAUDE_AGENT_SDK_AVAILABLE
            claude_sdk_available = CLAUDE_AGENT_SDK_AVAILABLE
            if claude_sdk_available:
                logger.info("✅ Claude Agent SDK available - enabling enhanced features")
        except ImportError:
            claude_sdk_available = False
            logger.info("⚠️ Claude Agent SDK not available - using standard workflow")
        
        # Create workflow with default settings
        workflow = create_dame_supervisor_workflow(
            enabled_features=["intent", "data", "optimize"],
            enabled_tools=["data", "optimize"],
            use_direct_pyomo=True  # DEFAULT: Direct Pyomo generation (SymPy sunset)
        )
        
        # Generate session ID
        session_id = f"mcp_{datetime.now().timestamp()}"
        
        # Check if Claude SDK is available for enhanced features
        try:
            from dcisionai_workflow.shared.agents.claude_sdk_adapter import CLAUDE_AGENT_SDK_AVAILABLE
            claude_sdk_available = CLAUDE_AGENT_SDK_AVAILABLE
        except ImportError:
            claude_sdk_available = False
        
        # Create initial state
        state = {
            "problem_description": problem_description,
            "session_id": session_id,
            "current_step": "start",
            "completed_steps": [],
            "errors": [],
            "warnings": [],
            "messages": [],
            "enabled_features": ["intent", "data", "optimize"],
            "enabled_tools": ["data", "optimize"],
            "reasoning_model": "claude-haiku-4-5-20251001",
            "code_model": "claude-sonnet-4-5-20250929",  # Use Claude Sonnet for code generation
            "enable_validation": False,
            "enable_templates": True,
            "template_preferences": {},
            "template_fallback": True,
            # Phase 2-4: Enable Claude SDK features if available
            "use_claude_sdk_for_pyomo": claude_sdk_available,  # Enable Claude SDK for Pyomo generation
            "use_parallel_execution": claude_sdk_available,  # Enable parallel execution (Phase 3)
            # Phase 4: DAME strategy/config generation (enabled via problem_characteristics)
        }
        
        # Phase 4: Enable Claude SDK for DAME strategy/config if available
        if claude_sdk_available:
            # These will be set in problem_characteristics when DAME solver runs
            state.setdefault("problem_characteristics", {})
            state["problem_characteristics"]["use_claude_sdk_for_strategy"] = True
            state["problem_characteristics"]["use_claude_sdk_for_config"] = True
        
        # Run workflow with thread configuration
        workflow_config = {
            "configurable": {
                "thread_id": session_id,
                "checkpoint_ns": "main"
            }
        }
        
        # Invoke workflow directly (no HTTP call)
        result = await workflow.ainvoke(state, config=workflow_config)
        
        # Format result
        formatted_result = {
            "status": "success",
            "session_id": session_id,
            "result": result,
            "message": "Optimization completed successfully"
        }
        
        return [
            TextContent(
                type="text",
                text=json.dumps(formatted_result, indent=2, default=str)
            )
        ]
    except ImportError as e:
        logger.error(f"Could not import DAME workflow: {e}", exc_info=True)
        return [
            TextContent(
                type="text",
                text=json.dumps({
                    "error": "DAME workflow not available",
                    "message": f"Could not import create_dame_supervisor_workflow: {str(e)}",
                    "suggestion": "Ensure dcisionai_graph is installed and accessible"
                }, indent=2)
            )
        ]
    except Exception as e:
        logger.error(f"Error in dcisionai_solve: {e}", exc_info=True)
        return [
            TextContent(
                type="text",
                text=json.dumps({
                    "error": "Optimization failed",
                    "message": str(e)
                }, indent=2)
            )
        ]


async def dcisionai_solve_with_model(
    model_id: str, 
    data: Dict[str, Any],
    options: Dict[str, Any] = None
) -> list[TextContent]:
    """
    Solve with deployed model using direct import from dcisionai_workflow.models.model_registry.
    
    This is a KEY FEATURE - deployed models are a core capability of dcisionai_graph.
    
    Args:
        model_id: Deployed model ID (e.g., 'portfolio_optimization_v1')
        data: Model-specific input data
        options: Optional solver options (solver, time_limit, verbose)
        
    Returns:
        Optimization results
    """
    try:
        # Direct import from core model registry (protocol-agnostic)
        from dcisionai_workflow.models.model_registry import run_deployed_model, MODEL_REGISTRY
        
        # Validate model exists
        if model_id not in MODEL_REGISTRY:
            available_models = list(MODEL_REGISTRY.keys())
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"Model '{model_id}' not found",
                        "available_models": available_models,
                        "message": f"Available models: {', '.join(available_models)}"
                    }, indent=2)
                )
            ]
        
        logger.info(f"dcisionai_solve_with_model: model_id={model_id}, data_keys={list(data.keys())}")
        
        # Run deployed model directly (no HTTP call)
        result = await run_deployed_model(model_id, data, options)
        
        # Format result
        formatted_result = {
            "status": "success",
            "model_id": model_id,
            "result": result,
            "message": f"Successfully executed model {model_id}"
        }
        
        return [
            TextContent(
                type="text",
                text=json.dumps(formatted_result, indent=2)
            )
        ]
    except Exception as e:
        logger.error(f"Error in dcisionai_solve_with_model: {e}", exc_info=True)
        return [
            TextContent(
                type="text",
                text=json.dumps({
                    "error": str(e),
                    "model_id": model_id,
                    "message": f"Failed to execute model {model_id}"
                }, indent=2)
            )
        ]
