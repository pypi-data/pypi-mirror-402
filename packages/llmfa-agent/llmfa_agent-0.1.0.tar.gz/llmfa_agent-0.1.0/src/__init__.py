"""
Financial Data Assistant - PocketFlow-based LLM Library

A simple Python library for financial data chat with tool calling.

Usage:
    from llm import generate_response, ChatResponse
    
    response = await generate_response([
        {"role": "user", "content": "What's the current price of NVDA?"}
    ])
    
    print(response.response)      # The assistant's reply
    print(response.tool_calls)    # List of tools called
    print(response.sources)       # Retrieved documents
"""

from .agent import generate_response, ChatResponse

__all__ = [
    "generate_response",
    "ChatResponse",
]
