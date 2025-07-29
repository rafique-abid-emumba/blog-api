import logging
from typing import Dict, Any, List
from deepeval import evaluate
from deepeval.test_case import LLMTestCase

from .environment import EnvironmentManager
from .metrics import MetricsFactory
from .test_cases import TestCaseFactory

logger = logging.getLogger(__name__)


class EvaluationService:
    
    @staticmethod
    def evaluate_service(
        test_cases: List[LLMTestCase],
        metrics: List,
        service_name: str
    ) -> Dict[str, Any]:
        EnvironmentManager.setup_groq_environment()
        
        try:
            results = evaluate(test_cases=test_cases, metrics=metrics)
            logger.info(f"{service_name} evaluation completed with {len(test_cases)} test cases")
            return results.model_dump()
        except Exception as e:
            logger.error(f"{service_name} evaluation failed: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def evaluate_qa_service(test_cases: List[LLMTestCase]) -> Dict[str, Any]:
        metrics = MetricsFactory.create_qa_metrics()
        return EvaluationService.evaluate_service(test_cases, metrics, "Q&A")
    
    @staticmethod
    def evaluate_summarization_service(test_cases: List[LLMTestCase]) -> Dict[str, Any]:
        metrics = MetricsFactory.create_summarization_metrics()
        return EvaluationService.evaluate_service(test_cases, metrics, "Summarization")
    
    @staticmethod
    def evaluate_title_tags_service(test_cases: List[LLMTestCase]) -> Dict[str, Any]:
        metrics = MetricsFactory.create_title_tags_metrics()
        return EvaluationService.evaluate_service(test_cases, metrics, "Title/Tags")
    
    @staticmethod
    def evaluate_sentiment_service(test_cases: List[LLMTestCase]) -> Dict[str, Any]:
        metrics = MetricsFactory.create_sentiment_analysis_metrics()
        return EvaluationService.evaluate_service(test_cases, metrics, "Sentiment Analysis")
    
    @staticmethod
    def test_minimal_evaluation():
        try:
            EnvironmentManager.setup_groq_environment()
            
            test_case = TestCaseFactory.create_qa_test_case(
                question="What is Python?",
                context="Python is a programming language.",
                actual_answer="Python is a programming language.",
                expected_answer="Python is a programming language."
            )
            
            metrics = MetricsFactory.create_qa_metrics()
            results = evaluate(test_cases=[test_case], metrics=metrics)
            
            logger.info(f"Minimal evaluation successful: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Minimal evaluation failed: {e}")
            raise