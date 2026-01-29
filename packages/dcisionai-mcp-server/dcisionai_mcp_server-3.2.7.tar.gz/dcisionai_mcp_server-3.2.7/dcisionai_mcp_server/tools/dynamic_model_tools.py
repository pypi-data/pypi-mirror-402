"""
Dynamic Model Tools Generator

Generates MCP tools dynamically for deployed models:
- Execution tool (dcisionai_model_{model_id})
- Simulation tools (5 tools per model):
  - Single scenario simulation
  - Multi-scenario comparison
  - Sensitivity analysis
  - Monte Carlo simulation
  - Mesa interactive simulation
"""

import json
import logging
import copy
from typing import Dict, Any, List, Optional, Callable
from functools import partial

from dcisionai_workflow.tools.mcp_decorator import mcp_tool

logger = logging.getLogger(__name__)


def generate_modification_schema(default_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate JSON Schema for modifications based on default_data structure.
    
    This allows agents to understand what parameters can be modified.
    """
    properties = {}
    
    # Extract parameters from default_data
    if "parameters" in default_data:
        params = default_data["parameters"]
        for key, value in params.items():
            if isinstance(value, (int, float)):
                properties[key] = {
                    "type": "number",
                    "description": f"Modify {key} parameter"
                }
            elif isinstance(value, bool):
                properties[key] = {
                    "type": "boolean",
                    "description": f"Modify {key} parameter"
                }
            elif isinstance(value, list):
                if len(value) > 0:
                    # Infer item type from first element
                    first_item = value[0]
                    if isinstance(first_item, (int, float)):
                        item_type = "number"
                    elif isinstance(first_item, bool):
                        item_type = "boolean"
                    elif isinstance(first_item, str):
                        item_type = "string"
                    elif isinstance(first_item, dict):
                        item_type = "object"
                    else:
                        item_type = "object"
                    
                    properties[key] = {
                        "type": "array",
                        "items": {"type": item_type},
                        "description": f"Modify {key} array"
                    }
                else:
                    properties[key] = {
                        "type": "array",
                        "description": f"Modify {key} array"
                    }
            elif isinstance(value, dict):
                properties[key] = {
                    "type": "object",
                    "description": f"Modify {key} object"
                }
            elif isinstance(value, str):
                properties[key] = {
                    "type": "string",
                    "description": f"Modify {key} parameter"
                }
    
    return properties


def extract_parameter_names(default_data: Dict[str, Any]) -> List[str]:
    """Extract parameter names from default_data for enum generation."""
    names = []
    if "parameters" in default_data and isinstance(default_data["parameters"], dict):
        names.extend(default_data["parameters"].keys())
    return names


def generate_execution_tool(model: Dict[str, Any]) -> Callable:
    """
    Generate execution tool for a deployed model.
    
    Tool name: dcisionai_model_{model_id}
    """
    model_id = model.get("model_id")
    name = model.get("name", model_id)
    description = model.get("description", f"Execute deployed model: {name}")
    default_data = model.get("default_data", {})
    
    # Generate input schema from default_data
    modification_schema = generate_modification_schema(default_data)
    
    input_schema = {
        "type": "object",
        "properties": {
            "data": {
                "type": "object",
                "description": "Model-specific input data. If not provided, uses model's default_data.",
                "properties": modification_schema
            },
            "options": {
                "type": "object",
                "description": "Optional solver options",
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
        }
    }
    
    @mcp_tool(
        name=f"dcisionai_model_{model_id}",
        description=description,
        input_schema=input_schema
    )
    async def execute_model_tool(data: Optional[Dict[str, Any]] = None, options: Optional[Dict[str, Any]] = None) -> List:
        """Execute deployed model with provided data."""
        from mcp.types import TextContent
        from dcisionai_workflow.models.model_registry import run_deployed_model
        
        try:
            # Use provided data or default_data
            input_data = data if data is not None else default_data
            
            # Execute model
            result = await run_deployed_model(
                model_id=model_id,
                data=input_data,
                options=options or {}
            )
            
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "success",
                        "model_id": model_id,
                        "result": result
                    }, indent=2, default=str)
                )
            ]
        except Exception as e:
            logger.error(f"Error executing model {model_id}: {e}", exc_info=True)
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "error",
                        "model_id": model_id,
                        "error": str(e)
                    })
                )
            ]
    
    return execute_model_tool


def generate_single_scenario_tool(model: Dict[str, Any]) -> Callable:
    """Generate single scenario simulation tool."""
    model_id = model.get("model_id")
    name = model.get("name", model_id)
    default_data = model.get("default_data", {})
    
    modification_schema = generate_modification_schema(default_data)
    
    input_schema = {
        "type": "object",
        "properties": {
            "modifications": {
                "type": "object",
                "description": "Modifications to apply to default parameters",
                "properties": modification_schema
            },
            "solver_options": {
                "type": "object",
                "properties": {
                    "solver": {"type": "string", "default": "scip"},
                    "time_limit": {"type": "integer", "default": 60},
                    "verbose": {"type": "boolean", "default": False}
                }
            }
        },
        "required": ["modifications"]
    }
    
    @mcp_tool(
        name=f"dcisionai_model_{model_id}_simulate",
        description=f"Simulate single scenario for {name}. Modify constraints, parameters, or objectives and see how the solution changes.",
        input_schema=input_schema
    )
    async def simulate_scenario_tool(modifications: Dict[str, Any], solver_options: Optional[Dict[str, Any]] = None) -> List:
        """Simulate single scenario with modifications."""
        from mcp.types import TextContent
        from dcisionai_workflow.models.model_registry import run_deployed_model
        
        try:
            # Apply modifications to default_data
            modified_data = copy.deepcopy(default_data)
            
            # Apply parameter modifications
            if "parameters" in modifications:
                if "parameters" not in modified_data:
                    modified_data["parameters"] = {}
                modified_data["parameters"].update(modifications["parameters"])
            
            # Apply direct modifications (for non-parameter fields)
            for key, value in modifications.items():
                if key != "parameters":
                    modified_data[key] = value
            
            # Execute model with modified data
            result = await run_deployed_model(
                model_id=model_id,
                data=modified_data,
                options=solver_options or {}
            )
            
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "success",
                        "model_id": model_id,
                        "scenario_result": result,
                        "modifications_applied": modifications
                    }, indent=2, default=str)
                )
            ]
        except Exception as e:
            logger.error(f"Error simulating scenario for {model_id}: {e}", exc_info=True)
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "error",
                        "model_id": model_id,
                        "error": str(e)
                    })
                )
            ]
    
    return simulate_scenario_tool


def generate_multi_scenario_tool(model: Dict[str, Any]) -> Callable:
    """Generate multi-scenario comparison tool."""
    model_id = model.get("model_id")
    name = model.get("name", model_id)
    default_data = model.get("default_data", {})
    
    modification_schema = generate_modification_schema(default_data)
    
    input_schema = {
        "type": "object",
        "properties": {
            "scenarios": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Scenario name (e.g., 'Conservative', 'Aggressive')"
                        },
                        "modifications": {
                            "type": "object",
                            "properties": modification_schema,
                            "description": "Modifications for this scenario"
                        }
                    },
                    "required": ["name", "modifications"]
                },
                "minItems": 2,
                "maxItems": 5,
                "description": "List of scenarios to compare (2-5 scenarios)"
            },
            "solver_options": {
                "type": "object",
                "properties": {
                    "solver": {"type": "string", "default": "scip"},
                    "time_limit": {"type": "integer", "default": 60}
                }
            }
        },
        "required": ["scenarios"]
    }
    
    @mcp_tool(
        name=f"dcisionai_model_{model_id}_compare",
        description=f"Compare multiple scenarios for {name}. Solves all scenarios in parallel and generates comparison report.",
        input_schema=input_schema
    )
    async def compare_scenarios_tool(scenarios: List[Dict[str, Any]], solver_options: Optional[Dict[str, Any]] = None) -> List:
        """Compare multiple scenarios."""
        from mcp.types import TextContent
        from dcisionai_workflow.models.model_registry import run_deployed_model
        import asyncio
        
        try:
            # Solve all scenarios in parallel
            tasks = []
            for scenario in scenarios:
                modified_data = copy.deepcopy(default_data)
                
                # Apply modifications
                if "parameters" in scenario["modifications"]:
                    if "parameters" not in modified_data:
                        modified_data["parameters"] = {}
                    modified_data["parameters"].update(scenario["modifications"]["parameters"])
                
                # Apply direct modifications
                for key, value in scenario["modifications"].items():
                    if key != "parameters":
                        modified_data[key] = value
                
                # Create task
                task = run_deployed_model(
                    model_id=model_id,
                    data=modified_data,
                    options=solver_options or {}
                )
                tasks.append((scenario["name"], task))
            
            # Execute all tasks
            results = []
            for name, task in tasks:
                result = await task
                results.append({
                    "name": name,
                    "result": result
                })
            
            # Generate comparison report
            comparison = generate_comparison_report(results)
            
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "success",
                        "model_id": model_id,
                        "scenarios": results,
                        "comparison": comparison
                    }, indent=2, default=str)
                )
            ]
        except Exception as e:
            logger.error(f"Error comparing scenarios for {model_id}: {e}", exc_info=True)
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "error",
                        "model_id": model_id,
                        "error": str(e)
                    })
                )
            ]
    
    return compare_scenarios_tool


def generate_sensitivity_tool(model: Dict[str, Any]) -> Callable:
    """Generate sensitivity analysis tool."""
    model_id = model.get("model_id")
    name = model.get("name", model_id)
    default_data = model.get("default_data", {})
    
    parameter_names = extract_parameter_names(default_data)
    
    input_schema = {
        "type": "object",
        "properties": {
            "parameter_ranges": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "parameter_name": {
                            "type": "string",
                            "description": f"Parameter to analyze. Available: {', '.join(parameter_names) if parameter_names else 'N/A'}"
                        },
                        "min_value": {"type": "number", "description": "Minimum parameter value"},
                        "max_value": {"type": "number", "description": "Maximum parameter value"},
                        "steps": {"type": "integer", "default": 10, "minimum": 2, "maximum": 50}
                    },
                    "required": ["parameter_name", "min_value", "max_value"]
                },
                "minItems": 1,
                "maxItems": 5
            },
            "solver_options": {
                "type": "object",
                "properties": {
                    "solver": {"type": "string", "default": "scip"},
                    "time_limit": {"type": "integer", "default": 30}
                }
            }
        },
        "required": ["parameter_ranges"]
    }
    
    @mcp_tool(
        name=f"dcisionai_model_{model_id}_sensitivity",
        description=f"Perform sensitivity analysis for {name}. Systematically varies parameters and analyzes objective value changes.",
        input_schema=input_schema
    )
    async def sensitivity_analysis_tool(parameter_ranges: List[Dict[str, Any]], solver_options: Optional[Dict[str, Any]] = None) -> List:
        """Perform sensitivity analysis."""
        from mcp.types import TextContent
        from dcisionai_workflow.models.model_registry import run_deployed_model
        try:
            import numpy as np
        except ImportError:
            logger.error("numpy is required for sensitivity analysis")
            raise ImportError("numpy is required for sensitivity analysis. Install with: pip install numpy")
        
        try:
            results = []
            
            for param_range in parameter_ranges:
                param_name = param_range["parameter_name"]
                min_val = param_range["min_value"]
                max_val = param_range["max_value"]
                steps = param_range.get("steps", 10)
                
                # Generate parameter values
                values = np.linspace(min_val, max_val, steps).tolist()
                
                param_results = []
                for value in values:
                    # Modify default_data
                    modified_data = copy.deepcopy(default_data)
                    if "parameters" not in modified_data:
                        modified_data["parameters"] = {}
                    modified_data["parameters"][param_name] = value
                    
                    # Solve with deployed model
                    result = await run_deployed_model(
                        model_id=model_id,
                        data=modified_data,
                        options=solver_options or {"time_limit": 30}
                    )
                    
                    param_results.append({
                        "parameter_value": value,
                        "objective_value": result.get("objective_value"),
                        "status": result.get("optimization_status") or result.get("status")
                    })
                
                results.append({
                    "parameter_name": param_name,
                    "results": param_results
                })
            
            # Generate sensitivity report
            report = generate_sensitivity_report(results)
            
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "success",
                        "model_id": model_id,
                        "sensitivity_analysis": results,
                        "report": report
                    }, indent=2, default=str)
                )
            ]
        except Exception as e:
            logger.error(f"Error in sensitivity analysis for {model_id}: {e}", exc_info=True)
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "error",
                        "model_id": model_id,
                        "error": str(e)
                    })
                )
            ]
    
    return sensitivity_analysis_tool


def generate_monte_carlo_tool(model: Dict[str, Any]) -> Callable:
    """Generate Monte Carlo simulation tool."""
    model_id = model.get("model_id")
    name = model.get("name", model_id)
    default_data = model.get("default_data", {})
    
    parameter_names = extract_parameter_names(default_data)
    
    input_schema = {
        "type": "object",
        "properties": {
            "parameter_distributions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "parameter_name": {
                            "type": "string",
                            "description": f"Parameter to sample. Available: {', '.join(parameter_names) if parameter_names else 'N/A'}"
                        },
                        "distribution_type": {
                            "type": "string",
                            "enum": ["normal", "uniform", "lognormal", "triangular"],
                            "description": "Probability distribution type"
                        },
                        "parameters": {
                            "type": "object",
                            "description": "Distribution parameters (mean/std for normal, min/max for uniform, etc.)"
                        }
                    },
                    "required": ["parameter_name", "distribution_type", "parameters"]
                },
                "minItems": 1,
                "maxItems": 10
            },
            "n_samples": {
                "type": "integer",
                "default": 100,
                "minimum": 10,
                "maximum": 1000,
                "description": "Number of Monte Carlo samples"
            },
            "solver_options": {
                "type": "object",
                "properties": {
                    "solver": {"type": "string", "default": "scip"},
                    "time_limit": {"type": "integer", "default": 30}
                }
            }
        },
        "required": ["parameter_distributions"]
    }
    
    @mcp_tool(
        name=f"dcisionai_model_{model_id}_monte_carlo",
        description=f"Perform Monte Carlo simulation for {name}. Samples parameters from probability distributions and analyzes objective value distribution.",
        input_schema=input_schema
    )
    async def monte_carlo_tool(parameter_distributions: List[Dict[str, Any]], n_samples: int = 100, solver_options: Optional[Dict[str, Any]] = None) -> List:
        """Perform Monte Carlo simulation."""
        from mcp.types import TextContent
        from dcisionai_workflow.models.model_registry import run_deployed_model
        try:
            import numpy as np
        except ImportError:
            logger.error("numpy is required for Monte Carlo simulation")
            raise ImportError("numpy is required for Monte Carlo simulation. Install with: pip install numpy")
        
        try:
            samples = []
            
            for i in range(n_samples):
                # Sample parameters from distributions
                modified_data = copy.deepcopy(default_data)
                if "parameters" not in modified_data:
                    modified_data["parameters"] = {}
                
                sampled_params = {}
                for dist in parameter_distributions:
                    param_name = dist["parameter_name"]
                    dist_type = dist["distribution_type"]
                    dist_params = dist["parameters"]
                    
                    # Sample value from distribution
                    value = sample_from_distribution(dist_type, dist_params)
                    sampled_params[param_name] = value
                    modified_data["parameters"][param_name] = value
                
                # Solve with deployed model
                result = await run_deployed_model(
                    model_id=model_id,
                    data=modified_data,
                    options=solver_options or {"time_limit": 30}
                )
                
                samples.append({
                    "sample_id": i,
                    "objective_value": result.get("objective_value"),
                    "status": result.get("optimization_status") or result.get("status"),
                    "parameters": sampled_params
                })
            
            # Generate Monte Carlo report
            report = generate_monte_carlo_report(samples)
            
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "success",
                        "model_id": model_id,
                        "monte_carlo_samples": samples,
                        "report": report
                    }, indent=2, default=str)
                )
            ]
        except Exception as e:
            logger.error(f"Error in Monte Carlo simulation for {model_id}: {e}", exc_info=True)
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "error",
                        "model_id": model_id,
                        "error": str(e)
                    })
                )
            ]
    
    return monte_carlo_tool


def generate_mesa_tool(model: Dict[str, Any]) -> Callable:
    """Generate Mesa interactive simulation tool."""
    model_id = model.get("model_id")
    name = model.get("name", model_id)
    default_data = model.get("default_data", {})
    problem_signature = model.get("problem_signature", {})
    
    modification_schema = generate_modification_schema(default_data)
    
    input_schema = {
        "type": "object",
        "properties": {
            "initial_parameters": {
                "type": "object",
                "description": "Initial parameter values (defaults to model's default_data)",
                "properties": modification_schema
            }
        }
    }
    
    @mcp_tool(
        name=f"dcisionai_model_{model_id}_mesa",
        description=f"Initialize Mesa interactive simulation for {name}. Real-time parameter adjustment with sliders.",
        input_schema=input_schema
    )
    async def mesa_tool(initial_parameters: Optional[Dict[str, Any]] = None) -> List:
        """Initialize Mesa interactive simulation."""
        from mcp.types import TextContent
        
        try:
            # Use existing Mesa service
            from dcisionai_workflow.tools.simulation.mesa_service import MesaOptimizationService
            
            service = MesaOptimizationService()
            
            # Extract numeric parameters from initial_parameters or default_data
            # Mesa expects Dict[str, float] for initial_parameters
            numeric_params = None
            if initial_parameters:
                # Extract numeric values from initial_parameters
                numeric_params = {}
                for key, value in initial_parameters.items():
                    if isinstance(value, (int, float)):
                        numeric_params[key] = float(value)
                    elif isinstance(value, dict) and 'parameters' in value:
                        # Handle nested parameters dict
                        for param_key, param_value in value['parameters'].items():
                            if isinstance(param_value, (int, float)):
                                numeric_params[param_key] = float(param_value)
            elif default_data and 'parameters' in default_data:
                # Extract numeric parameters from default_data
                params = default_data['parameters']
                if isinstance(params, dict):
                    numeric_params = {}
                    for key, value in params.items():
                        if isinstance(value, (int, float)):
                            numeric_params[key] = float(value)
            
            # Initialize Mesa model with deployed model
            mesa_model_id = await service.initialize_with_deployed_model(
                model_id=model_id,
                problem_signature=problem_signature,
                default_data=default_data,
                initial_parameters=numeric_params
            )
            
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "success",
                        "mesa_model_id": mesa_model_id,
                        "model_id": model_id,
                        "message": "Mesa model initialized. Use dcisionai_update_mesa_parameter to adjust parameters."
                    }, indent=2)
                )
            ]
        except Exception as e:
            logger.error(f"Error initializing Mesa model for {model_id}: {e}", exc_info=True)
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "error",
                        "model_id": model_id,
                        "error": str(e)
                    })
                )
            ]
    
    return mesa_tool


# Helper functions

def generate_comparison_report(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate comparison report from scenario results."""
    if not results:
        return {}
    
    objective_values = []
    for r in results:
        obj_val = r.get("result", {}).get("objective_value")
        if obj_val is not None:
            objective_values.append((r["name"], obj_val))
    
    if not objective_values:
        return {"message": "No valid objective values to compare"}
    
    # Sort by objective value
    objective_values.sort(key=lambda x: x[1])
    
    best_scenario = objective_values[0][0]
    worst_scenario = objective_values[-1][0]
    
    return {
        "best_scenario": best_scenario,
        "worst_scenario": worst_scenario,
        "objective_range": {
            "min": objective_values[0][1],
            "max": objective_values[-1][1],
            "range": objective_values[-1][1] - objective_values[0][1]
        },
        "scenario_count": len(results)
    }


def generate_sensitivity_report(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate sensitivity analysis report."""
    report = {
        "parameters_analyzed": len(results),
        "findings": []
    }
    
    try:
        import numpy as np
        has_numpy = True
    except ImportError:
        has_numpy = False
    
    for param_result in results:
        param_name = param_result["parameter_name"]
        param_results = param_result["results"]
        
        # Extract objective values
        obj_values = [r["objective_value"] for r in param_results if r["objective_value"] is not None]
        
        if obj_values:
            if has_numpy:
                mean_val = np.mean(obj_values)
                sensitivity = "high" if (max(obj_values) - min(obj_values)) > 0.1 * abs(mean_val) else "low"
            else:
                mean_val = sum(obj_values) / len(obj_values)
                sensitivity = "high" if (max(obj_values) - min(obj_values)) > 0.1 * abs(mean_val) else "low"
            
            report["findings"].append({
                "parameter": param_name,
                "objective_min": min(obj_values),
                "objective_max": max(obj_values),
                "objective_range": max(obj_values) - min(obj_values),
                "sensitivity": sensitivity
            })
    
    return report


def generate_monte_carlo_report(samples: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate Monte Carlo simulation report."""
    obj_values = [s["objective_value"] for s in samples if s["objective_value"] is not None]
    
    if not obj_values:
        return {"message": "No valid objective values"}
    
    try:
        import numpy as np
        has_numpy = True
    except ImportError:
        has_numpy = False
    
    if has_numpy:
        return {
            "total_samples": len(samples),
            "successful_samples": len(obj_values),
            "success_rate": len(obj_values) / len(samples),
            "statistics": {
                "mean": float(np.mean(obj_values)),
                "std": float(np.std(obj_values)),
                "min": float(np.min(obj_values)),
                "max": float(np.max(obj_values))
            },
            "percentiles": {
                "5th": float(np.percentile(obj_values, 5)),
                "25th": float(np.percentile(obj_values, 25)),
                "50th": float(np.percentile(obj_values, 50)),
                "75th": float(np.percentile(obj_values, 75)),
                "95th": float(np.percentile(obj_values, 95))
            }
        }
    else:
        # Fallback without numpy
        sorted_vals = sorted(obj_values)
        n = len(sorted_vals)
        return {
            "total_samples": len(samples),
            "successful_samples": len(obj_values),
            "success_rate": len(obj_values) / len(samples),
            "statistics": {
                "mean": sum(obj_values) / n,
                "std": (sum((x - sum(obj_values) / n) ** 2 for x in obj_values) / n) ** 0.5,
                "min": min(obj_values),
                "max": max(obj_values)
            },
            "percentiles": {
                "5th": sorted_vals[int(n * 0.05)] if n > 0 else 0,
                "25th": sorted_vals[int(n * 0.25)] if n > 0 else 0,
                "50th": sorted_vals[int(n * 0.5)] if n > 0 else 0,
                "75th": sorted_vals[int(n * 0.75)] if n > 0 else 0,
                "95th": sorted_vals[int(n * 0.95)] if n > 0 else 0
            }
        }


def sample_from_distribution(dist_type: str, params: Dict[str, Any]) -> float:
    """Sample a value from a probability distribution."""
    try:
        import numpy as np
        has_numpy = True
    except ImportError:
        has_numpy = False
        import random
        import math
    
    if dist_type == "normal":
        if has_numpy:
            mean = params.get("mean", 0)
            std = params.get("std", 1)
            return float(np.random.normal(mean, std))
        else:
            # Box-Muller transform for normal distribution
            u1, u2 = random.random(), random.random()
            z = (-2 * math.log(u1)) ** 0.5 * math.cos(2 * math.pi * u2)
            mean = params.get("mean", 0)
            std = params.get("std", 1)
            return float(z * std + mean)
    elif dist_type == "uniform":
        if has_numpy:
            min_val = params.get("min", 0)
            max_val = params.get("max", 1)
            return float(np.random.uniform(min_val, max_val))
        else:
            return float(random.uniform(params.get("min", 0), params.get("max", 1)))
    elif dist_type == "lognormal":
        if has_numpy:
            mean = params.get("mean", 0)
            std = params.get("std", 1)
            return float(np.random.lognormal(mean, std))
        else:
            raise ValueError("lognormal distribution requires numpy")
    elif dist_type == "triangular":
        if has_numpy:
            left = params.get("left", 0)
            mode = params.get("mode", 0.5)
            right = params.get("right", 1)
            return float(np.random.triangular(left, mode, right))
        else:
            raise ValueError("triangular distribution requires numpy")
    else:
        raise ValueError(f"Unknown distribution type: {dist_type}")
    
    if dist_type == "normal":
        mean = params.get("mean", 0)
        std = params.get("std", 1)
        return float(np.random.normal(mean, std))
    elif dist_type == "uniform":
        min_val = params.get("min", 0)
        max_val = params.get("max", 1)
        return float(np.random.uniform(min_val, max_val))
    elif dist_type == "lognormal":
        mean = params.get("mean", 0)
        std = params.get("std", 1)
        return float(np.random.lognormal(mean, std))
    elif dist_type == "triangular":
        left = params.get("left", 0)
        mode = params.get("mode", 0.5)
        right = params.get("right", 1)
        return float(np.random.triangular(left, mode, right))
    else:
        raise ValueError(f"Unknown distribution type: {dist_type}")


async def register_dynamic_model_tools(model: Dict[str, Any]) -> List[Callable]:
    """
    Generate and register all tools (execution + 5 simulation) for a deployed model.
    
    Args:
        model: Model metadata from deployed_models table
        
    Returns:
        List of 6 tool functions (1 execution + 5 simulation)
    """
    model_id = model.get("model_id")
    if not model_id:
        logger.warning("Model missing model_id, skipping tool generation")
        return []
    
    tools = []
    
    try:
        # 1. Execution tool
        execution_tool = generate_execution_tool(model)
        tools.append(execution_tool)
        
        # 2. Simulation tools
        tools.append(generate_single_scenario_tool(model))
        tools.append(generate_multi_scenario_tool(model))
        tools.append(generate_sensitivity_tool(model))
        tools.append(generate_monte_carlo_tool(model))
        tools.append(generate_mesa_tool(model))
        
        logger.info(f"✅ Generated {len(tools)} tools for model {model_id}")
        
    except Exception as e:
        logger.error(f"Error generating tools for model {model_id}: {e}", exc_info=True)
    
    return tools


async def register_all_dynamic_model_tools() -> List[Callable]:
    """
    Register all dynamic tools for all deployed models.
    
    This function:
    1. Fetches all deployed models from database
    2. Generates tools for each model (execution + 5 simulation)
    3. Returns all generated tools
    
    Returns:
        List of all generated tool functions
    """
    try:
        from dcisionai_mcp_server.resources.models import read_model_resource
        
        # Get all deployed models
        models_json = await read_model_resource("dcisionai://models/list", tenant_id=None, is_admin=False)
        models_data = json.loads(models_json)
        models = models_data.get("models", [])
        
        if not models:
            logger.info("No deployed models found, skipping dynamic tool generation")
            return []
        
        logger.info(f"Found {len(models)} deployed models, generating dynamic tools...")
        
        all_tools = []
        for model in models:
            model_tools = await register_dynamic_model_tools(model)
            all_tools.extend(model_tools)
        
        logger.info(f"✅ Generated {len(all_tools)} dynamic tools ({len(models)} models × {len(all_tools) // len(models) if models else 0} tools each)")
        
        return all_tools
        
    except Exception as e:
        logger.error(f"Error registering dynamic model tools: {e}", exc_info=True)
        return []

