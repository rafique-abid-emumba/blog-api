import json
import logging
from typing import Dict, Any, Optional, Union
from pydantic import BaseModel

import openai
from deepeval.models import DeepEvalBaseLLM

logger = logging.getLogger(__name__)


class GroqModel(DeepEvalBaseLLM):
    
    def __init__(self, model: str, api_key: str):
        super().__init__()
        self.model = model
        self.api_key = api_key
        self.client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1"
        )
    
    def generate(self, prompt: str, **kwargs) -> str:
        import asyncio
        return asyncio.run(self.a_generate(prompt, **kwargs))
    
    async def a_generate(self, prompt: str, schema: Optional[BaseModel] = None, **kwargs) -> Union[str, BaseModel]:
        try:
            logger.debug(f"GroqModel.a_generate called with prompt: {prompt[:100]}...")
            logger.debug(f"Schema: {schema}")
            logger.debug(f"Kwargs: {kwargs}")
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            content = response.choices[0].message.content
            
            logger.debug(f"Groq response: {content}")
            
            if not schema:
                return content.strip()
            
            return self._parse_schema_response(content, schema)
            
        except Exception as e:
            logger.error(f"Error generating response with Groq: {e}")
            raise
    
    def _parse_schema_response(self, content: str, schema: BaseModel) -> Union[str, BaseModel]:
        try:
            cleaned_content = self._clean_json_content(content)
            data = json.loads(cleaned_content)
            logger.debug(f"Parsed JSON data: {data}")
            
            return self._create_schema_model(data, schema)
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"JSON parsing error: {e}")
            return self._create_fallback_model(content, schema)
    
    def _clean_json_content(self, content: str) -> str:
        cleaned = content.strip()
        if cleaned.startswith('```json'):
            cleaned = cleaned[7:]
        elif cleaned.startswith('```'):
            cleaned = cleaned[3:]
        if cleaned.endswith('```'):
            cleaned = cleaned[:-3]
        return cleaned
    
    def _create_schema_model(self, data: Dict[str, Any], schema: BaseModel) -> BaseModel:
        schema_name = schema.__name__
        
        schema_handlers = {
            'Opinions': lambda: schema(opinions=data.get('opinions', [])),
            'Statements': lambda: schema(statements=data.get('statements', [])),
            'Truths': lambda: schema(truths=data.get('truths', [])),
            'Claims': lambda: schema(claims=data.get('claims', [])),
            'ContextualRelevancyVerdicts': lambda: schema(verdicts=data.get('verdicts', [])),
            'Verdicts': lambda: schema(verdicts=data.get('verdicts', [])),
            'ContextualRelevancyScoreReason': lambda: schema(reason=data.get('reason', '')),
            'AnswerRelevancyScoreReason': lambda: schema(reason=data.get('reason', '')),
            'FaithfulnessScoreReason': lambda: schema(reason=data.get('reason', '')),
        }
        
        for key, handler in schema_handlers.items():
            if key in schema_name:
                result = handler()
                logger.debug(f"Created {schema_name} model: {result}")
                return result
        
        if 'ScoreReason' in schema_name:
            result = schema(reason=data.get('reason', ''))
            logger.debug(f"Created {schema_name} model: {result}")
            return result
        
        logger.warning(f"No handler found for schema {schema_name}, using default values")
        return schema()
    
    def _create_fallback_model(self, content: str, schema: BaseModel) -> Union[str, BaseModel]:
        schema_name = schema.__name__
        cleaned_content = self._clean_json_content(content)
        
        fallback_handlers = {
            'ScoreReason': lambda: schema(reason=cleaned_content),
            'Truths': lambda: schema(truths=[cleaned_content]),
            'Claims': lambda: schema(claims=[cleaned_content]),
            'ContextualRelevancyVerdicts': lambda: schema(verdicts=[{"verdict": "yes", "statement": cleaned_content}]),
            'Verdicts': lambda: schema(verdicts=[{"verdict": "yes", "statement": cleaned_content}]),
        }
        
        for key, handler in fallback_handlers.items():
            if key in schema_name:
                result = handler()
                logger.debug(f"Created fallback {schema_name} model: {result}")
                return result
        
        return cleaned_content
    
    def get_model_name(self) -> str:
        return self.model
    
    def load_model(self):
        pass