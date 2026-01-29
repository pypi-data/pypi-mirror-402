"""
Example usage of the Financial Data Assistant library.
"""

import asyncio
from src import generate_response


async def main():
    print("=" * 60)
    print("Financial Data Assistant - Example Usage")
    print("=" * 60)
    
    # Example 1: Simple stock price query (English)
    print("\n--- Example 1: Stock Price Query (English) ---")
    response = await generate_response([
        {"role": "user", "content": "What's the current price of NVDA?"}
    ])
    print(f"Response: {response.response}")
    print(f"Tools called: {len(response.tool_calls)}")
    for tc in response.tool_calls:
        print(f"  - {tc['tool']}: {tc['args']}")
    
    # Example 2: Thai language query
    print("\n--- Example 2: Stock Price Query (Thai) ---")
    response = await generate_response([
        {"role": "user", "content": "ราคาหุ้น AAPL ตอนนี้เท่าไหร่?"}
    ])
    print(f"Response: {response.response}")
    
    # Example 3: Multi-turn conversation
    print("\n--- Example 3: Multi-turn Conversation ---")
    response = await generate_response([
        {"role": "user", "content": "Tell me about MSFT stock"},
        {"role": "assistant", "content": "Microsoft (MSFT) is a major technology company. Let me get the current price for you."},
        {"role": "user", "content": "Yes, please show me the latest price."}
    ])
    print(f"Response: {response.response}")
    print(f"Model: {response.model}")


if __name__ == "__main__":
    asyncio.run(main())
