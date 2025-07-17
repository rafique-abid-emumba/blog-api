import json
import re
import logging
from app.genai.llm import get_llm
from app.genai.embeddings import get_embedding_model
from app.genai.vectorstore import get_vector_store
from app.services.vectorstore_service import get_nodes_by_post_id
from app.core.redis import redis_client
from llama_index.core import VectorStoreIndex
from llama_index.core.settings import Settings
from llama_index.core.schema import TextNode

logger = logging.getLogger(__name__)


def suggest_title_and_tags(post_content: str) -> dict:
    logger.info("Suggesting title and tags for post content")
    llm = get_llm()
    prompt = (
        "Given the following blog post content, suggest a concise, catchy title and 3-5 relevant tags. "
        "Return as JSON: {\"title\": ..., \"tags\": [...]}.\n\n"
        f"Content:\n{post_content}"
    )
    try:
        response = llm.complete(prompt=prompt)
        text = response.text
        match = re.search(r"\{.*?\}", text, re.DOTALL)
        if not match:
            logger.error("No valid JSON object found in LLM response for title/tags")
            raise ValueError("No valid JSON object found in LLM response")
        json_str = match.group(0)
        result = json.loads(json_str)
        logger.info("Successfully suggested title and tags")
        return result
    except Exception as e:
        logger.error(f"Error suggesting title/tags: {e}")
        raise


def summarize_post(post_content: str) -> dict:
    logger.info("Summarizing post content")
    llm = get_llm()
    prompt = (
        "Summarize the following blog post in 2-3 sentences for quick reading. "
        "Also, provide references to the parts of the original text used for the summary. "
        "Return as JSON: {\"summary\": ..., \"citations\": [...]}.\n\n"
        f"Content:\n{post_content}"
    )
    try:
        response = llm.complete(prompt=prompt)
        text = response.text
        match = re.search(r"\{.*?\}", text, re.DOTALL)
        if not match:
            logger.error("No valid JSON object found in LLM response for summary")
            raise ValueError("No valid JSON object found in LLM response")
        json_str = match.group(0)
        result = json.loads(json_str)
        logger.info("Successfully summarized post")
        return result
    except Exception as e:
        logger.error(f"Error summarizing post: {e}")
        raise


def answer_question_about_post(post_id: int, question: str, top_k: int = 3) -> dict:
    """
    Answers a question about a blog post using RAG (Retrieval-Augmented Generation).
    Retrieves post chunks from Redis (or QDrantDB as fallback), finds the most relevant chunks,
    and prompts the LLM to answer with citations.
    """
    cache_key = f"post:{post_id}:qa:{question}"
    try:
        cached = redis_client.get(cache_key)
        if cached:
            logger.info(f"Cache hit for Q&A: post_id={post_id}, question='{question}'")
            return json.loads(cached)
        logger.info(f"Cache miss for Q&A: post_id={post_id}, question='{question}'")

        chunks_json = redis_client.get(f"post:{post_id}:chunks")
        if chunks_json:
            logger.info(f"Found chunks in Redis for post {post_id}")
            chunks = json.loads(chunks_json)
            nodes = [
                TextNode(text=chunk, metadata={"post_id": post_id, "chunk_index": idx})
                for idx, chunk in enumerate(chunks)
            ]
        else:
            logger.info(f"Chunks not found in Redis, fetching from Qdrant for post {post_id}")
            vector_store = get_vector_store()
            try:
                nodes = get_nodes_by_post_id(post_id)
                # all_nodes = vector_store.get_nodes()
                # nodes = [node for node in all_nodes if getattr(node, "metadata", {}).get("post_id") == post_id]
            except AttributeError:
                logger.error(f"No chunks found for post {post_id} in QdrantDB (AttributeError)")
                raise ValueError("No chunks found for this post in QDrantDB.")
            if not nodes:
                logger.error(f"No chunks found for post {post_id} in QdrantDB (empty nodes)")
                raise ValueError("No chunks found for this post in QDrantDB.")
            chunks = [node.text for node in nodes]
            redis_client.set(f"post:{post_id}:chunks", json.dumps(chunks))
            logger.info(f"Cached chunks in Redis for post {post_id}")

        vector_store = get_vector_store()
        embed_model = get_embedding_model()
        Settings.embed_model = embed_model
        index = VectorStoreIndex(nodes=nodes, vector_store=vector_store)
        retriever = index.as_retriever(similarity_top_k=top_k)
        retrieved_nodes = retriever.retrieve(question)
        top_chunks = [node.text for node in retrieved_nodes]
        logger.info(f"Retrieved top {top_k} chunks for Q&A on post {post_id}")

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
            logger.error("No valid JSON object found in LLM response for Q&A")
            raise ValueError("No valid JSON object found in LLM response")
        result = json.loads(match.group(0))

        result["citations"] = [
            top_chunks[i-1] for i in result.get("citations", []) if 1 <= i <= len(top_chunks)
        ]

        redis_client.set(cache_key, json.dumps(result), ex=3600)
        logger.info(f"Cached Q&A result for post {post_id}, question='{question}'")
        return result
    except Exception as e:
        logger.error(f"Error in answer_question_about_post: {e}")
        raise