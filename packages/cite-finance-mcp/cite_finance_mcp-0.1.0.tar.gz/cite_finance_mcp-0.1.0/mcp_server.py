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
        
        # 1. Check for API Key (Monetization Gate)
        if not API_KEY:
            # 2. Serve Demo Data if available
            if ticker in DEMO_DATA:
                data = DEMO_DATA[ticker]
                result_text = (
                    f"📊 **{ticker} Financials (DEMO MODE)**\n"
                    f"Revenue (TTM): ${data['value']:,} {data['unit']}\n"
                    f"Source: [{data['source']}]({data['url']})\n"
                    f"Confidence: {data['consistency_score']*100}%\n\n"
                    f"ℹ️ *This is cached demo data. To get live data for all 5000+ tickers, set CITE_FINANCE_API_KEY.*"
                )
                return [TextContent(type="text", text=result_text)]
            else:
                # 3. Hard Stop for non-demo tickers
                return [TextContent(type="text", text=f"⚠️ **API Key Required**\n\nData for '{ticker}' requires a live API key.\nCite-Finance provides hallucination-free SEC data.\n\n👉 **Get a key:** https://cite-finance.io/pricing")]

        # 4. If Key exists, try Live API
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    f"{API_BASE_URL}/financials/{ticker}",
                    headers={"X-API-Key": API_KEY},
                    timeout=8.0
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return [TextContent(type="text", text=f"📊 **{ticker} Live Data**\n{json.dumps(data, indent=2)}")]
                elif resp.status_code == 503:
                    return [TextContent(type="text", text=f"⚠️ **Maintenance Mode**\nThe live API is currently sleeping. Please try the demo tickers (AAPL, TSLA) or check back later.")]
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
