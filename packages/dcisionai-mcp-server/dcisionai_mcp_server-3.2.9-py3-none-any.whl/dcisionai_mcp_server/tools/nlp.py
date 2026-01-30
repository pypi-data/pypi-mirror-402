"""
NLP Query Tool - Direct dcisionai_graph Integration

Answers natural language questions using DcisionAI NLP capabilities.
Directly imports from dcisionai_workflow.tools.nlp.query_tool.
"""

import json
import logging
from typing import Dict, Any, Optional
from mcp.types import Tool, TextContent

logger = logging.getLogger(__name__)


def get_tools() -> list[Tool]:
    """Get list of NLP tools"""
    return [
        Tool(
            name="dcisionai_nlp_query",
            description="Answers natural language questions about Salesforce data or optimization problems. Uses Schema+EDA approach when available for SOQL query generation, or provides optimization-aware answers.",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Natural language question to answer"
                    },
                    "salesforce_data": {
                        "type": "object",
                        "description": "Optional Salesforce data (legacy approach - use schema_json + eda_json instead)"
                    },
                    "org_context": {
                        "type": "object",
                        "description": "Optional organization context (domain, industry, etc.)"
                    },
                    "schema_json": {
                        "type": "string",
                        "description": "Optional Salesforce schema JSON (preferred over salesforce_data)"
                    },
                    "eda_json": {
                        "type": "string",
                        "description": "Optional Exploratory Data Analysis JSON (preferred over salesforce_data)"
                    }
                },
                "required": ["question"]
            }
        ),
    ]


async def dcisionai_nlp_query(
    question: str,
    salesforce_data: Optional[Dict[str, Any]] = None,
    org_context: Optional[Dict[str, Any]] = None,
    schema_json: Optional[str] = None,
    eda_json: Optional[str] = None
) -> list[TextContent]:
    """
    Answer natural language questions using DcisionAI NLP capabilities.
    
    Directly imports from dcisionai_workflow.tools.nlp.query_tool.
    No HTTP calls - direct Python import.
    
    Args:
        question: Natural language question
        salesforce_data: Optional Salesforce data (legacy)
        org_context: Optional organization context
        schema_json: Optional schema JSON (preferred)
        eda_json: Optional EDA JSON (preferred)
        
    Returns:
        Answer JSON with intent classification and response
    """
    try:
        # Direct import from dcisionai_graph (no HTTP call)
        from dcisionai_workflow.tools.nlp.query_tool import answer_nlp_query
        
        # Prepare arguments for LangGraph tool
        tool_args = {
            "question": question,
            "salesforce_data": salesforce_data,
            "org_context": org_context
        }
        
        # Only add schema_json and eda_json if they're provided (non-empty strings)
        if schema_json is not None and isinstance(schema_json, str) and len(schema_json.strip()) > 0:
            tool_args["schema_json"] = schema_json
            logger.info(f"MCP Server 2.0: Passing schema_json ({len(schema_json)} chars)")
        else:
            logger.debug(f"MCP Server 2.0: schema_json not provided or empty")
            
        if eda_json is not None and isinstance(eda_json, str) and len(eda_json.strip()) > 0:
            tool_args["eda_json"] = eda_json
            logger.info(f"MCP Server 2.0: Passing eda_json ({len(eda_json)} chars)")
        else:
            logger.debug(f"MCP Server 2.0: eda_json not provided or empty")
        
        # Call LangGraph tool directly (no HTTP call)
        # LangChain @tool decorator wraps function in StructuredTool, use ainvoke()
        result = await answer_nlp_query.ainvoke(tool_args)
        
        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )
        ]
        
    except ImportError as e:
        logger.error(f"Could not import answer_nlp_query: {e}", exc_info=True)
        return [
            TextContent(
                type="text",
                text=json.dumps({
                    "error": "NLP tool not available",
                    "message": f"Could not import answer_nlp_query: {str(e)}",
                    "suggestion": "Ensure dcisionai_graph is installed and accessible"
                }, indent=2)
            )
        ]
    except Exception as e:
        logger.error(f"Error in dcisionai_nlp_query: {e}", exc_info=True)
        return [
            TextContent(
                type="text",
                text=json.dumps({
                    "error": "NLP query failed",
                    "message": str(e)
                }, indent=2)
            )
        ]

