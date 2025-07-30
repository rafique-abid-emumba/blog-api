from typing import List, Dict, Any, Optional
from app.deepeval import (
    TestCaseFactory,
    EvaluationService
)
from app.genai.pipelines import answer_question_about_post, answer_question_global, summarize_post
from app.services.post_service import get_post
from app.db.deps import get_db
from app.utils.constants import QA_TEST_CASES, GLOBAL_QA_TEST_CASES, SUMMARIZATION_TEST_CASES
import logging

logger = logging.getLogger(__name__)

class GenAIEvaluationService:
    
    @staticmethod
    def evaluate_qa_service_with_synthetic_data() -> Dict[str, Any]:
        test_cases = []
        
        for test_case in QA_TEST_CASES:
            try:
                test_case_obj = TestCaseFactory.create_qa_test_case(
                    question=test_case["question"],
                    context=test_case["context"],
                    actual_answer=test_case["expected_answer"],
                    expected_answer=test_case["expected_answer"]
                )
                test_cases.append(test_case_obj)
                
            except Exception as e:
                logger.error(f"Failed to create QA test case: {e}")
                continue
        
        if not test_cases:
            return {"error": "No valid test cases could be created"}
        
        return EvaluationService.evaluate_qa_service(test_cases)
    
    @staticmethod
    def evaluate_summarization_service_with_synthetic_data() -> Dict[str, Any]:
        test_cases = []
        
        for test_case in SUMMARIZATION_TEST_CASES:
            try:
                test_case_obj = TestCaseFactory.create_summarization_test_case(
                    content=test_case["content"],
                    actual_summary=test_case["expected_summary"],
                    expected_summary=test_case["expected_summary"]
                )
                test_cases.append(test_case_obj)
                
            except Exception as e:
                logger.error(f"Failed to create summarization test case: {e}")
                continue
        
        if not test_cases:
            return {"error": "No valid summarization test cases could be created"}
        
        return EvaluationService.evaluate_summarization_service(test_cases)
    
    @staticmethod
    def evaluate_global_qa_service_with_synthetic_data() -> Dict[str, Any]:
        test_cases = []
        
        for test_case in GLOBAL_QA_TEST_CASES:
            try:
                test_case_obj = TestCaseFactory.create_qa_test_case(
                    question=test_case["question"],
                    context=test_case["context"],
                    actual_answer=test_case["expected_answer"],
                    expected_answer=test_case["expected_answer"]
                )
                test_cases.append(test_case_obj)
                
            except Exception as e:
                logger.error(f"Failed to create Global QA test case: {e}")
                continue
        
        if not test_cases:
            return {"error": "No valid Global QA test cases could be created"}
        
        return EvaluationService.evaluate_qa_service(test_cases)
    
    @staticmethod
    def evaluate_global_qa_service_with_real_data(
        questions: List[str],
        expected_answers: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        test_cases = []
        
        for i, question in enumerate(questions):
            try:
                actual_result = answer_question_global(question)
                actual_answer = actual_result.get("answer", "")
                
                expected_answer = expected_answers[i] if expected_answers and i < len(expected_answers) else None
                
                test_case = TestCaseFactory.create_qa_test_case(
                    question=question,
                    context=question,
                    actual_answer=actual_answer,
                    expected_answer=expected_answer
                )
                test_cases.append(test_case)
                
            except Exception as e:
                logger.error(f"Failed to evaluate Global Q&A for question '{question}': {e}")
                continue
        
        if not test_cases:
            return {"error": "No valid Global QA test cases could be created"}
        
        return EvaluationService.evaluate_qa_service(test_cases)
    
    @staticmethod
    def evaluate_qa_service_with_real_data(
        post_id: int,
        questions: List[str],
        expected_answers: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        test_cases = []
        
        for i, question in enumerate(questions):
            try:
                actual_result = answer_question_about_post(post_id, question)
                actual_answer = actual_result.get("answer", "")
                
                expected_answer = expected_answers[i] if expected_answers and i < len(expected_answers) else None
                
                test_case = TestCaseFactory.create_qa_test_case(
                    question=question,
                    context=question,
                    actual_answer=actual_answer,
                    expected_answer=expected_answer
                )
                test_cases.append(test_case)
                
            except Exception as e:
                logger.error(f"Failed to evaluate Q&A for question '{question}': {e}")
                continue
        
        if not test_cases:
            return {"error": "No valid test cases could be created"}
        
        return EvaluationService.evaluate_qa_service(test_cases) 
    
    @staticmethod
    def evaluate_summarization_service_with_real_data(
        post_id: int,
        expected_summary: Optional[str] = None
    ) -> Dict[str, Any]:
        test_cases = []
        
        try:
            db = next(get_db())
            post = get_post(db, post_id)
            post_content = post.content
            
            actual_result = summarize_post(post_content)
            actual_summary = actual_result.get("summary", "")
            
            test_case = TestCaseFactory.create_summarization_test_case(
                content=post_content,
                actual_summary=actual_summary,
                expected_summary=expected_summary
            )
            test_cases.append(test_case)
            
        except Exception as e:
            logger.error(f"Failed to evaluate summarization for post {post_id}: {e}")
            return {"error": f"Failed to evaluate summarization: {str(e)}"}
        
        if not test_cases:
            return {"error": "No valid summarization test cases could be created"}
        
        return EvaluationService.evaluate_summarization_service(test_cases)

    @staticmethod
    def evaluate_summarization_service_with_content(
        post_content: str,
        expected_summary: Optional[str] = None
    ) -> Dict[str, Any]:
        test_cases = []
        
        try:
            actual_result = summarize_post(post_content)
            actual_summary = actual_result.get("summary", "")
            
            test_case = TestCaseFactory.create_summarization_test_case(
                content=post_content,
                actual_summary=actual_summary,
                expected_summary=expected_summary
            )
            test_cases.append(test_case)
            
        except Exception as e:
            logger.error(f"Failed to evaluate summarization for content: {e}")
            return {"error": f"Failed to evaluate summarization: {str(e)}"}
        
        if not test_cases:
            return {"error": "No valid summarization test cases could be created"}
        
        return EvaluationService.evaluate_summarization_service(test_cases) 