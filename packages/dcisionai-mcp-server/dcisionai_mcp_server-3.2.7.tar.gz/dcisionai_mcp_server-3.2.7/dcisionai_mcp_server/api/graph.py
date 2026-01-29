"""
Graph Query API Endpoints

Provides REST API endpoints for querying Neo4j decision traces:
- Execute Cypher queries
- Get trace graphs
- Natural language querying (NeoConverse integration)
- Trace summaries and navigation
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Graph-native components
try:
    from dcisionai_workflow.shared.graph.executor import GraphExecutor
    from dcisionai_workflow.shared.graph.config import load_neo4j_config
    GRAPH_IMPORTS_AVAILABLE = True
    _GRAPH_IMPORT_ERROR = None
except ImportError as e:
    GRAPH_IMPORTS_AVAILABLE = False
    _GRAPH_IMPORT_ERROR = str(e)
    logging.warning(f"Graph components not available: {e}", exc_info=True)
except Exception as e:
    # Catch any other errors during import (e.g., missing dependencies)
    GRAPH_IMPORTS_AVAILABLE = False
    _GRAPH_IMPORT_ERROR = str(e)
    logging.error(f"Graph components failed to import: {e}", exc_info=True)

# Runtime connection check
def check_graph_connection() -> Tuple[bool, Optional[str]]:
    """
    Check if Neo4j connection is actually working.
    
    Returns:
        (is_available, error_message)
    """
    if not GRAPH_IMPORTS_AVAILABLE:
        error_msg = f"Graph components not imported: {_GRAPH_IMPORT_ERROR}" if _GRAPH_IMPORT_ERROR else "Graph components not imported"
        return False, error_msg
    
    try:
        # Try to load config
        config = load_neo4j_config()
        uri = config.get("uri", "")
        user = config.get("user", "")
        password = config.get("password", "")
        
        if not uri:
            return False, "NEO4J_URI not set in environment variables"
        if not password:
            return False, "NEO4J_PASSWORD not set in environment variables"
        
        # Try to create a connection
        executor = GraphExecutor(uri=uri, user=user, password=password)
        try:
            # Test with a simple query using verify_connection which is more reliable
            is_connected = executor.verify_connection()
            executor.close()
            if is_connected:
                return True, None
            else:
                return False, "Neo4j connection test query returned no results - check Neo4j is running and credentials are correct"
        except Exception as e:
            executor.close()
            return False, f"Neo4j connection failed: {str(e)}"
    except Exception as e:
        return False, f"Failed to load Neo4j config: {str(e)}"


# API key middleware (must be before router and routes)
try:
    from dcisionai_mcp_server.middleware.api_key_auth import verify_api_key_optional
except ImportError:
    async def verify_api_key_optional():
        from dcisionai_mcp_server.config import MCPConfig
        return {"tenant_id": MCPConfig.DEFAULT_TENANT_ID, "is_admin": False}

logger = logging.getLogger(__name__)

# Create FastAPI router (must be before route definitions)
router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("/decisions/patterns/{decision_type}", response_model=Dict[str, Any])
async def get_decision_patterns(
    decision_type: str,
    min_occurrences: int = Query(default=5, description="Minimum occurrences to consider a pattern"),
    time_window_days: int = Query(default=30, description="Time window in days"),
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get learned patterns for a decision type.
    
    Analyzes decision traces to extract:
    - Successful patterns (high success rate)
    - Common reasoning patterns
    - Context patterns that lead to success
    
    This enables the flywheel: learn from past decisions to improve future ones.
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        from dcisionai_workflow.shared.graph.feedback_analyzer import FeedbackAnalyzer
        
        analyzer = FeedbackAnalyzer(executor)
        patterns = analyzer.analyze_decision_patterns(
            decision_type=decision_type,
            min_occurrences=min_occurrences,
            time_window_days=time_window_days
        )
        
        return patterns
    except Exception as e:
        logger.error(f"Failed to get decision patterns: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze patterns: {str(e)}")
    finally:
        executor.close()


@router.get("/decisions/feedback/{decision_type}", response_model=Dict[str, Any])
async def get_decision_feedback(
    decision_type: str,
    context: str = Query(default="{}", description="JSON string of context"),
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get feedback/recommendations for making a decision.
    
    Uses learned patterns to suggest what has worked in similar contexts.
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        import json
        context_dict = json.loads(context) if context else {}
        
        from dcisionai_workflow.shared.graph.feedback_analyzer import FeedbackAnalyzer
        
        analyzer = FeedbackAnalyzer(executor)
        feedback = analyzer.provide_decision_feedback(
            decision_type=decision_type,
            context=context_dict
        )
        
        return feedback
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in context parameter")
    except Exception as e:
        logger.error(f"Failed to get decision feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get feedback: {str(e)}")
    finally:
        executor.close()


@router.get("/decisions/query-by-context", response_model=Dict[str, Any])
async def query_decisions_by_context(
    constraint_count: Optional[int] = Query(default=None, description="Filter by constraint_count"),
    solve_time_ms: Optional[int] = Query(default=None, description="Filter by solve_time_ms (max)"),
    status: Optional[str] = Query(default=None, description="Filter by status"),
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Query DecisionEvents by context properties using DecisionContext nodes.
    
    Enables queries like:
    - Find all decisions where constraint_count > 10
    - Find all decisions where solve_time_ms < 100
    - Find all decisions where status = 'optimal'
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        from dcisionai_workflow.shared.graph.context_extractor import query_decisions_by_context
        
        # Build filters
        filters = {}
        if constraint_count is not None:
            filters["constraint_count"] = {"$gte": constraint_count}
        if solve_time_ms is not None:
            filters["solve_time_ms"] = {"$lte": solve_time_ms}
        if status:
            filters["status"] = status
        
        decisions = query_decisions_by_context(executor, filters)
        
        return {
            "decisions": decisions,
            "count": len(decisions)
        }
    except Exception as e:
        logger.error(f"Failed to query decisions by context: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to query decisions: {str(e)}")
    finally:
        executor.close()


@router.get("/traces/{trace_id}/analysis", response_model=Dict[str, Any])
async def get_trace_analysis(
    trace_id: str,
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get analysis and learnings from a completed trace.
    
    Analyzes the trace to extract successful patterns and learnings.
    This implements the feedback loop: analyze completed traces to improve future decisions.
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        from dcisionai_workflow.shared.graph.feedback_analyzer import analyze_trace_for_improvement
        
        analysis = analyze_trace_for_improvement(executor, trace_id)
        
        return analysis
    except Exception as e:
        logger.error(f"Failed to analyze trace: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze trace: {str(e)}")
    finally:
        executor.close()


@router.get("/decisions/patterns/{decision_type}", response_model=Dict[str, Any])
async def get_decision_patterns(
    decision_type: str,
    min_occurrences: int = Query(default=5, description="Minimum occurrences to consider a pattern"),
    time_window_days: int = Query(default=30, description="Time window in days"),
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get learned patterns for a decision type.
    
    Analyzes decision traces to extract:
    - Successful patterns (high success rate)
    - Common reasoning patterns
    - Context patterns that lead to success
    
    This enables the flywheel: learn from past decisions to improve future ones.
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        from dcisionai_workflow.shared.graph.feedback_analyzer import FeedbackAnalyzer
        
        analyzer = FeedbackAnalyzer(executor)
        patterns = analyzer.analyze_decision_patterns(
            decision_type=decision_type,
            min_occurrences=min_occurrences,
            time_window_days=time_window_days
        )
        
        return patterns
    except Exception as e:
        logger.error(f"Failed to get decision patterns: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze patterns: {str(e)}")
    finally:
        executor.close()


@router.get("/decisions/feedback/{decision_type}", response_model=Dict[str, Any])
async def get_decision_feedback(
    decision_type: str,
    context: str = Query(default="{}", description="JSON string of context"),
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get feedback/recommendations for making a decision.
    
    Uses learned patterns to suggest what has worked in similar contexts.
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        import json
        context_dict = json.loads(context) if context else {}
        
        from dcisionai_workflow.shared.graph.feedback_analyzer import FeedbackAnalyzer
        
        analyzer = FeedbackAnalyzer(executor)
        feedback = analyzer.provide_decision_feedback(
            decision_type=decision_type,
            context=context_dict
        )
        
        return feedback
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in context parameter")
    except Exception as e:
        logger.error(f"Failed to get decision feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get feedback: {str(e)}")
    finally:
        executor.close()


@router.get("/decisions/query-by-context", response_model=Dict[str, Any])
async def query_decisions_by_context(
    constraint_count: Optional[int] = Query(default=None, description="Filter by constraint_count"),
    solve_time_ms: Optional[int] = Query(default=None, description="Filter by solve_time_ms (max)"),
    status: Optional[str] = Query(default=None, description="Filter by status"),
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Query DecisionEvents by context properties using DecisionContext nodes.
    
    Enables queries like:
    - Find all decisions where constraint_count > 10
    - Find all decisions where solve_time_ms < 100
    - Find all decisions where status = 'optimal'
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        from dcisionai_workflow.shared.graph.context_extractor import query_decisions_by_context
        
        # Build filters
        filters = {}
        if constraint_count is not None:
            filters["constraint_count"] = {"$gte": constraint_count}
        if solve_time_ms is not None:
            filters["solve_time_ms"] = {"$lte": solve_time_ms}
        if status:
            filters["status"] = status
        
        decisions = query_decisions_by_context(executor, filters)
        
        return {
            "decisions": decisions,
            "count": len(decisions)
        }
    except Exception as e:
        logger.error(f"Failed to query decisions by context: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to query decisions: {str(e)}")
    finally:
        executor.close()


@router.get("/traces/{trace_id}/analysis", response_model=Dict[str, Any])
async def get_trace_analysis(
    trace_id: str,
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get analysis and learnings from a completed trace.
    
    Analyzes the trace to extract successful patterns and learnings.
    This implements the feedback loop: analyze completed traces to improve future decisions.
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        from dcisionai_workflow.shared.graph.feedback_analyzer import analyze_trace_for_improvement
        
        analysis = analyze_trace_for_improvement(executor, trace_id)
        
        return analysis
    except Exception as e:
        logger.error(f"Failed to analyze trace: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze trace: {str(e)}")
    finally:
        executor.close()

# Lazy connection check - will be tested on first use
# Set initial state based on imports only
GRAPH_AVAILABLE = GRAPH_IMPORTS_AVAILABLE
GRAPH_ERROR = None

# Cache for connection check result
_graph_connection_checked = False
_graph_connection_available = False
_graph_connection_error = None

def ensure_graph_connection():
    """
    Ensure graph connection is checked and available.
    Updates GRAPH_AVAILABLE and GRAPH_ERROR globals.
    """
    global GRAPH_AVAILABLE, GRAPH_ERROR, _graph_connection_checked, _graph_connection_available, _graph_connection_error
    
    if not GRAPH_IMPORTS_AVAILABLE:
        error_msg = f"Graph components not imported: {_GRAPH_IMPORT_ERROR}" if _GRAPH_IMPORT_ERROR else "Graph components not imported"
        GRAPH_AVAILABLE = False
        GRAPH_ERROR = error_msg
        return False
    
    # Only check once (lazy initialization)
    if not _graph_connection_checked:
        _graph_connection_available, _graph_connection_error = check_graph_connection()
        _graph_connection_checked = True
        GRAPH_AVAILABLE = _graph_connection_available
        GRAPH_ERROR = _graph_connection_error
        
        if GRAPH_AVAILABLE:
            logging.info("✅ Graph connection verified and available")
        else:
            logging.warning(f"Graph connection not available: {GRAPH_ERROR}")
    
    GRAPH_AVAILABLE = _graph_connection_available
    GRAPH_ERROR = _graph_connection_error
    return GRAPH_AVAILABLE



# ========== REQUEST/RESPONSE MODELS ==========

class GraphQueryRequest(BaseModel):
    """Request for executing a Cypher query."""
    cypher: str = Field(..., description="Cypher query to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Query parameters")
    format: str = Field(default="records", description="Response format: 'records' or 'nvl'")


class GraphChatRequest(BaseModel):
    """Request for graph chat endpoint."""
    message: str = Field(..., description="User message/question")
    trace_id: Optional[str] = Field(None, description="Optional trace ID to scope the conversation")


class NLQueryRequest(BaseModel):
    """Request for natural language query."""
    query: str = Field(..., description="Natural language question")
    trace_id: Optional[str] = Field(None, description="Optional trace ID to scope query")
    generate_chart: bool = Field(default=False, description="Generate chart visualization spec")


class TraceSummaryResponse(BaseModel):
    """Response with trace summary."""
    trace_id: str
    problem_type: Optional[str]
    domain: Optional[str]
    confidence: Optional[float]
    constraint_count: int
    objective_count: int
    parameter_count: int
    chunk_count: int
    assumption_count: int
    question_count: int
    solution_status: Optional[str]
    created_at: Optional[str]


# ========== HELPER FUNCTIONS ==========

def serialize_neo4j_value(value: Any) -> Any:
    """
    Recursively serialize Neo4j values to JSON-serializable types.
    
    Handles:
    - neo4j.time.DateTime
    - neo4j.time.Date
    - neo4j.time.Time
    - neo4j.time.Duration
    - Other Neo4j types
    """
    if value is None:
        return None
    
    # Check for Neo4j time types
    if hasattr(value, '__class__'):
        class_name = value.__class__.__name__
        module_name = getattr(value.__class__, '__module__', '')
        
        # Neo4j DateTime
        if 'DateTime' in class_name or (module_name and 'neo4j' in module_name and 'time' in module_name and 'DateTime' in str(type(value))):
            try:
                # Convert to ISO format string
                return value.iso_format() if hasattr(value, 'iso_format') else str(value)
            except:
                return str(value)
        
        # Neo4j Date
        elif 'Date' in class_name and 'DateTime' not in class_name:
            try:
                return value.iso_format() if hasattr(value, 'iso_format') else str(value)
            except:
                return str(value)
        
        # Neo4j Time
        elif 'Time' in class_name and 'DateTime' not in class_name:
            try:
                return value.iso_format() if hasattr(value, 'iso_format') else str(value)
            except:
                return str(value)
        
        # Neo4j Duration
        elif 'Duration' in class_name:
            return str(value)
        
        # Dict-like objects (Node, Relationship properties)
        elif hasattr(value, 'keys') and hasattr(value, '__getitem__'):
            return {k: serialize_neo4j_value(v) for k, v in value.items()}
        
        # List-like objects
        elif isinstance(value, (list, tuple)):
            return [serialize_neo4j_value(item) for item in value]
    
    # Standard Python types
    if isinstance(value, dict):
        return {k: serialize_neo4j_value(v) for k, v in value.items()}
    elif isinstance(value, (list, tuple)):
        return [serialize_neo4j_value(item) for item in value]
    
    # Try to convert to standard types
    try:
        if isinstance(value, (int, float, str, bool)):
            return value
        # For other types, try str conversion
        return str(value)
    except:
        return None


def format_for_nvl(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Transform Neo4j records to NVL (Neo4j Visualization Library) format.
    
    NVL expects:
    {
        "nodes": [
            {"id": "node1", "labels": ["Label"], "properties": {...}}
        ],
        "relationships": [
            {"id": "rel1", "type": "REL_TYPE", "startNodeId": "node1", "endNodeId": "node2", "properties": {...}}
        ]
    }
    
    Handles both raw Neo4j objects and serialized dicts.
    """
    nodes = []
    relationships = []
    node_map = {}  # Track nodes by their internal Neo4j ID
    
    for record in records:
        # Extract nodes and relationships from record
        for key, value in record.items():
            if value is None:
                continue  # Skip None values from OPTIONAL MATCH
                
            # Check if it's a raw Neo4j object
            if hasattr(value, '__class__'):
                # Check if it's a Relationship (has type, start_node, end_node attributes)
                # Note: Relationship class name is the relationship type (e.g., 'DECOMPOSED_TO'), not 'Relationship'
                if hasattr(value, 'type') and hasattr(value, 'start_node') and hasattr(value, 'end_node'):
                    # It's a Relationship
                    rel_id = str(getattr(value, 'id', getattr(value, 'element_id', '')))
                    # Serialize properties to handle DateTime and other Neo4j types
                    properties = serialize_neo4j_value(dict(value))
                    rel = {
                        "id": rel_id,
                        "type": value.type,
                        "startNodeId": str(getattr(value.start_node, 'id', getattr(value.start_node, 'element_id', ''))),
                        "endNodeId": str(getattr(value.end_node, 'id', getattr(value.end_node, 'element_id', ''))),
                        "properties": properties
                    }
                    relationships.append(rel)
                
                # Check if it's a Node (has labels attribute)
                elif hasattr(value, 'labels'):
                    node_id = str(getattr(value, 'id', getattr(value, 'element_id', '')))
                    if node_id not in node_map:
                        # Serialize properties to handle DateTime and other Neo4j types
                        properties = serialize_neo4j_value(dict(value))
                        node = {
                            "id": node_id,
                            "labels": list(value.labels),
                            "properties": properties
                        }
                        # CRITICAL: If this is the Problem node (key 'p'), add it at the beginning
                        if key == 'p':
                            nodes.insert(0, node)  # Insert at beginning to make it the root
                        else:
                            nodes.append(node)
                        node_map[node_id] = node
            
            # Check if it's already a serialized dict (from JSON deserialization)
            elif isinstance(value, dict):
                # Check if it looks like a Node dict
                if "id" in value and "labels" in value:
                    node_id = str(value.get("id"))
                    if node_id not in node_map:
                        node = {
                            "id": node_id,
                            "labels": value.get("labels", []),
                            "properties": value.get("properties", {})
                        }
                        # CRITICAL: If this is the Problem node (key 'p'), add it at the beginning
                        if key == 'p':
                            nodes.insert(0, node)  # Insert at beginning to make it the root
                        else:
                            nodes.append(node)
                        node_map[node_id] = node
                
                # Check if it looks like a Relationship dict
                elif "type" in value and ("startNodeId" in value or "start_node" in value):
                    start_node_id = str(value.get("startNodeId") or value.get("start_node", {}).get("id", ""))
                    end_node_id = str(value.get("endNodeId") or value.get("end_node", {}).get("id", ""))
                    if start_node_id and end_node_id:
                        rel = {
                            "id": str(value.get("id", f"{start_node_id}-{end_node_id}")),
                            "type": value.get("type", ""),
                            "startNodeId": start_node_id,
                            "endNodeId": end_node_id,
                            "properties": value.get("properties", {})
                        }
                        relationships.append(rel)
    
    # CRITICAL: Create virtual relationships for orphaned nodes to Problem node
    # Orphaned nodes are nodes that belong to the trace but aren't connected via relationships
    # Find Problem node
    problem_node = None
    for node in nodes:
        if "Problem" in node.get("labels", []):
            problem_node = node
            break
    
    if problem_node:
        problem_id = problem_node.get("id")
        connected_node_ids = set()
        
        # Track which nodes are connected to Problem
        for rel in relationships:
            if rel.get("startNodeId") == problem_id:
                connected_node_ids.add(rel.get("endNodeId"))
            elif rel.get("endNodeId") == problem_id:
                connected_node_ids.add(rel.get("startNodeId"))
        
        # Create virtual relationships for orphaned nodes
        for node in nodes:
            node_id = node.get("id")
            if node_id != problem_id and node_id not in connected_node_ids:
                # Determine relationship type based on node labels
                labels = node.get("labels", [])
                rel_type = "RELATED_TO"  # Default
                
                if "Constraint" in labels:
                    rel_type = "HAS_CONSTRAINT"
                elif "Objective" in labels:
                    rel_type = "HAS_OBJECTIVE"
                elif "Parameter" in labels:
                    rel_type = "HAS_PARAMETER"
                elif "DecisionEvent" in labels:
                    rel_type = "TRIGGERED"
                elif "Chunk" in labels:
                    rel_type = "DECOMPOSED_TO"
                elif "Assumption" in labels:
                    rel_type = "ASSUMES"
                elif "Question" in labels:
                    rel_type = "NEEDS_CLARIFICATION"
                elif "Solution" in labels:
                    rel_type = "SOLVED_BY"
                
                # Create virtual relationship
                virtual_rel = {
                    "id": f"virtual_{problem_id}_{node_id}",
                    "type": rel_type,
                    "startNodeId": problem_id,
                    "endNodeId": node_id,
                    "properties": {
                        "is_virtual": True,
                        "reason": "Orphaned node - created without proper relationship to Problem"
                    }
                }
                relationships.append(virtual_rel)
                logger.info(f"Created virtual relationship: {rel_type} from Problem to {labels[0] if labels else 'Node'}")
    
    return {
        "nodes": nodes,
        "relationships": relationships
    }


def convert_nl_to_cypher(nl_query: str, trace_id: Optional[str] = None) -> str:
    """
    Convert natural language query to Cypher.
    
    This is a simplified implementation. For production, integrate NeoConverse:
    - pip install neoconverse
    - Use NeoConverse API for LLM-powered NL-to-Cypher translation
    
    For now, we use pattern matching for common queries.
    """
    query_lower = nl_query.lower()
    
    # Pattern: "binding constraints" - return ONLY constraint nodes (not all nodes)
    # Note: "Binding" constraints are those that actually limit the solution
    # Since is_binding may not be set, return all constraints for now
    if "binding" in query_lower and "constraint" in query_lower:
        if trace_id:
            return """
                MATCH (p:Problem {trace_id: $trace_id})-[:HAS_CONSTRAINT]->(c:Constraint)
                WHERE c.is_binding = true OR c.binding_nature = 'binding' OR c.is_binding IS NULL
                RETURN c
                ORDER BY c.name
            """
        else:
            return """
                MATCH (c:Constraint)
                WHERE c.is_binding = true OR c.binding_nature = 'binding' OR c.is_binding IS NULL
                RETURN c
                ORDER BY c.name
                LIMIT 100
            """
    
    # Pattern: "Show me all constraints" or "constraints" - return only constraint nodes
    if "constraint" in query_lower:
        if trace_id:
            return """
                MATCH (p:Problem {trace_id: $trace_id})-[:HAS_CONSTRAINT]->(c:Constraint)
                RETURN c
                ORDER BY c.name
            """
        else:
            return """
                MATCH (c:Constraint)
                RETURN c
                ORDER BY c.name
                LIMIT 100
            """
    
    # Pattern: "What objectives were identified"
    if "objective" in query_lower:
        if trace_id:
            return """
                MATCH (p:Problem {trace_id: $trace_id})-[:HAS_OBJECTIVE]->(o:Objective)
                RETURN o
                ORDER BY o.name
            """
        else:
            return """
                MATCH (o:Objective)
                RETURN o
                ORDER BY o.name
                LIMIT 100
            """
    
    # Pattern: "Show me the decision trace"
    if "trace" in query_lower or "decision" in query_lower:
        if trace_id:
            return """
                MATCH (p:Problem {trace_id: $trace_id})-[*]-(n)
                RETURN p, n
                LIMIT 500
            """
        else:
            return """
                MATCH (p:Problem)
                OPTIONAL MATCH (p)-[*]-(n)
                RETURN p, n
                LIMIT 500
            """
    
    # Default: Return problem and related nodes
    if trace_id:
        return """
            MATCH (p:Problem {trace_id: $trace_id})-[*]-(n)
            RETURN p, n
            LIMIT 500
        """
    else:
        return """
            MATCH (p:Problem)
            OPTIONAL MATCH (p)-[:HAS_CONSTRAINT|HAS_OBJECTIVE|HAS_PARAMETER]->(n)
            RETURN p, n
            LIMIT 500
        """


# ========== ENDPOINTS ==========

@router.post("/chat", response_model=Dict[str, Any])
async def graph_chat(
    request: GraphChatRequest,
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Chat endpoint for querying decisions, entities, and policies using natural language.
    
    Uses LLM with full trace context to answer questions about:
    - Decisions made for a trace
    - Similar decisions
    - Causal chains
    - Entities involved
    - Policies applied
    
    Returns structured data to update graph and decision trace panels.
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    message = request.message
    trace_id = request.trace_id
    
    if not trace_id:
        return {
            "response": "Please provide a trace_id to query the decision trace.",
            "decisions": [],
            "entities": [],
            "decision_id": None,
            "node_ids": [],
            "recommended_questions": [
                "What decisions were made for this problem?",
                "Show me the causal chain of decisions",
                "What constraints affected the decisions?",
                "Which objectives were optimized?",
                "What risks were identified?"
            ]
        }
    
    executor = GraphExecutor()
    try:
        # Load full trace graph data for LLM context
        logger.info(f"[graph_chat] Loading full trace graph for trace_id: {trace_id}")
        
        # Get trace summary first
        cypher_summary = """
            MATCH (p:Problem {trace_id: $trace_id})
            OPTIONAL MATCH (p)-[:TRIGGERED]->(de:DecisionEvent)
            OPTIONAL MATCH (p)-[:HAS_CONSTRAINT]->(c:Constraint)
            OPTIONAL MATCH (p)-[:HAS_OBJECTIVE]->(o:Objective)
            OPTIONAL MATCH (p)-[:HAS_PARAMETER]->(param:Parameter)
            RETURN 
                p.problem_type as problem_type,
                p.domain as domain,
                p.description as problem_description,
                count(DISTINCT de) as decision_count,
                count(DISTINCT c) as constraint_count,
                count(DISTINCT o) as objective_count,
                count(DISTINCT param) as parameter_count
        """
        summary_records = executor.execute_read(cypher_summary, {"trace_id": trace_id})
        trace_summary = summary_records[0] if summary_records else {}
        
        # Get all DecisionEvents with their details
        cypher_decisions = """
            MATCH (p:Problem {trace_id: $trace_id})-[:TRIGGERED]->(de:DecisionEvent)
            OPTIONAL MATCH (de)-[:ABOUT]->(entity)
            OPTIONAL MATCH (a:Actor)-[:MADE_DECISION]->(de)
            OPTIONAL MATCH (de)-[:MEASURES]->(m:Metric)
            OPTIONAL MATCH (de)-[:IMPLEMENTS]->(i:Intervention)
            OPTIONAL MATCH (de)-[:IDENTIFIES]->(r:Risk)
            RETURN de,
                   collect(DISTINCT {id: entity.id, label: labels(entity), name: entity.name}) as linked_entities,
                   collect(DISTINCT {id: a.id, name: a.name, type: a.type}) as actors,
                   collect(DISTINCT {id: m.id, name: m.name, value: m.value}) as metrics,
                   collect(DISTINCT {id: i.id, type: i.type, action: i.action}) as interventions,
                   collect(DISTINCT {id: r.id, type: r.type, severity: r.severity}) as risks
            ORDER BY de.timestamp
        """
        decision_records = executor.execute_read(cypher_decisions, {"trace_id": trace_id})
        
        # Format trace data for LLM
        trace_context = {
            "trace_id": trace_id,
            "problem": {
                "type": trace_summary.get("problem_type", "Unknown"),
                "domain": trace_summary.get("domain", "Unknown"),
                "description": trace_summary.get("problem_description", ""),
                "constraints_count": trace_summary.get("constraint_count", 0),
                "objectives_count": trace_summary.get("objective_count", 0),
                "parameters_count": trace_summary.get("parameter_count", 0)
            },
            "decisions": []
        }
        
        for record in decision_records:
            de = record.get("de")
            if de:
                de_dict = dict(de)
                trace_context["decisions"].append({
                    "id": str(de_dict.get("id", "")),
                    "decision_type": de_dict.get("decision_type", ""),
                    "decision": de_dict.get("decision", ""),
                    "reasoning": de_dict.get("reasoning", ""),
                    "agent": de_dict.get("agent", ""),
                    "timestamp": str(de_dict.get("timestamp", "")) if de_dict.get("timestamp") else None,
                    "linked_entities": record.get("linked_entities", []),
                    "actors": record.get("actors", []),
                    "metrics": record.get("metrics", []),
                    "interventions": record.get("interventions", []),
                    "risks": record.get("risks", [])
                })
        
        # Use LLM to answer the question with full trace context
        try:
            from dcisionai_workflow.shared.llm.client import LLMClient
            llm_client = LLMClient()
            
            # Build prompt for LLM
            system_prompt = """You are a decision trace analyst helping users understand optimization decisions.

You have access to a complete decision trace graph that shows:
- The problem being solved
- All decisions made during optimization
- Entities involved (constraints, objectives, parameters)
- Actors who made decisions
- Metrics measured
- Interventions implemented
- Risks identified
- Causal relationships between decisions

Your task is to answer the user's question based on the trace data provided. Be specific and reference actual decisions, entities, and relationships from the trace.

When answering:
1. Reference specific decisions by their decision_type and reasoning
2. Mention relevant entities (constraints, objectives, parameters)
3. Explain causal relationships when relevant
4. If the question asks about a specific decision, provide its ID in the response

Format your response as natural language, but be precise and factual based on the trace data."""
            
            user_prompt = f"""Trace Context:
{json.dumps(trace_context, indent=2)}

User Question: {message}

Please answer the user's question based on the trace data above. Be specific and reference actual decisions, entities, and relationships from the trace.

If the question asks about a specific decision, identify which decision(s) are relevant and provide their IDs.

Format your response as clear, natural language."""
            
            llm_response = await llm_client.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=2000
            )
            
            # Parse LLM response to extract decision IDs and entity references
            # Simple extraction - can be enhanced with structured output
            decision_ids = []
            node_ids = []
            
            # Extract decision IDs mentioned in response
            for decision in trace_context["decisions"]:
                if decision["id"] in llm_response or decision["decision_type"] in llm_response:
                    decision_ids.append(decision["id"])
            
            # Build response
            response = {
                "response": llm_response,
                "decisions": [d for d in trace_context["decisions"] if d["id"] in decision_ids],
                "entities": [],
                "decision_id": decision_ids[0] if decision_ids else None,
                "node_ids": node_ids,  # For graph highlighting
                "recommended_questions": [
                    "What decisions were made for this problem?",
                    "Show me the causal chain of decisions",
                    "What constraints affected the decisions?",
                    "Which objectives were optimized?",
                    "What risks were identified?"
                ]
            }
            
            return response
            
        except Exception as llm_error:
            logger.error(f"[graph_chat] LLM error: {llm_error}", exc_info=True)
            # Fallback to keyword-based routing
            message_lower = message.lower()
            response = {
                "response": "",
                "decisions": [],
                "entities": [],
                "decision_id": None,
                "node_ids": [],
                "recommended_questions": [
                    "What decisions were made for this problem?",
                    "Show me the causal chain of decisions",
                    "What constraints affected the decisions?",
                    "Which objectives were optimized?",
                    "What risks were identified?"
                ]
            }
            
            # Query for decisions in a trace
            if "decision" in message_lower or "what" in message_lower or "show" in message_lower:
                cypher = """
                    MATCH (p:Problem {trace_id: $trace_id})-[:TRIGGERED]->(de:DecisionEvent)
                    RETURN de
                    ORDER BY de.timestamp
                    LIMIT 10
                """
                records = executor.execute_read(cypher, {"trace_id": trace_id})
                decisions = []
                for record in records:
                    de = record.get("de")
                    if de:
                        decisions.append({
                            "id": str(de.id),
                            "decision": dict(de).get("decision", ""),
                            "decision_type": dict(de).get("decision_type", ""),
                            "reasoning": dict(de).get("reasoning", ""),
                            "timestamp": dict(de).get("timestamp", ""),
                        })
                response["decisions"] = decisions
                response["response"] = f"Found {len(decisions)} decisions for this trace."
                if decisions:
                    response["decision_id"] = decisions[0]["id"]
            
            return response
        
    except Exception as e:
        logger.error(f"Failed to process chat message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process chat: {str(e)}")
    finally:
        executor.close()


@router.get("/health")
async def graph_health():
    """
    Health check for graph API.
    
    Returns detailed information about graph availability and connection status.
    """
    # Force re-check connection for health endpoint
    is_available, error_msg = check_graph_connection()
    # Update global state
    global GRAPH_AVAILABLE, GRAPH_ERROR, _graph_connection_checked, _graph_connection_available, _graph_connection_error
    _graph_connection_available = is_available
    _graph_connection_error = error_msg
    _graph_connection_checked = True
    GRAPH_AVAILABLE = is_available
    GRAPH_ERROR = error_msg
    
    # Try to get config info (without sensitive data)
    config_info = {}
    try:
        if GRAPH_IMPORTS_AVAILABLE:
            config = load_neo4j_config()
            config_info = {
                "uri_configured": bool(config.get("uri")),
                "user_configured": bool(config.get("user")),
                "password_configured": bool(config.get("password")),
                "uri_preview": config.get("uri", "")[:50] + "..." if config.get("uri") else None
            }
        else:
            config_info = {"error": "Graph imports not available"}
    except Exception as e:
        config_info = {"error": str(e)}
    
    return {
        "status": "ok" if is_available else "error",
        "graph_available": is_available,
        "imports_available": GRAPH_IMPORTS_AVAILABLE,
        "error": error_msg,
        "config": config_info,
        "endpoints": [
            "/api/graph/query",
            "/api/graph/trace/{trace_id}",
            "/api/graph/trace/{trace_id}/summary",
            "/api/graph/nl-query"
        ]
    }


@router.post("/query", response_model=Dict[str, Any])
async def execute_graph_query(
    request: GraphQueryRequest,
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Execute a Cypher query and return results.
    
    Supports two formats:
    - "records": Raw Neo4j records (default)
    - "nvl": Neo4j Visualization Library format
    """
    # Ensure connection is checked
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        # Execute query
        records = executor.execute_read(request.cypher, request.parameters)
        
        # Format response
        if request.format == "nvl":
            formatted = format_for_nvl(records)
            return formatted
        else:
            # Return as records (convert to JSON-serializable format)
            result = []
            for record in records:
                record_dict = {}
                for key, value in record.items():
                    # Convert Neo4j types to Python types using serialize_neo4j_value
                    if hasattr(value, '__class__'):
                        class_name = value.__class__.__name__
                        if class_name in ['Node', 'Relationship', 'Path']:
                            # Convert to dict representation
                            if class_name == 'Node':
                                record_dict[key] = {
                                    "id": str(value.id),
                                    "labels": list(value.labels),
                                    "properties": serialize_neo4j_value(dict(value))
                                }
                            elif class_name == 'Relationship':
                                record_dict[key] = {
                                    "id": str(value.id),
                                    "type": value.type,
                                    "startNodeId": str(value.start_node.id),
                                    "endNodeId": str(value.end_node.id),
                                    "properties": serialize_neo4j_value(dict(value))
                                }
                            else:
                                record_dict[key] = serialize_neo4j_value(value)
                        else:
                            record_dict[key] = serialize_neo4j_value(value)
                    else:
                        record_dict[key] = serialize_neo4j_value(value)
                result.append(record_dict)
            
            return {
                "records": result,
                "count": len(result)
            }
    except Exception as e:
        logger.error(f"Graph query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")
    finally:
        executor.close()


@router.get("/decisions/patterns/{decision_type}", response_model=Dict[str, Any])
async def get_decision_patterns(
    decision_type: str,
    min_occurrences: int = Query(default=5, description="Minimum occurrences to consider a pattern"),
    time_window_days: int = Query(default=30, description="Time window in days"),
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get learned patterns for a decision type.
    
    Analyzes decision traces to extract:
    - Successful patterns (high success rate)
    - Common reasoning patterns
    - Context patterns that lead to success
    
    This enables the flywheel: learn from past decisions to improve future ones.
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        from dcisionai_workflow.shared.graph.feedback_analyzer import FeedbackAnalyzer
        
        analyzer = FeedbackAnalyzer(executor)
        patterns = analyzer.analyze_decision_patterns(
            decision_type=decision_type,
            min_occurrences=min_occurrences,
            time_window_days=time_window_days
        )
        
        return patterns
    except Exception as e:
        logger.error(f"Failed to get decision patterns: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze patterns: {str(e)}")
    finally:
        executor.close()


@router.get("/decisions/feedback/{decision_type}", response_model=Dict[str, Any])
async def get_decision_feedback(
    decision_type: str,
    context: str = Query(default="{}", description="JSON string of context"),
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get feedback/recommendations for making a decision.
    
    Uses learned patterns to suggest what has worked in similar contexts.
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        import json
        context_dict = json.loads(context) if context else {}
        
        from dcisionai_workflow.shared.graph.feedback_analyzer import FeedbackAnalyzer
        
        analyzer = FeedbackAnalyzer(executor)
        feedback = analyzer.provide_decision_feedback(
            decision_type=decision_type,
            context=context_dict
        )
        
        return feedback
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in context parameter")
    except Exception as e:
        logger.error(f"Failed to get decision feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get feedback: {str(e)}")
    finally:
        executor.close()


@router.get("/decisions/query-by-context", response_model=Dict[str, Any])
async def query_decisions_by_context(
    constraint_count: Optional[int] = Query(default=None, description="Filter by constraint_count"),
    solve_time_ms: Optional[int] = Query(default=None, description="Filter by solve_time_ms (max)"),
    status: Optional[str] = Query(default=None, description="Filter by status"),
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Query DecisionEvents by context properties using DecisionContext nodes.
    
    Enables queries like:
    - Find all decisions where constraint_count > 10
    - Find all decisions where solve_time_ms < 100
    - Find all decisions where status = 'optimal'
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        from dcisionai_workflow.shared.graph.context_extractor import query_decisions_by_context
        
        # Build filters
        filters = {}
        if constraint_count is not None:
            filters["constraint_count"] = {"$gte": constraint_count}
        if solve_time_ms is not None:
            filters["solve_time_ms"] = {"$lte": solve_time_ms}
        if status:
            filters["status"] = status
        
        decisions = query_decisions_by_context(executor, filters)
        
        return {
            "decisions": decisions,
            "count": len(decisions)
        }
    except Exception as e:
        logger.error(f"Failed to query decisions by context: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to query decisions: {str(e)}")
    finally:
        executor.close()


@router.get("/traces/{trace_id}/analysis", response_model=Dict[str, Any])
async def get_trace_analysis(
    trace_id: str,
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get analysis and learnings from a completed trace.
    
    Analyzes the trace to extract successful patterns and learnings.
    This implements the feedback loop: analyze completed traces to improve future decisions.
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        from dcisionai_workflow.shared.graph.feedback_analyzer import analyze_trace_for_improvement
        
        analysis = analyze_trace_for_improvement(executor, trace_id)
        
        return analysis
    except Exception as e:
        logger.error(f"Failed to analyze trace: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze trace: {str(e)}")
    finally:
        executor.close()


@router.get("/trace/{trace_id}", response_model=Dict[str, Any])
async def get_trace_graph(
    trace_id: str,
    format: str = Query(default="nvl", description="Response format: 'records' or 'nvl'"),
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get complete decision trace graph for a given trace_id.
    
    Returns all nodes and relationships connected to the Problem node.
    """
    # Ensure connection is checked
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        executor.set_trace_id(trace_id)
        
        # Query for decision trace graph with clear causal flow
        # Strategy: Use UNION to avoid cartesian products, emphasize Problem → DecisionEvent chain → Entities
        # This creates a cleaner, more structured visualization showing the decision flow
        cypher = """
            MATCH (p:Problem {trace_id: $trace_id})
            
            // Use UNION to combine different relationship types without cartesian products
            // 1. Problem node itself
            RETURN p as p, null as n, null as r, 'problem' as type
            
            UNION ALL
            
            // 2. Problem → DecisionEvents/Decisions (TRIGGERED)
            // Support both DecisionEvent (our schema) and Decision (context-graph-demo schema)
            MATCH (p:Problem {trace_id: $trace_id})-[r:TRIGGERED]->(de)
            WHERE 'DecisionEvent' IN labels(de) OR 'Decision' IN labels(de)
            RETURN p, de as n, r as r, 'triggered' as type
            
            UNION ALL
            
            // 3. DecisionEvent/Decision chain (LED_TO, CAUSED, INFLUENCED)
            // Support both DecisionEvent and Decision labels
            MATCH (p:Problem {trace_id: $trace_id})-[:TRIGGERED]->(de1)
            WHERE 'DecisionEvent' IN labels(de1) OR 'Decision' IN labels(de1)
            MATCH path = (de1)-[:LED_TO|CAUSED|INFLUENCED*]->(de2)
            WHERE ('DecisionEvent' IN labels(de2) OR 'Decision' IN labels(de2))
            UNWIND relationships(path) as rel
            WITH p, startNode(rel) as fromNode, endNode(rel) as toNode, rel, type(rel) as relType
            RETURN p, toNode as n, rel as r, 'decision_chain' as type
            
            UNION ALL
            
            // 4. DecisionEvents/Decisions → Entities (ABOUT)
            MATCH (p:Problem {trace_id: $trace_id})-[:TRIGGERED]->(de)
            WHERE 'DecisionEvent' IN labels(de) OR 'Decision' IN labels(de)
            MATCH (de)-[r:ABOUT]->(entity)
            RETURN p, entity as n, r as r, 'about' as type
            
            UNION ALL
            
            // 5. Problem → Constraints (HAS_CONSTRAINT)
            MATCH (p:Problem {trace_id: $trace_id})-[r:HAS_CONSTRAINT]->(constraint:Constraint)
            RETURN p, constraint as n, r as r, 'constraint' as type
            
            UNION ALL
            
            // 6. Problem → Objectives (HAS_OBJECTIVE)
            MATCH (p:Problem {trace_id: $trace_id})-[r:HAS_OBJECTIVE]->(objective:Objective)
            RETURN p, objective as n, r as r, 'objective' as type
            
            UNION ALL
            
            // 7. Problem → Parameters (HAS_PARAMETER)
            MATCH (p:Problem {trace_id: $trace_id})-[r:HAS_PARAMETER]->(parameter:Parameter)
            RETURN p, parameter as n, r as r, 'parameter' as type
            
            UNION ALL
            
            // 8. Problem → Solution (SOLVED_BY)
            MATCH (p:Problem {trace_id: $trace_id})-[r:SOLVED_BY]->(solution:Solution)
            RETURN p, solution as n, r as r, 'solution' as type
            
            UNION ALL
            
            // 9. DecisionEvents/Decisions → DecisionContext (HAS_CONTEXT)
            MATCH (p:Problem {trace_id: $trace_id})-[:TRIGGERED]->(de)
            WHERE 'DecisionEvent' IN labels(de) OR 'Decision' IN labels(de)
            MATCH (de)-[r:HAS_CONTEXT]->(ctx:DecisionContext)
            RETURN p, ctx as n, r as r, 'context' as type
            
            UNION ALL
            
            // 10. DecisionEvents/Decisions → Exceptions (GRANTED_EXCEPTION)
            MATCH (p:Problem {trace_id: $trace_id})-[:TRIGGERED]->(de)
            WHERE 'DecisionEvent' IN labels(de) OR 'Decision' IN labels(de)
            MATCH (de)-[r:GRANTED_EXCEPTION]->(exc:Exception)
            RETURN p, exc as n, r as r, 'exception' as type
            
            UNION ALL
            
            // 11. DecisionEvents/Decisions → Policies (APPLIED_POLICY)
            MATCH (p:Problem {trace_id: $trace_id})-[:TRIGGERED]->(de)
            WHERE 'DecisionEvent' IN labels(de) OR 'Decision' IN labels(de)
            MATCH (de)-[r:APPLIED_POLICY]->(pol:Policy)
            RETURN p, pol as n, r as r, 'policy' as type
            
            UNION ALL
            
            // 12. Actors → DecisionEvents/Decisions (MADE_DECISION)
            MATCH (p:Problem {trace_id: $trace_id})-[:TRIGGERED]->(de)
            WHERE 'DecisionEvent' IN labels(de) OR 'Decision' IN labels(de)
            MATCH (a:Actor)-[r:MADE_DECISION]->(de)
            RETURN p, a as n, r as r, 'actor' as type
            
            UNION ALL
            
            // 13. DecisionEvents/Decisions → Metrics (MEASURES)
            MATCH (p:Problem {trace_id: $trace_id})-[:TRIGGERED]->(de)
            WHERE 'DecisionEvent' IN labels(de) OR 'Decision' IN labels(de)
            MATCH (de)-[r:MEASURES]->(m:Metric)
            RETURN p, m as n, r as r, 'metric' as type
            
            UNION ALL
            
            // 14. DecisionEvents/Decisions → Interventions (IMPLEMENTS)
            MATCH (p:Problem {trace_id: $trace_id})-[:TRIGGERED]->(de)
            WHERE 'DecisionEvent' IN labels(de) OR 'Decision' IN labels(de)
            MATCH (de)-[r:IMPLEMENTS]->(i:Intervention)
            RETURN p, i as n, r as r, 'intervention' as type
            
            UNION ALL
            
            // 15. DecisionEvents/Decisions → Risks (IDENTIFIES)
            MATCH (p:Problem {trace_id: $trace_id})-[:TRIGGERED]->(de)
            WHERE 'DecisionEvent' IN labels(de) OR 'Decision' IN labels(de)
            MATCH (de)-[r:IDENTIFIES]->(risk:Risk)
            RETURN p, risk as n, r as r, 'risk' as type
            
            UNION ALL
            
            // 16. Interventions → Solutions (PRODUCED)
            MATCH (p:Problem {trace_id: $trace_id})-[:TRIGGERED]->(de)
            WHERE 'DecisionEvent' IN labels(de) OR 'Decision' IN labels(de)
            MATCH (de)-[:IMPLEMENTS]->(i:Intervention)
            MATCH (i)-[r:PRODUCED]->(s:Solution)
            RETURN p, s as n, r as r, 'solution' as type
            
            UNION ALL
            
            // 17. Risks → Exceptions (TRIGGERED)
            MATCH (p:Problem {trace_id: $trace_id})-[:TRIGGERED]->(de)
            WHERE 'DecisionEvent' IN labels(de) OR 'Decision' IN labels(de)
            MATCH (de)-[:IDENTIFIES]->(risk:Risk)
            MATCH (risk)-[r:TRIGGERED]->(exc:Exception)
            RETURN p, exc as n, r as r, 'exception' as type
            """
        
        records = executor.execute_read(cypher, {"trace_id": trace_id})
        
        logger.info(f"[get_trace_graph] Query returned {len(records) if records else 0} records for trace_id: {trace_id}")
        
        # Filter out null nodes and deduplicate
        if records:
            seen_nodes = set()
            seen_relationships = set()
            filtered_records = []
            
            for record in records:
                p = record.get("p")
                n = record.get("n")
                r = record.get("r")
                
                # Skip if both n and r are null (except for problem node itself)
                if not n and not r and record.get("type") != "problem":
                    continue
                
                # Deduplicate nodes - add node if not seen
                if n:
                    node_id = str(n.id) if hasattr(n, 'id') else str(getattr(n, 'element_id', ''))
                    if node_id and node_id in seen_nodes:
                        # Node already added, but we might need to add the relationship
                        if r:
                            # Create relationship key
                            start_id = str(p.id) if p and hasattr(p, 'id') else (str(n.id) if n and hasattr(n, 'id') else '')
                            end_id = node_id
                            rel_type = r.type if hasattr(r, 'type') else 'RELATED_TO'
                            rel_key = f"{start_id}-{rel_type}-{end_id}"
                            
                            if rel_key not in seen_relationships:
                                # Find existing record with this node and add relationship
                                for existing_record in filtered_records:
                                    existing_n = existing_record.get("n")
                                    if existing_n and hasattr(existing_n, 'id'):
                                        existing_node_id = str(existing_n.id)
                                        if existing_node_id == node_id:
                                            # Add relationship to this record
                                            existing_record["r"] = r
                                            seen_relationships.add(rel_key)
                                            break
                        continue
                    if node_id:
                        seen_nodes.add(node_id)
                
                # Deduplicate relationships
                if r:
                    # Determine start and end nodes for relationship
                    if hasattr(r, 'start_node') and hasattr(r, 'end_node'):
                        start_id = str(r.start_node.id) if hasattr(r.start_node, 'id') else ''
                        end_id = str(r.end_node.id) if hasattr(r.end_node, 'id') else ''
                    elif p and n:
                        # Infer from context: if we have p and n, relationship is p->n
                        start_id = str(p.id) if hasattr(p, 'id') else ''
                        end_id = str(n.id) if hasattr(n, 'id') else ''
                    else:
                        start_id = ''
                        end_id = ''
                    
                    rel_type = r.type if hasattr(r, 'type') else 'RELATED_TO'
                    rel_key = f"{start_id}-{rel_type}-{end_id}"
                    
                    if rel_key in seen_relationships:
                        continue
                    seen_relationships.add(rel_key)
                
                filtered_records.append({"p": p, "n": n, "r": r})
            
            records = filtered_records
            logger.info(f"[get_trace_graph] Filtered to {len(records)} unique records with {len(seen_relationships)} relationships")
        
        # Debug: Log if no records found
        if not records or len(records) == 0:
            logger.warning(f"No records found for trace_id: {trace_id}")
            # Try a simpler query to check if Problem node exists
            check_cypher = "MATCH (p:Problem {trace_id: $trace_id}) RETURN p LIMIT 1"
            check_records = executor.execute_read(check_cypher, {"trace_id": trace_id})
            if not check_records or len(check_records) == 0:
                logger.warning(f"Problem node not found for trace_id: {trace_id}")
                # Return empty graph instead of error
                if format == "nvl":
                    return {"nodes": [], "relationships": []}
                else:
                    return {
                        "trace_id": trace_id,
                        "records": [],
                        "count": 0
                    }
            else:
                logger.info(f"Problem node exists but no connected nodes found for trace_id: {trace_id}")
                # Return at least the Problem node
                problem_record = check_records[0]
                if format == "nvl":
                    # Format just the Problem node
                    formatted = format_for_nvl([{"p": problem_record.get("p")}])
                    logger.info(f"[get_trace_graph] Formatted Problem node only: {len(formatted.get('nodes', []))} nodes, {len(formatted.get('relationships', []))} relationships")
                    return formatted
                else:
                    return {
                        "trace_id": trace_id,
                        "records": [{"p": serialize_neo4j_value(problem_record.get("p"))}],
                        "count": 1
                    }
        
        # Format response
        if format == "nvl":
            formatted = format_for_nvl(records)
            logger.info(f"[get_trace_graph] Formatted result: {len(formatted.get('nodes', []))} nodes, {len(formatted.get('relationships', []))} relationships")
            # Ensure at least the Problem node is included
            if not formatted.get("nodes") or len(formatted.get("nodes", [])) == 0:
                logger.warning(f"format_for_nvl returned no nodes for trace_id: {trace_id}, records: {len(records)}")
                # Log first record structure for debugging
                if records and len(records) > 0:
                    logger.warning(f"First record keys: {list(records[0].keys()) if records[0] else 'empty'}")
            return formatted
        else:
            # Return as records (convert to JSON-serializable format)
            result = []
            for record in records:
                record_dict = {}
                for key, value in record.items():
                    # Convert Neo4j types to Python types using serialize_neo4j_value
                    if hasattr(value, '__class__'):
                        class_name = value.__class__.__name__
                        if class_name == 'Node':
                            record_dict[key] = {
                                "id": str(value.id),
                                "labels": list(value.labels),
                                "properties": serialize_neo4j_value(dict(value))
                            }
                        else:
                            record_dict[key] = serialize_neo4j_value(value)
                    else:
                        record_dict[key] = serialize_neo4j_value(value)
                result.append(record_dict)
            
            return {
                "trace_id": trace_id,
                "records": result,
                "count": len(result)
            }
    except Exception as e:
        logger.error(f"Failed to get trace graph: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve trace: {str(e)}")
    finally:
        executor.close()


@router.get("/nodes/{node_id}/connected", response_model=Dict[str, Any])
async def get_connected_nodes(
    node_id: str,
    depth: int = Query(default=1, description="Depth of connections to fetch (1 = direct neighbors)"),
    limit: int = Query(default=50, description="Maximum number of nodes to return"),
    format: str = Query(default="nvl", description="Response format: 'records' or 'nvl'"),
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get connected nodes for a given node ID.
    
    Used for double-click to expand functionality in the graph visualization.
    
    For DecisionEvent nodes, follows the causal chain:
    - Upstream: Nodes that CAUSED or INFLUENCED this decision (backward traversal)
    - Downstream: Nodes this decision CAUSED or INFLUENCED (forward traversal)
    - Also includes entities linked via ABOUT relationships
    
    For other nodes, returns all connected nodes.
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        # First, check if the node is a DecisionEvent
        # If so, follow causal chain (CAUSED, INFLUENCED) like context-graph-demo
        check_cypher = """
            MATCH (start)
            WHERE elementId(start) = $node_id OR id(start) = toInteger($node_id)
            RETURN labels(start) as labels
            LIMIT 1
        """
        check_result = executor.execute_read(check_cypher, {"node_id": node_id})
        
        is_decision = False
        if check_result and check_result[0].get("labels"):
            labels = check_result[0]["labels"]
            is_decision = "DecisionEvent" in labels or "Decision" in labels
        
        if is_decision:
            # For DecisionEvent/Decision: Follow causal chain (CAUSED, INFLUENCED) backward and forward
            # This matches context-graph-demo behavior where double-click shows causal chain
            # Use UNION ALL to combine different relationship types (like context-graph-demo)
            # Support both DecisionEvent and Decision labels
            cypher = f"""
                MATCH (start)
                WHERE (elementId(start) = $node_id OR id(start) = toInteger($node_id))
                AND ('DecisionEvent' IN labels(start) OR 'Decision' IN labels(start))
                
                // 1. Upstream causes: What CAUSED or INFLUENCED this decision (backward traversal)
                // Matches context-graph-demo: MATCH path = (d:Decision)<-[:CAUSED|INFLUENCED*]-(cause:Decision)
                OPTIONAL MATCH path_up = (cause)-[:CAUSED|INFLUENCED*1..{depth}]->(start)
                WHERE ('DecisionEvent' IN labels(cause) OR 'Decision' IN labels(cause))
                UNWIND relationships(path_up) as r_up
                WITH start, cause as node, r_up as rel
                WHERE node IS NOT NULL
                RETURN node, rel
                
                UNION ALL
                
                // 2. Downstream effects: What this decision CAUSED or INFLUENCED (forward traversal)
                // Matches context-graph-demo: MATCH path = (d:Decision)-[:CAUSED|INFLUENCED*]->(effect:Decision)
                MATCH (start)
                WHERE (elementId(start) = $node_id OR id(start) = toInteger($node_id))
                AND ('DecisionEvent' IN labels(start) OR 'Decision' IN labels(start))
                OPTIONAL MATCH path_down = (start)-[:CAUSED|INFLUENCED*1..{depth}]->(effect)
                WHERE ('DecisionEvent' IN labels(effect) OR 'Decision' IN labels(effect))
                UNWIND relationships(path_down) as r_down
                WITH start, effect as node, r_down as rel
                WHERE node IS NOT NULL
                RETURN node, rel
                
                UNION ALL
                
                // 3. Entities linked via ABOUT relationships
                MATCH (start)
                WHERE (elementId(start) = $node_id OR id(start) = toInteger($node_id))
                AND ('DecisionEvent' IN labels(start) OR 'Decision' IN labels(start))
                OPTIONAL MATCH (start)-[r_about:ABOUT]->(entity)
                RETURN entity as node, r_about as rel
                
                UNION ALL
                
                // 4. LED_TO relationships (sequential flow) - backward
                MATCH (start)
                WHERE (elementId(start) = $node_id OR id(start) = toInteger($node_id))
                AND ('DecisionEvent' IN labels(start) OR 'Decision' IN labels(start))
                OPTIONAL MATCH (prev)-[r_prev:LED_TO]->(start)
                WHERE ('DecisionEvent' IN labels(prev) OR 'Decision' IN labels(prev))
                RETURN prev as node, r_prev as rel
                
                UNION ALL
                
                // 5. LED_TO relationships (sequential flow) - forward
                MATCH (start)
                WHERE (elementId(start) = $node_id OR id(start) = toInteger($node_id))
                AND ('DecisionEvent' IN labels(start) OR 'Decision' IN labels(start))
                OPTIONAL MATCH (start)-[r_next:LED_TO]->(next)
                WHERE ('DecisionEvent' IN labels(next) OR 'Decision' IN labels(next))
                RETURN next as node, r_next as rel
                
                UNION ALL
                
                // 6. Actors linked via MADE_DECISION
                MATCH (start)
                WHERE (elementId(start) = $node_id OR id(start) = toInteger($node_id))
                AND ('DecisionEvent' IN labels(start) OR 'Decision' IN labels(start))
                OPTIONAL MATCH (a:Actor)-[r_made:MADE_DECISION]->(start)
                RETURN a as node, r_made as rel
                
                UNION ALL
                
                // 7. Metrics linked via MEASURES
                MATCH (start)
                WHERE (elementId(start) = $node_id OR id(start) = toInteger($node_id))
                AND ('DecisionEvent' IN labels(start) OR 'Decision' IN labels(start))
                OPTIONAL MATCH (start)-[r_measures:MEASURES]->(m:Metric)
                RETURN m as node, r_measures as rel
                
                UNION ALL
                
                // 8. Interventions linked via IMPLEMENTS
                MATCH (start)
                WHERE (elementId(start) = $node_id OR id(start) = toInteger($node_id))
                AND ('DecisionEvent' IN labels(start) OR 'Decision' IN labels(start))
                OPTIONAL MATCH (start)-[r_implements:IMPLEMENTS]->(i:Intervention)
                RETURN i as node, r_implements as rel
                
                UNION ALL
                
                // 9. Risks linked via IDENTIFIES
                MATCH (start)
                WHERE (elementId(start) = $node_id OR id(start) = toInteger($node_id))
                AND ('DecisionEvent' IN labels(start) OR 'Decision' IN labels(start))
                OPTIONAL MATCH (start)-[r_identifies:IDENTIFIES]->(risk:Risk)
                RETURN risk as node, r_identifies as rel
                
                UNION ALL
                
                // 10. Interventions → Solutions (PRODUCED)
                MATCH (start)
                WHERE (elementId(start) = $node_id OR id(start) = toInteger($node_id))
                AND ('DecisionEvent' IN labels(start) OR 'Decision' IN labels(start))
                OPTIONAL MATCH (start)-[:IMPLEMENTS]->(i:Intervention)-[r_produced:PRODUCED]->(s:Solution)
                RETURN s as node, r_produced as rel
                
                UNION ALL
                
                // 11. Risks → Exceptions (TRIGGERED)
                MATCH (start)
                WHERE (elementId(start) = $node_id OR id(start) = toInteger($node_id))
                AND ('DecisionEvent' IN labels(start) OR 'Decision' IN labels(start))
                OPTIONAL MATCH (start)-[:IDENTIFIES]->(risk:Risk)-[r_triggered:TRIGGERED]->(exc:Exception)
                RETURN exc as node, r_triggered as rel
                
                LIMIT $limit
            """
        else:
            # For non-DecisionEvent nodes: Return all connected nodes (original behavior)
            cypher = """
                MATCH (start)
                WHERE elementId(start) = $node_id OR id(start) = toInteger($node_id)
                WITH start
                MATCH (start)-[r]-(connected)
                WHERE elementId(connected) <> elementId(start)
                RETURN DISTINCT connected as node, r as rel, 'connected' as type
                LIMIT $limit
                
                UNION ALL
                
                // Also return the start node itself
                MATCH (start)
                WHERE elementId(start) = $node_id OR id(start) = toInteger($node_id)
                RETURN start as node, null as rel, 'start' as type
            """
        
        records = executor.execute_read(cypher, {"node_id": node_id, "limit": limit})
        
        logger.info(f"[get_connected_nodes] Found {len(records) if records else 0} connected nodes for node_id: {node_id}")
        
        if format == "nvl":
            formatted = format_for_nvl(records)
            return formatted
        else:
            # Return as records
            result = []
            for record in records:
                record_dict = {}
                for key, value in record.items():
                    if hasattr(value, '__class__'):
                        class_name = value.__class__.__name__
                        if class_name in ['Node', 'Relationship', 'Path']:
                            if class_name == 'Node':
                                record_dict[key] = {
                                    "id": str(value.id),
                                    "labels": list(value.labels),
                                    "properties": serialize_neo4j_value(dict(value))
                                }
                            elif class_name == 'Relationship':
                                record_dict[key] = {
                                    "id": str(value.id),
                                    "type": value.type,
                                    "startNodeId": str(value.start_node.id),
                                    "endNodeId": str(value.end_node.id),
                                    "properties": serialize_neo4j_value(dict(value))
                                }
                            else:
                                record_dict[key] = serialize_neo4j_value(value)
                        else:
                            record_dict[key] = serialize_neo4j_value(value)
                    else:
                        record_dict[key] = serialize_neo4j_value(value)
                result.append(record_dict)
            
            return {
                "node_id": node_id,
                "records": result,
                "count": len(result)
            }
    except Exception as e:
        logger.error(f"Failed to get connected nodes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get connected nodes: {str(e)}")
    finally:
        executor.close()


@router.get("/decisions/patterns/{decision_type}", response_model=Dict[str, Any])
async def get_decision_patterns(
    decision_type: str,
    min_occurrences: int = Query(default=5, description="Minimum occurrences to consider a pattern"),
    time_window_days: int = Query(default=30, description="Time window in days"),
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get learned patterns for a decision type.
    
    Analyzes decision traces to extract:
    - Successful patterns (high success rate)
    - Common reasoning patterns
    - Context patterns that lead to success
    
    This enables the flywheel: learn from past decisions to improve future ones.
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        from dcisionai_workflow.shared.graph.feedback_analyzer import FeedbackAnalyzer
        
        analyzer = FeedbackAnalyzer(executor)
        patterns = analyzer.analyze_decision_patterns(
            decision_type=decision_type,
            min_occurrences=min_occurrences,
            time_window_days=time_window_days
        )
        
        return patterns
    except Exception as e:
        logger.error(f"Failed to get decision patterns: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze patterns: {str(e)}")
    finally:
        executor.close()


@router.get("/decisions/feedback/{decision_type}", response_model=Dict[str, Any])
async def get_decision_feedback(
    decision_type: str,
    context: str = Query(default="{}", description="JSON string of context"),
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get feedback/recommendations for making a decision.
    
    Uses learned patterns to suggest what has worked in similar contexts.
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        import json
        context_dict = json.loads(context) if context else {}
        
        from dcisionai_workflow.shared.graph.feedback_analyzer import FeedbackAnalyzer
        
        analyzer = FeedbackAnalyzer(executor)
        feedback = analyzer.provide_decision_feedback(
            decision_type=decision_type,
            context=context_dict
        )
        
        return feedback
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in context parameter")
    except Exception as e:
        logger.error(f"Failed to get decision feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get feedback: {str(e)}")
    finally:
        executor.close()


@router.get("/decisions/query-by-context", response_model=Dict[str, Any])
async def query_decisions_by_context(
    constraint_count: Optional[int] = Query(default=None, description="Filter by constraint_count"),
    solve_time_ms: Optional[int] = Query(default=None, description="Filter by solve_time_ms (max)"),
    status: Optional[str] = Query(default=None, description="Filter by status"),
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Query DecisionEvents by context properties using DecisionContext nodes.
    
    Enables queries like:
    - Find all decisions where constraint_count > 10
    - Find all decisions where solve_time_ms < 100
    - Find all decisions where status = 'optimal'
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        from dcisionai_workflow.shared.graph.context_extractor import query_decisions_by_context
        
        # Build filters
        filters = {}
        if constraint_count is not None:
            filters["constraint_count"] = {"$gte": constraint_count}
        if solve_time_ms is not None:
            filters["solve_time_ms"] = {"$lte": solve_time_ms}
        if status:
            filters["status"] = status
        
        decisions = query_decisions_by_context(executor, filters)
        
        return {
            "decisions": decisions,
            "count": len(decisions)
        }
    except Exception as e:
        logger.error(f"Failed to query decisions by context: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to query decisions: {str(e)}")
    finally:
        executor.close()


@router.get("/traces/{trace_id}/analysis", response_model=Dict[str, Any])
async def get_trace_analysis(
    trace_id: str,
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get analysis and learnings from a completed trace.
    
    Analyzes the trace to extract successful patterns and learnings.
    This implements the feedback loop: analyze completed traces to improve future decisions.
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        from dcisionai_workflow.shared.graph.feedback_analyzer import analyze_trace_for_improvement
        
        analysis = analyze_trace_for_improvement(executor, trace_id)
        
        return analysis
    except Exception as e:
        logger.error(f"Failed to analyze trace: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze trace: {str(e)}")
    finally:
        executor.close()


@router.get("/trace/{trace_id}/precedents")
async def get_trace_precedents(
    trace_id: str,
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get precedents (similar past traces) for a given trace_id.
    
    Precedents are similar past decisions that inform the current decision.
    This aligns with Foundation Capital's Context Graph vision of making
    precedent searchable.
    
    Returns:
        {
            "trace_id": "...",
            "precedents": [
                {
                    "trace_id": "...",
                    "similarity_score": 0.85,
                    "learned_from": "...",
                    "shared_patterns": ["..."],
                    "problem_type": "...",
                    "domain": "..."
                }
            ]
        }
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        executor.set_trace_id(trace_id)
        
        # Query for precedents (SIMILAR_TO relationships)
        cypher = """
            MATCH (current:Problem {trace_id: $trace_id})-[r:SIMILAR_TO]->(precedent:Problem)
            OPTIONAL MATCH (precedent)-[:HAS_CONSTRAINT]->(c:Constraint)
            OPTIONAL MATCH (precedent)-[:SOLVED_BY]->(s:Solution)
            WITH current, precedent, r,
                 collect(DISTINCT c.category) as constraint_categories,
                 s.status as solution_status
            RETURN precedent.trace_id as trace_id,
                   precedent.problem_type as problem_type,
                   precedent.domain as domain,
                   precedent.description as description,
                   r.similarity_score as similarity_score,
                   r.learned_from as learned_from,
                   r.shared_patterns as shared_patterns,
                   constraint_categories,
                   solution_status
            ORDER BY r.similarity_score DESC
        """
        
        records = executor.execute_read(cypher, {"trace_id": trace_id})
        
        precedents = []
        for record in records:
            precedents.append({
                "trace_id": record.get("trace_id"),
                "problem_type": record.get("problem_type"),
                "domain": record.get("domain"),
                "description": record.get("description"),
                "similarity_score": float(record.get("similarity_score", 0.0)) if record.get("similarity_score") else None,
                "learned_from": record.get("learned_from"),
                "shared_patterns": record.get("shared_patterns") or [],
                "constraint_categories": record.get("constraint_categories") or [],
                "solution_status": record.get("solution_status")
            })
        
        return {
            "trace_id": trace_id,
            "precedents": precedents,
            "count": len(precedents)
        }
    except Exception as e:
        logger.error(f"Failed to get precedents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve precedents: {str(e)}")
    finally:
        executor.close()


@router.get("/decisions/patterns/{decision_type}", response_model=Dict[str, Any])
async def get_decision_patterns(
    decision_type: str,
    min_occurrences: int = Query(default=5, description="Minimum occurrences to consider a pattern"),
    time_window_days: int = Query(default=30, description="Time window in days"),
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get learned patterns for a decision type.
    
    Analyzes decision traces to extract:
    - Successful patterns (high success rate)
    - Common reasoning patterns
    - Context patterns that lead to success
    
    This enables the flywheel: learn from past decisions to improve future ones.
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        from dcisionai_workflow.shared.graph.feedback_analyzer import FeedbackAnalyzer
        
        analyzer = FeedbackAnalyzer(executor)
        patterns = analyzer.analyze_decision_patterns(
            decision_type=decision_type,
            min_occurrences=min_occurrences,
            time_window_days=time_window_days
        )
        
        return patterns
    except Exception as e:
        logger.error(f"Failed to get decision patterns: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze patterns: {str(e)}")
    finally:
        executor.close()


@router.get("/decisions/feedback/{decision_type}", response_model=Dict[str, Any])
async def get_decision_feedback(
    decision_type: str,
    context: str = Query(default="{}", description="JSON string of context"),
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get feedback/recommendations for making a decision.
    
    Uses learned patterns to suggest what has worked in similar contexts.
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        import json
        context_dict = json.loads(context) if context else {}
        
        from dcisionai_workflow.shared.graph.feedback_analyzer import FeedbackAnalyzer
        
        analyzer = FeedbackAnalyzer(executor)
        feedback = analyzer.provide_decision_feedback(
            decision_type=decision_type,
            context=context_dict
        )
        
        return feedback
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in context parameter")
    except Exception as e:
        logger.error(f"Failed to get decision feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get feedback: {str(e)}")
    finally:
        executor.close()


@router.get("/decisions/query-by-context", response_model=Dict[str, Any])
async def query_decisions_by_context(
    constraint_count: Optional[int] = Query(default=None, description="Filter by constraint_count"),
    solve_time_ms: Optional[int] = Query(default=None, description="Filter by solve_time_ms (max)"),
    status: Optional[str] = Query(default=None, description="Filter by status"),
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Query DecisionEvents by context properties using DecisionContext nodes.
    
    Enables queries like:
    - Find all decisions where constraint_count > 10
    - Find all decisions where solve_time_ms < 100
    - Find all decisions where status = 'optimal'
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        from dcisionai_workflow.shared.graph.context_extractor import query_decisions_by_context
        
        # Build filters
        filters = {}
        if constraint_count is not None:
            filters["constraint_count"] = {"$gte": constraint_count}
        if solve_time_ms is not None:
            filters["solve_time_ms"] = {"$lte": solve_time_ms}
        if status:
            filters["status"] = status
        
        decisions = query_decisions_by_context(executor, filters)
        
        return {
            "decisions": decisions,
            "count": len(decisions)
        }
    except Exception as e:
        logger.error(f"Failed to query decisions by context: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to query decisions: {str(e)}")
    finally:
        executor.close()


@router.get("/traces/{trace_id}/analysis", response_model=Dict[str, Any])
async def get_trace_analysis(
    trace_id: str,
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get analysis and learnings from a completed trace.
    
    Analyzes the trace to extract successful patterns and learnings.
    This implements the feedback loop: analyze completed traces to improve future decisions.
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        from dcisionai_workflow.shared.graph.feedback_analyzer import analyze_trace_for_improvement
        
        analysis = analyze_trace_for_improvement(executor, trace_id)
        
        return analysis
    except Exception as e:
        logger.error(f"Failed to analyze trace: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze trace: {str(e)}")
    finally:
        executor.close()


@router.get("/trace/{trace_id}/summary", response_model=TraceSummaryResponse)
async def get_trace_summary(
    trace_id: str,
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get summary of a decision trace (counts, status, metadata).
    """
    # Ensure connection is checked
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        executor.set_trace_id(trace_id)
        
        # Query for summary
        cypher = """
            MATCH (p:Problem {trace_id: $trace_id})
            OPTIONAL MATCH (p)-[:HAS_CONSTRAINT]->(c:Constraint)
            OPTIONAL MATCH (p)-[:HAS_OBJECTIVE]->(o:Objective)
            OPTIONAL MATCH (p)-[:HAS_PARAMETER]->(param:Parameter)
            OPTIONAL MATCH (p)-[:DECOMPOSED_TO]->(chunk:Chunk)
            OPTIONAL MATCH (p)-[:ASSUMES]->(a:Assumption)
            OPTIONAL MATCH (p)-[:NEEDS_CLARIFICATION]->(q:Question)
            OPTIONAL MATCH (p)-[:SOLVED_BY]->(s:Solution)
            RETURN 
                p.problem_type as problem_type,
                p.domain as domain,
                p.classification_confidence as confidence,
                p.created_at as created_at,
                count(DISTINCT c) as constraint_count,
                count(DISTINCT o) as objective_count,
                count(DISTINCT param) as parameter_count,
                count(DISTINCT chunk) as chunk_count,
                count(DISTINCT a) as assumption_count,
                count(DISTINCT q) as question_count,
                s.status as solution_status
        """
        
        records = executor.execute_read(cypher, {"trace_id": trace_id})
        
        if not records:
            raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
        
        record = records[0]
        
        # Serialize DateTime objects
        created_at = record.get("created_at")
        if created_at:
            created_at = serialize_neo4j_value(created_at)
        
        return TraceSummaryResponse(
            trace_id=trace_id,
            problem_type=record.get("problem_type"),
            domain=record.get("domain"),
            confidence=record.get("confidence"),
            constraint_count=record.get("constraint_count", 0),
            objective_count=record.get("objective_count", 0),
            parameter_count=record.get("parameter_count", 0),
            chunk_count=record.get("chunk_count", 0),
            assumption_count=record.get("assumption_count", 0),
            question_count=record.get("question_count", 0),
            solution_status=record.get("solution_status"),
            created_at=created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get trace summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve trace summary: {str(e)}")
    finally:
        executor.close()


@router.get("/decisions/patterns/{decision_type}", response_model=Dict[str, Any])
async def get_decision_patterns(
    decision_type: str,
    min_occurrences: int = Query(default=5, description="Minimum occurrences to consider a pattern"),
    time_window_days: int = Query(default=30, description="Time window in days"),
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get learned patterns for a decision type.
    
    Analyzes decision traces to extract:
    - Successful patterns (high success rate)
    - Common reasoning patterns
    - Context patterns that lead to success
    
    This enables the flywheel: learn from past decisions to improve future ones.
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        from dcisionai_workflow.shared.graph.feedback_analyzer import FeedbackAnalyzer
        
        analyzer = FeedbackAnalyzer(executor)
        patterns = analyzer.analyze_decision_patterns(
            decision_type=decision_type,
            min_occurrences=min_occurrences,
            time_window_days=time_window_days
        )
        
        return patterns
    except Exception as e:
        logger.error(f"Failed to get decision patterns: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze patterns: {str(e)}")
    finally:
        executor.close()


@router.get("/decisions/feedback/{decision_type}", response_model=Dict[str, Any])
async def get_decision_feedback(
    decision_type: str,
    context: str = Query(default="{}", description="JSON string of context"),
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get feedback/recommendations for making a decision.
    
    Uses learned patterns to suggest what has worked in similar contexts.
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        import json
        context_dict = json.loads(context) if context else {}
        
        from dcisionai_workflow.shared.graph.feedback_analyzer import FeedbackAnalyzer
        
        analyzer = FeedbackAnalyzer(executor)
        feedback = analyzer.provide_decision_feedback(
            decision_type=decision_type,
            context=context_dict
        )
        
        return feedback
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in context parameter")
    except Exception as e:
        logger.error(f"Failed to get decision feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get feedback: {str(e)}")
    finally:
        executor.close()


@router.get("/decisions/query-by-context", response_model=Dict[str, Any])
async def query_decisions_by_context(
    constraint_count: Optional[int] = Query(default=None, description="Filter by constraint_count"),
    solve_time_ms: Optional[int] = Query(default=None, description="Filter by solve_time_ms (max)"),
    status: Optional[str] = Query(default=None, description="Filter by status"),
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Query DecisionEvents by context properties using DecisionContext nodes.
    
    Enables queries like:
    - Find all decisions where constraint_count > 10
    - Find all decisions where solve_time_ms < 100
    - Find all decisions where status = 'optimal'
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        from dcisionai_workflow.shared.graph.context_extractor import query_decisions_by_context
        
        # Build filters
        filters = {}
        if constraint_count is not None:
            filters["constraint_count"] = {"$gte": constraint_count}
        if solve_time_ms is not None:
            filters["solve_time_ms"] = {"$lte": solve_time_ms}
        if status:
            filters["status"] = status
        
        decisions = query_decisions_by_context(executor, filters)
        
        return {
            "decisions": decisions,
            "count": len(decisions)
        }
    except Exception as e:
        logger.error(f"Failed to query decisions by context: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to query decisions: {str(e)}")
    finally:
        executor.close()


@router.get("/traces/{trace_id}/analysis", response_model=Dict[str, Any])
async def get_trace_analysis(
    trace_id: str,
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get analysis and learnings from a completed trace.
    
    Analyzes the trace to extract successful patterns and learnings.
    This implements the feedback loop: analyze completed traces to improve future decisions.
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        from dcisionai_workflow.shared.graph.feedback_analyzer import analyze_trace_for_improvement
        
        analysis = analyze_trace_for_improvement(executor, trace_id)
        
        return analysis
    except Exception as e:
        logger.error(f"Failed to analyze trace: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze trace: {str(e)}")
    finally:
        executor.close()


@router.post("/nl-query", response_model=Dict[str, Any])
async def natural_language_query(
    request: NLQueryRequest,
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Convert natural language query to Cypher and execute.
    
    This endpoint provides agentic capabilities for querying the graph.
    For production, integrate NeoConverse for LLM-powered NL-to-Cypher translation.
    
    Current implementation uses pattern matching. Future: Use NeoConverse.
    """
    # Ensure connection is checked
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        # Convert NL to Cypher (simplified - use NeoConverse in production)
        cypher_query = convert_nl_to_cypher(request.query, request.trace_id)
        
        # Prepare parameters
        parameters = {}
        if request.trace_id:
            parameters["trace_id"] = request.trace_id
        
        # Execute query
        records = executor.execute_read(cypher_query, parameters)
        
        # Format results
        formatted_results = format_for_nvl(records)
        
        # Generate visualization spec if requested
        visualization = None
        if request.generate_chart:
            # Simple chart spec generation (enhance with NeoConverse in production)
            if "bar chart" in request.query.lower() or "chart" in request.query.lower():
                visualization = {
                    "type": "bar",
                    "data": formatted_results.get("nodes", [])[:10],  # Limit for chart
                    "xAxis": "name",
                    "yAxis": "count"
                }
        
        return {
            "query": request.query,
            "cypher": cypher_query,
            "results": formatted_results,
            "record_count": len(records),
            "visualization": visualization
        }
    except Exception as e:
        logger.error(f"NL query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"NL query failed: {str(e)}")
    finally:
        executor.close()


@router.get("/decisions/patterns/{decision_type}", response_model=Dict[str, Any])
async def get_decision_patterns(
    decision_type: str,
    min_occurrences: int = Query(default=5, description="Minimum occurrences to consider a pattern"),
    time_window_days: int = Query(default=30, description="Time window in days"),
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get learned patterns for a decision type.
    
    Analyzes decision traces to extract:
    - Successful patterns (high success rate)
    - Common reasoning patterns
    - Context patterns that lead to success
    
    This enables the flywheel: learn from past decisions to improve future ones.
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        from dcisionai_workflow.shared.graph.feedback_analyzer import FeedbackAnalyzer
        
        analyzer = FeedbackAnalyzer(executor)
        patterns = analyzer.analyze_decision_patterns(
            decision_type=decision_type,
            min_occurrences=min_occurrences,
            time_window_days=time_window_days
        )
        
        return patterns
    except Exception as e:
        logger.error(f"Failed to get decision patterns: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze patterns: {str(e)}")
    finally:
        executor.close()


@router.get("/decisions/feedback/{decision_type}", response_model=Dict[str, Any])
async def get_decision_feedback(
    decision_type: str,
    context: str = Query(default="{}", description="JSON string of context"),
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get feedback/recommendations for making a decision.
    
    Uses learned patterns to suggest what has worked in similar contexts.
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        import json
        context_dict = json.loads(context) if context else {}
        
        from dcisionai_workflow.shared.graph.feedback_analyzer import FeedbackAnalyzer
        
        analyzer = FeedbackAnalyzer(executor)
        feedback = analyzer.provide_decision_feedback(
            decision_type=decision_type,
            context=context_dict
        )
        
        return feedback
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in context parameter")
    except Exception as e:
        logger.error(f"Failed to get decision feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get feedback: {str(e)}")
    finally:
        executor.close()


@router.get("/decisions/query-by-context", response_model=Dict[str, Any])
async def query_decisions_by_context(
    constraint_count: Optional[int] = Query(default=None, description="Filter by constraint_count"),
    solve_time_ms: Optional[int] = Query(default=None, description="Filter by solve_time_ms (max)"),
    status: Optional[str] = Query(default=None, description="Filter by status"),
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Query DecisionEvents by context properties using DecisionContext nodes.
    
    Enables queries like:
    - Find all decisions where constraint_count > 10
    - Find all decisions where solve_time_ms < 100
    - Find all decisions where status = 'optimal'
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        from dcisionai_workflow.shared.graph.context_extractor import query_decisions_by_context
        
        # Build filters
        filters = {}
        if constraint_count is not None:
            filters["constraint_count"] = {"$gte": constraint_count}
        if solve_time_ms is not None:
            filters["solve_time_ms"] = {"$lte": solve_time_ms}
        if status:
            filters["status"] = status
        
        decisions = query_decisions_by_context(executor, filters)
        
        return {
            "decisions": decisions,
            "count": len(decisions)
        }
    except Exception as e:
        logger.error(f"Failed to query decisions by context: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to query decisions: {str(e)}")
    finally:
        executor.close()


@router.get("/traces/{trace_id}/analysis", response_model=Dict[str, Any])
async def get_trace_analysis(
    trace_id: str,
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get analysis and learnings from a completed trace.
    
    Analyzes the trace to extract successful patterns and learnings.
    This implements the feedback loop: analyze completed traces to improve future decisions.
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        from dcisionai_workflow.shared.graph.feedback_analyzer import analyze_trace_for_improvement
        
        analysis = analyze_trace_for_improvement(executor, trace_id)
        
        return analysis
    except Exception as e:
        logger.error(f"Failed to analyze trace: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze trace: {str(e)}")
    finally:
        executor.close()


@router.get("/trace/{trace_id}/path")
async def get_trace_path(
    trace_id: str,
    from_node: str = Query(..., description="Start node ID"),
    to_node: str = Query(..., description="End node ID"),
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get shortest path between two nodes in a trace.
    """
    # Ensure connection is checked
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        executor.set_trace_id(trace_id)
        
        cypher = """
            MATCH (p:Problem {trace_id: $trace_id})
            MATCH path = shortestPath((from)-[*]-(to))
            WHERE from.id = $from_node AND to.id = $to_node
            RETURN path
            LIMIT 1
        """
        
        records = executor.execute_read(cypher, {
            "trace_id": trace_id,
            "from_node": from_node,
            "to_node": to_node
        })
        
        if not records:
            return {"path": None, "message": "No path found"}
        
        # Format path
        path = records[0].get("path")
        if path:
            return {
                "path": {
                    "length": len(path.relationships),
                    "nodes": [{"id": str(n.id), "labels": list(n.labels)} for n in path.nodes],
                    "relationships": [{"type": r.type, "id": str(r.id)} for r in path.relationships]
                }
            }
        
        return {"path": None}
    except Exception as e:
        logger.error(f"Failed to get path: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get path: {str(e)}")
    finally:
        executor.close()


@router.get("/decisions/patterns/{decision_type}", response_model=Dict[str, Any])
async def get_decision_patterns(
    decision_type: str,
    min_occurrences: int = Query(default=5, description="Minimum occurrences to consider a pattern"),
    time_window_days: int = Query(default=30, description="Time window in days"),
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get learned patterns for a decision type.
    
    Analyzes decision traces to extract:
    - Successful patterns (high success rate)
    - Common reasoning patterns
    - Context patterns that lead to success
    
    This enables the flywheel: learn from past decisions to improve future ones.
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        from dcisionai_workflow.shared.graph.feedback_analyzer import FeedbackAnalyzer
        
        analyzer = FeedbackAnalyzer(executor)
        patterns = analyzer.analyze_decision_patterns(
            decision_type=decision_type,
            min_occurrences=min_occurrences,
            time_window_days=time_window_days
        )
        
        return patterns
    except Exception as e:
        logger.error(f"Failed to get decision patterns: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze patterns: {str(e)}")
    finally:
        executor.close()


@router.get("/decisions/feedback/{decision_type}", response_model=Dict[str, Any])
async def get_decision_feedback(
    decision_type: str,
    context: str = Query(default="{}", description="JSON string of context"),
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get feedback/recommendations for making a decision.
    
    Uses learned patterns to suggest what has worked in similar contexts.
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        import json
        context_dict = json.loads(context) if context else {}
        
        from dcisionai_workflow.shared.graph.feedback_analyzer import FeedbackAnalyzer
        
        analyzer = FeedbackAnalyzer(executor)
        feedback = analyzer.provide_decision_feedback(
            decision_type=decision_type,
            context=context_dict
        )
        
        return feedback
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in context parameter")
    except Exception as e:
        logger.error(f"Failed to get decision feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get feedback: {str(e)}")
    finally:
        executor.close()


@router.get("/decisions/query-by-context", response_model=Dict[str, Any])
async def query_decisions_by_context(
    constraint_count: Optional[int] = Query(default=None, description="Filter by constraint_count"),
    solve_time_ms: Optional[int] = Query(default=None, description="Filter by solve_time_ms (max)"),
    status: Optional[str] = Query(default=None, description="Filter by status"),
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Query DecisionEvents by context properties using DecisionContext nodes.
    
    Enables queries like:
    - Find all decisions where constraint_count > 10
    - Find all decisions where solve_time_ms < 100
    - Find all decisions where status = 'optimal'
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        from dcisionai_workflow.shared.graph.context_extractor import query_decisions_by_context
        
        # Build filters
        filters = {}
        if constraint_count is not None:
            filters["constraint_count"] = {"$gte": constraint_count}
        if solve_time_ms is not None:
            filters["solve_time_ms"] = {"$lte": solve_time_ms}
        if status:
            filters["status"] = status
        
        decisions = query_decisions_by_context(executor, filters)
        
        return {
            "decisions": decisions,
            "count": len(decisions)
        }
    except Exception as e:
        logger.error(f"Failed to query decisions by context: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to query decisions: {str(e)}")
    finally:
        executor.close()


@router.get("/traces/{trace_id}/analysis", response_model=Dict[str, Any])
async def get_trace_analysis(
    trace_id: str,
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get analysis and learnings from a completed trace.
    
    Analyzes the trace to extract successful patterns and learnings.
    This implements the feedback loop: analyze completed traces to improve future decisions.
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        from dcisionai_workflow.shared.graph.feedback_analyzer import analyze_trace_for_improvement
        
        analysis = analyze_trace_for_improvement(executor, trace_id)
        
        return analysis
    except Exception as e:
        logger.error(f"Failed to analyze trace: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze trace: {str(e)}")
    finally:
        executor.close()


@router.get("/find-by-job/{job_id}", response_model=Dict[str, Any])
async def find_trace_by_job(
    job_id: str,
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Find graph-native trace_id by job_id.
    
    Searches for traces that match the job's problem description or were created
    around the same time as the job.
    
    Returns the most likely matching trace_id, or null if not found.
    """
    # Ensure connection is checked
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    try:
        # Get job information
        from dcisionai_mcp_server.api.jobs import get_job
        job_record = get_job(job_id)
        if not job_record:
            raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
        
        # Extract problem description from job
        user_query = job_record.get("user_query", "")
        created_at = job_record.get("created_at")
        
        executor = GraphExecutor()
        try:
            # Strategy 1: Find traces created within 5 minutes of job creation
            if created_at:
                try:
                    if dateutil_parser:
                        job_time = dateutil_parser.parse(created_at) if isinstance(created_at, str) else created_at
                    else:
                        # Fallback: try to parse ISO format manually
                        if isinstance(created_at, str):
                            job_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        else:
                            job_time = created_at
                    time_window_start = job_time - timedelta(minutes=5)
                    time_window_end = job_time + timedelta(minutes=5)
                    
                    cypher = """
                        MATCH (p:Problem)
                        WHERE p.created_at >= $start_time AND p.created_at <= $end_time
                        RETURN p.trace_id as trace_id, p.description as description, p.created_at as created_at
                        ORDER BY p.created_at DESC
                        LIMIT 5
                    """
                    
                    records = executor.execute_read(cypher, {
                        "start_time": time_window_start,
                        "end_time": time_window_end
                    })
                    
                    if records:
                        # Strategy 2: Match by problem description keywords
                        if user_query:
                            query_keywords = [word.lower() for word in user_query.split() if len(word) > 3][:5]
                            
                            for record in records:
                                desc = (record.get("description") or "").lower()
                                # Check if at least 2 keywords match
                                matches = sum(1 for keyword in query_keywords if keyword in desc)
                                if matches >= 2:
                                    return {
                                        "trace_id": record["trace_id"],
                                        "match_method": "time_and_description",
                                        "confidence": "high",
                                        "description": record.get("description", "")[:200]
                                    }
                        
                        # Fallback: Return most recent trace in time window
                        return {
                            "trace_id": records[0]["trace_id"],
                            "match_method": "time_window",
                            "confidence": "medium",
                            "description": records[0].get("description", "")[:200]
                        }
                except Exception as e:
                    logger.warning(f"Time-based search failed: {e}")
            
            # Strategy 3: Search by problem description keywords
            if user_query:
                query_keywords = [word.lower() for word in user_query.split() if len(word) > 3][:5]
                keyword_pattern = "|".join(query_keywords)
                
                cypher = """
                    MATCH (p:Problem)
                    WHERE toLower(p.description) CONTAINS $keyword1
                       OR toLower(p.description) CONTAINS $keyword2
                    RETURN p.trace_id as trace_id, p.description as description, p.created_at as created_at
                    ORDER BY p.created_at DESC
                    LIMIT 5
                """
                
                if len(query_keywords) >= 2:
                    records = executor.execute_read(cypher, {
                        "keyword1": query_keywords[0],
                        "keyword2": query_keywords[1] if len(query_keywords) > 1 else query_keywords[0]
                    })
                    
                    if records:
                        return {
                            "trace_id": records[0]["trace_id"],
                            "match_method": "description_keywords",
                            "confidence": "medium",
                            "description": records[0].get("description", "")[:200]
                        }
            
            # No match found
            return {
                "trace_id": None,
                "match_method": None,
                "confidence": None,
                "message": "No matching trace found in Neo4j"
            }
            
        finally:
            executor.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to find trace by job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to find trace: {str(e)}")


@router.get("/decisions/patterns/{decision_type}", response_model=Dict[str, Any])
async def get_decision_patterns(
    decision_type: str,
    min_occurrences: int = Query(default=5, description="Minimum occurrences to consider a pattern"),
    time_window_days: int = Query(default=30, description="Time window in days"),
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get learned patterns for a decision type.
    
    Analyzes decision traces to extract:
    - Successful patterns (high success rate)
    - Common reasoning patterns
    - Context patterns that lead to success
    
    This enables the flywheel: learn from past decisions to improve future ones.
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        from dcisionai_workflow.shared.graph.feedback_analyzer import FeedbackAnalyzer
        
        analyzer = FeedbackAnalyzer(executor)
        patterns = analyzer.analyze_decision_patterns(
            decision_type=decision_type,
            min_occurrences=min_occurrences,
            time_window_days=time_window_days
        )
        
        return patterns
    except Exception as e:
        logger.error(f"Failed to get decision patterns: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze patterns: {str(e)}")
    finally:
        executor.close()


@router.get("/decisions/feedback/{decision_type}", response_model=Dict[str, Any])
async def get_decision_feedback(
    decision_type: str,
    context: str = Query(default="{}", description="JSON string of context"),
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get feedback/recommendations for making a decision.
    
    Uses learned patterns to suggest what has worked in similar contexts.
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        import json
        context_dict = json.loads(context) if context else {}
        
        from dcisionai_workflow.shared.graph.feedback_analyzer import FeedbackAnalyzer
        
        analyzer = FeedbackAnalyzer(executor)
        feedback = analyzer.provide_decision_feedback(
            decision_type=decision_type,
            context=context_dict
        )
        
        return feedback
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in context parameter")
    except Exception as e:
        logger.error(f"Failed to get decision feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get feedback: {str(e)}")
    finally:
        executor.close()


@router.get("/decisions/query-by-context", response_model=Dict[str, Any])
async def query_decisions_by_context(
    constraint_count: Optional[int] = Query(default=None, description="Filter by constraint_count"),
    solve_time_ms: Optional[int] = Query(default=None, description="Filter by solve_time_ms (max)"),
    status: Optional[str] = Query(default=None, description="Filter by status"),
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Query DecisionEvents by context properties using DecisionContext nodes.
    
    Enables queries like:
    - Find all decisions where constraint_count > 10
    - Find all decisions where solve_time_ms < 100
    - Find all decisions where status = 'optimal'
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        from dcisionai_workflow.shared.graph.context_extractor import query_decisions_by_context
        
        # Build filters
        filters = {}
        if constraint_count is not None:
            filters["constraint_count"] = {"$gte": constraint_count}
        if solve_time_ms is not None:
            filters["solve_time_ms"] = {"$lte": solve_time_ms}
        if status:
            filters["status"] = status
        
        decisions = query_decisions_by_context(executor, filters)
        
        return {
            "decisions": decisions,
            "count": len(decisions)
        }
    except Exception as e:
        logger.error(f"Failed to query decisions by context: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to query decisions: {str(e)}")
    finally:
        executor.close()


@router.get("/traces/{trace_id}/analysis", response_model=Dict[str, Any])
async def get_trace_analysis(
    trace_id: str,
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get analysis and learnings from a completed trace.
    
    Analyzes the trace to extract successful patterns and learnings.
    This implements the feedback loop: analyze completed traces to improve future decisions.
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        from dcisionai_workflow.shared.graph.feedback_analyzer import analyze_trace_for_improvement
        
        analysis = analyze_trace_for_improvement(executor, trace_id)
        
        return analysis
    except Exception as e:
        logger.error(f"Failed to analyze trace: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze trace: {str(e)}")
    finally:
        executor.close()


@router.get("/decisions/{decision_id}", response_model=Dict[str, Any])
async def get_decision(
    decision_id: str,
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get details of a specific DecisionEvent.
    
    Returns:
        {
            "id": "...",
            "decision_type": "...",
            "decision": "...",
            "reasoning": "...",
            "agent": "...",
            "timestamp": "...",
            "context_snapshot": {...},
            "linked_entities": [...],
            "policies_applied": [...],
            "exceptions_granted": [...]
        }
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        # Try to match by custom 'id' property first, then by Neo4j internal ID
        # This handles both cases: custom ID (string) and Neo4j internal ID (number)
        cypher = """
            MATCH (de:DecisionEvent)
            WHERE de.id = $decision_id 
               OR elementId(de) = $decision_id 
               OR id(de) = toInteger($decision_id)
            WITH de LIMIT 1
            OPTIONAL MATCH (de)-[:ABOUT]->(entity)
            OPTIONAL MATCH (de)-[:APPLIED_POLICY]->(p:Policy)
            OPTIONAL MATCH (de)-[:GRANTED_EXCEPTION]->(e:Exception)
            OPTIONAL MATCH (de)<-[:CAUSED|INFLUENCED|LED_TO]-(parent:DecisionEvent)
            OPTIONAL MATCH (de)-[:CAUSED|INFLUENCED|LED_TO]->(child:DecisionEvent)
            OPTIONAL MATCH (a:Actor)-[:MADE_DECISION]->(de)
            OPTIONAL MATCH (de)-[:MEASURES]->(m:Metric)
            OPTIONAL MATCH (de)-[:IMPLEMENTS]->(i:Intervention)
            OPTIONAL MATCH (de)-[:IDENTIFIES]->(r:Risk)
            RETURN de,
                   collect(DISTINCT {id: entity.id, label: labels(entity), name: entity.name}) as linked_entities,
                   collect(DISTINCT {id: p.id, name: p.name}) as policies_applied,
                   collect(DISTINCT {id: e.id, exception_type: e.exception_type, justification: e.justification}) as exceptions_granted,
                   collect(DISTINCT {id: parent.id, decision_type: parent.decision_type}) as parent_decisions,
                   collect(DISTINCT {id: child.id, decision_type: child.decision_type}) as child_decisions,
                   collect(DISTINCT {id: a.id, name: a.name, type: a.type, role: a.role}) as actors,
                   collect(DISTINCT {id: m.id, name: m.name, value: m.value, unit: m.unit, target: m.target, direction: m.direction}) as metrics,
                   collect(DISTINCT {id: i.id, type: i.type, action: i.action, status: i.status, outcome: i.outcome}) as interventions,
                   collect(DISTINCT {id: r.id, type: r.type, severity: r.severity, probability: r.probability, impact: r.impact, mitigation: r.mitigation}) as risks
        """
        
        records = executor.execute_read(cypher, {"decision_id": decision_id})
        
        if not records or not records[0].get("de"):
            raise HTTPException(status_code=404, detail=f"Decision not found: {decision_id}")
        
        de = records[0]["de"]
        
        # Parse context_snapshot if it's a JSON string
        context_snapshot = de.get("context_snapshot", {})
        if isinstance(context_snapshot, str):
            try:
                context_snapshot = json.loads(context_snapshot)
            except:
                context_snapshot = {}
        
        return {
            "id": de.get("id"),
            "decision_type": de.get("decision_type"),
            "decision": de.get("decision"),
            "reasoning": de.get("reasoning"),
            "agent": de.get("agent"),
            "timestamp": str(de.get("timestamp")) if de.get("timestamp") else None,
            "context_snapshot": context_snapshot,
            "linked_entities": records[0].get("linked_entities", []),
            "policies_applied": records[0].get("policies_applied", []),
            "exceptions_granted": records[0].get("exceptions_granted", []),
            "parent_decisions": records[0].get("parent_decisions", []),
            "child_decisions": records[0].get("child_decisions", []),
            "actors": records[0].get("actors", []),
            "metrics": records[0].get("metrics", []),
            "interventions": records[0].get("interventions", []),
            "risks": records[0].get("risks", [])
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get decision: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve decision: {str(e)}")
    finally:
        executor.close()


@router.get("/decisions/patterns/{decision_type}", response_model=Dict[str, Any])
async def get_decision_patterns(
    decision_type: str,
    min_occurrences: int = Query(default=5, description="Minimum occurrences to consider a pattern"),
    time_window_days: int = Query(default=30, description="Time window in days"),
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get learned patterns for a decision type.
    
    Analyzes decision traces to extract:
    - Successful patterns (high success rate)
    - Common reasoning patterns
    - Context patterns that lead to success
    
    This enables the flywheel: learn from past decisions to improve future ones.
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        from dcisionai_workflow.shared.graph.feedback_analyzer import FeedbackAnalyzer
        
        analyzer = FeedbackAnalyzer(executor)
        patterns = analyzer.analyze_decision_patterns(
            decision_type=decision_type,
            min_occurrences=min_occurrences,
            time_window_days=time_window_days
        )
        
        return patterns
    except Exception as e:
        logger.error(f"Failed to get decision patterns: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze patterns: {str(e)}")
    finally:
        executor.close()


@router.get("/decisions/feedback/{decision_type}", response_model=Dict[str, Any])
async def get_decision_feedback(
    decision_type: str,
    context: str = Query(default="{}", description="JSON string of context"),
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get feedback/recommendations for making a decision.
    
    Uses learned patterns to suggest what has worked in similar contexts.
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        import json
        context_dict = json.loads(context) if context else {}
        
        from dcisionai_workflow.shared.graph.feedback_analyzer import FeedbackAnalyzer
        
        analyzer = FeedbackAnalyzer(executor)
        feedback = analyzer.provide_decision_feedback(
            decision_type=decision_type,
            context=context_dict
        )
        
        return feedback
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in context parameter")
    except Exception as e:
        logger.error(f"Failed to get decision feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get feedback: {str(e)}")
    finally:
        executor.close()


@router.get("/decisions/query-by-context", response_model=Dict[str, Any])
async def query_decisions_by_context(
    constraint_count: Optional[int] = Query(default=None, description="Filter by constraint_count"),
    solve_time_ms: Optional[int] = Query(default=None, description="Filter by solve_time_ms (max)"),
    status: Optional[str] = Query(default=None, description="Filter by status"),
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Query DecisionEvents by context properties using DecisionContext nodes.
    
    Enables queries like:
    - Find all decisions where constraint_count > 10
    - Find all decisions where solve_time_ms < 100
    - Find all decisions where status = 'optimal'
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        from dcisionai_workflow.shared.graph.context_extractor import query_decisions_by_context
        
        # Build filters
        filters = {}
        if constraint_count is not None:
            filters["constraint_count"] = {"$gte": constraint_count}
        if solve_time_ms is not None:
            filters["solve_time_ms"] = {"$lte": solve_time_ms}
        if status:
            filters["status"] = status
        
        decisions = query_decisions_by_context(executor, filters)
        
        return {
            "decisions": decisions,
            "count": len(decisions)
        }
    except Exception as e:
        logger.error(f"Failed to query decisions by context: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to query decisions: {str(e)}")
    finally:
        executor.close()


@router.get("/traces/{trace_id}/analysis", response_model=Dict[str, Any])
async def get_trace_analysis(
    trace_id: str,
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get analysis and learnings from a completed trace.
    
    Analyzes the trace to extract successful patterns and learnings.
    This implements the feedback loop: analyze completed traces to improve future decisions.
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        from dcisionai_workflow.shared.graph.feedback_analyzer import analyze_trace_for_improvement
        
        analysis = analyze_trace_for_improvement(executor, trace_id)
        
        return analysis
    except Exception as e:
        logger.error(f"Failed to analyze trace: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze trace: {str(e)}")
    finally:
        executor.close()


@router.get("/decisions/{decision_id}/causal-chain", response_model=Dict[str, Any])
async def get_decision_causal_chain(
    decision_id: str,
    direction: str = Query(default="both", description="Direction: 'upstream', 'downstream', or 'both'"),
    max_depth: int = Query(default=10, description="Maximum depth to traverse"),
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get causal chain for a DecisionEvent.
    
    Traverses CAUSED, INFLUENCED, and LED_TO relationships to find
    upstream causes and downstream effects.
    
    Args:
        decision_id: ID of DecisionEvent
        direction: 'upstream' (causes), 'downstream' (effects), or 'both'
        max_depth: Maximum depth to traverse (default: 10)
    
    Returns:
        {
            "decision_id": "...",
            "upstream": [...],  // Decisions that caused/influenced this
            "downstream": [...] // Decisions caused/influenced by this
        }
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        upstream = []
        downstream = []
        
        if direction in ["upstream", "both"]:
            # Get upstream causes/influences
            cypher = f"""
                MATCH path = (de:DecisionEvent {{id: $decision_id}})<-[:CAUSED|INFLUENCED|LED_TO*1..{max_depth}]-(cause:DecisionEvent)
                RETURN DISTINCT cause.id as id,
                       cause.decision_type as decision_type,
                       cause.decision as decision,
                       cause.reasoning as reasoning,
                       cause.agent as agent,
                       cause.timestamp as timestamp,
                       length(path) as depth
                ORDER BY depth, cause.timestamp DESC
            """
            upstream_records = executor.execute_read(cypher, {"decision_id": decision_id})
            upstream = [
                {
                    "id": r.get("id"),
                    "decision_type": r.get("decision_type"),
                    "decision": r.get("decision"),
                    "reasoning": r.get("reasoning"),
                    "agent": r.get("agent"),
                    "timestamp": str(r.get("timestamp")) if r.get("timestamp") else None,
                    "depth": r.get("depth", 0)
                }
                for r in upstream_records
            ]
        
        if direction in ["downstream", "both"]:
            # Get downstream effects
            cypher = f"""
                MATCH path = (de:DecisionEvent {{id: $decision_id}})-[:CAUSED|INFLUENCED|LED_TO*1..{max_depth}]->(effect:DecisionEvent)
                RETURN DISTINCT effect.id as id,
                       effect.decision_type as decision_type,
                       effect.decision as decision,
                       effect.reasoning as reasoning,
                       effect.agent as agent,
                       effect.timestamp as timestamp,
                       length(path) as depth
                ORDER BY depth, effect.timestamp ASC
            """
            downstream_records = executor.execute_read(cypher, {"decision_id": decision_id})
            downstream = [
                {
                    "id": r.get("id"),
                    "decision_type": r.get("decision_type"),
                    "decision": r.get("decision"),
                    "reasoning": r.get("reasoning"),
                    "agent": r.get("agent"),
                    "timestamp": str(r.get("timestamp")) if r.get("timestamp") else None,
                    "depth": r.get("depth", 0)
                }
                for r in downstream_records
            ]
        
        return {
            "decision_id": decision_id,
            "direction": direction,
            "upstream": upstream,
            "downstream": downstream
        }
    except Exception as e:
        logger.error(f"Failed to get causal chain: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve causal chain: {str(e)}")
    finally:
        executor.close()


@router.get("/decisions/patterns/{decision_type}", response_model=Dict[str, Any])
async def get_decision_patterns(
    decision_type: str,
    min_occurrences: int = Query(default=5, description="Minimum occurrences to consider a pattern"),
    time_window_days: int = Query(default=30, description="Time window in days"),
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get learned patterns for a decision type.
    
    Analyzes decision traces to extract:
    - Successful patterns (high success rate)
    - Common reasoning patterns
    - Context patterns that lead to success
    
    This enables the flywheel: learn from past decisions to improve future ones.
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        from dcisionai_workflow.shared.graph.feedback_analyzer import FeedbackAnalyzer
        
        analyzer = FeedbackAnalyzer(executor)
        patterns = analyzer.analyze_decision_patterns(
            decision_type=decision_type,
            min_occurrences=min_occurrences,
            time_window_days=time_window_days
        )
        
        return patterns
    except Exception as e:
        logger.error(f"Failed to get decision patterns: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze patterns: {str(e)}")
    finally:
        executor.close()


@router.get("/decisions/feedback/{decision_type}", response_model=Dict[str, Any])
async def get_decision_feedback(
    decision_type: str,
    context: str = Query(default="{}", description="JSON string of context"),
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get feedback/recommendations for making a decision.
    
    Uses learned patterns to suggest what has worked in similar contexts.
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        import json
        context_dict = json.loads(context) if context else {}
        
        from dcisionai_workflow.shared.graph.feedback_analyzer import FeedbackAnalyzer
        
        analyzer = FeedbackAnalyzer(executor)
        feedback = analyzer.provide_decision_feedback(
            decision_type=decision_type,
            context=context_dict
        )
        
        return feedback
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in context parameter")
    except Exception as e:
        logger.error(f"Failed to get decision feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get feedback: {str(e)}")
    finally:
        executor.close()


@router.get("/decisions/query-by-context", response_model=Dict[str, Any])
async def query_decisions_by_context(
    constraint_count: Optional[int] = Query(default=None, description="Filter by constraint_count"),
    solve_time_ms: Optional[int] = Query(default=None, description="Filter by solve_time_ms (max)"),
    status: Optional[str] = Query(default=None, description="Filter by status"),
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Query DecisionEvents by context properties using DecisionContext nodes.
    
    Enables queries like:
    - Find all decisions where constraint_count > 10
    - Find all decisions where solve_time_ms < 100
    - Find all decisions where status = 'optimal'
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        from dcisionai_workflow.shared.graph.context_extractor import query_decisions_by_context
        
        # Build filters
        filters = {}
        if constraint_count is not None:
            filters["constraint_count"] = {"$gte": constraint_count}
        if solve_time_ms is not None:
            filters["solve_time_ms"] = {"$lte": solve_time_ms}
        if status:
            filters["status"] = status
        
        decisions = query_decisions_by_context(executor, filters)
        
        return {
            "decisions": decisions,
            "count": len(decisions)
        }
    except Exception as e:
        logger.error(f"Failed to query decisions by context: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to query decisions: {str(e)}")
    finally:
        executor.close()


@router.get("/traces/{trace_id}/analysis", response_model=Dict[str, Any])
async def get_trace_analysis(
    trace_id: str,
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get analysis and learnings from a completed trace.
    
    Analyzes the trace to extract successful patterns and learnings.
    This implements the feedback loop: analyze completed traces to improve future decisions.
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        from dcisionai_workflow.shared.graph.feedback_analyzer import analyze_trace_for_improvement
        
        analysis = analyze_trace_for_improvement(executor, trace_id)
        
        return analysis
    except Exception as e:
        logger.error(f"Failed to analyze trace: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze trace: {str(e)}")
    finally:
        executor.close()


@router.get("/decisions/{decision_id}/similar", response_model=Dict[str, Any])
async def get_similar_decisions(
    decision_id: str,
    limit: int = Query(default=5, description="Maximum number of similar decisions to return"),
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Find similar DecisionEvents using hybrid search (semantic + structural).
    
    Uses both semantic similarity (Pinecone) and structural similarity (FastRP)
    to find decisions with similar context and graph structure.
    
    Returns:
        {
            "decision_id": "...",
            "similar_decisions": [
                {
                    "id": "...",
                    "decision_type": "...",
                    "decision": "...",
                    "similarity_score": 0.85,
                    "semantic_score": 0.80,
                    "structural_score": 0.90
                }
            ]
        }
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        # Get the decision to find similar ones for
        cypher = """
            MATCH (de:DecisionEvent {id: $decision_id})
            RETURN de.decision as decision,
                   de.decision_type as decision_type,
                   de.reasoning as reasoning,
                   de.trace_id as trace_id
        """
        decision_records = executor.execute_read(cypher, {"decision_id": decision_id})
        
        if not decision_records:
            raise HTTPException(status_code=404, detail=f"Decision not found: {decision_id}")
        
        decision_data = decision_records[0]
        trace_id = decision_data.get("trace_id")
        
        # Use hybrid search from precedent_finder
        from dcisionai_workflow.shared.graph.precedent_finder import find_similar_traces_hybrid
        
        # For now, we'll find similar traces and then filter to DecisionEvents
        # In the future, we could create a DecisionEvent-specific similarity search
        similar_traces = await find_similar_traces_hybrid(
            executor=executor,
            trace_id=trace_id,
            problem_description=decision_data.get("decision", ""),
            problem_type=decision_data.get("decision_type"),
            limit=limit * 2  # Get more to filter
        )
        
        # Get DecisionEvents from similar traces
        similar_decisions = []
        for trace in similar_traces[:limit]:
            similar_trace_id = trace.get("trace_id")
            if similar_trace_id == trace_id:
                continue  # Skip self
            
            # Get DecisionEvents from this trace with similar decision_type
            cypher = """
                MATCH (p:Problem {trace_id: $trace_id})-[:TRIGGERED]->(de:DecisionEvent)
                WHERE de.decision_type = $decision_type
                RETURN de.id as id,
                       de.decision_type as decision_type,
                       de.decision as decision,
                       de.reasoning as reasoning,
                       de.agent as agent,
                       de.timestamp as timestamp
                ORDER BY de.timestamp DESC
                LIMIT 1
            """
            similar_de_records = executor.execute_read(cypher, {
                "trace_id": similar_trace_id,
                "decision_type": decision_data.get("decision_type")
            })
            
            for de_record in similar_de_records:
                similar_decisions.append({
                    "id": de_record.get("id"),
                    "decision_type": de_record.get("decision_type"),
                    "decision": de_record.get("decision"),
                    "reasoning": de_record.get("reasoning"),
                    "agent": de_record.get("agent"),
                    "timestamp": str(de_record.get("timestamp")) if de_record.get("timestamp") else None,
                    "similarity_score": trace.get("similarity_score", 0.0),
                    "trace_id": similar_trace_id
                })
        
        return {
            "decision_id": decision_id,
            "similar_decisions": similar_decisions[:limit]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to find similar decisions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to find similar decisions: {str(e)}")
    finally:
        executor.close()


@router.get("/decisions/patterns/{decision_type}", response_model=Dict[str, Any])
async def get_decision_patterns(
    decision_type: str,
    min_occurrences: int = Query(default=5, description="Minimum occurrences to consider a pattern"),
    time_window_days: int = Query(default=30, description="Time window in days"),
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get learned patterns for a decision type.
    
    Analyzes decision traces to extract:
    - Successful patterns (high success rate)
    - Common reasoning patterns
    - Context patterns that lead to success
    
    This enables the flywheel: learn from past decisions to improve future ones.
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        from dcisionai_workflow.shared.graph.feedback_analyzer import FeedbackAnalyzer
        
        analyzer = FeedbackAnalyzer(executor)
        patterns = analyzer.analyze_decision_patterns(
            decision_type=decision_type,
            min_occurrences=min_occurrences,
            time_window_days=time_window_days
        )
        
        return patterns
    except Exception as e:
        logger.error(f"Failed to get decision patterns: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze patterns: {str(e)}")
    finally:
        executor.close()


@router.get("/decisions/feedback/{decision_type}", response_model=Dict[str, Any])
async def get_decision_feedback(
    decision_type: str,
    context: str = Query(default="{}", description="JSON string of context"),
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get feedback/recommendations for making a decision.
    
    Uses learned patterns to suggest what has worked in similar contexts.
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        import json
        context_dict = json.loads(context) if context else {}
        
        from dcisionai_workflow.shared.graph.feedback_analyzer import FeedbackAnalyzer
        
        analyzer = FeedbackAnalyzer(executor)
        feedback = analyzer.provide_decision_feedback(
            decision_type=decision_type,
            context=context_dict
        )
        
        return feedback
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in context parameter")
    except Exception as e:
        logger.error(f"Failed to get decision feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get feedback: {str(e)}")
    finally:
        executor.close()


@router.get("/decisions/query-by-context", response_model=Dict[str, Any])
async def query_decisions_by_context(
    constraint_count: Optional[int] = Query(default=None, description="Filter by constraint_count"),
    solve_time_ms: Optional[int] = Query(default=None, description="Filter by solve_time_ms (max)"),
    status: Optional[str] = Query(default=None, description="Filter by status"),
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Query DecisionEvents by context properties using DecisionContext nodes.
    
    Enables queries like:
    - Find all decisions where constraint_count > 10
    - Find all decisions where solve_time_ms < 100
    - Find all decisions where status = 'optimal'
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        from dcisionai_workflow.shared.graph.context_extractor import query_decisions_by_context
        
        # Build filters
        filters = {}
        if constraint_count is not None:
            filters["constraint_count"] = {"$gte": constraint_count}
        if solve_time_ms is not None:
            filters["solve_time_ms"] = {"$lte": solve_time_ms}
        if status:
            filters["status"] = status
        
        decisions = query_decisions_by_context(executor, filters)
        
        return {
            "decisions": decisions,
            "count": len(decisions)
        }
    except Exception as e:
        logger.error(f"Failed to query decisions by context: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to query decisions: {str(e)}")
    finally:
        executor.close()


@router.get("/traces/{trace_id}/analysis", response_model=Dict[str, Any])
async def get_trace_analysis(
    trace_id: str,
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
):
    """
    Get analysis and learnings from a completed trace.
    
    Analyzes the trace to extract successful patterns and learnings.
    This implements the feedback loop: analyze completed traces to improve future decisions.
    """
    if not ensure_graph_connection():
        error_msg = f"Graph components not available: {GRAPH_ERROR}" if GRAPH_ERROR else "Graph components not available"
        raise HTTPException(status_code=503, detail=error_msg)
    
    executor = GraphExecutor()
    try:
        from dcisionai_workflow.shared.graph.feedback_analyzer import analyze_trace_for_improvement
        
        analysis = analyze_trace_for_improvement(executor, trace_id)
        
        return analysis
    except Exception as e:
        logger.error(f"Failed to analyze trace: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze trace: {str(e)}")
    finally:
        executor.close()

