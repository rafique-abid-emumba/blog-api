from pydantic import BaseModel
from typing import Dict, Any, Optional, List


class QAEvaluationRequest(BaseModel):
    post_id: int
    questions: List[str]
    expected_answers: Optional[List[str]] = None


class GlobalQAEvaluationRequest(BaseModel):
    questions: List[str]
    expected_answers: Optional[List[str]] = None


class EvaluationResponse(BaseModel):
    success: bool
    results: Dict[str, Any]
    message: Optional[str] = None 