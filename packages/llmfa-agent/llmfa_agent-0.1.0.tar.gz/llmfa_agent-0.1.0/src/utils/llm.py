"""
Gemini LLM wrapper for PocketFlow-based agent.
Uses google-genai SDK with gemini-3-flash-preview model.
"""

from google import genai
from google.genai import types
import google.generativeai as genai_legacy
from typing import Any
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize client
_client: genai.Client | None = None

def get_client() -> genai.Client:
    """Get or create the Gemini client."""
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        _client = genai.Client(api_key=api_key)
    return _client


async def call_llm(
    messages: list[dict[str, str]],
    system_prompt: str | None = None,
    tools: list[dict[str, Any]] | None = None,
    model: str = "gemini-3-flash-preview",
) -> types.GenerateContentResponse:
    """
    Call Gemini LLM with chat messages and optional tools.
    
    Args:
        messages: List of {"role": "user"|"assistant"|"model", "content": "..."}
        system_prompt: Optional system instruction
        tools: Optional list of tool definitions for function calling
        model: Model name (default: gemini-3-flash-preview)
    
    Returns:
        GenerateContentResponse from Gemini
    """
    client = get_client()
    
    # Convert messages to Gemini format
    contents = []
    for msg in messages:
        role = msg["role"]
        # Gemini uses "model" instead of "assistant"
        if role == "assistant":
            role = "model"
        contents.append(types.Content(
            role=role,
            parts=[types.Part.from_text(text=msg["content"])]
        ))
    
    # Build config
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
    )
    
    # Add tools if provided
    if tools:
        config.tools = tools
    
    response = await client.aio.models.generate_content(
        model=model,
        contents=contents,
        config=config,
    )
    
    return response


async def embed_text(text: str, model: str = "gemini-embedding-001") -> list[float]:
    """
    Generate embeddings for text using Gemini API.
    
    Args:
        text: Text to embed
        model: Embedding model name
    
    Returns:
        List of floats representing the embedding
    """
    # Use legacy API for embeddings (more stable)
    api_key = os.getenv("GEMINI_API_KEY")
    genai_legacy.configure(api_key=api_key)
    
    result = genai_legacy.embed_content(
        model=model,
        content=text,
        task_type="RETRIEVAL_QUERY",
        output_dimensionality=1536
    )
    return result['embedding']
