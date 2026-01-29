"""
YFinance tool for fetching real-time stock data.
Simplified from Parlant version - plain async function.
"""

from typing import Literal
import asyncio
import yfinance as yf
import pandas as pd


async def get_minute_bars(
    ticker: str,
    period: Literal["1d", "5d", "7d"] = "1d",
    limit_rows: int = 20,
) -> dict:
    """
    Fetch 1-minute OHLCV data for a ticker using yfinance.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'NVDA', '^GSPC')
        period: Lookback window ('1d', '5d', '7d'). Yahoo limits 1m data to ~7 days.
        limit_rows: Number of most recent rows to return (keeps response small)
    
    Returns:
        Dict with status, data, and metadata
    """
    if period not in {"1d", "5d", "7d"}:
        return {
            "success": False,
            "error": "Period must be one of '1d', '5d', '7d' for 1-minute data",
        }

    try:
        df = await asyncio.to_thread(
            yf.download,
            tickers=ticker,
            interval="1m",
            period=period,
            prepost=False,
            progress=False,
            threads=True,
            group_by="column",
            auto_adjust=True,
        )

        if df is None or df.empty:
            return {
                "success": False,
                "error": f"No data returned for {ticker} with period='{period}'",
            }

        # Normalize MultiIndex columns
        if isinstance(df.columns, pd.MultiIndex):
            if df.columns.nlevels == 2 and len(df.columns.get_level_values(1).unique()) == 1:
                df.columns = df.columns.droplevel(1)

        # Get recent rows
        tail = df.tail(limit_rows)
        
        # Build response
        last_row = tail.iloc[-1]
        
        return {
            "success": True,
            "symbol": ticker.upper(),
            "period": period,
            "interval": "1m",
            "total_rows": len(df),
            "time_range": {
                "start": str(df.index[0]),
                "end": str(df.index[-1]),
            },
            "latest": {
                "datetime": str(tail.index[-1]),
                "open": float(last_row.get("Open", 0)),
                "high": float(last_row.get("High", 0)),
                "low": float(last_row.get("Low", 0)),
                "close": float(last_row.get("Close", 0)),
                "volume": int(last_row.get("Volume", 0)) if pd.notna(last_row.get("Volume")) else 0,
            },
            "recent_bars": [
                {
                    "datetime": str(idx),
                    "open": float(row.get("Open", 0)),
                    "high": float(row.get("High", 0)),
                    "low": float(row.get("Low", 0)),
                    "close": float(row.get("Close", 0)),
                    "volume": int(row.get("Volume", 0)) if pd.notna(row.get("Volume")) else 0,
                }
                for idx, row in tail.iterrows()
            ],
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }
