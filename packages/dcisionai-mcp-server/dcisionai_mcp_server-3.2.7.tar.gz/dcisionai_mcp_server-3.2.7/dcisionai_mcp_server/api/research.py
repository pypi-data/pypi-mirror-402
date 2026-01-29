"""
Research API Endpoints

Provides endpoints for research and planning assistance:
- Chat interface for research questions
- Plan generation
- Context graph generation
"""

import json
import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Import HITL architecture services (same as hitl_router)
try:
    from dcisionai_workflow.services.vagueness_detector import VaguenessDetector
except ImportError as e:
    logger.warning(f"Failed to import VaguenessDetector: {e}")
    VaguenessDetector = None

try:
    from dcisionai_workflow.services.automated_hitl import AutomatedHITLService
except ImportError as e:
    logger.warning(f"Failed to import AutomatedHITLService: {e}")
    AutomatedHITLService = None

# Import intent discovery tools
try:
    from dcisionai_kb.templates.template_matcher import match_problem_to_template
except ImportError as e:
    logger.warning(f"Failed to import template_matcher: {e}")
    match_problem_to_template = None

try:
    from dcisionai_workflow.tools.intent.classification import ProblemClassifier
except ImportError as e:
    logger.warning(f"Failed to import ProblemClassifier: {e}")
    ProblemClassifier = None

# Create FastAPI router
router = APIRouter(prefix="/api/research", tags=["research"])


# ========== HEALTH CHECK ==========

@router.get("/health")
async def research_health():
    """Health check for research API"""
    return {
        "status": "healthy",
        "endpoints": [
            "/api/research/report",
            "/api/research/chat",
            "/api/research/generate-plan",
            "/api/research/plans"
        ]
    }


# ========== REQUEST/RESPONSE MODELS ==========

class ChatMessage(BaseModel):
    """Chat message"""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ResearchChatRequest(BaseModel):
    """Request for research chat"""
    message: str = Field(..., description="User's question or message")
    conversation_history: Optional[List[ChatMessage]] = Field(default=[], description="Previous conversation messages")
    session_id: Optional[str] = Field(None, description="Research session ID")


class ResearchChatResponse(BaseModel):
    """Response from research chat"""
    response: str = Field(..., description="Assistant's response")
    insights: Optional[List[str]] = Field(default=[], description="Key insights")
    context_graph: Optional[Dict[str, Any]] = Field(None, description="Context graph data")
    planning_state: Optional[Dict[str, Any]] = Field(None, description="Current planning state")
    session_id: str = Field(..., description="Research session ID")


class ResearchReportRequest(BaseModel):
    """Request for research report generation"""
    query: str = Field(..., description="User's research query or problem description")
    session_id: Optional[str] = Field(None, description="Research session ID")


class ResearchReportResponse(BaseModel):
    """Response with research report"""
    report: Dict[str, Any] = Field(..., description="Generated research report")
    session_id: str = Field(..., description="Research session ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "report": {
                    "executive_summary": "...",
                    "problem_analysis": {...},
                    "recommended_approach": {...},
                    "data_requirements": {...},
                    "implementation_steps": [...],
                    "templates": [...],
                    "citations": [...]
                }
            }
        }


class PlanGenerationRequest(BaseModel):
    """Request for plan generation"""
    conversation_id: str = Field(..., description="Research conversation ID")
    refinements: Optional[Dict[str, Any]] = Field(default={}, description="User refinements to plan")


class PlanGenerationResponse(BaseModel):
    """Response with generated plan"""
    plan: Dict[str, Any] = Field(..., description="Generated optimization plan")
    context_graph: Dict[str, Any] = Field(..., description="Context graph snapshot")
    planning_trail: List[Dict[str, Any]] = Field(default=[], description="Planning reasoning trail")


# ========== HELPER FUNCTIONS ==========

async def _generate_contextual_response(
    user_message: str,
    problem_analysis: Dict[str, Any],
    template_matches: List[Dict[str, Any]],
    hitl_questions: List[str],
    vagueness_result: Dict[str, Any],
    message_length: int
) -> str:
    """
    Generate contextual response using HITL architecture.
    
    Uses LLM-generated expert questions (from AutomatedHITLService) and research analysis.
    No keyword matching - pure LLM-based analysis like HITL router.
    """
    response_parts = []
    
    # Use HITL-generated expert questions if available
    if hitl_questions:
        # Acknowledge what we learned from research
        response_parts.append("Thanks for sharing that! I've been analyzing what you described. ")
        
        # Add problem type context if available
        problem_type = problem_analysis.get('problem_type', '')
        domain = problem_analysis.get('domain', '')
        
        if problem_type:
            problem_type_readable = problem_type.replace('_', ' ').title()
            response_parts.append(f"From what I can tell, you're working on a {problem_type_readable.lower()} problem. ")
        elif domain:
            domain_readable = domain.replace('_', ' ').title()
            response_parts.append(f"This looks like a {domain_readable.lower()} challenge. ")
        
        # Add template match context if available
        if template_matches:
            best_match_tuple = template_matches[0]
            # Unpack tuple: (template, score, source, model)
            if isinstance(best_match_tuple, tuple) and len(best_match_tuple) >= 2:
                template_obj, match_score, source, _ = best_match_tuple[:4] if len(best_match_tuple) >= 4 else (*best_match_tuple[:3], None)
                template_name = getattr(template_obj, 'name', '') or getattr(template_obj, 'template_name', '') or str(template_obj)
            else:
                template_obj = best_match_tuple
                match_score = 0.0
                template_name = getattr(template_obj, 'name', '') or getattr(template_obj, 'template_name', '') or str(template_obj)
            
            if match_score > 0.7:
                response_parts.append(f"I found a solution approach called **{template_name}** that looks like a strong fit. ")
            else:
                response_parts.append(f"I found something similar called **{template_name}** that might work, though we may need to adapt it. ")
        
        # Use HITL expert questions
        response_parts.append("\n\nTo help me create a better plan, could you tell me:\n\n")
        for i, q in enumerate(hitl_questions[:3], 1):  # Limit to 3 questions
            response_parts.append(f"{i}. {q}\n")
        response_parts.append("\nFeel free to answer in your own words - no need to be technical!")
        
        return ''.join(response_parts)
    
    # If we have problem analysis but no HITL questions, use analysis-based response
    elif problem_analysis.get('problem_type') or problem_analysis.get('domain'):
        problem_type = problem_analysis.get('problem_type', '')
        domain = problem_analysis.get('domain', '')
        
        # Acknowledge what we learned
        response_parts.append("Thanks for sharing that! I've been analyzing what you described. ")
        
        # Add domain-specific context
        if domain:
            domain_readable = domain.replace('_', ' ').title()
            response_parts.append(f"This looks like a {domain_readable.lower()} challenge. ")
        
        # Add problem type context
        if problem_type:
            problem_type_readable = problem_type.replace('_', ' ').title()
            response_parts.append(f"From what I can tell, you're working on a {problem_type_readable.lower()} problem. ")
        
        # Add template match context if available
        if template_matches:
            best_match_tuple = template_matches[0]
            # Unpack tuple: (template, score, source, model)
            if isinstance(best_match_tuple, tuple) and len(best_match_tuple) >= 2:
                template_obj, match_score, source, _ = best_match_tuple[:4] if len(best_match_tuple) >= 4 else (*best_match_tuple[:3], None)
                template_name = getattr(template_obj, 'name', '') or getattr(template_obj, 'template_name', '') or str(template_obj)
            else:
                template_obj = best_match_tuple
                match_score = 0.0
                template_name = getattr(template_obj, 'name', '') or getattr(template_obj, 'template_name', '') or str(template_obj)
            
            if match_score > 0.7:
                response_parts.append(f"I found a solution approach called **{template_name}** that looks like a strong fit. ")
            else:
                response_parts.append(f"I found something similar called **{template_name}** that might work, though we may need to adapt it. ")
        
        # Ask for more information based on analysis
        response_parts.append("\n\nTo help me create a better plan, could you provide more details about your specific situation? ")
        response_parts.append("For example, what are your main goals, what constraints do you have, and what options are you considering?")
        
        return ''.join(response_parts)
    
    # Fallback: If no HITL questions and no analysis, ask for more information
    else:
        if message_length < 30:
            return ("I'd love to help! Could you tell me a bit more about what you're trying to accomplish? "
                    "Just describe your problem in your own words, and I'll help you plan it out.")
        else:
            return ("Thanks for sharing that! I'm working on understanding your situation better. "
                    "Could you provide a bit more detail about what you're trying to achieve? "
                    "The more context you give me, the better I can help you create a plan.")


# ========== RESEARCH REPORT GENERATION ==========

async def _generate_research_report_with_claude(
    query: str,
    problem_analysis: Dict[str, Any],
    classification_result: Optional[Dict[str, Any]],
    vagueness_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate comprehensive PhD-level domain research report using Claude SDK.
    
    Uses Claude to generate deep, domain-expert level research content.
    """
    logger.info(f"[Research] ===== _generate_research_report_with_claude CALLED =====")
    logger.info(f"[Research] Query: {query[:100]}")
    logger.info(f"[Research] Problem analysis keys: {list(problem_analysis.keys())}")
    
    try:
        import os
        import json
        
        logger.info("[Research] Step 1: Checking ANTHROPIC_API_KEY...")
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key and ',' in api_key:
            # Handle comma-separated keys - use first one
            api_key = api_key.split(',')[0].strip()
            logger.info(f"[Research] Multiple API keys found, using first one")
        
        logger.info(f"[Research] ANTHROPIC_API_KEY status: {'✅ SET' if api_key else '❌ NOT SET'}")
        if api_key:
            logger.info(f"[Research] API key preview: {api_key[:20]}... (length: {len(api_key)} chars)")
        
        if not api_key:
            error_msg = "ANTHROPIC_API_KEY not set. First-principles research requires Claude SDK. Please set ANTHROPIC_API_KEY environment variable."
            logger.error(f"[Research] ❌ {error_msg}")
            raise ValueError(error_msg)
        
        logger.info("[Research] Step 2: Importing Anthropic SDK...")
        try:
            from anthropic import Anthropic
            logger.info("[Research] ✅ Anthropic SDK imported successfully")
        except ImportError as import_err:
            error_msg = f"Failed to import Anthropic SDK: {import_err}. Install with: pip install anthropic"
            logger.error(f"[Research] ❌ {error_msg}")
            raise ImportError(error_msg) from import_err
        
        logger.info("[Research] Step 3: Initializing Anthropic client...")
        try:
            client = Anthropic(api_key=api_key)
            logger.info("[Research] ✅ Anthropic client initialized successfully")
        except Exception as client_err:
            error_msg = f"Failed to initialize Anthropic client: {client_err}"
            logger.error(f"[Research] ❌ {error_msg}", exc_info=True)
            raise RuntimeError(error_msg) from client_err
        
        model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
        logger.info(f"[Research] Step 4: Using Claude model: {model}")
        logger.info(f"[Research] Step 5: Building research prompt (first-principles, SME whiteboarding style)...")
        
        problem_type = problem_analysis.get('problem_type', '')
        domain = problem_analysis.get('domain', '')
        complexity = problem_analysis.get('complexity', '')
        optimization_type = problem_analysis.get('optimization_type', '')
        
        # Build comprehensive research prompt - SME whiteboarding session style
        domain_context = domain if domain else 'operations research'
        problem_context = f"{problem_type} in {domain_context}" if problem_type and domain else (problem_type or domain_context or 'optimization')
        
        research_prompt = f"""You are a senior optimization consultant (PhD-level) having a whiteboarding session with stakeholders. Your role is to help them understand their optimization problem from first principles.

**Your Approach:**
- Think like an SME explaining to business stakeholders
- Use business-friendly language with technical depth
- Show your reasoning trail (like drawing on a whiteboard)
- Use domain knowledge to illuminate mathematical structure
- Reference similar structures for context (not for matching)
- Build understanding from first principles

**Problem Query:** {query}

**Problem Classification (for context):**
- Problem Type: {problem_type if problem_type else 'Analyze from query'}
- Domain: {domain if domain else 'Infer from query'}
- Complexity: {complexity if complexity else 'Assess from query'}
- Optimization Type: {optimization_type if optimization_type else 'Determine from query'}

**Your Expertise:**
You understand:
- Mathematical optimization theory (LP, QP, MILP, NLP, etc.)
- How to explain technical concepts in business terms
- Domain knowledge that helps illuminate structure
- Similar problem structures for reference
- Common pitfalls and considerations

**Your Task:**
Generate a research report like you're whiteboarding with stakeholders. Show your reasoning trail and build understanding from first principles.

1. **Executive Summary** (2-3 paragraphs, business-friendly):
   - What problem are we solving? (In business terms)
   - Why is optimization valuable here?
   - High-level approach (what we'll do, why it works)

2. **Problem Decomposition** (first principles, show reasoning):
   - **Decision Variables**: What choices are being made? (Explain in business terms, then technical)
   - **Constraints**: What limits solutions? (Business rules → mathematical form)
   - **Objectives**: What are we optimizing? (Business goals → mathematical function)
   - **Mathematical Structure**: What type of problem is this? (LP/QP/MILP/etc. and WHY)
   - **Reasoning Trail**: Show how you arrived at this understanding

3. **Mathematical Analysis** (technical depth, business context):
   - Variable types and structure (continuous/integer/binary - why?)
   - Constraint forms (linear/nonlinear - what makes them so?)
   - Objective function form (linear/quadratic/nonlinear - why?)
   - Problem classification (based on structure, not domain)
   - Domain knowledge that illuminates structure (e.g., "Color matching uses CIE Lab → nonlinear constraints")

4. **Approach Derivation** (show reasoning):
   - **Why this problem type?** (Based on mathematical structure, show reasoning)
   - **Why these algorithms?** (Based on problem properties, explain trade-offs)
   - **Why these solvers?** (Based on characteristics, explain selection)
   - **Alternatives considered**: What other approaches? Why not those?
   - **Trade-offs**: Speed vs. accuracy, exact vs. heuristic, etc.

5. **Similar Structures** (reference, not matching):
   - What other problems have similar mathematical structure?
   - How are they similar? (Mathematical properties)
   - How are they different? (Key distinctions)
   - What can we learn from those? (Insights, not templates)

6. **Data Requirements** (derived from structure):
   - Decision variables needed (what values?)
   - Parameters required (what data?)
   - Constraints to specify (what limits?)
   - Objectives to define (what metrics?)
   - Data quality considerations

7. **Implementation Considerations**:
   - Computational complexity (what to expect)
   - Scalability (how it scales)
   - Common pitfalls (what to watch for)
   - Success factors (what makes this work)

**Requirements:**
- **Style**: Like an SME whiteboarding session - conversational, educational, transparent
- **Language**: Business-friendly with technical depth (explain technical terms)
- **Reasoning**: Show your thought process (like drawing on a whiteboard)
- **Domain Knowledge**: Use domain context to illuminate mathematical structure
- **First Principles**: Build understanding from fundamentals, not templates
- **Reference Similar Structures**: Mention similar problems for context, not matching
- **Be Specific**: Use the actual problem details, not generic statements

**Output Format:**
CRITICAL: You MUST return ONLY valid JSON. Do not include any markdown code blocks, explanations, or text outside the JSON object.

Return a JSON object with the following EXACT structure:
{{
  "executive_summary": "Business-friendly executive summary (2-3 paragraphs) explaining the problem and approach in stakeholder language",
  "problem_decomposition": {{
    "decision_variables": "What decisions are being made? Explain in business terms, then technical structure",
    "constraints": "What limits solutions? Business rules → mathematical forms",
    "objectives": "What are we optimizing? Business goals → mathematical functions",
    "mathematical_structure": "Problem type (LP/QP/MILP/etc.) and WHY - show reasoning",
    "reasoning_trail": "Step-by-step reasoning: how you decomposed the problem and arrived at this understanding"
  }},
  "mathematical_analysis": {{
    "variable_types": "Variable types (continuous/integer/binary) and structure - explain why",
    "constraint_forms": "Constraint forms (linear/nonlinear) - what makes them so?",
    "objective_form": "Objective function form (linear/quadratic/nonlinear) - why?",
    "problem_classification": "Problem classification based on mathematical structure",
    "domain_insights": "Domain knowledge that illuminates structure (e.g., 'Color matching uses CIE Lab → nonlinear constraints')"
  }},
  "approach_derivation": {{
    "problem_type_rationale": "Why this problem type? Show mathematical reasoning",
    "algorithm_selection": "Why these algorithms? Based on problem properties, explain trade-offs",
    "solver_selection": "Why these solvers? Based on characteristics, explain selection",
    "alternatives_considered": "What other approaches were considered? Why not those?",
    "trade_offs": "Speed vs accuracy, exact vs heuristic, etc."
  }},
  "similar_structures": [
    {{
      "problem_name": "Name of similar problem",
      "similarity": "How is it similar? (Mathematical properties)",
      "differences": "How is it different? (Key distinctions)",
      "insights": "What can we learn from this? (Not templates, but insights)"
    }}
  ],
  "data_requirements": {{
    "decision_variables": "Decision variables needed - what values?",
    "parameters": "Parameters required - what data?",
    "constraints": "Constraints to specify - what limits?",
    "objectives": "Objectives to define - what metrics?",
    "data_quality": "Data quality considerations"
  }},
  "implementation_considerations": {{
    "computational_complexity": "What to expect computationally",
    "scalability": "How it scales",
    "common_pitfalls": "What to watch for",
    "success_factors": "What makes this work"
  }},
  "implementation_steps": [
    {{"step": 1, "title": "Step 1 title", "description": "Detailed description with reasoning"}},
    {{"step": 2, "title": "Step 2 title", "description": "Detailed description with reasoning"}},
    {{"step": 3, "title": "Step 3 title", "description": "Detailed description with reasoning"}},
    {{"step": 4, "title": "Step 4 title", "description": "Detailed description with reasoning"}},
    {{"step": 5, "title": "Step 5 title", "description": "Detailed description with reasoning"}}
  ]
}}

IMPORTANT: 
- Write like an SME whiteboarding session - conversational, educational, transparent
- Show reasoning trail (how you think through the problem)
- Use business-friendly language with technical depth
- Use domain knowledge to illuminate mathematical structure
- Reference similar structures for context (not matching)
- Be specific to the problem: "{query}"
- Return ONLY the JSON object, no other text

Generate the research report now as valid JSON only."""
        
        logger.info("[Research] Step 6: Calling Claude API for PhD-level research report generation...")
        logger.info(f"[Research] Model: {model}, Query: {query[:100]}...")
        logger.info(f"[Research] Prompt length: {len(research_prompt)} characters")
        
        try:
            # Use system message to enforce JSON output
            system_message = """You are a PhD-level optimization research expert. You MUST respond with valid JSON only. 
Do not include markdown code blocks, explanations, or any text outside the JSON object. 
Your response should be a valid JSON object that can be parsed directly."""
            
            logger.info("[Research] Making Claude API call...")
            message = client.messages.create(
                model=model,
                max_tokens=8000,
                temperature=0.3,  # Lower temperature for more focused, technical content
                system=system_message,
                messages=[
                    {
                        "role": "user",
                        "content": research_prompt
                    }
                ]
            )
            
            logger.info(f"[Research] ✅ Claude API call successful!")
            logger.info(f"[Research] Response type: {type(message)}")
            logger.info(f"[Research] Response has content: {hasattr(message, 'content')}")
        except Exception as api_error:
            error_msg = f"Claude API call failed: {api_error}"
            logger.error(f"[Research] ❌ {error_msg}", exc_info=True)
            logger.error(f"[Research] Error type: {type(api_error).__name__}")
            logger.error(f"[Research] Error message: {str(api_error)}")
            raise RuntimeError(error_msg) from api_error
        
        # Extract response
        response_text = ""
        if hasattr(message, 'content') and message.content:
            for content_block in message.content:
                if hasattr(content_block, 'text'):
                    response_text += content_block.text
                elif isinstance(content_block, dict) and 'text' in content_block:
                    response_text += content_block['text']
        
        logger.info(f"[Research] Claude response length: {len(response_text)} characters")
        logger.debug(f"[Research] Claude response preview: {response_text[:300]}...")
        
        if not response_text:
            logger.warning("[Research] Empty response from Claude, falling back to basic report")
            return await _generate_basic_research_report(query, problem_analysis, classification_result, vagueness_result)
        
        # Parse JSON response - be more flexible with format
        claude_report = None
        try:
            # Try direct JSON parse first
            try:
                claude_report = json.loads(response_text)
                logger.info("[Research] Successfully parsed Claude response as direct JSON")
            except json.JSONDecodeError:
                # Try extracting JSON from markdown code blocks
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    claude_report = json.loads(json_str)
                    logger.info("[Research] Successfully parsed Claude response by extracting JSON from text")
                else:
                    raise ValueError("No JSON found in response")
        except (json.JSONDecodeError, ValueError) as e:
            error_msg = f"Failed to parse Claude response as JSON: {e}. Response preview: {response_text[:500]}"
            logger.error(f"[Research] ❌ {error_msg}")
            logger.error(f"[Research] Full response text (first 1000 chars): {response_text[:1000]}")
            raise ValueError(error_msg) from e
        
        # Build report structure (first principles - SME whiteboarding style)
        report = {
            "executive_summary": claude_report.get("executive_summary", ""),
            "problem_analysis": {
                **problem_analysis,
                **claude_report.get("problem_decomposition", {}),
                **claude_report.get("mathematical_analysis", {})
            },
            "recommended_approach": {
                "description": _format_approach_from_claude_first_principles(claude_report.get("approach_derivation", {})),
                "solver_strategy": "hybrid",
                "primary_solver": "mathematical",
                "secondary_solver": "dame"
            },
            "data_requirements": {
                "description": _format_data_requirements_from_claude(claude_report.get("data_requirements", {})),
                **claude_report.get("data_requirements", {})
            },
            "similar_structures": claude_report.get("similar_structures", []),
            "implementation_considerations": claude_report.get("implementation_considerations", {}),
            "implementation_steps": claude_report.get("implementation_steps", []),
            "reasoning_trail": claude_report.get("problem_decomposition", {}).get("reasoning_trail", ""),
            "templates": [],
            "citations": [],
            "confidence_score": _calculate_confidence_from_analysis(problem_analysis)
        }
        
        logger.info("[Research] Successfully generated PhD-level research report using Claude SDK")
        return report
        
    except Exception as e:
        logger.error(f"[Research] Claude SDK research generation failed: {e}", exc_info=True)
        # Re-raise the exception instead of falling back
        raise


def _format_approach_from_claude_first_principles(approach_dict: Dict[str, Any]) -> str:
    """Format Claude's approach derivation (first principles) into markdown."""
    parts = []
    parts.append("## Recommended Approach\n\n")
    
    if approach_dict.get("problem_type_rationale"):
        parts.append(f"**Why This Problem Type?**\n{approach_dict['problem_type_rationale']}\n\n")
    
    if approach_dict.get("algorithm_selection"):
        parts.append(f"**Algorithm Selection:**\n{approach_dict['algorithm_selection']}\n\n")
    
    if approach_dict.get("solver_selection"):
        parts.append(f"**Solver Selection:**\n{approach_dict['solver_selection']}\n\n")
    
    if approach_dict.get("alternatives_considered"):
        parts.append(f"**Alternatives Considered:**\n{approach_dict['alternatives_considered']}\n\n")
    
    if approach_dict.get("trade_offs"):
        parts.append(f"**Trade-offs:**\n{approach_dict['trade_offs']}\n\n")
    
    parts.append(
        "**Solver Implementation:**\n"
        "We recommend using a hybrid approach:\n"
        "- Mathematical solver (SCIP/HiGHS) for fast, optimal solutions\n"
        "- DAME solver for domain-specific optimization and business rule validation\n"
        "- Both solvers run in parallel for comprehensive results\n\n"
    )
    
    return ''.join(parts)


def _format_data_requirements_from_claude(data_dict: Dict[str, Any]) -> str:
    """Format Claude's data requirements into markdown."""
    parts = []
    parts.append("## Data Requirements\n\n")
    parts.append("To successfully implement this optimization, you'll need:\n\n")
    
    if data_dict.get("decision_variables"):
        parts.append(f"**Decision Variables:**\n{data_dict['decision_variables']}\n\n")
    
    if data_dict.get("parameters"):
        parts.append(f"**Parameters:**\n{data_dict['parameters']}\n\n")
    
    if data_dict.get("constraints"):
        parts.append(f"**Constraints:**\n{data_dict['constraints']}\n\n")
    
    if data_dict.get("objectives"):
        parts.append(f"**Objectives:**\n{data_dict['objectives']}\n\n")
    
    if data_dict.get("data_quality"):
        parts.append(f"**Data Quality Considerations:**\n{data_dict['data_quality']}\n\n")
    
    return ''.join(parts)


def _calculate_confidence_from_analysis(problem_analysis: Dict[str, Any]) -> float:
    """Calculate confidence score based on problem analysis."""
    confidence = 0.5
    if problem_analysis.get('problem_type'):
        confidence += 0.3
    if problem_analysis.get('domain'):
        confidence += 0.1
    if problem_analysis.get('complexity'):
        confidence += 0.1
    return min(confidence, 1.0)


async def _generate_basic_research_report(
    query: str,
    problem_analysis: Dict[str, Any],
    classification_result: Optional[Dict[str, Any]],
    vagueness_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate basic research report using intent discovery tools (first-principles fallback).
    
    Uses EntityExtractor, ObjectiveExtractor, ConstraintExtractor to build understanding
    from first principles, even when Claude SDK is unavailable.
    
    Returns a structured report with:
    - Executive summary (business terms)
    - Problem decomposition (first principles)
    - Mathematical analysis
    - Recommended approach
    - Data requirements
    - Implementation steps
    """
    logger.info("[Research] Generating basic research report using intent discovery tools (first-principles)")
    report = {
        "executive_summary": "",
        "problem_analysis": {},
        "recommended_approach": {},
        "data_requirements": {},
        "implementation_steps": [],
        "templates": [],
        "citations": [],
        "confidence_score": 0.0
    }
    
    # Executive Summary - Business-focused explanation
    problem_type = problem_analysis.get('problem_type', '')
    domain = problem_analysis.get('domain', '')
    complexity = problem_analysis.get('complexity', '')
    
    executive_summary_parts = []
    executive_summary_parts.append(f"## Executive Summary\n\n")
    
    if problem_type:
        problem_type_readable = problem_type.replace('_', ' ').title()
        executive_summary_parts.append(
            f"Based on your query, this appears to be a **{problem_type_readable}** optimization challenge. "
        )
    else:
        executive_summary_parts.append(
            "Based on your query, this appears to be an optimization challenge. "
        )
    
    if domain:
        domain_readable = domain.replace('_', ' ').title()
        executive_summary_parts.append(
            f"This falls within the **{domain_readable}** domain, where optimization can deliver significant business value. "
        )
    
    # Note about solving
    executive_summary_parts.append(
        "When you proceed to solve this problem, our system will automatically analyze your requirements "
        "and select the best optimization approach for your specific needs. "
    )
    
    executive_summary_parts.append(
        "This report outlines the recommended approach, data requirements, and implementation steps "
        "to successfully optimize your problem.\n\n"
    )
    
    # Problem Analysis
    report["problem_analysis"] = {
        "problem_type": problem_type,
        "domain": domain,
        "complexity": complexity,
        "optimization_type": problem_analysis.get('optimization_type', ''),
        "temporal_characteristics": problem_analysis.get('temporal_characteristics', {}),
        "characteristics": problem_analysis.get('characteristics', {}),
        "mathematical_structure": problem_analysis.get('mathematical_structure', {})
    }
    
    # Recommended Approach
    approach_parts = []
    approach_parts.append("## Recommended Approach\n\n")
    
    # Focus on general optimization approach, not template-specific
    # Template matching will be handled by the solve workflow with full context
    approach_parts.append("**Optimization Strategy:**\n")
    
    # Add optimization approach based on problem type
    if problem_type:
        if 'portfolio' in problem_type.lower():
            approach_parts.append(
                "Portfolio optimization typically involves:\n"
                "- Asset allocation decisions across multiple investment options\n"
                "- Risk-return tradeoff analysis\n"
                "- Constraint handling (budget, regulatory, diversification)\n"
                "- Multi-objective optimization (maximize returns, minimize risk)\n\n"
            )
        elif 'scheduling' in problem_type.lower():
            approach_parts.append(
                "Scheduling optimization typically involves:\n"
                "- Time-based resource allocation\n"
                "- Constraint satisfaction (availability, capacity, preferences)\n"
                "- Multi-period planning\n"
                "- Fairness and efficiency balancing\n\n"
            )
        elif 'routing' in problem_type.lower() or 'vehicle' in problem_type.lower():
            approach_parts.append(
                "Routing optimization typically involves:\n"
                "- Path finding and sequence optimization\n"
                "- Distance/time minimization\n"
                "- Capacity constraints\n"
                "- Time window constraints\n\n"
            )
        elif 'inventory' in problem_type.lower() or 'supply' in problem_type.lower():
            approach_parts.append(
                "Supply chain optimization typically involves:\n"
                "- Inventory level decisions\n"
                "- Order quantity optimization\n"
                "- Multi-echelon coordination\n"
                "- Demand forecasting integration\n\n"
            )
        elif 'pricing' in problem_type.lower():
            approach_parts.append(
                "Pricing optimization typically involves:\n"
                "- Price point decisions across products/markets\n"
                "- Demand elasticity modeling\n"
                "- Competitive positioning\n"
                "- Revenue/profit maximization\n\n"
            )
        else:
            approach_parts.append(
                "Based on the problem type, we'll use an optimization approach that:\n"
                "- Identifies decision variables (what you're optimizing)\n"
                "- Defines objective functions (what you're maximizing/minimizing)\n"
                "- Incorporates constraints (limits and restrictions)\n"
                "- Uses appropriate optimization techniques for your domain\n\n"
            )
    else:
        approach_parts.append(
            "We'll use a systematic optimization approach that:\n"
            "- Identifies decision variables (what you're optimizing)\n"
            "- Defines objective functions (what you're maximizing/minimizing)\n"
            "- Incorporates constraints (limits and restrictions)\n"
            "- Selects appropriate optimization techniques based on problem characteristics\n\n"
        )
    
    # Add optimization approach based on problem type
    if problem_type:
        if 'portfolio' in problem_type.lower():
            approach_parts.append(
                "**Optimization Strategy:** Portfolio optimization typically involves:\n"
                "- Asset allocation decisions across multiple investment options\n"
                "- Risk-return tradeoff analysis\n"
                "- Constraint handling (budget, regulatory, diversification)\n"
                "- Multi-objective optimization (maximize returns, minimize risk)\n\n"
            )
        elif 'scheduling' in problem_type.lower():
            approach_parts.append(
                "**Optimization Strategy:** Scheduling optimization typically involves:\n"
                "- Time-based resource allocation\n"
                "- Constraint satisfaction (availability, capacity, preferences)\n"
                "- Multi-period planning\n"
                "- Fairness and efficiency balancing\n\n"
            )
        elif 'routing' in problem_type.lower():
            approach_parts.append(
                "**Optimization Strategy:** Routing optimization typically involves:\n"
                "- Path finding and sequence optimization\n"
                "- Distance/time minimization\n"
                "- Capacity constraints\n"
                "- Time window constraints\n\n"
            )
    
    approach_parts.append(
        "**Solver Strategy:**\n"
        "We recommend using a hybrid approach:\n"
        "- Mathematical solver (SCIP/HiGHS) for fast, optimal solutions\n"
        "- DAME solver for domain-specific optimization and business rule validation\n"
        "- Both solvers run in parallel for comprehensive results\n\n"
    )
    
    report["recommended_approach"] = {
        "description": ''.join(approach_parts),
        "solver_strategy": "hybrid",
        "primary_solver": "mathematical",
        "secondary_solver": "dame"
    }
    
    # Data Requirements
    data_requirements_parts = []
    data_requirements_parts.append("## Data Requirements\n\n")
    data_requirements_parts.append("To successfully implement this optimization, you'll need:\n\n")
    
    math_structure = problem_analysis.get('mathematical_structure', {})
    objectives = math_structure.get('objectives', [])
    constraint_types = math_structure.get('constraint_types', [])
    
    if objectives:
        data_requirements_parts.append("**Objective Data:**\n")
        for obj in objectives[:3]:
            data_requirements_parts.append(f"- {obj}\n")
        data_requirements_parts.append("\n")
    
    if constraint_types:
        data_requirements_parts.append("**Constraint Data:**\n")
        for constraint in constraint_types[:5]:
            constraint_readable = constraint.replace('_', ' ').title()
            data_requirements_parts.append(f"- {constraint_readable} values and limits\n")
        data_requirements_parts.append("\n")
    
    data_requirements_parts.append(
        "**General Requirements:**\n"
        "- Decision variables: What you're optimizing (e.g., allocation amounts, assignments)\n"
        "- Parameters: Input data needed (e.g., costs, capacities, preferences)\n"
        "- Constraints: Limits and restrictions (e.g., budgets, time windows, capacity)\n"
        "- Objective function: What you're trying to maximize or minimize\n\n"
    )
    
    report["data_requirements"] = {
        "description": ''.join(data_requirements_parts),
        "objectives": objectives,
        "constraints": constraint_types,
        "parameters_needed": []
    }
    
    # Implementation Steps
    implementation_steps = [
        {
            "step": 1,
            "title": "Problem Definition",
            "description": "Clearly define your optimization objectives, decision variables, and constraints in business terms."
        },
        {
            "step": 2,
            "title": "Data Preparation",
            "description": "Gather and prepare the required data: decision variables, parameters, constraints, and objective metrics."
        },
        {
            "step": 3,
            "title": "Model Generation",
            "description": "Generate the optimization model using the recommended template and your specific data."
        },
        {
            "step": 4,
            "title": "Solver Execution",
            "description": "Execute both mathematical and DAME solvers to find optimal solutions."
        },
        {
            "step": 5,
            "title": "Solution Analysis",
            "description": "Analyze the results, validate against business rules, and interpret the solution."
        }
    ]
    
    report["implementation_steps"] = implementation_steps
    
    # Citations - removed template citations since we're not matching templates in research phase
    # Template matching will happen in solve workflow
    citations = []
    report["citations"] = citations
    
    # Confidence Score - based on problem understanding, not template matching
    confidence = 0.5
    if problem_type:
        confidence += 0.3  # Problem type identified
    if domain:
        confidence += 0.1  # Domain identified
    if complexity:
        confidence += 0.1  # Complexity assessed
    report["confidence_score"] = min(confidence, 1.0)
    
    # Complete Executive Summary
    report["executive_summary"] = ''.join(executive_summary_parts)
    
    return report


# ========== RESEARCH REPORT ENDPOINT ==========

@router.post("/report", response_model=ResearchReportResponse, name="generate_research_report")
async def generate_research_report(request: ResearchReportRequest):
    """
    Generate first-principles research report using Claude SDK.
    
    This endpoint requires ANTHROPIC_API_KEY to be set. It will fail with a clear error
    message if Claude SDK is unavailable, rather than falling back to generic reports.
    
    Returns a structured research report with:
    - Executive summary in business terms
    - Problem decomposition (first principles)
    - Mathematical analysis
    - Recommended approach
    - Data requirements
    - Implementation steps
    """
    try:
        session_id = request.session_id or f"research_{uuid.uuid4().hex[:12]}"
        
        logger.info(f"[Research] Report generation request: {request.query[:100]}...")
        logger.info(f"[Research] Session ID: {session_id}")
        
        # RESEARCH PHASE: Deep analysis
        classification_result = None
        template_matches = []
        problem_analysis = {}
        
        # Step 1: Detect vagueness
        vagueness_result = {}
        if VaguenessDetector is not None:
            try:
                logger.info("[Research] Detecting vagueness...")
                detector = VaguenessDetector()
                result = detector.detect_vagueness(request.query)
                if isinstance(result, dict):
                    vagueness_result = result
            except Exception as e:
                logger.error(f"[Research] Vagueness detection failed: {e}", exc_info=True)
        
        # Step 2: Classify the problem
        try:
            if ProblemClassifier is not None:
                logger.info("[Research] Running problem classification...")
                classifier = ProblemClassifier()
                classification_result = await classifier.classify(request.query)
                
                if classification_result and classification_result.get('result'):
                    result = classification_result['result']
                    problem_analysis = {
                        "problem_type": result.get('problem_type', ''),
                        "problem_subtype": result.get('problem_subtype'),
                        "domain": result.get('domain', ''),
                        "complexity": result.get('complexity'),
                        "optimization_type": result.get('optimization_type'),
                        "temporal_characteristics": result.get('temporal_characteristics', {}),
                        "characteristics": result.get('characteristics', {}),
                        "mathematical_structure": result.get('mathematical_structure', {}),
                        "reasoning": classification_result.get('reasoning', {})
                    }
        except Exception as e:
            logger.error(f"[Research] Classification failed: {e}", exc_info=True)
        
        # Step 3: Skip template matching - let solve workflow handle it
        # Template matching will be done by knowledgebase_research node in the solve workflow
        # with full context and better accuracy
        template_matches = []
        
        # Step 4: Generate research report using Claude SDK for PhD-level domain research
        logger.info("[Research] ===== STEP 4: Generating research report with Claude SDK =====")
        logger.info(f"[Research] Calling _generate_research_report_with_claude...")
        logger.info(f"[Research] Problem analysis: {problem_analysis}")
        
        report = await _generate_research_report_with_claude(
            query=request.query,
            problem_analysis=problem_analysis,
            classification_result=classification_result,
            vagueness_result=vagueness_result
        )
        
        logger.info(f"[Research] Report generated. Executive summary length: {len(report.get('executive_summary', ''))}")
        logger.info(f"[Research] Report keys: {list(report.keys())}")
        
        return ResearchReportResponse(
            report=report,
            session_id=session_id
        )
        
    except Exception as e:
        logger.error(f"[Research] Report generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Research report generation failed: {str(e)}")


# ========== RESEARCH CHAT ENDPOINT (DEPRECATED - Keep for backward compat) ==========

@router.post("/chat", response_model=ResearchChatResponse)
async def research_chat(request: ResearchChatRequest):
    """
    Research chat endpoint - conversational planning assistance.
    
    Processes user questions and provides:
    - Helpful responses about optimization problems
    - Template recommendations
    - Problem analysis
    - Planning guidance
    """
    try:
        session_id = request.session_id or f"research_{uuid.uuid4().hex[:12]}"
        
        logger.info(f"[Research] Chat request: {request.message[:100]}...")
        logger.info(f"[Research] Session ID: {session_id}")
        logger.info(f"[Research] Conversation history length: {len(request.conversation_history or [])}")
        
        # Build accumulated context from conversation history
        conversation_history = request.conversation_history or []
        accumulated_context = []
        previous_questions = []
        
        # Extract accumulated information from conversation history
        for msg in conversation_history:
            if msg.role == 'user':
                accumulated_context.append(msg.content)
            elif msg.role == 'assistant':
                # Check if assistant asked questions (look for numbered questions)
                if any(char.isdigit() for char in msg.content[:50]):
                    # Extract questions from assistant message
                    lines = msg.content.split('\n')
                    for line in lines:
                        if line.strip() and (line.strip()[0].isdigit() or '?' in line):
                            previous_questions.append(line.strip())
        
        # Build full problem description from accumulated context + current message
        full_problem_description = ' '.join(accumulated_context + [request.message]).strip()
        
        # Detect if user is answering previous questions (short message after questions were asked)
        is_followup_answer = (
            len(previous_questions) > 0 and 
            message_length < 100 and 
            not any(q_word in message_lower for q_word in ['what', 'how', 'why', 'when', 'where', 'who', '?'])
        )
        
        # Step 1: Research Phase - Deep analysis before generating questions
        # Use natural language and avoid technical jargon
        response_text = ""
        insights = []
        planning_state = {
            "session_id": session_id,
            "problem_description": full_problem_description if full_problem_description else request.message,
            "complete": False,
            "conversation_context": accumulated_context
        }
        
        # Check if message contains optimization problem description
        message_lower = request.message.lower()
        message_length = len(request.message.strip())
        
        # Detect greeting or casual questions
        greetings = ["hi", "hello", "hey", "help", "what can you do"]
        is_greeting = any(greet in message_lower for greet in greetings) and message_length < 50
        
        if is_greeting:
            response_text = "Hi! I'm here to help you figure out the best way to solve your problem. "
            response_text += "Whether you're trying to optimize your portfolio, schedule resources, allocate budgets, or anything else - "
            response_text += "just tell me what you're working on and I'll help you plan it out. What's on your mind?"
        else:
            # RESEARCH PHASE: Use HITL architecture (same as hitl_router)
            classification_result = None
            template_matches = []
            problem_analysis = {}
            hitl_questions = []
            
            # Step 1: Detect vagueness (same as HITL router)
            # Use full accumulated context for analysis, not just current message
            analysis_text = full_problem_description if full_problem_description else request.message
            
            vagueness_result = {}
            if VaguenessDetector is not None:
                try:
                    logger.info(f"[Research] Detecting vagueness in problem description (using {'accumulated context' if full_problem_description else 'current message'})...")
                    detector = VaguenessDetector()
                    result = detector.detect_vagueness(analysis_text)
                    # Ensure result is a dict
                    if isinstance(result, dict):
                        vagueness_result = result
                    else:
                        logger.warning(f"[Research] Vagueness detector returned non-dict: {type(result)}")
                        vagueness_result = {}
                    
                    vagueness_score = vagueness_result.get('vagueness_score', 0.0) if vagueness_result else 0.0
                    needs_clarification = vagueness_result.get('needs_clarification', False) if vagueness_result else False
                    logger.info(f"[Research] Vagueness score: {vagueness_score:.2f}, Needs clarification: {needs_clarification}")
                    planning_state['vagueness_score'] = vagueness_score
                except Exception as e:
                    logger.error(f"[Research] Vagueness detection failed: {e}", exc_info=True)
                    vagueness_result = {}
            
            # Step 2: Classify the problem to understand its structure
            # Use accumulated context for classification
            try:
                if ProblemClassifier is not None:
                    logger.info(f"[Research] Running problem classification (using {'accumulated context' if full_problem_description else 'current message'})...")
                    classifier = ProblemClassifier()
                    classification_result = await classifier.classify(analysis_text)
                    
                    if classification_result and classification_result.get('result'):
                        result = classification_result['result']
                        problem_analysis = {
                            "problem_type": result.get('problem_type', ''),
                            "problem_subtype": result.get('problem_subtype'),
                            "domain": result.get('domain', ''),
                            "complexity": result.get('complexity'),
                            "optimization_type": result.get('optimization_type'),
                            "temporal_characteristics": result.get('temporal_characteristics', {}),
                            "characteristics": result.get('characteristics', {}),
                            "mathematical_structure": result.get('mathematical_structure', {}),
                            "reasoning": classification_result.get('reasoning', {})
                        }
                        planning_state.update(problem_analysis)
                        insights.append(f"Problem type: {problem_analysis.get('problem_type', 'unknown')}")
            except Exception as e:
                logger.error(f"[Research] Classification failed: {e}", exc_info=True)
            
            # Step 3: Match to templates using classification if available
            # Use accumulated context for template matching
            try:
                if match_problem_to_template is not None:
                    logger.info("[Research] Matching to templates...")
                    matches = match_problem_to_template(
                        problem_description=analysis_text,
                        classification=classification_result,
                        use_semantic=True,
                        semantic_weight=0.7,
                        include_models=True
                    )
                    # match_problem_to_template returns List[Tuple[template, score, source, model]]
                    template_matches = matches or []
                    
                    if template_matches:
                        # Unpack tuple: (template, score, source, model)
                        best_match_tuple = template_matches[0]
                        if isinstance(best_match_tuple, tuple) and len(best_match_tuple) >= 2:
                            template_obj, match_score, source, _ = best_match_tuple[:4] if len(best_match_tuple) >= 4 else (*best_match_tuple[:3], None)
                            # Extract template name from template object
                            template_name = getattr(template_obj, 'name', '') or getattr(template_obj, 'template_name', '') or str(template_obj)
                        else:
                            # Fallback if structure is different
                            template_obj = best_match_tuple
                            match_score = 0.0
                            source = 'unknown'
                            template_name = getattr(template_obj, 'name', '') or getattr(template_obj, 'template_name', '') or str(template_obj)
                        
                        planning_state["recommended_template"] = template_name
                        planning_state["template_match_score"] = match_score
                        insights.append(f"Template match: {template_name}")
            except Exception as e:
                logger.error(f"[Research] Template matching failed: {e}", exc_info=True)
            
            # Step 4: Generate expert questions using HITL service (same as hitl_router)
            # If user is answering previous questions, acknowledge and continue planning
            if is_followup_answer:
                logger.info("[Research] Detected follow-up answer to previous questions")
                # Acknowledge the answer and continue with accumulated context
                response_text = f"Got it! Thanks for that information. "
                response_text += "I'm updating my understanding based on what you've shared. "
                
                # Re-analyze with accumulated context
                if AutomatedHITLService is not None and vagueness_result:
                    try:
                        hitl_service = AutomatedHITLService()
                        domain_hint = problem_analysis.get('domain')
                        if not domain_hint and classification_result:
                            domain_hint = hitl_service._infer_domain_from_problem(analysis_text)
                        
                        # Generate new questions based on updated context
                        questions = await hitl_service.generate_expert_questions(
                            problem_description=analysis_text,
                            vagueness_result=vagueness_result,
                            domain_hint=domain_hint
                        )
                        
                        if questions:
                            hitl_questions = [q.question for q in questions]
                            response_text += "\n\nTo continue building your plan, could you tell me:\n\n"
                            for i, q in enumerate(hitl_questions[:3], 1):
                                response_text += f"{i}. {q}\n"
                            response_text += "\nFeel free to answer in your own words!"
                        else:
                            # If no more questions needed, suggest generating plan
                            response_text += "\n\nI think I have enough information to create a plan. Would you like me to generate one?"
                    except Exception as e:
                        logger.error(f"[Research] HITL question generation failed: {e}", exc_info=True)
                        response_text += "\n\nCould you provide a bit more detail about your problem?"
            elif AutomatedHITLService is not None and vagueness_result:
                try:
                    logger.info("[Research] Generating expert questions using HITL service...")
                    hitl_service = AutomatedHITLService()
                    
                    # Infer domain from classification or problem description
                    domain_hint = problem_analysis.get('domain')
                    if not domain_hint and classification_result:
                        domain_hint = hitl_service._infer_domain_from_problem(analysis_text)
                    
                    # Generate expert questions (same as HITL router)
                    questions = await hitl_service.generate_expert_questions(
                        problem_description=analysis_text,
                        vagueness_result=vagueness_result,
                        domain_hint=domain_hint
                    )
                    
                    if questions:
                        hitl_questions = [q.question for q in questions]
                        logger.info(f"[Research] Generated {len(hitl_questions)} expert questions")
                    else:
                        # Fallback to HITL fallback questions
                        fallback_questions = hitl_service._generate_fallback_questions(vagueness_result)
                        hitl_questions = [q.question for q in fallback_questions]
                        logger.info(f"[Research] Using {len(hitl_questions)} fallback questions")
                except Exception as e:
                    logger.error(f"[Research] HITL question generation failed: {e}", exc_info=True)
            
            # Step 5: Generate contextual response using research analysis
            # Only generate if not already handled as follow-up answer
            if not is_followup_answer or not response_text:
                response_text = await _generate_contextual_response(
                    user_message=request.message,
                    problem_analysis=problem_analysis,
                    template_matches=template_matches,
                    hitl_questions=hitl_questions,
                    vagueness_result=vagueness_result,
                    message_length=message_length
                )
        
        # Capture problem description if user provided meaningful input
        if message_length > 20 and not is_greeting:  # Reasonable problem description
            planning_state["problem_description"] = request.message
        
        # Build context graph (simplified)
        context_graph = {
            "nodes": [
                {
                    "id": "problem",
                    "label": "Problem",
                    "type": "input",
                    "x": 100,
                    "y": 200
                }
            ],
            "links": []
        }
        
        if planning_state.get("recommended_template"):
            context_graph["nodes"].append({
                "id": "template",
                "label": planning_state["recommended_template"],
                "type": "template",
                "x": 300,
                "y": 200
            })
            context_graph["links"].append({
                "source": "problem",
                "target": "template"
            })
        
        planning_state["context_graph"] = context_graph
        
        return ResearchChatResponse(
            response=response_text,
            insights=insights,
            context_graph=context_graph,
            planning_state=planning_state,
            session_id=session_id
        )
        
    except Exception as e:
        logger.error(f"[Research] Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Research chat failed: {str(e)}")


@router.post("/generate-plan", response_model=PlanGenerationResponse)
async def generate_plan(request: PlanGenerationRequest):
    """
    Generate a structured optimization plan from research conversation.
    
    Uses intent discovery tools to extract:
    - Problem type
    - Entities (decision variables, parameters)
    - Objectives
    - Constraints
    - Recommended template
    - Solver strategy
    """
    try:
        logger.info(f"[Research] Generating plan for conversation: {request.conversation_id}")
        
        # TODO: Retrieve conversation history from storage
        # For now, use refinements to build plan
        
        # Extract problem description from refinements or use default
        problem_description = request.refinements.get('problem_description', '')
        
        if not problem_description:
            raise HTTPException(status_code=400, detail="Problem description required for plan generation")
        
        # Run intent discovery tools
        plan_data = {
            "problem_description": problem_description,
            "problem_type": None,
            "entities": {},
            "objectives": [],
            "constraints": [],
            "recommended_template": None,
            "solver_strategy": {},
            "confidence_score": 0.8
        }
        
        # Classify problem
        try:
            classifier = ProblemClassifier()
            classification = await classifier.classify(problem_description)
            if classification and classification.get('result'):
                plan_data["problem_type"] = classification['result'].get('problem_type', '')
        except Exception as e:
            logger.warning(f"[Research] Classification failed: {e}")
        
        # Match template
        try:
            matches = match_problem_to_template(
                problem_description=problem_description,
                classification=plan_data["problem_type"],
                use_semantic=True,
                semantic_weight=0.7
            )
            if matches and len(matches) > 0:
                plan_data["recommended_template"] = matches[0].get('template_name')
        except Exception as e:
            logger.warning(f"[Research] Template matching failed: {e}")
        
        # Extract entities (simplified - full extraction needs classification)
        # For now, return basic plan structure
        
        # Build context graph
        context_graph = {
            "nodes": [
                {"id": "problem", "label": "Problem", "type": "input", "x": 100, "y": 200}
            ],
            "links": []
        }
        
        if plan_data["problem_type"]:
            context_graph["nodes"].append({
                "id": "classification",
                "label": plan_data["problem_type"],
                "type": "decision",
                "x": 300,
                "y": 200
            })
            context_graph["links"].append({"source": "problem", "target": "classification"})
        
        # Planning trail
        planning_trail = [
            {
                "step": "problem_input",
                "question": "What problem are you trying to solve?",
                "response": problem_description,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ]
        
        return PlanGenerationResponse(
            plan=plan_data,
            context_graph=context_graph,
            planning_trail=planning_trail
        )
        
    except Exception as e:
        logger.error(f"[Research] Plan generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Plan generation failed: {str(e)}")


@router.get("/plans/{plan_id}")
async def get_plan(plan_id: str):
    """Get a saved plan by ID"""
    # TODO: Implement plan storage and retrieval
    raise HTTPException(status_code=501, detail="Plan storage not yet implemented")


@router.post("/plans")
async def save_plan(plan: Dict[str, Any]):
    """Save a plan"""
    # TODO: Implement plan storage
    plan_id = f"plan_{uuid.uuid4().hex[:12]}"
    return {"plan_id": plan_id, "status": "saved"}

