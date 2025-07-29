from typing import List
from deepeval.metrics import (
    AnswerRelevancyMetric,
    BiasMetric,
    ContextualRelevancyMetric,
    FaithfulnessMetric,
    ToxicityMetric
)

from .groq_llm import GroqModel
from app.core.config import settings


def create_groq_llm() -> GroqModel:
    try:
        llm = GroqModel(
            model=settings.LLM_MODEL,
            api_key=settings.GROQ_API_KEY
        )
        return llm
    except Exception as e:
        raise Exception(f"Error creating Groq LLM: {e}")


class MetricsFactory:
    
    @staticmethod
    def create_qa_metrics() -> List:
        groq_llm = create_groq_llm()
        return [
            AnswerRelevancyMetric(threshold=0.7, model=groq_llm),
            ContextualRelevancyMetric(threshold=0.7, model=groq_llm),
            FaithfulnessMetric(threshold=0.7, model=groq_llm)
        ]
    
    @staticmethod
    def create_summarization_metrics() -> List:
        groq_llm = create_groq_llm()
        return [
            AnswerRelevancyMetric(threshold=0.7, model=groq_llm),
            ContextualRelevancyMetric(threshold=0.7, model=groq_llm)
        ]
    
    @staticmethod
    def create_title_tags_metrics() -> List:
        groq_llm = create_groq_llm()
        return [
            AnswerRelevancyMetric(threshold=0.7, model=groq_llm)
        ]
    
    @staticmethod
    def create_sentiment_analysis_metrics() -> List:
        groq_llm = create_groq_llm()
        return [
            BiasMetric(threshold=0.3, model=groq_llm),
            ToxicityMetric(threshold=0.3, model=groq_llm)
        ]