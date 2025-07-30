from app.core.config import settings

def get_llm():
    if getattr(settings, "LLM_PROVIDER", None) == "openai":
        from llama_index.llms.openai import OpenAI
        return OpenAI(api_key=settings.OPENAI_API_KEY)
    else:
        from llama_index.llms.groq import Groq
        return Groq(api_key=settings.GROQ_API_KEY, model=settings.LLM_MODEL, temperature=0.2) 