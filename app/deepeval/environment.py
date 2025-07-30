import os
from app.core.config import settings


class EnvironmentManager:
    
    @staticmethod
    def setup_groq_environment():
        env_vars = {
            "GROQ_API_KEY": settings.GROQ_API_KEY,
            "DEEPEVAL_MODEL": settings.LLM_MODEL,
            "OPENAI_API_KEY": settings.GROQ_API_KEY,
            "OPENAI_API_BASE": "https://api.groq.com/openai/v1"
        }
        
        for key, value in env_vars.items():
            os.environ[key] = value