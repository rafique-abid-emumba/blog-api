import json
import re
from app.genai.llm import get_llm
from app.genai.embeddings import get_embedding_model
from llama_index.core import ServiceContext

def get_service_context():
    return ServiceContext.from_defaults(
        llm=get_llm(),
        embed_model=get_embedding_model(),
    )

def suggest_title_and_tags(post_content: str) -> dict:
    llm = get_llm()
    prompt = (
        "Given the following blog post content, suggest a concise, catchy title and 3-5 relevant tags. "
        "Return as JSON: {\"title\": ..., \"tags\": [...]}.\n\n"
        f"Content:\n{post_content}"
    )
    response = llm.complete(prompt=prompt)
    text = response.text
    match = re.search(r"\{.*?\}", text, re.DOTALL)
    if not match:
        raise ValueError("No valid JSON object found in LLM response")
    json_str = match.group(0)
    return json.loads(json_str) 