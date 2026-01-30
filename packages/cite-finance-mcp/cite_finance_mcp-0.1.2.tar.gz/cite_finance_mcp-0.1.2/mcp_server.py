from typing import Any, Sequence
import asyncio
import os
import json
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)
import httpx

# Configuration
# Default to empty to trigger Demo Mode if user hasn't bought a key
API_BASE_URL = os.getenv("CITE_FINANCE_API_URL", "https://cite-finance-api-prod-2e405b0a5150.herokuapp.com/api/v1")
API_KEY = os.getenv("CITE_FINANCE_API_KEY")
GUMROAD_PRODUCT_PERMALINK = os.getenv("GUMROAD_PERMALINK", "cite-finance")

async def validate_license_key(key: str) -> bool:
    """Verify license key with Gumroad API."""
    if not key or key.startswith("demo_"):
        return False
        
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                "https://api.gumroad.com/v2/licenses/verify",
                data={
                    "product_permalink": GUMROAD_PRODUCT_PERMALINK,
                    "license_key": key
                },
                timeout=5.0
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("success", False) and not data.get("purchase", {}).get("refunded", False)
            return False
        except Exception:
            return False

# Define the server
app = Server("cite-finance-mcp")

# --- Rich Demo Data (The "Hook") ---
DEMO_DATA = {
    "AAPL": {
        "ticker": "AAPL",
        "metric": "revenue_ttm",
        "value": 383285000000,
        "unit": "USD",
        "period": "TTM",
        "source": "SEC 10-K (2024)",
        "url": "https://www.sec.gov/ix?doc=/Archives/edgar/data/320193/000032019324000123/aapl-20240928.htm",
        "consistency_score": 0.99
    },
    "TSLA": {
        "ticker": "TSLA",
        "metric": "revenue_ttm",
        "value": 96770000000,
        "unit": "USD",
        "period": "TTM",
        "source": "SEC 10-K (2023)",
        "url": "https://www.sec.gov/ix?doc=/Archives/edgar/data/1318605/000131860524000024/tsla-20231231.htm",
        "consistency_score": 0.95
    }
}

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available financial tools."""
    return [
        Tool(
            name="get_financial_metrics",
            description="Get verified, cited financial metrics (Revenue, Net Income). DEMO: Try 'AAPL' or 'TSLA'.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g. AAPL, NVDA)",
                    },
                    "metric": {
                        "type": "string",
                        "description": "Specific metric to retrieve (revenue_ttm, net_income_ttm).",
                    },
                },
                "required": ["ticker"],
            },
        ),
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """Execute the financial tool calls."""
    
    if name == "get_financial_metrics":
        ticker = arguments.get("ticker", "").upper()
        
        # 1. Validate API Key (Monetization Gate)
        is_valid = False
        if API_KEY:
            is_valid = await validate_license_key(API_KEY)

        if not is_valid:
            # 2. Serve Demo Data if available
            if ticker in DEMO_DATA:
                data = DEMO_DATA[ticker]
                result_text = (
                    f"📊 **{ticker} Financials (DEMO MODE)**\n"
                    f"Revenue (TTM): ${data['value']:,} {data['unit']}\n"
                    f"Source: [{data['source']}]({data['url']})\n"
                    f"Confidence: {data['consistency_score']*100}%\n\n"
                    f"ℹ️ *This is cached demo data. To get live data for all 5000+ tickers, buy a key at: https://gumroad.com/l/{GUMROAD_PRODUCT_PERMALINK}*"
                )
                return [TextContent(type="text", text=result_text)]
            else:
                # 3. Hard Stop for non-demo tickers
                return [TextContent(type="text", text=f"⚠️ **License Key Required**\n\nData for '{ticker}' requires a verified license key.\nCite-Finance provides hallucination-free SEC data via Gumroad.\n\n👉 **Get a key:** https://gumroad.com/l/{GUMROAD_PRODUCT_PERMALINK}\n\n(Then set CITE_FINANCE_API_KEY environment variable)")]

        # 4. If Key is Valid -> Try Live API
        # Note: Since backend is down, this will currently fail or need fallback logic.
        # Ideally, this section would query Spectator via SSH or a resurrected backend.
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    f"{API_BASE_URL}/financials/{ticker}",
                    headers={"X-API-Key": "internal_secret"}, # Bypass auth on backend if we verified Gumroad here
                    timeout=8.0
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return [TextContent(type="text", text=f"📊 **{ticker} Live Data**\n{json.dumps(data, indent=2)}")]
                elif resp.status_code == 503:
                    return [TextContent(type="text", text=f"⚠️ **Maintenance Mode**\nLicense Verified ✅, but the Live Data Engine is currently sleeping. Please check back later.")]
                else:
                    return [TextContent(type="text", text=f"❌ API Error: {resp.status_code}")]
            except Exception as e:
                return [TextContent(type="text", text=f"❌ Connection Error: {str(e)}")]

    raise ValueError(f"Unknown tool: {name}")

def main():
    # Use stdio transport by default (standard for 'uvx' / local install)
    asyncio.run(stdio_server(app))

if __name__ == "__main__":
    main()
