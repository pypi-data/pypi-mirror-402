# Cite-Finance API - Launch Materials

## Product Hunt Launch

### Title
Cite-Finance API - LLM-ready financial data with SEC citations

### Tagline
Stop hallucinating. Start citing sources.

### Description

**What is Cite-Finance?**

Cite-Finance is a financial data API optimized for LLM applications. Unlike traditional APIs that return raw data, we return **structured, cited answers** with cross-source validation.

**The Problem:**
- LLMs hallucinate financial numbers
- Traditional APIs require complex parsing
- No way to verify data sources
- Slow response times kill UX

**Our Solution:**
✅ Structured JSON (no LLM inference needed)
✅ SEC citations with direct URLs
✅ Consistency scores (0-1 validation metric)
✅ Sub-300ms p95 latency
✅ LLM-ready format option

**Perfect For:**
- Financial chatbots & AI assistants
- Trading bots requiring verified data
- Compliance tools needing source citations
- Real-time dashboards

**Example:**
```python
# One API call
response = cite-finance.get("AAPL", "revenue_ttm")

# Returns:
{
  "value": 383285000000,
  "sources": [{"filing": "10-K", "url": "..."}],
  "consistency_score": 0.96  # 96% confidence
}
```

**Pricing:**
- Free: 50 calls/mo
- Starter: $49/mo - 2K calls, LLM answers
- Pro: $199/mo - 10K calls, 99.9% SLA
- Enterprise: Custom

**Try it now:** https://api.cite-finance.io

---

### First Comment (Post-Launch)

Hey Product Hunt! 👋

I'm the creator of Cite-Finance API. Here's why I built this:

**The Backstory:**
I was building a financial AI chatbot and realized LLMs constantly hallucinate numbers. Even when I fed them real data, there was no way for users to verify sources.

**What Makes Cite-Finance Different:**
1. **No Hallucination**: Pure structured data, no LLM inference
2. **Verifiable**: Every number links to an SEC filing
3. **Confidence Scores**: Cross-source validation (0-1 metric)
4. **Fast**: <300ms response time

**Who Is This For:**
- Building a financial chatbot? ✅
- Need verifiable data for compliance? ✅
- Want to avoid LLM hallucination? ✅

**What I'd Love Feedback On:**
- Is $49/mo reasonable for 2K calls?
- What metrics would YOU want to see?
- Would you use the LLM-ready format?

Try it free (50 calls): https://api.cite-finance.io/docs

Happy to answer any questions!

---

## Twitter Launch Thread

### Tweet 1 (Hook)
🚀 Launching Cite-Finance API – LLM-ready financial data with SEC citations

Stop hallucinating. Start citing sources.

Sub-300ms responses. 0.96 consistency scores. Production-ready.

Free tier: 50 calls/mo
Paid: Starting at $49/mo

https://api.cite-finance.io

🧵 Here's why it matters...

### Tweet 2 (Problem)
The problem with financial LLMs:

❌ They hallucinate numbers
❌ No source verification
❌ Slow response times
❌ Complex data parsing

Building a financial chatbot? You need VERIFIED data, not guesses.

### Tweet 3 (Solution)
Cite-Finance solves this with:

✅ Structured JSON (no LLM inference)
✅ Direct SEC citations
✅ Consistency scores (cross-validation)
✅ <300ms latency
✅ LLM-ready format

One API call. Verified data. Done.

### Tweet 4 (Example)
Here's what you get:

```json
{
  "ticker": "AAPL",
  "value": 383285000000,
  "sources": [{
    "filing": "10-K",
    "url": "sec.gov/..."
  }],
  "consistency_score": 0.96
}
```

96% confidence. Direct citation. 200ms response.

### Tweet 5 (Use Cases)
Perfect for:

🤖 Financial chatbots
📊 Trading bots
📈 Real-time dashboards
📝 Compliance tools

Used by developers building LLM-first financial apps.

### Tweet 6 (Pricing/CTA)
Pricing:
• Free: 50 calls/mo
• Starter: $49/mo (2K calls)
• Pro: $199/mo (10K calls + SLA)
• Enterprise: Custom

Start free: https://api.cite-finance.io

Built for developers who need verifiable financial data.

RT if useful! 🔄

---

## Reddit Posts

### r/SideProject

**Title:** Built Cite-Finance API - LLM-ready financial data with SEC citations

**Post:**

Hey r/SideProject! 👋

I just launched **Cite-Finance API** - a financial data API optimized for LLM applications.

**What it does:**
Returns structured, cited financial data in <300ms. Every response includes:
- Direct SEC filing citations
- Consistency scores (cross-source validation)
- LLM-ready format option

**Why I built it:**
I was building a financial chatbot and LLMs kept hallucinating numbers. Even with real data, users couldn't verify sources. Cite-Finance solves this.

**Example response:**
```json
{
  "ticker": "AAPL",
  "metric": "revenue_ttm",
  "value": 383285000000,
  "sources": [{"filing": "10-K", "url": "https://sec.gov/..."}],
  "consistency_score": 0.96
}
```

**Pricing:**
- Free: 50 calls/mo
- Starter: $49/mo (2K calls)
- Pro: $199/mo (10K calls + SLA)

**Looking for:**
- Early adopter feedback
- Feature requests
- Beta testers

**Try it:** https://api.cite-finance.io

Would love your thoughts! What metrics would you want to see?

---

### r/LangChain

**Title:** [Tool] Cite-Finance API - Verifiable financial data for LLM agents

**Post:**

For anyone building financial agents with LangChain:

I built **Cite-Finance API** to solve the hallucination problem with financial data.

**Key features for agents:**
- Structured JSON (no parsing needed)
- SEC citations with URLs
- Consistency scores (0-1 validation)
- `format=llm` option for prompt injection

**Example integration:**
```python
from langchain.tools import Tool

def get_financial_fact(query: str) -> str:
    response = cite-finance.get(ticker, metric, format="llm")
    return response["prompt_snippet"]

financial_tool = Tool(
    name="FinancialData",
    func=get_financial_fact,
    description="Get verified financial data with citations"
)
```

**Why it's useful:**
- No hallucination (pure data)
- Verifiable sources (SEC URLs)
- Fast (<300ms)

Free tier: 50 calls/mo
Docs: https://api.cite-finance.io/docs

Feedback welcome!

---

## Hacker News (Show HN)

**Title:** Show HN: Cite-Finance API – LLM-ready financial data with SEC citations

**Post:**

Hey HN,

I built Cite-Finance API (https://api.cite-finance.io) - a financial data API optimized for LLM applications.

**Backstory:**
I was building a financial AI assistant and kept running into two problems:
1. LLMs hallucinate numbers constantly
2. Even with real data, there was no way for users to verify sources

Traditional financial APIs (Alpha Vantage, Polygon, etc.) return raw data dumps. You still need to parse, validate, and format them for LLM consumption.

**What Cite-Finance does differently:**
- Returns structured, citation-backed answers (not raw data)
- Every number includes a direct SEC filing link
- Cross-source validation with consistency scores (0-1)
- Sub-300ms p95 latency
- Optional LLM-ready format for prompt injection

**Example:**
```
GET /api/v1/answers?ticker=AAPL&metric=revenue_ttm

{
  "value": 383285000000,
  "sources": [{"filing": "10-K", "url": "..."}],
  "consistency_score": 0.96,
  "retrieved_at": "2025-11-24T12:00:00Z"
}
```

**Tech stack:**
- FastAPI + async/await
- Redis for caching & rate limiting
- PostgreSQL for usage tracking
- Stripe for billing
- Sentry for monitoring

**Pricing:**
- Free: 50 calls/mo
- Paid: $49-$999/mo

**Questions I'd love feedback on:**
1. Is the `consistency_score` actually useful?
2. Would you use this vs. building on yfinance yourself?
3. What other metrics would be valuable?

Code is open for inspection (with some proprietary bits): https://github.com/Spectating101/cite-finance-api

Thanks for checking it out!

---

## Email Outreach Template

**Subject:** Cite-Finance API - Verifiable financial data for [USE_CASE]

Hi [NAME],

I saw you're working on [THEIR_PROJECT] and thought you might find Cite-Finance API useful.

**Quick pitch:**
LLM-ready financial data with SEC citations in <300ms.

**What makes it different:**
✅ Structured JSON (no hallucination)
✅ Direct SEC filing links
✅ Consistency scores (cross-validation)
✅ Production-ready (99.9% SLA)

**Example:**
```
GET /answers?ticker=AAPL&metric=revenue_ttm

Returns:
- Value: $383B
- Source: 10-K filing (with URL)
- Confidence: 96%
- Latency: 200ms
```

**Free tier:** 50 calls/mo to test
**Paid:** $49/mo for 2K calls

Would you be interested in a 7-day pilot? Happy to help with integration.

Docs: https://api.cite-finance.io/docs

Best,
[YOUR_NAME]

---

## Launch Checklist

- [ ] Post on Product Hunt (morning Pacific Time)
- [ ] Post Twitter thread
- [ ] Post to r/SideProject
- [ ] Post to r/LangChain
- [ ] Post to Hacker News (Show HN)
- [ ] Email 10-20 potential customers
- [ ] Monitor feedback and respond quickly
- [ ] Track signups in Stripe dashboard
- [ ] Update landing page based on feedback

**Goal:** 50 signups in first week
**Stretch goal:** 3-5 paying customers in first month

---

Built with 💪 by someone who was tired of LLMs making up financial numbers.
