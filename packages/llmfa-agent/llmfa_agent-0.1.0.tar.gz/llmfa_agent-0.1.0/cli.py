#!/usr/bin/env python
"""
Interactive CLI for testing the Financial Data Assistant.

Run: uv run python cli.py
"""

import asyncio
import sys
from src import generate_response, ChatResponse


def print_response(response: ChatResponse):
    """Pretty print the response."""
    print("\n" + "=" * 60)
    print("🤖 ASSISTANT RESPONSE")
    print("=" * 60)
    print(response.response)
    
    if response.tool_calls:
        print("\n" + "-" * 40)
        print(f"🔧 TOOLS CALLED ({len(response.tool_calls)})")
        print("-" * 40)
        for i, tc in enumerate(response.tool_calls, 1):
            print(f"\n  [{i}] {tc['tool']}")
            print(f"      Args: {tc['args']}")
            # Truncate result if too long
            result_str = str(tc.get('result', {}))
            if len(result_str) > 200:
                result_str = result_str[:200] + "..."
            print(f"      Result: {result_str}")
    
    if response.sources:
        print("\n" + "-" * 40)
        print(f"📚 SOURCES ({len(response.sources)})")
        print("-" * 40)
        for i, source in enumerate(response.sources, 1):
            print(f"\n  [{i}] {source.get('source', 'Unknown')}")
            content = source.get('content', '')[:100]
            print(f"      {content}...")
    
    print("\n" + "-" * 40)
    print(f"Model: {response.model}")
    print("=" * 60 + "\n")


async def chat_loop():
    """Interactive chat loop."""
    print("\n" + "=" * 60)
    print("💬 Financial Data Assistant CLI")
    print("=" * 60)
    print("Type your message and press Enter.")
    print("Commands:")
    print("  /quit or /exit - Exit the CLI")
    print("  /clear         - Clear conversation history")
    print("  /history       - Show conversation history")
    print("=" * 60 + "\n")
    
    conversation: list[dict[str, str]] = []
    
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nGoodbye! 👋")
            break
        
        if not user_input:
            continue
        
        # Handle commands
        if user_input.lower() in ["/quit", "/exit"]:
            print("\nGoodbye! 👋")
            break
        
        if user_input.lower() == "/clear":
            conversation = []
            print("✨ Conversation cleared.\n")
            continue
        
        if user_input.lower() == "/history":
            if not conversation:
                print("📜 No conversation history.\n")
            else:
                print("\n📜 Conversation History:")
                for msg in conversation:
                    role = "You" if msg["role"] == "user" else "Assistant"
                    content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
                    print(f"  {role}: {content}")
                print()
            continue
        
        # Add user message to conversation
        conversation.append({"role": "user", "content": user_input})
        
        print("\n⏳ Thinking...")
        
        try:
            response = await generate_response(conversation)
            
            # Add assistant response to conversation
            conversation.append({"role": "assistant", "content": response.response})
            
            print_response(response)
            
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
            # Remove the failed user message
            conversation.pop()


async def single_query(query: str):
    """Run a single query and exit."""
    print(f"\n📤 Query: {query}")
    print("⏳ Processing...")
    
    try:
        response = await generate_response([
            {"role": "user", "content": query}
        ])
        print_response(response)
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # Single query mode: python cli.py "What's the price of NVDA?"
        query = " ".join(sys.argv[1:])
        asyncio.run(single_query(query))
    else:
        # Interactive mode
        asyncio.run(chat_loop())


if __name__ == "__main__":
    main()
