from fastapi import APIRouter, Depends, HTTPException
from app.services.evaluation_service import GenAIEvaluationService
from app.core.deps import require_role
from app.schemas.evaluation import QAEvaluationRequest, GlobalQAEvaluationRequest, SummarizationEvaluationRequest, EvaluationResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/evaluation", tags=["evaluation"])

@router.post("/qa", response_model=EvaluationResponse, dependencies=[Depends(require_role(["Admin"]))])
def evaluate_qa_service(request: QAEvaluationRequest):
    try:
        results = GenAIEvaluationService.evaluate_qa_service_with_real_data(
            post_id=request.post_id,
            questions=request.questions,
            expected_answers=request.expected_answers
        )
        
        if "error" in results:
            return EvaluationResponse(
                success=False,
                results={},
                message=f"Q&A evaluation failed: {results['error']}"
            )
        
        return EvaluationResponse(
            success=True,
            results=results,
            message="Q&A evaluation completed successfully"
        )
    except Exception as e:
        logger.error(f"Q&A evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")

@router.post("/qa-global", response_model=EvaluationResponse, dependencies=[Depends(require_role(["Admin"]))])
def evaluate_global_qa_service(request: GlobalQAEvaluationRequest):
    try:
        results = GenAIEvaluationService.evaluate_global_qa_service_with_real_data(
            questions=request.questions,
            expected_answers=request.expected_answers
        )
        
        if "error" in results:
            return EvaluationResponse(
                success=False,
                results={},
                message=f"Global Q&A evaluation failed: {results['error']}"
            )
        
        return EvaluationResponse(
            success=True,
            results=results,
            message="Global Q&A evaluation completed successfully"
        )
    except Exception as e:
        logger.error(f"Global Q&A evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")

@router.post("/summarization", response_model=EvaluationResponse, dependencies=[Depends(require_role(["Admin"]))])
def evaluate_summarization_service(request: SummarizationEvaluationRequest):
    try:
        results = GenAIEvaluationService.evaluate_summarization_service_with_content(
            post_content=request.post_content,
            expected_summary=request.expected_summary
        )
        
        if "error" in results:
            return EvaluationResponse(
                success=False,
                results={},
                message=f"Summarization evaluation failed: {results['error']}"
            )
        
        return EvaluationResponse(
            success=True,
            results=results,
            message="Summarization evaluation completed successfully"
        )
    except Exception as e:
        logger.error(f"Summarization evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")