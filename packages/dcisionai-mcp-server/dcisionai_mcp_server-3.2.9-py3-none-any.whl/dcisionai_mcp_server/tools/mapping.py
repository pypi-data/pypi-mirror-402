"""
Concept Mapping Tool - Direct dcisionai_graph Integration

Maps business concepts to platform schema using Claude.
Directly imports from dcisionai_workflow.tools.data.schema_mapping.
"""

import json
import logging
from typing import List, Optional
from mcp.types import Tool, TextContent

logger = logging.getLogger(__name__)


def get_tools() -> list[Tool]:
    """Get list of mapping tools"""
    return [
        Tool(
            name="dcisionai_map_concepts",
            description="Map business concepts to platform schema (e.g., Salesforce objects/fields) using Claude's semantic understanding. Returns mapping recommendations with confidence scores.",
            inputSchema={
                "type": "object",
                "properties": {
                    "required_concepts": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of business concepts to map (e.g., ['client', 'portfolio', 'risk tolerance'])"
                    },
                    "schema_json": {
                        "type": "string",
                        "description": "Platform schema JSON (e.g., Salesforce objects and fields)"
                    },
                    "intent_description": {
                        "type": "string",
                        "description": "Optional description of the optimization intent to provide context for mapping"
                    }
                },
                "required": ["required_concepts", "schema_json"]
            }
        ),
    ]


async def dcisionai_map_concepts(
    required_concepts: List[str],
    schema_json: str,
    intent_description: Optional[str] = None
) -> list[TextContent]:
    """
    Map business concepts to platform schema using Claude.
    
    Directly imports from dcisionai_workflow.tools.data.schema_mapping.
    No HTTP calls - direct Python import.
    
    Args:
        required_concepts: List of business concepts to map
        schema_json: Platform schema JSON
        intent_description: Optional optimization intent description
        
    Returns:
        Mapping recommendations with confidence scores
    """
    try:
        # Direct import from dcisionai_graph (no HTTP call)
        from dcisionai_workflow.tools.data.schema_mapping import map_concepts_to_schema
        
        # Call mapping function directly (no HTTP call)
        result = await map_concepts_to_schema(
            required_concepts=required_concepts,
            schema_json=schema_json,
            intent_description=intent_description
        )
        
        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )
        ]
        
    except ImportError as e:
        logger.error(f"Could not import map_concepts_to_schema: {e}", exc_info=True)
        return [
            TextContent(
                type="text",
                text=json.dumps({
                    "error": "Mapping tool not available",
                    "message": f"Could not import map_concepts_to_schema: {str(e)}",
                    "suggestion": "Ensure dcisionai_graph is installed and accessible"
                }, indent=2)
            )
        ]
    except Exception as e:
        logger.error(f"Error in dcisionai_map_concepts: {e}", exc_info=True)
        return [
            TextContent(
                type="text",
                text=json.dumps({
                    "error": "Concept mapping failed",
                    "message": str(e)
                }, indent=2)
            )
        ]

