# LLMFA Agent

A PocketFlow-based Python library for financial data chat with tool calling using Gemini AI.

## Installation

```bash
pip install llmfa-agent
```

## Quick Start

```python
import asyncio
from src import generate_response

async def main():
    response = await generate_response([
        {"role": "user", "content": "What's the current price of NVDA?"}
    ])
    
    print(response.response)      # The assistant's reply
    print(response.tool_calls)    # Tools called with results
    print(response.sources)       # Retrieved documents

asyncio.run(main())
```

## Environment Variables

```bash
export GEMINI_API_KEY=your_gemini_api_key
export MONGO_CONNECTION_STRING=mongodb+srv://...  # Optional
```

## Features

- 🤖 **Gemini 3 Flash** - Powered by Google's latest AI model
- 🔧 **Tool Calling** - Automatic function execution for stock data
- 📊 **Real-time Data** - Live stock prices via yfinance
- 📚 **RAG Support** - Vector search for document retrieval
- 🌐 **Multilingual** - Thai and English language support

## Available Tools

- **get_minute_bars**: Real-time 1-minute OHLCV data (via yfinance)
- **get_market_data**: Historical stock data from MongoDB
- **vector_search**: Semantic search for financial documents

## License

MIT
