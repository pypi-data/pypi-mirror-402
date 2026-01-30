# Glama.ai / Smithery.ai Submission

**Title:**
Cite-Finance: SEC & FRED Data with Citations

**Short Description (140 chars):**
MCP server providing financial metrics from SEC EDGAR (XBRL) and FRED with direct source URLs and provenance metadata.

**Long Description / README:**
A Python-based Model Context Protocol (MCP) server that retrieves verified financial data from primary sources (SEC EDGAR and Federal Reserve Economic Data).

Unlike standard financial APIs that return raw values, **Cite-Finance** returns a structured object containing the value, unit, reporting period, and a **direct URL to the source filing** (e.g., specific 10-K/10-Q report) where the data originated. This enables AI agents to verify data provenance programmatically.

### Capabilities
*   **SEC EDGAR Retrieval:** Fetches XBRL-tagged metrics (Revenue, Net Income, Assets, etc.) directly from filings.
*   **Source Links:** Every response includes `source_url` and `filing_date` for auditability.
*   **Demo Mode:** Access AAPL and TSLA data immediately without an API key.
*   **Live Access:** Full market coverage (5,000+ tickers) requires a license key.

### Tools
*   `get_financial_metrics`: Retrieve specific XBRL tags for a given ticker and period.
*   `get_market_sentiment`: (Beta) Sentiment analysis on recent filings.

### Installation
```bash
uvx cite-finance-mcp
```

### Configuration
The server runs in Demo Mode by default.
To unlock full market access, set the license key environment variable:
`CITE_FINANCE_API_KEY` (Keys available via Gumroad).

**Tags:**
Finance, SEC, EDGAR, Data, XBRL, Stocks, Provenance

**Repository URL:**
https://github.com/[YOUR_USERNAME]/cite-finance-api