from typing import List, Optional
from deepeval.test_case import LLMTestCase


class TestCaseFactory:
    
    @staticmethod
    def create_qa_test_case(
        question: str,
        context: str,
        actual_answer: str,
        expected_answer: Optional[str] = None
    ) -> LLMTestCase:
        return LLMTestCase(
            input=question,
            actual_output=actual_answer,
            expected_output=expected_answer,
            context=[context],
            retrieval_context=[context]
        )
    
    @staticmethod
    def create_summarization_test_case(
        content: str,
        actual_summary: str,
        expected_summary: Optional[str] = None
    ) -> LLMTestCase:
        return LLMTestCase(
            input=content,
            actual_output=actual_summary,
            expected_output=expected_summary,
            context=[content],
            retrieval_context=[content]
        )
    
    @staticmethod
    def create_title_tags_test_case(
        content: str,
        actual_title: str,
        actual_tags: List[str],
        expected_title: Optional[str] = None,
        expected_tags: Optional[List[str]] = None
    ) -> LLMTestCase:
        actual_output = f"Title: {actual_title}\nTags: {', '.join(actual_tags)}"
        expected_output = None
        if expected_title and expected_tags:
            expected_output = f"Title: {expected_title}\nTags: {', '.join(expected_tags)}"
        
        return LLMTestCase(
            input=content,
            actual_output=actual_output,
            expected_output=expected_output,
            context=[content],
            retrieval_context=[content]
        )
    
    @staticmethod
    def create_sentiment_test_case(
        comment: str,
        actual_sentiment: str,
        actual_is_abusive: bool,
        expected_sentiment: Optional[str] = None,
        expected_is_abusive: Optional[bool] = None
    ) -> LLMTestCase:
        actual_output = f"Sentiment: {actual_sentiment}, Abusive: {actual_is_abusive}"
        expected_output = None
        if expected_sentiment is not None and expected_is_abusive is not None:
            expected_output = f"Sentiment: {expected_sentiment}, Abusive: {expected_is_abusive}"
        
        return LLMTestCase(
            input=comment,
            actual_output=actual_output,
            expected_output=expected_output,
            context=[comment],
            retrieval_context=[comment]
        )