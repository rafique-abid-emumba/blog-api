from typing import List, Dict, Any, Optional
from app.deepeval import (
    TestCaseFactory,
    EvaluationService
)
from app.genai.pipelines import answer_question_about_post, answer_question_global
import logging

logger = logging.getLogger(__name__)

class GenAIEvaluationService:
    
    QA_TEST_CASES = [
        {
            "question": "What is FastAPI?",
            "context": "FastAPI is a modern web framework for building APIs with Python. It provides automatic API documentation and is built on top of Starlette.",
            "expected_answer": "FastAPI is a modern web framework for building APIs with Python that provides automatic API documentation."
        },
        {
            "question": "How does Redis work?",
            "context": "Redis is an in-memory data structure store that can be used as a database, cache, and message broker. It supports various data structures.",
            "expected_answer": "Redis is an in-memory data structure store that can be used as a database, cache, and message broker."
        }
    ]
    
    GLOBAL_QA_TEST_CASES = [
        {
            "question": "What are the main features of modern web frameworks?",
            "context": "Modern web frameworks like FastAPI, Django, and Flask provide features such as automatic API documentation, request validation, and database integration. They help developers build scalable web applications quickly.",
            "expected_answer": "Modern web frameworks provide features like automatic API documentation, request validation, and database integration to help build scalable web applications."
        },
        {
            "question": "How do vector databases work?",
            "context": "Vector databases store and retrieve high-dimensional vectors efficiently. They use similarity search algorithms to find the most relevant vectors for a given query, making them ideal for AI applications.",
            "expected_answer": "Vector databases store high-dimensional vectors and use similarity search algorithms to find relevant vectors for queries, making them ideal for AI applications."
        }
    ]
    
    SUMMARIZATION_TEST_CASES = [
        {
            "content": "Docker is a platform for developing, shipping, and running applications in containers. Containers are lightweight and include everything needed to run the application.",
            "expected_summary": "Docker is a platform for containerizing applications, making them lightweight and portable."
        },
        {
            "content": "Python is a high-level programming language known for its simplicity and readability. It's widely used in web development, data science, and AI.",
            "expected_summary": "Python is a high-level programming language valued for simplicity and used in web development, data science, and AI."
        }
    ]
    
    TITLE_TAGS_TEST_CASES = [
        {
            "content": "Machine learning algorithms can be trained on large datasets to make predictions and classifications. Deep learning uses neural networks with multiple layers.",
            "expected_title": "Machine Learning and Deep Learning",
            "expected_tags": ["machine-learning", "deep-learning", "ai", "neural-networks"]
        },
        {
            "content": "Web development involves creating websites and web applications. Frontend development focuses on user interface, while backend handles server-side logic.",
            "expected_title": "Web Development: Frontend and Backend",
            "expected_tags": ["web-development", "frontend", "backend", "programming"]
        }
    ]
    
    @staticmethod
    def evaluate_qa_service_with_synthetic_data() -> Dict[str, Any]:
        test_cases = []
        
        for test_case in GenAIEvaluationService.QA_TEST_CASES:
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
    def evaluate_global_qa_service_with_synthetic_data() -> Dict[str, Any]:
        test_cases = []
        
        for test_case in GenAIEvaluationService.GLOBAL_QA_TEST_CASES:
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