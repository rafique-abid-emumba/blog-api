from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class QAEvaluationRequest(BaseModel):
    post_id: int
    questions: List[str]
    expected_answers: Optional[List[str]] = None


class GlobalQAEvaluationRequest(BaseModel):
    questions: List[str]
    expected_answers: Optional[List[str]] = None


class SummarizationEvaluationRequest(BaseModel):
    post_content: str
    expected_summary: Optional[str] = None


class EvaluationResponse(BaseModel):
    success: Optional[bool] = None
    results: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    overall_score: Optional[float] = None
    passed_metrics: Optional[int] = None
    total_metrics: Optional[int] = None
    test_results: Optional[List[dict]] = None
    confident_link: Optional[str] = None
    error: Optional[str] = None 