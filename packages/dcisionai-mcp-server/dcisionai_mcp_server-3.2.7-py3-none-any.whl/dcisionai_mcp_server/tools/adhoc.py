"""
Ad-Hoc Optimization Tool - Direct dcisionai_graph Integration

Builds and solves optimization problems from natural language descriptions.
Directly imports from dcisionai_workflow.tools.optimization.adhoc_optimize.
"""

import json
import logging
from typing import Dict, Any, Optional
from mcp.types import Tool, TextContent

logger = logging.getLogger(__name__)


def get_tools() -> list[Tool]:
    """Get list of ad-hoc optimization tools"""
    return [
        Tool(
            name="dcisionai_adhoc_optimize",
            description="Build and solve optimization problems from natural language descriptions. Dynamically builds optimization models and solves them using DcisionAI backend. Can use Salesforce data if provided.",
            inputSchema={
                "type": "object",
                "properties": {
                    "problem_description": {
                        "type": "string",
                        "description": "Natural language description of the optimization problem"
                    },
                    "salesforce_data": {
                        "type": "object",
                        "description": "Optional Salesforce data to use (if provided, will be used instead of mock data)"
                    },
                    "org_context": {
                        "type": "object",
                        "description": "Optional organization context (domain, industry, etc.)"
                    }
                },
                "required": ["problem_description"]
            }
        ),
    ]


async def dcisionai_adhoc_optimize(
    problem_description: str,
    salesforce_data: Optional[Dict[str, Any]] = None,
    org_context: Optional[Dict[str, Any]] = None
) -> list[TextContent]:
    """
    Solve an ad-hoc optimization problem from natural language description.
    
    Directly imports from dcisionai_workflow.tools.optimization.adhoc_optimize.
    No HTTP calls - direct Python import.
    
    Args:
        problem_description: Natural language description of optimization problem
        salesforce_data: Optional Salesforce data to use
        org_context: Optional organization context
        
    Returns:
        Optimization results JSON
    """
    try:
        # Direct import from dcisionai_graph (no HTTP call)
        from dcisionai_workflow.tools.optimization.adhoc_optimize import solve_adhoc_optimization
        
        # Call LangGraph tool directly (no HTTP call)
        # LangChain @tool decorator wraps function in StructuredTool, use ainvoke()
        result = await solve_adhoc_optimization.ainvoke({
            "problem_description": problem_description,
            "salesforce_data": salesforce_data,
            "org_context": org_context
        })
        
        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )
        ]
        
    except ImportError as e:
        logger.error(f"Could not import solve_adhoc_optimization: {e}", exc_info=True)
        return [
            TextContent(
                type="text",
                text=json.dumps({
                    "error": "Ad-hoc optimization tool not available",
                    "message": f"Could not import solve_adhoc_optimization: {str(e)}",
                    "suggestion": "Ensure dcisionai_graph is installed and accessible"
                }, indent=2)
            )
        ]
    except Exception as e:
        logger.error(f"Error in dcisionai_adhoc_optimize: {e}", exc_info=True)
        return [
            TextContent(
                type="text",
                text=json.dumps({
                    "error": "Ad-hoc optimization failed",
                    "message": str(e)
                }, indent=2)
            )
        ]

