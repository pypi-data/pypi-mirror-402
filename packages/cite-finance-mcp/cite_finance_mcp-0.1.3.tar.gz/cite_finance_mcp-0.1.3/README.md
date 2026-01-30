# Cite-Finance API

**Production-grade financial data API with AI-powered synthesis**

## Overview

Cite-Finance provides SEC EDGAR data, market data, and financial calculations through a clean REST API with built-in AI synthesis capabilities.

## What Makes Cite-Finance Different

### ✅ Zero Hallucination
Pure structured JSON responses - no LLM inference, no made-up numbers.

### ⚡ Lightning Fast
Sub-300ms p95 latency with 99.9% SLA (Pro tier).

### 📊 Consistency Scores
Cross-source validation gives you a 0-1 confidence metric on every response.

### 🔗 SEC Citations
Every data point includes direct links to source filings - perfect for compliance.

### 🤖 LLM-Ready Format
`format=llm` option returns prompt-ready text snippets with metadata.

### 🛡️ Production Grade
Sentry monitoring, Stripe billing, Redis caching, full observability.

## Architecture

```
cite-finance-api/
├── src/
│   ├── api/          # API routes (FastAPI)
│   ├── core/         # Business logic (calculations, metrics)
│   ├── data_sources/ # Plugin-based data source adapters
│   ├── auth/         # API key management
│   ├── billing/      # Stripe integration, usage tracking
│   ├── middleware/   # Rate limiting, auth
│   ├── models/       # Pydantic models
│   └── utils/        # Shared utilities
├── tests/            # Test suite
├── docs/             # API documentation
└── config/           # Configuration files
```

## Quick Start

### Installation
```bash
pip install -r requirements.txt
```

### Configuration
```bash
cp .env.example .env
# Edit .env with your API keys
```

### Run
```bash
uvicorn src.main:app --reload
```

### API Documentation
Once running, visit: http://localhost:8000/docs

## Pricing

| Tier | Price | Calls/Month | Key Features |
|------|-------|-------------|--------------|
| **Free** | $0 | 50 | Basic metrics, testing |
| **Starter** | $49 | 2,000 | **LLM answers**, citations, consistency |
| **Professional** | $199 | 10,000 | All features, **99.9% SLA** |
| **Enterprise** | $999 | Unlimited | Custom metrics, dedicated support |

## Quick Start

### 1. Get Your API Key

```bash
curl -X POST https://api.cite-finance.io/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "you@company.com"}'
```

### 2. Make Your First Request

```bash
curl -H "X-API-Key: your_key" \
  "https://api.cite-finance.io/api/v1/answers?ticker=AAPL&metric=revenue_ttm&format=json"
```

### 3. Get Structured, Cited Data

```json
{
  "ticker": "AAPL",
  "metric": "revenue_ttm",
  "value": 383285000000,
  "unit": "USD",
  "period": "TTM",
  "as_of": "2024-09-30",
  "sources": [
    {
      "type": "sec_filing",
      "filing": "10-K",
      "url": "https://www.sec.gov/...",
      "excerpt": "Total net sales: $383,285 million"
    }
  ],
  "consistency_score": 0.96,
  "retrieved_at": "2025-11-24T12:00:00Z"
}
```

**Key Benefits:**
- ✅ Structured JSON (no hallucination)
- ✅ SEC citations with URLs
- ✅ 96% consistency score
- ✅ Sub-300ms response time

## Use Cases

- **AI Chatbots**: Financial Q&A with verified sources
- **Trading Bots**: High-confidence data for algorithmic trading
- **Dashboards**: Real-time financial metrics with citations
- **Research Tools**: Compliance-ready data with SEC links

## Documentation

- [API Docs](https://api.cite-finance.io/docs)
- [Monetization Guide](./MONETIZATION_GUIDE.md)
- [Deployment Guide](./DEPLOYMENT_CHECKLIST.md)
- [Integration Examples](./MONETIZATION_GUIDE.md#integration-examples)

## Built For

LLM-first financial applications that need:
- Structured data (no hallucination)
- Verified sources (SEC citations)
- High confidence (consistency scores)
- Production speed (<300ms)

---

**Ready to launch?** See [DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md)

## License

Proprietary - All Rights Reserved
