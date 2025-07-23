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
    
    fallback_response = {
        "title": "Untitled Post",
        "tags": ["general", "blog"]
    }
    
    prompt = f"""# INSTRUCTION: Generate Title and Tags

You are an AI assistant that generates catchy titles and relevant tags for blog posts.

## TASK:
Analyze the following blog post content and generate:
1. A concise, catchy title (max 60 characters)
2. 3-5 relevant tags that describe the main topics

## OUTPUT FORMAT:
You must respond with ONLY a valid JSON object in this exact format:
{{
    "title": "Your suggested title here",
    "tags": ["tag1", "tag2", "tag3"]
}}

## IMPORTANT RULES:
- If you cannot generate a proper title, use "Untitled Post"
- If you cannot generate tags, use ["general", "blog"]
- Never include explanations, markdown, or extra text
- Only return the JSON object

## BLOG POST CONTENT:
{post_content}

## RESPONSE:"""
    
    try:
        text = _llm_complete(prompt)
        result = _extract_json_from_text(text)
        
        if not isinstance(result, dict) or 'title' not in result or 'tags' not in result:
            logger.warning("Invalid response structure, using fallback")
            return fallback_response
        
        if not result['title'] or len(result['title']) > 60:
            result['title'] = fallback_response['title']
        
        if not result['tags'] or not isinstance(result['tags'], list):
            result['tags'] = fallback_response['tags']
        
        logger.info("Successfully suggested title and tags")
        return result
    except Exception as e:
        logger.error(f"Error suggesting title/tags: {e}")
        return fallback_response

def summarize_post(post_content: str) -> Dict[str, Any]:
    """
    Summarizes a blog post using GenAI.
    """
    logger.info("Summarizing post content")
    
    # Predefined fallback response
    fallback_response = {
        "summary": "This post discusses various topics and provides insights on the subject matter.",
        "citations": ["Content analysis"]
    }
    
    prompt = f"""# INSTRUCTION: Summarize Blog Post

You are an AI assistant that creates concise summaries of blog posts.

## TASK:
Create a 2-3 sentence summary of the following blog post that captures the main points.
Also identify key phrases or concepts from the original text that support your summary.

## OUTPUT FORMAT:
You must respond with ONLY a valid JSON object in this exact format:
{{
    "summary": "Your 2-3 sentence summary here",
    "citations": ["key phrase 1", "key phrase 2"]
}}

## IMPORTANT RULES:
- If you cannot generate a proper summary, use "This post discusses various topics and provides insights on the subject matter."
- If you cannot identify citations, use ["Content analysis"]
- Never include explanations, markdown, or extra text
- Only return the JSON object
- Summary should be 2-3 sentences maximum

## BLOG POST CONTENT:
{post_content}

## RESPONSE:"""
    
    try:
        text = _llm_complete(prompt)
        result = _extract_json_from_text(text)
        
        if not isinstance(result, dict) or 'summary' not in result or 'citations' not in result:
            logger.warning("Invalid response structure, using fallback")
            return fallback_response
        
        if not result['summary'] or len(result['summary']) > 500:
            result['summary'] = fallback_response['summary']
        
        if not result['citations'] or not isinstance(result['citations'], list):
            result['citations'] = fallback_response['citations']
        
        logger.info("Successfully summarized post")
        return result
    except Exception as e:
        logger.error(f"Error summarizing post: {e}")
        return fallback_response

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
        
        fallback_response = {
            "answer": "I cannot find specific information to answer this question based on the available content.",
            "citations": []
        }
        
        prompt = f"""# INSTRUCTION: Answer Question About Blog Post

You are an AI assistant that answers questions about blog posts using only the provided context.

## TASK:
Answer the given question using ONLY the information from the provided context.
Cite the specific chunks (by number) that support your answer.

## OUTPUT FORMAT:
You must respond with ONLY a valid JSON object in this exact format:
{{
    "answer": "Your answer based on the context",
    "citations": [1, 2, 3]
}}

## IMPORTANT RULES:
- Only use information from the provided context
- If the context doesn't contain relevant information, use "I cannot find specific information to answer this question based on the available content."
- If you cannot identify citations, use []
- Never include explanations, markdown, or extra text
- Only return the JSON object
- Citations should be chunk numbers (1, 2, 3, etc.)

## CONTEXT (Chunks from blog post):
{context}

## QUESTION:
{question}

## RESPONSE:"""
        
        text = _llm_complete(prompt)
        result = _extract_json_from_text(text)
        
        if not isinstance(result, dict) or 'answer' not in result or 'citations' not in result:
            logger.warning("Invalid response structure, using fallback")
            result = fallback_response
        else:
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
    
    fallback_response = {
        "sentiment": "neutral",
        "is_abusive": False
    }
    
    prompt = f"""# INSTRUCTION: Analyze Comment Sentiment and Abuse

You are an AI assistant that analyzes comments for sentiment and potential abuse.

## TASK:
Analyze the following comment and determine:
1. Sentiment: positive, negative, or neutral
2. Whether the comment contains abusive content

## OUTPUT FORMAT:
You must respond with ONLY a valid JSON object in this exact format:
{{
    "sentiment": "positive|negative|neutral",
    "is_abusive": true|false
}}

## IMPORTANT RULES:
- If you cannot determine sentiment, use "neutral"
- If you cannot determine abuse, use false
- Never include explanations, markdown, or extra text
- Only return the JSON object
- Sentiment must be exactly: "positive", "negative", or "neutral"
- is_abusive must be exactly: true or false

## COMMENT TO ANALYZE:
{comment}

## RESPONSE:"""
    
    try:
        text = _llm_complete(prompt)
        result = _extract_json_from_text(text)
        
        if not isinstance(result, dict) or 'sentiment' not in result or 'is_abusive' not in result:
            logger.warning("Invalid response structure, using fallback")
            return fallback_response
        
        if result['sentiment'] not in ['positive', 'negative', 'neutral']:
            result['sentiment'] = fallback_response['sentiment']
        
        if not isinstance(result['is_abusive'], bool):
            result['is_abusive'] = fallback_response['is_abusive']
        
        logger.info(f"Comment analysis result: sentiment='{result['sentiment']}', abusive={result['is_abusive']}")
        return result
    except Exception as e:
        logger.error(f"Error analyzing comment: {e}")
        return fallback_response

def suggest_trending_tags(posts_with_comments: List[dict], top_k: int = 10) -> List[str]:
    """
    Analyze recent posts and their top-level comments to suggest trending tags.
    Uses GenAI to identify semantic trends and popular topics.
    """
    logger.info(f"Analyzing {len(posts_with_comments)} posts for trending tags")
    
    fallback_response = ["general", "blog", "discussion"]
    
    prompt = f"""# INSTRUCTION: Identify Trending Tags

You are an AI assistant that identifies trending topics from blog posts and comments.

## TASK:
Analyze the following recent blog posts and their comments to identify the top {top_k} trending tags.
Consider both explicit tags mentioned and implicit topics discussed.

## OUTPUT FORMAT:
You must respond with ONLY a valid JSON array of strings in this exact format:
["tag1", "tag2", "tag3"]

## IMPORTANT RULES:
- If you cannot identify trending tags, use ["general", "blog", "discussion"]
- Never include explanations, markdown, or extra text
- Only return the JSON array
- Maximum {top_k} tags
- Tags should be lowercase, single words or short phrases

## RECENT CONTENT:
"""
    
    for i, post_data in enumerate(posts_with_comments, 1):
        prompt += f"{i}. Post Title: {post_data['title']}\n"
        prompt += f"   Content: {post_data['content'][:500]}...\n"
        prompt += f"   Tags: {', '.join(post_data.get('tags', []))}\n"
        if post_data.get('comments'):
            prompt += f"   Top Comments ({len(post_data['comments'])}):\n"
            for j, comment in enumerate(post_data['comments'][:5], 1):
                prompt += f"     {j}. {comment['content'][:200]}...\n"
        prompt += "\n"
    
    prompt += f"""## RESPONSE:"""
    
    try:
        text = _llm_complete(prompt)
        result = _extract_json_from_text(text, expect_array=True)
        
        if not isinstance(result, list) or not all(isinstance(tag, str) for tag in result):
            logger.warning("Invalid response structure, using fallback")
            return fallback_response[:top_k]
        
        result = result[:top_k]
        
        logger.info(f"Successfully identified {len(result)} trending tags: {result}")
        return result
    except Exception as e:
        logger.error(f"Error suggesting trending tags: {e}")
        return fallback_response[:top_k]