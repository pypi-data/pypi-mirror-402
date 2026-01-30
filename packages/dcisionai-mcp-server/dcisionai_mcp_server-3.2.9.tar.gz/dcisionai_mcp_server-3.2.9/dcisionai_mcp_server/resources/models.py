"""
Model Resources - Direct dcisionai_workflow Integration

Exposes deployed models as MCP resources by directly importing
the model registry from dcisionai_workflow.models.model_registry.
"""

import json
import logging
from typing import Optional
from mcp.types import Resource

# Handle both relative and absolute imports
try:
    from ..config import MCPConfig
except ImportError:
    import os
    import sys
    import importlib.util
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.py')
    config_spec = importlib.util.spec_from_file_location('config', config_path)
    config_module = importlib.util.module_from_spec(config_spec)
    config_spec.loader.exec_module(config_module)
    MCPConfig = config_module.MCPConfig

logger = logging.getLogger(__name__)


def get_model_resources() -> list[Resource]:
    """Get list of model resources"""
    return [
        Resource(
            uri="dcisionai://models/list",
            name="Deployed Models",
            description="List of all deployed DcisionAI models with metadata, capabilities, and usage examples",
            mimeType="application/json"
        )
    ]


async def read_model_resource(uri: str, tenant_id: Optional[str] = None, is_admin: bool = False) -> str:
    """
    Read model resource by directly importing from dcisionai_workflow.models.model_registry
    
    Args:
        uri: Resource URI (e.g., dcisionai://models/list)
        
    Returns:
        Resource content as JSON string (filtered by domain if configured)
    """
    if uri == "dcisionai://models/list":
        try:
            # Direct import from dcisionai_workflow.models.model_registry (no HTTP call)
            # Add project root to sys.path if needed
            import os
            import sys
            
            # In Docker/Railway, PYTHONPATH is set to /app, so dcisionai_workflow should be importable directly
            # Get project root (two levels up from this file: resources/models.py -> dcisionai_mcp_server -> project root)
            current_file = os.path.abspath(__file__)
            project_root = os.path.abspath(os.path.join(os.path.dirname(current_file), '..', '..'))
            
            # Also check /app (Docker default) and current working directory
            possible_roots = [
                project_root,
                '/app',  # Docker default
                os.getcwd(),  # Current working directory
            ]
            
            # Add all possible roots to sys.path
            for root in possible_roots:
                if root and os.path.exists(root) and root not in sys.path:
                    sys.path.insert(0, root)
                    logger.info(f"Added to sys.path: {root}")
            
            # Log current sys.path for debugging
            logger.info(f"Current sys.path (first 5): {sys.path[:5]}")
            logger.info(f"PYTHONPATH env: {os.getenv('PYTHONPATH', 'not set')}")
            
            # Fetch models ONLY from Supabase database
            models_list = []
            try:
                from dcisionai_mcp_server.jobs.storage import supabase_client
                
                if not supabase_client:
                    logger.warning("Supabase client not available - returning empty model list")
                    models_response = {"models": [], "total": 0, "message": "Database not available"}
                else:
                    try:
                        # Query Supabase for deployed models with tenant filtering
                        query = supabase_client.table("deployed_models").select("*")
                        
                        # Apply tenant filtering if tenant_id provided and not admin
                        # If tenant_id is None, return all models (for backward compatibility)
                        if tenant_id and not is_admin:
                            # Explicit tenant filtering (more reliable than RLS)
                            query = query.eq("tenant_id", tenant_id)
                            logger.info(f"✅ Filtering models by tenant_id: {tenant_id}")
                        elif is_admin:
                            logger.info("✅ Admin access - returning all models")
                        else:
                            # No tenant_id provided - return all models
                            # This allows the API page to show all models when no API key is provided
                            logger.info("⚠️ No tenant_id provided - returning all models")
                        
                        response = query.order("created_at", desc=True).execute()
                        
                        logger.info(f"✅ Query executed: found {len(response.data) if response.data else 0} models")
                        
                        if response.data:
                            logger.info(f"✅ Found {len(response.data)} models in Supabase")
                            
                            # Convert Supabase models to the expected format
                            for supabase_model in response.data:
                                # Get all versions for this base_name to determine if this is latest
                                base_name = supabase_model.get('base_name')
                                version = supabase_model.get('version', 1)
                                
                                # Query for all versions of this base model
                                versions_response = supabase_client.table("deployed_models").select("model_id, version").eq("base_name", base_name).order("version", desc=True).execute()
                                all_versions = [v.get('model_id') for v in versions_response.data] if versions_response.data else [supabase_model.get('model_id')]
                                
                                models_list.append({
                                    'id': supabase_model.get('model_id'),
                                    'model_id': supabase_model.get('model_id'),
                                    'base_name': base_name,
                                    'version': str(version),
                                    'all_versions': all_versions,
                                    'is_latest': supabase_model.get('model_id') == all_versions[0] if all_versions else True,
                                    'name': supabase_model.get('name'),
                                    'description': supabase_model.get('description'),
                                    'domain': supabase_model.get('domain', 'general'),
                                    'status': 'active',
                                    'created_at': supabase_model.get('created_at'),
                                    'avg_solve_time': supabase_model.get('avg_solve_time', 0.0),
                                    'variables': supabase_model.get('variables', 0),
                                    'constraints': supabase_model.get('constraints', 0),
                                    'solver': supabase_model.get('solver', 'scip'),
                                    'problem_type': supabase_model.get('problem_type', 'linear_programming'),
                                    'file_path': supabase_model.get('file_path'),
                                    'class_name': supabase_model.get('class_name'),
                                    'module_name': supabase_model.get('module_name'),
                                    'default_data': supabase_model.get('default_data', {}),
                                    'problem_signature': supabase_model.get('problem_signature'),
                                    'optimization_plan': supabase_model.get('optimization_plan'),
                                    'solver_result': supabase_model.get('solver_result'),
                                    'source_job_id': supabase_model.get('source_job_id'),
                                    'tenant_id': supabase_model.get('tenant_id'),
                                    'data_requirements': {'required': [], 'optional': []}
                                })
                        else:
                            logger.info("No models found in Supabase")
                        
                        models_response = {
                            "models": models_list,
                            "total": len(models_list),
                            "source": "supabase"
                        }
                    except Exception as supabase_error:
                        logger.error(f"❌ Failed to fetch models from Supabase: {supabase_error}", exc_info=True)
                        models_response = {
                            "models": [],
                            "total": 0,
                            "error": str(supabase_error),
                            "message": "Failed to load models from database"
                        }
            except Exception as e:
                logger.error(f"❌ Error fetching models from Supabase: {e}", exc_info=True)
                models_response = {
                    "models": [],
                    "total": 0,
                    "error": str(e),
                    "message": "Failed to connect to database"
                }
            
            # Apply domain filtering if configured
            domain_filter = MCPConfig.get_domain_filter()
            if domain_filter != "all" and "models" in models_response:
                models_list = models_response.get("models", [])
                filtered_models = [
                    model for model in models_list
                    if model.get("domain", "").lower() == domain_filter.lower()
                ]
                models_response = {
                    "models": filtered_models,
                    "filtered_by_domain": domain_filter,
                    "total_models": len(models_list),
                    "filtered_count": len(filtered_models)
                }
            
            return json.dumps(models_response, indent=2)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"Error reading model resource: {e}", exc_info=True)
            
            # Include detailed error information in response for debugging
            error_response = {
                "error": str(e),
                "message": "Failed to load deployed models. Ensure dcisionai_workflow.shared.core.models.model_registry is accessible.",
                "error_type": type(e).__name__,
                "traceback": error_details.split('\n')[-10:] if len(error_details) > 10 else error_details.split('\n')
            }
            
            # Add sys.path info for debugging
            import sys
            error_response["sys_path"] = sys.path[:10]
            error_response["pythonpath_env"] = os.getenv('PYTHONPATH', 'not set')
            error_response["cwd"] = os.getcwd()
            
            return json.dumps(error_response, indent=2)
    else:
        return json.dumps({"error": f"Unknown resource URI: {uri}"})

