"""
MongoDB stock data tool for fetching historical OHLCV data.
Simplified from Parlant version - plain async function.
"""

import json
from datetime import timezone
from dateutil import parser as dtparser
from pymongo import AsyncMongoClient
import os
from dotenv import load_dotenv

load_dotenv()


async def get_market_data(symbol: str, datetime_utc: str) -> dict:
    """
    Fetch OHLCV for a stock symbol at (or near) the specified UTC datetime from MongoDB.
    
    If no exact match, returns the closest available record.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'NVDA', 'MSFT', 'AAPL')
        datetime_utc: Target datetime in UTC (e.g., '20 Aug 2025 14:00 UTC')
    
    Returns:
        Dict with found status, match type, and data
    """
    # Parse datetime
    try:
        dt = dtparser.parse(datetime_utc)
        if dt.tzinfo is None:
            return {
                "success": False,
                "error": "Datetime must include UTC timezone (e.g., 'UTC' or 'Z')",
            }
        dt_utc = dt.astimezone(timezone.utc)
    except Exception as e:
        return {
            "success": False,
            "error": f"Could not parse datetime: {e}",
        }

    iso_z = dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    sym = symbol.upper()

    # Connect to MongoDB
    try:
        conn_string = os.getenv("MONGO_CONNECTION_STRING")
        if not conn_string:
            return {"success": False, "error": "MONGO_CONNECTION_STRING not configured"}
        
        client = AsyncMongoClient(conn_string)
        db = client["stockdb"]
        collection = db["stock_data"]
    except Exception as e:
        return {"success": False, "error": f"Database connection failed: {e}"}

    def clean_doc(doc):
        if not doc:
            return None
        doc = dict(doc)
        doc.pop("_id", None)
        doc["symbol"] = str(doc.get("symbol"))
        doc["datetime"] = str(doc.get("datetime"))
        return doc

    def parse_ts(ts_str):
        try:
            d = dtparser.parse(ts_str)
            if d.tzinfo is None:
                d = d.replace(tzinfo=timezone.utc)
            return d.astimezone(timezone.utc)
        except Exception:
            return None

    try:
        # 1. Exact match
        doc = await collection.find_one({"symbol": sym, "datetime": iso_z})
        if doc:
            return {
                "success": True,
                "match_type": "exact",
                "requested_datetime": iso_z,
                "data": clean_doc(doc),
                "delta_seconds": 0,
            }

        # 2. At or before
        doc = await collection.find_one(
            {"symbol": sym, "datetime": {"$lte": iso_z}}, 
            sort=[("datetime", -1)]
        )
        if doc:
            d_doc = parse_ts(doc["datetime"])
            delta = int((d_doc - dt_utc).total_seconds()) if d_doc else None
            return {
                "success": True,
                "match_type": "at_or_before",
                "requested_datetime": iso_z,
                "data": clean_doc(doc),
                "delta_seconds": delta,
                "note": "Returned last available before requested time",
            }

        # 3. At or after
        doc = await collection.find_one(
            {"symbol": sym, "datetime": {"$gte": iso_z}}, 
            sort=[("datetime", 1)]
        )
        if doc:
            d_doc = parse_ts(doc["datetime"])
            delta = int((d_doc - dt_utc).total_seconds()) if d_doc else None
            return {
                "success": True,
                "match_type": "at_or_after",
                "requested_datetime": iso_z,
                "data": clean_doc(doc),
                "delta_seconds": delta,
                "note": "Returned earliest after requested time",
            }

        # 4. Latest overall
        doc = await collection.find_one({"symbol": sym}, sort=[("datetime", -1)])
        if doc:
            d_doc = parse_ts(doc["datetime"])
            delta = int((d_doc - dt_utc).total_seconds()) if d_doc else None
            return {
                "success": True,
                "match_type": "latest_overall",
                "requested_datetime": iso_z,
                "data": clean_doc(doc),
                "delta_seconds": delta,
                "note": "Returned latest available record",
            }

        # No data found
        return {
            "success": False,
            "requested_datetime": iso_z,
            "error": f"No records found for symbol {sym}",
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
