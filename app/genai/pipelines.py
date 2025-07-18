import json
import re
import logging
from typing import Any, Dict, List

from app.genai.llm import get_llm
from app.genai.embeddings import get_embedding_model
from app.genai.vectorstore import get_vector_store
from app.services.vectorstore_service import get_nodes_by_post_id
from app.core.redis import redis_client
from llama_index.core import VectorStoreIndex
from llama_index.core.settings import Settings
from llama_index.core.schema import TextNode
from app.utils import _extract_json_from_text, _llm_complete

logger = logging.getLogger(__name__)

def suggest_title_and_tags(post_content: str) -> Dict[str, Any]:
    """
    Suggests a title and tags for a blog post using GenAI.
    """
    logger.info("Suggesting title and tags for post content")
    prompt = (
        "Given the following blog post content, suggest a concise, catchy title and 3-5 relevant tags. "
        "Return as JSON: {\"title\": ..., \"tags\": [...]}.",
        f"\n\nContent:\n{post_content}"
    )
    try:
        text = _llm_complete("".join(prompt))
        result = _extract_json_from_text(text)
        logger.info("Successfully suggested title and tags")
        return result
    except Exception as e:
        logger.error(f"Error suggesting title/tags: {e}")
        raise

def summarize_post(post_content: str) -> Dict[str, Any]:
    """
    Summarizes a blog post using GenAI.
    """
    logger.info("Summarizing post content")
    prompt = (
        "Summarize the following blog post in 2-3 sentences for quick reading. "
        "Also, provide references to the parts of the original text used for the summary. "
        "Return as JSON: {\"summary\": ..., \"citations\": [...]}.",
        f"\n\nContent:\n{post_content}"
    )
    try:
        text = _llm_complete("".join(prompt))
        result = _extract_json_from_text(text)
        logger.info("Successfully summarized post")
        return result
    except Exception as e:
        logger.error(f"Error summarizing post: {e}")
        raise

def answer_question_about_post(post_id: int, question: str, top_k: int = 3) -> Dict[str, Any]:
    """
    Answers a question about a blog post using RAG (Retrieval-Augmented Generation).
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
        prompt = (
            "Answer the following question using ONLY the provided context from the blog post. "
            "Cite the relevant chunk(s) by their order (1, 2, 3, ...). "
            "Return as JSON: {\"answer\": ..., \"citations\": [chunk_indices]}\n\n"
            f"Context:\n{context}\n\nQuestion: {question}"
        )
        text = _llm_complete(prompt)
        result = _extract_json_from_text(text)
        # Map chunk indices to actual chunk text for citations
        result["citations"] = [
            top_chunks[i-1] for i in result.get("citations", []) if 1 <= i <= len(top_chunks)
        ]
        redis_client.set(cache_key, json.dumps(result), ex=3600)
        logger.info(f"Cached Q&A result for post {post_id}, question='{question}'")
        return result
    except Exception as e:
        logger.error(f"Error in answer_question_about_post: {e}")
        raise

def analyze_comment_sentiment(comment: str) -> dict:
    """
    Analyze a comment for both sentiment and abuse detection.
    Returns a dictionary with 'sentiment' and 'is_abusive' keys.
    """
    logger.info(f"Analyzing comment for sentiment and abuse: '{comment[:50]}...'")
    prompt = (
        "Analyze the following comment. "
        "Return as JSON: {\"sentiment\": \"positive|negative|neutral\", \"is_abusive\": true|false}.\n\n"
        f"Comment: {comment}"
    )
    try:
        text = _llm_complete(prompt)
        result = _extract_json_from_text(text)
        if not isinstance(result, dict) or 'sentiment' not in result or 'is_abusive' not in result:
            logger.error("Invalid comment analysis format from LLM")
            raise ValueError("Invalid comment analysis format")
        logger.info(f"Comment analysis result: sentiment='{result['sentiment']}', abusive={result['is_abusive']}")
        return result
    except Exception as e:
        logger.error(f"Error analyzing comment: {e}")
        raise

def suggest_trending_tags(posts_with_comments: List[dict], top_k: int = 10) -> List[str]:
    """
    Analyze recent posts and their top-level comments to suggest trending tags.
    Uses GenAI to identify semantic trends and popular topics.
    """
    logger.info(f"Analyzing {len(posts_with_comments)} posts for trending tags")
    prompt = (
        "Based on the following recent blog posts and their top-level comments, "
        f"identify the top {top_k} trending tags that represent current popular topics, "
        "themes, or discussions. Consider both explicit tags and implicit topics.\n\n"
        "Recent content:\n"
    )
    for i, post_data in enumerate(posts_with_comments, 1):
        prompt += f"{i}. Post Title: {post_data['title']}\n"
        prompt += f"   Content: {post_data['content'][:500]}...\n"
        prompt += f"   Tags: {', '.join(post_data.get('tags', []))}\n"
        if post_data.get('comments'):
            prompt += f"   Top Comments ({len(post_data['comments'])}):\n"
            for j, comment in enumerate(post_data['comments'][:5], 1):
                prompt += f"     {j}. {comment['content'][:200]}...\n"
        prompt += "\n"
    prompt += (
        f"Based on this content, what are the top {top_k} trending tags? "
        "Return ONLY a JSON array of strings, e.g.: [\"tag1\", \"tag2\", \"tag3\"]"
    )
    try:
        text = _llm_complete(prompt)
        result = _extract_json_from_text(text, expect_array=True)
        if not isinstance(result, list) or not all(isinstance(tag, str) for tag in result):
            logger.error("Invalid trending tags format from LLM")
            raise ValueError("Invalid trending tags format")
        logger.info(f"Successfully identified {len(result)} trending tags: {result}")
        return result[:top_k]
    except Exception as e:
        logger.error(f"Error suggesting trending tags: {e}")
        raise