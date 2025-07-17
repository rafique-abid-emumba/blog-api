import json
import re
from app.genai.llm import get_llm
from app.genai.embeddings import get_embedding_model
from app.genai.vectorstore import get_vector_store
from app.core.redis import redis_client
from llama_index.core import VectorStoreIndex
from llama_index.core.settings import Settings
from llama_index.core.schema import TextNode

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


def summarize_post(post_content: str) -> dict:
    llm = get_llm()
    prompt = (
        "Summarize the following blog post in 2-3 sentences for quick reading. "
        "Also, provide references to the parts of the original text used for the summary. "
        "Return as JSON: {\"summary\": ..., \"citations\": [...]}.\n\n"
        f"Content:\n{post_content}"
    )
    response = llm.complete(prompt=prompt)
    text = response.text
    match = re.search(r"\{.*?\}", text, re.DOTALL)
    if not match:
        raise ValueError("No valid JSON object found in LLM response")
    json_str = match.group(0)
    return json.loads(json_str)


def answer_question_about_post(post_id: int, question: str, top_k: int = 3) -> dict:
    """
    Answers a question about a blog post using RAG (Retrieval-Augmented Generation).
    Retrieves post chunks from Redis (or ChromaDB as fallback), finds the most relevant chunks,
    and prompts the LLM to answer with citations.
    """
    cache_key = f"post:{post_id}:qa:{question}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    chunks_json = redis_client.get(f"post:{post_id}:chunks")
    if chunks_json:
        chunks = json.loads(chunks_json)
        nodes = [
            TextNode(text=chunk, metadata={"post_id": post_id, "chunk_index": idx})
            for idx, chunk in enumerate(chunks)
        ]
    else:
        vector_store = get_vector_store()
        try:
            nodes = vector_store.get_nodes(metadata_filter={"post_id": post_id})
        except AttributeError:
            raise ValueError("No chunks found for this post in ChromaDB.")
        if not nodes:
            raise ValueError("No chunks found for this post in ChromaDB.")
        chunks = [node.text for node in nodes]
        
        redis_client.set(f"post:{post_id}:chunks", json.dumps(chunks))

    vector_store = get_vector_store()
    embed_model = get_embedding_model()
    Settings.embed_model = embed_model
    index = VectorStoreIndex(nodes=nodes, vector_store=vector_store)
    retriever = index.as_retriever(similarity_top_k=top_k)
    retrieved_nodes = retriever.retrieve(question)
    top_chunks = [node.text for node in retrieved_nodes]

    context = "\n---\n".join(top_chunks)

    llm = get_llm()
    prompt = (
        "Answer the following question using ONLY the provided context from the blog post. "
        "Cite the relevant chunk(s) by their order (1, 2, 3, ...). "
        "Return as JSON: {\"answer\": ..., \"citations\": [chunk_indices]}\n\n"
        f"Context:\n{context}\n\nQuestion: {question}"
    )
    response = llm.complete(prompt=prompt)
    match = re.search(r"\{.*?\}", response.text, re.DOTALL)
    if not match:
        raise ValueError("No valid JSON object found in LLM response")
    result = json.loads(match.group(0))

    result["citations"] = [
        top_chunks[i-1] for i in result.get("citations", []) if 1 <= i <= len(top_chunks)
    ]

    redis_client.set(cache_key, json.dumps(result), ex=3600)
    return result 