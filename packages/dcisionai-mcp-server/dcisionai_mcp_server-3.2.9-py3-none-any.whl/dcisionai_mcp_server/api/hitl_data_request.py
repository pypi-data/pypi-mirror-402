"""
HITL Data Request API Endpoints

Handles user answers to HITL data request questions and resumes workflow.
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from dcisionai_mcp_server.middleware.api_key_auth import verify_api_key_optional
from dcisionai_mcp_server.jobs.storage import get_job_by_session_id, update_job_state
from dcisionai_workflow.services.hitl_data_request import HITLDataRequestService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/hitl/data-request", tags=["hitl"])


class DataRequestAnswer(BaseModel):
    """Answer to a data request question."""
    question_id: str = Field(..., description="Question ID")
    parameter_name: str = Field(..., description="Parameter name")
    data: Optional[Any] = Field(None, description="User-provided data (None if synthetic chosen)")
    chose_synthetic: bool = Field(False, description="True if user chose synthetic option")


class SubmitDataRequestAnswersRequest(BaseModel):
    """Request to submit answers to HITL data request questions."""
    session_id: str = Field(..., description="Workflow session ID")
    answers: List[DataRequestAnswer] = Field(..., description="List of answers to questions")


class SubmitDataRequestAnswersResponse(BaseModel):
    """Response after submitting answers."""
    session_id: str
    status: str
    message: str
    validated: bool
    errors: List[str] = []


@router.post("/submit-answers", response_model=SubmitDataRequestAnswersResponse)
async def submit_data_request_answers(
    request: SubmitDataRequestAnswersRequest,
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
) -> SubmitDataRequestAnswersResponse:
    """
    Submit answers to HITL data request questions and resume workflow.
    
    This endpoint:
    1. Validates user-provided data
    2. Merges answers into workflow state
    3. Updates state to unpause workflow
    """
    session_id = request.session_id
    answers = request.answers
    
    logger.info(f"📋 Received HITL data request answers for session {session_id}: {len(answers)} answers")
    
    try:
        # Get job/workflow state from database
        job = get_job_by_session_id(session_id, tenant_info.get('tenant_id'), tenant_info.get('is_admin', False))
        if not job:
            raise HTTPException(status_code=404, detail=f"Job not found for session {session_id}")
        
        # Get workflow state from job
        workflow_state = job.get('workflow_state') or {}
        
        # Check if workflow is paused for data request
        if not workflow_state.get('workflow_paused') or workflow_state.get('paused_for') != 'hitl_data_request':
            raise HTTPException(
                status_code=400,
                detail=f"Workflow is not paused for data request. Status: {workflow_state.get('workflow_paused')}, paused_for: {workflow_state.get('paused_for')}"
            )
        
        # Get questions from state
        questions = workflow_state.get('hitl_data_questions', [])
        if not questions:
            raise HTTPException(status_code=400, detail="No data request questions found in workflow state")
        
        # Validate answers
        service = HITLDataRequestService()
        validation_errors = []
        
        # Create answer objects
        answer_objects = []
        for answer_data in answers:
            # Find corresponding question
            question = next((q for q in questions if q.get('id') == answer_data.question_id), None)
            if not question:
                validation_errors.append(f"Question {answer_data.question_id} not found")
                continue
            
            # Validate user-provided data if not synthetic
            if not answer_data.chose_synthetic and answer_data.data is not None:
                # Parse JSON if string
                try:
                    import json
                    if isinstance(answer_data.data, str):
                        answer_data.data = json.loads(answer_data.data)
                except json.JSONDecodeError:
                    validation_errors.append(f"Invalid JSON for {answer_data.parameter_name}")
                    continue
                
                # Get parameter info from question
                param_info = {
                    'name': answer_data.parameter_name,
                    'type': question.get('data_structure', {}).get('type', 'scalar'),
                    'indices': question.get('data_structure', {}).get('indices', [])
                }
                
                validation_result = service.validate_user_data(answer_data.data, param_info)
                if not validation_result['valid']:
                    validation_errors.extend(validation_result['errors'])
                    continue
            
            # Create answer object
            from dcisionai_workflow.services.hitl_data_request import DataRequestAnswer as ServiceAnswer
            answer_objects.append(ServiceAnswer(
                question_id=answer_data.question_id,
                parameter_name=answer_data.parameter_name,
                data=answer_data.data,
                chose_synthetic=answer_data.chose_synthetic,
                validation_errors=None
            ))
        
        if validation_errors:
            return SubmitDataRequestAnswersResponse(
                session_id=session_id,
                status="validation_failed",
                message="Validation errors found",
                validated=False,
                errors=validation_errors
            )
        
        # Merge answers into workflow state
        updated_state = service.merge_user_data(workflow_state, answer_objects)
        
        # Update workflow state: unpause and mark data request complete
        updated_state['workflow_paused'] = False
        updated_state['paused_for'] = None
        updated_state['hitl_data_request_complete'] = True
        
        # Store answers in state
        updated_state['hitl_data_answers'] = [
            {
                'question_id': a.question_id,
                'parameter_name': a.parameter_name,
                'data': a.data,
                'chose_synthetic': a.chose_synthetic,
                'validation_errors': a.validation_errors
            }
            for a in answer_objects
        ]
        
        # Update job state in database
        update_job_state(job['id'], updated_state, tenant_info.get('tenant_id'), tenant_info.get('is_admin', False))
        
        logger.info(f"✅ Updated workflow state for session {session_id}")
        logger.info(f"   User-provided parameters: {updated_state.get('user_provided_params', [])}")
        logger.info(f"   Synthetic parameters: {updated_state.get('synthetic_params', [])}")
        
        # Note: Workflow resume will be handled by the frontend
        # The frontend should send a resume message via WebSocket or trigger continuation
        # For now, we just update the state and let the frontend handle resumption
        
        return SubmitDataRequestAnswersResponse(
            session_id=session_id,
            status="success",
            message="Answers submitted successfully. Workflow will resume.",
            validated=True,
            errors=[]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing data request answers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing answers: {str(e)}")


@router.get("/questions/{session_id}")
async def get_data_request_questions(
    session_id: str,
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
) -> Dict[str, Any]:
    """
    Get current data request questions for a session.
    """
    try:
        job = get_job_by_session_id(session_id, tenant_info.get('tenant_id'), tenant_info.get('is_admin', False))
        if not job:
            raise HTTPException(status_code=404, detail=f"Job not found for session {session_id}")
        
        workflow_state = job.get('workflow_state') or {}
        questions = workflow_state.get('hitl_data_questions', [])
        
        return {
            "session_id": session_id,
            "questions": questions,
            "paused": workflow_state.get('workflow_paused', False),
            "paused_for": workflow_state.get('paused_for')
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting data request questions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting questions: {str(e)}")


@router.post("/resume/{session_id}")
async def resume_workflow(
    session_id: str,
    tenant_info: Dict[str, Any] = Depends(verify_api_key_optional)
) -> Dict[str, Any]:
    """
    Resume workflow after HITL data request answers are submitted.
    
    This endpoint triggers workflow continuation from checkpoint.
    """
    try:
        job = get_job_by_session_id(session_id, tenant_info.get('tenant_id'), tenant_info.get('is_admin', False))
        if not job:
            raise HTTPException(status_code=404, detail=f"Job not found for session {session_id}")
        
        workflow_state = job.get('workflow_state') or {}
        
        # Check if workflow is ready to resume
        if workflow_state.get('workflow_paused') and workflow_state.get('hitl_data_request_complete'):
            # Unpause workflow
            workflow_state['workflow_paused'] = False
            workflow_state['paused_for'] = None
            
            # Update job state
            update_job_state(job['id'], workflow_state, tenant_info.get('tenant_id'), tenant_info.get('is_admin', False))
            
            logger.info(f"🔄 Workflow resumed for session {session_id}")
            
            return {
                "session_id": session_id,
                "status": "resumed",
                "message": "Workflow resumed successfully"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Workflow is not ready to resume. paused: {workflow_state.get('workflow_paused')}, complete: {workflow_state.get('hitl_data_request_complete')}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming workflow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error resuming workflow: {str(e)}")
