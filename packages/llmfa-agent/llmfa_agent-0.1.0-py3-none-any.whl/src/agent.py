"""
PocketFlow-based Financial Data Assistant Agent.
Provides a simple async interface for chat with tool calling.
"""

from dataclasses import dataclass, field
from typing import Any
import json
from pocketflow import AsyncNode, AsyncFlow
from google.genai import types

from .config.prompts import SYSTEM_PROMPT
from .tools import get_minute_bars, get_market_data, vector_search
from .utils.llm import call_llm


@dataclass
class ChatResponse:
    """Response from the generate_response function."""
    response: str                          # Final text response
    tool_calls: list[dict] = field(default_factory=list)  # Tools called with params and results
    sources: list[dict] = field(default_factory=list)     # Retrieved documents from vector search
    model: str = "gemini-3-flash-preview"        # Model used


# Tool definitions for Gemini function calling
TOOL_DEFINITIONS = [
    {
        "name": "get_minute_bars",
        "description": "Fetch real-time 1-minute OHLCV price data for a stock ticker. Use this for latest, current, most recent, or intraday prices.",
        "parameters": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Stock ticker symbol (e.g., 'AAPL', 'NVDA', '^GSPC')"
                },
                "period": {
                    "type": "string",
                    "enum": ["1d", "5d", "7d"],
                    "description": "Lookback window. Default is '1d'."
                },
                "limit_rows": {
                    "type": "integer",
                    "description": "Number of recent rows to return. Default is 20."
                }
            },
            "required": ["ticker"]
        }
    },
    {
        "name": "get_market_data",
        "description": "Fetch historical OHLCV data from the database for a specific datetime. Use this for past/historical stock prices.",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Stock ticker symbol (e.g., 'NVDA', 'MSFT', 'AAPL')"
                },
                "datetime_utc": {
                    "type": "string",
                    "description": "Target datetime in UTC (e.g., '20 Aug 2025 14:00 UTC')"
                }
            },
            "required": ["symbol", "datetime_utc"]
        }
    },
    {
        "name": "vector_search",
        "description": "Search for relevant financial documents and analysis. Use this for context, background information, and company analysis.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query text"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results. Default is 5."
                }
            },
            "required": ["query"]
        }
    }
]


# Tool name to function mapping
TOOL_FUNCTIONS = {
    "get_minute_bars": get_minute_bars,
    "get_market_data": get_market_data,
    "vector_search": vector_search,
}


async def execute_tool(name: str, args: dict) -> Any:
    """Execute a tool by name with given arguments."""
    if name not in TOOL_FUNCTIONS:
        return {"error": f"Unknown tool: {name}"}
    
    func = TOOL_FUNCTIONS[name]
    try:
        result = await func(**args)
        return result
    except Exception as e:
        return {"error": str(e)}


class AgentNode(AsyncNode):
    """PocketFlow Node that runs the agent loop."""
    
    async def prep_async(self, shared: dict) -> dict:
        """Prepare the node - get messages from shared store."""
        return {
            "messages": shared.get("messages", []),
            "tool_calls": shared.get("tool_calls", []),
            "sources": shared.get("sources", []),
        }
    
    async def exec_async(self, prep_result: dict) -> dict:
        """Execute LLM call and handle tool calls."""
        messages = prep_result["messages"]
        tool_calls = prep_result["tool_calls"]
        sources = prep_result["sources"]
        
        # Build tools config for Gemini
        tools_config = [types.Tool(function_declarations=[
            types.FunctionDeclaration(
                name=t["name"],
                description=t["description"],
                parameters=t["parameters"]
            )
            for t in TOOL_DEFINITIONS
        ])]
        
        # Call LLM
        response = await call_llm(
            messages=messages,
            system_prompt=SYSTEM_PROMPT,
            tools=tools_config,
        )
        
        # Check for function calls
        candidate = response.candidates[0] if response.candidates else None
        if not candidate:
            return {
                "done": True,
                "response": "I apologize, but I couldn't generate a response.",
                "tool_calls": tool_calls,
                "sources": sources,
            }
        
        content = candidate.content
        
        # Check if there are function calls
        function_calls = []
        text_parts = []
        
        for part in content.parts:
            if hasattr(part, 'function_call') and part.function_call:
                function_calls.append(part.function_call)
            elif hasattr(part, 'text') and part.text:
                text_parts.append(part.text)
        
        if function_calls:
            # Execute tool calls
            tool_results = []
            for fc in function_calls:
                tool_name = fc.name
                tool_args = dict(fc.args) if fc.args else {}
                
                result = await execute_tool(tool_name, tool_args)
                
                # Track tool call
                tool_call_record = {
                    "tool": tool_name,
                    "args": tool_args,
                    "result": result,
                }
                tool_calls.append(tool_call_record)
                
                # Track sources from vector search
                if tool_name == "vector_search" and isinstance(result, list):
                    sources.extend(result)
                
                tool_results.append({
                    "name": tool_name,
                    "result": result,
                })
            
            # Add assistant message with function call
            messages.append({
                "role": "assistant",
                "content": f"[Called tools: {', '.join(fc.name for fc in function_calls)}]"
            })
            
            # Add tool results as user message
            tool_results_text = "\n".join([
                f"Result from {tr['name']}:\n{json.dumps(tr['result'], indent=2, default=str)}"
                for tr in tool_results
            ])
            messages.append({
                "role": "user",
                "content": f"Tool results:\n{tool_results_text}"
            })
            
            return {
                "done": False,
                "messages": messages,
                "tool_calls": tool_calls,
                "sources": sources,
            }
        else:
            # No function calls - we have a final response
            final_text = " ".join(text_parts) if text_parts else ""
            return {
                "done": True,
                "response": final_text,
                "tool_calls": tool_calls,
                "sources": sources,
            }
    
    async def post_async(self, shared: dict, prep_result: dict, exec_result: dict) -> str:
        """Post-process and update shared store."""
        if exec_result.get("done"):
            shared["final_response"] = exec_result.get("response", "")
            shared["tool_calls"] = exec_result.get("tool_calls", [])
            shared["sources"] = exec_result.get("sources", [])
            return "done"
        else:
            # Continue looping
            shared["messages"] = exec_result.get("messages", [])
            shared["tool_calls"] = exec_result.get("tool_calls", [])
            shared["sources"] = exec_result.get("sources", [])
            return "continue"


def create_agent_flow() -> AsyncFlow:
    """Create the PocketFlow agent flow."""
    agent_node = AgentNode()
    
    # Loop back to self on "continue", end on "done"
    # PocketFlow uses - "action" >> next_node syntax
    agent_node - "continue" >> agent_node
    
    flow = AsyncFlow(start=agent_node)
    return flow


async def generate_response(
    messages: list[dict[str, str]],
    max_iterations: int = 10,
) -> ChatResponse:
    """
    Generate a response for the given chat messages.
    
    This is the main interface for the library. Pass a list of messages
    and receive a rich response with the assistant's reply, any tool calls
    made, and sources retrieved.
    
    Args:
        messages: List of {"role": "user"|"assistant", "content": "..."}
        max_iterations: Maximum number of agent loop iterations (default: 10)
    
    Returns:
        ChatResponse with response, tool_calls, sources, and model info
    
    Example:
        response = await generate_response([
            {"role": "user", "content": "What's the current price of NVDA?"}
        ])
        print(response.response)
        print(response.tool_calls)
    """
    # Initialize shared store
    shared = {
        "messages": list(messages),  # Copy to avoid mutation
        "tool_calls": [],
        "sources": [],
        "final_response": "",
    }
    
    # Create and run flow
    flow = create_agent_flow()
    
    # Run the async flow - it handles transitions internally
    await flow.run_async(shared)
    
    return ChatResponse(
        response=shared.get("final_response", ""),
        tool_calls=shared.get("tool_calls", []),
        sources=shared.get("sources", []),
        model="gemini-3-flash-preview",
    )

