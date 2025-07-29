from unittest.mock import patch
from deepeval.test_case import LLMTestCase
from app.deepeval import (
    MetricsFactory,
    TestCaseFactory,
    EvaluationService
)
from app.services.evaluation_service import GenAIEvaluationService

class TestDeepEvalIntegration:
    
    def test_qa_evaluation_with_synthetic_data(self):
        with patch('app.services.evaluation_service.answer_question_about_post') as mock_qa, \
             patch('app.deepeval.evaluation.evaluate') as mock_evaluate:
            mock_qa.return_value = {
                "answer": "FastAPI is a modern web framework for building APIs with Python.",
                "citations": ["FastAPI", "Python"]
            }
            
            mock_result = type('MockEvaluationResult', (), {
                'model_dump': lambda *args, **kwargs: {
                    "overall_score": 0.85,
                    "passed_metrics": 2,
                    "total_metrics": 2
                }
            })()
            mock_evaluate.return_value = mock_result

            results = GenAIEvaluationService.evaluate_qa_service_with_synthetic_data()

            assert "error" not in results
            assert "overall_score" in results
            assert results["overall_score"] == 0.85

    def test_global_qa_evaluation_with_synthetic_data(self):
        with patch('app.services.evaluation_service.answer_question_global') as mock_qa, \
             patch('app.deepeval.evaluation.evaluate') as mock_evaluate:
            mock_qa.return_value = {
                "answer": "Modern web frameworks provide features like automatic API documentation, request validation, and database integration to help build scalable web applications.",
                "citations": ["web-frameworks", "api-documentation"]
            }
            
            mock_result = type('MockEvaluationResult', (), {
                'model_dump': lambda *args, **kwargs: {
                    "overall_score": 0.90,
                    "passed_metrics": 3,
                    "total_metrics": 3
                }
            })()
            mock_evaluate.return_value = mock_result

            results = GenAIEvaluationService.evaluate_global_qa_service_with_synthetic_data()

            assert "error" not in results
            assert "overall_score" in results
            assert results["overall_score"] == 0.90

    def test_qa_test_cases_structure(self):
        for test_case in GenAIEvaluationService.QA_TEST_CASES:
            assert "question" in test_case
            assert "context" in test_case
            assert "expected_answer" in test_case
            assert isinstance(test_case["question"], str)
            assert isinstance(test_case["context"], str)
            assert isinstance(test_case["expected_answer"], str)
    
    def test_global_qa_test_cases_structure(self):
        for test_case in GenAIEvaluationService.GLOBAL_QA_TEST_CASES:
            assert "question" in test_case
            assert "context" in test_case
            assert "expected_answer" in test_case
            assert isinstance(test_case["question"], str)
            assert isinstance(test_case["context"], str)
            assert isinstance(test_case["expected_answer"], str)
    
    def test_deepeval_config_qa_metrics(self):
        metrics = MetricsFactory.create_qa_metrics()
        assert len(metrics) == 3
        metric_names = [metric.__class__.__name__ for metric in metrics]
        expected_names = ["AnswerRelevancyMetric", "ContextualRelevancyMetric", "FaithfulnessMetric"]
        for name in expected_names:
            assert name in metric_names
    
    def test_deepeval_config_summarization_metrics(self):
        metrics = MetricsFactory.create_summarization_metrics()
        assert len(metrics) == 2
        metric_names = [metric.__class__.__name__ for metric in metrics]
        expected_names = ["AnswerRelevancyMetric", "ContextualRelevancyMetric"]
        for name in expected_names:
            assert name in metric_names
    
    def test_deepeval_config_title_tags_metrics(self):
        metrics = MetricsFactory.create_title_tags_metrics()
        assert len(metrics) == 1
        metric_names = [metric.__class__.__name__ for metric in metrics]
        expected_names = ["AnswerRelevancyMetric"]
        for name in expected_names:
            assert name in metric_names
    
    def test_deepeval_config_sentiment_metrics(self):
        metrics = MetricsFactory.create_sentiment_analysis_metrics()
        assert len(metrics) == 2
        metric_names = [metric.__class__.__name__ for metric in metrics]
        expected_names = ["BiasMetric", "ToxicityMetric"]
        for name in expected_names:
            assert name in metric_names
    
    def test_create_qa_test_case(self):
        test_case = TestCaseFactory.create_qa_test_case(
            question="What is FastAPI?",
            context="FastAPI is a modern web framework.",
            actual_answer="FastAPI is a modern web framework for building APIs.",
            expected_answer="FastAPI is a modern web framework for building APIs with Python."
        )
        
        assert isinstance(test_case, LLMTestCase)
        assert test_case.input == "What is FastAPI?"
        assert test_case.actual_output == "FastAPI is a modern web framework for building APIs."
        assert test_case.expected_output == "FastAPI is a modern web framework for building APIs with Python."
        assert test_case.context == ["FastAPI is a modern web framework."]
        assert test_case.retrieval_context == ["FastAPI is a modern web framework."]
    
    def test_create_summarization_test_case(self):
        test_case = TestCaseFactory.create_summarization_test_case(
            content="Docker is a platform for containerizing applications.",
            actual_summary="Docker helps containerize apps.",
            expected_summary="Docker is a platform for containerizing applications."
        )
        
        assert isinstance(test_case, LLMTestCase)
        assert test_case.input == "Docker is a platform for containerizing applications."
        assert test_case.actual_output == "Docker helps containerize apps."
        assert test_case.expected_output == "Docker is a platform for containerizing applications."
        assert test_case.context == ["Docker is a platform for containerizing applications."]
        assert test_case.retrieval_context == ["Docker is a platform for containerizing applications."]
    
    def test_create_title_tags_test_case(self):
        test_case = TestCaseFactory.create_title_tags_test_case(
            content="Machine learning algorithms for AI.",
            actual_title="Machine Learning for AI",
            actual_tags=["machine-learning", "ai"],
            expected_title="Machine Learning and AI",
            expected_tags=["machine-learning", "ai", "algorithms"]
        )
        
        assert isinstance(test_case, LLMTestCase)
        assert test_case.input == "Machine learning algorithms for AI."
        assert test_case.actual_output == "Title: Machine Learning for AI\nTags: machine-learning, ai"
        assert test_case.expected_output == "Title: Machine Learning and AI\nTags: machine-learning, ai, algorithms"
        assert test_case.context == ["Machine learning algorithms for AI."]
    
    def test_create_sentiment_test_case(self):
        test_case = TestCaseFactory.create_sentiment_test_case(
            comment="This is a great article!",
            actual_sentiment="positive",
            actual_is_abusive=False,
            expected_sentiment="positive",
            expected_is_abusive=False
        )
        
        assert isinstance(test_case, LLMTestCase)
        assert test_case.input == "This is a great article!"
        assert test_case.actual_output == "Sentiment: positive, Abusive: False"
        assert test_case.expected_output == "Sentiment: positive, Abusive: False"
        assert test_case.context == ["This is a great article!"]
        assert test_case.retrieval_context == ["This is a great article!"]
    
    def test_evaluation_error_handling(self):
        with patch('app.services.evaluation_service.answer_question_about_post') as mock_qa:
            mock_qa.side_effect = Exception("Service error")
            
            results = GenAIEvaluationService.evaluate_qa_service_with_synthetic_data()
            
            assert "error" in results
            assert isinstance(results["error"], str)
    
    def test_minimal_evaluation(self):
        try:
            with patch('app.deepeval.evaluation.evaluate') as mock_evaluate:
                mock_result = type('MockEvaluationResult', (), {
                    'model_dump': lambda *args, **kwargs: {
                        "overall_score": 0.85,
                        "passed": True,
                        "metrics": {
                            "answer_relevancy": {
                                "score": 0.85,
                                "passed": True
                            }
                        }
                    }
                })()
                mock_evaluate.return_value = mock_result
                
                result = EvaluationService.test_minimal_evaluation()
                assert result is not None
                mock_evaluate.assert_called_once()
        except Exception as e:
            import traceback
            print(f"Minimal evaluation error: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            raise e