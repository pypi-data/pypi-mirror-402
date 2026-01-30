# Cite-Finance API - Monetization & Integration Guide

**LLM-ready, cited financial answers in <300ms**

---

## 🎯 Value Proposition

Cite-Finance provides **structured, cited financial data optimized for LLM consumption** - no hallucination, no free-form text, just facts with sources.

**Key Differentiators:**
- ✅ Structured JSON (no LLM inference needed)
- ✅ Multi-source citations with URLs
- ✅ Consistency scores (cross-validation)
- ✅ Sub-300ms response time
- ✅ LLM-ready format option

---

## 💰 Pricing (Updated)

| Tier | Price | Calls/Month | Key Features | Best For |
|------|-------|-------------|--------------|----------|
| **Free** | $0 | 50 | Basic metrics only | Testing & POC |
| **Starter** | $49/mo | 2,000 | LLM answers + citations | Indie devs, chatbots |
| **Professional** | $199/mo | 10,000 | All features + SLA | Production apps |
| **Enterprise** | $999/mo | Unlimited | Custom + dedicated | Large orgs |

**New Pricing Optimizations:**
- Free tier reduced to 50 calls (lead gen focus)
- Starter gets **LLM answers** (main monetization wedge)
- Pro includes **SLA** (99.9% uptime, 300ms p95 latency)
- Enterprise gets dedicated support + custom metrics

---

## 🚀 Quick Start

### 1. Get API Key

```bash
curl -X POST https://api.cite-finance.io/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "you@company.com",
    "company_name": "Your Startup"
  }'
```

**Response:**
```json
{
  "api_key": "fsk_1234567890abcdef",
  "user_id": "usr_xyz",
  "tier": "free"
}
```

### 2. Make Your First Request

```bash
curl -H "X-API-Key: fsk_1234567890abcdef" \
  "https://api.cite-finance.io/api/v1/answers?ticker=AAPL&metric=revenue_ttm&format=json"
```

**Response:**
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
      "url": "https://www.sec.gov/cgi-bin/viewer?action=view&cik=0000320193&accession_number=0000320193-24-000123",
      "excerpt": "Total net sales: $383,285 million"
    }
  ],
  "consistency_score": 0.96,
  "retrieved_at": "2025-11-24T12:00:00Z"
}
```

---

## 📚 API Endpoints

### `/api/v1/answers` - LLM-Ready Answers (Starter+)

**The main monetization endpoint** - structured, cited financial data.

#### JSON Format (Default)

```python
import requests

response = requests.get(
    "https://api.cite-finance.io/api/v1/answers",
    params={
        "ticker": "NVDA",
        "metric": "revenue_ttm",
        "format": "json"
    },
    headers={"X-API-Key": "your_api_key"}
)

data = response.json()
print(f"{data['ticker']} revenue: ${data['value']:,.0f}")
print(f"Confidence: {data['consistency_score']:.0%}")
print(f"Source: {data['sources'][0]['url']}")
```

#### LLM Format (for prompts)

```python
response = requests.get(
    "https://api.cite-finance.io/api/v1/answers",
    params={
        "ticker": "AAPL",
        "metric": "net_income_ttm",
        "format": "llm"  # Returns formatted text
    },
    headers={"X-API-Key": "your_api_key"}
)

result = response.json()
print(result["prompt_snippet"])
```

**Output:**
```
**AAPL - net_income_ttm**
Value: 96,995,000,000 USD
Period: TTM
As of: 2024-09-30
Confidence: 96%

**Sources:**
1. 10-K filing
   URL: https://www.sec.gov/...
```

#### Available Metrics

| Metric | Description | Tier Required |
|--------|-------------|---------------|
| `revenue_ttm` | Trailing 12-month revenue | Starter |
| `revenue_latest` | Most recent quarter revenue | Starter |
| `net_income_ttm` | TTM net income | Starter |
| `total_assets` | Latest total assets | Starter |
| `shareholders_equity` | Latest equity | Starter |
| `cash_equivalents` | Cash & equivalents | Starter |
| `total_debt` | Total debt | Professional |
| `operating_income_ttm` | TTM operating income | Professional |

---

### `/api/v1/metrics` - Basic Metrics (Free+)

Legacy endpoint for simple metric queries.

```bash
curl -H "X-API-Key: your_key" \
  "https://api.cite-finance.io/api/v1/metrics?ticker=MSFT&metrics=revenue,netIncome&period=2023-Q4"
```

---

## 🔧 Integration Examples

### ChatGPT Plugin / Custom GPT

```python
def get_financial_fact(ticker: str, metric: str) -> str:
    """Fetch verified financial data for LLM context."""
    response = requests.get(
        "https://api.cite-finance.io/api/v1/answers",
        params={"ticker": ticker, "metric": metric, "format": "llm"},
        headers={"X-API-Key": os.getenv("FINSIGHT_API_KEY")}
    )

    if response.status_code == 200:
        return response.json()["prompt_snippet"]
    else:
        return f"Error: {response.json()['detail']}"

# Use in your GPT prompt
context = get_financial_fact("AAPL", "revenue_ttm")
prompt = f"Given this data:\n{context}\n\nAnalyze Apple's revenue trend..."
```

### Financial Dashboard

```javascript
// React component
const FinancialWidget = ({ ticker }) => {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetch(`https://api.cite-finance.io/api/v1/answers?ticker=${ticker}&metric=revenue_ttm`, {
      headers: { 'X-API-Key': process.env.FINSIGHT_KEY }
    })
    .then(r => r.json())
    .then(setData);
  }, [ticker]);

  if (!data) return <div>Loading...</div>;

  return (
    <div>
      <h3>{data.ticker} Revenue (TTM)</h3>
      <p className="value">${(data.value / 1e9).toFixed(1)}B</p>
      <p className="source">
        Source: <a href={data.sources[0].url}>{data.sources[0].filing}</a>
      </p>
      <p className="confidence">Confidence: {(data.consistency_score * 100).toFixed(0)}%</p>
    </div>
  );
};
```

### Trading Bot

```python
class FinancialDataFetcher:
    """Fetch verified financial data for trading decisions."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.cite-finance.io/api/v1"

    def get_metric(self, ticker: str, metric: str) -> dict:
        """Get single metric with source validation."""
        response = requests.get(
            f"{self.base_url}/answers",
            params={"ticker": ticker, "metric": metric},
            headers={"X-API-Key": self.api_key}
        )
        response.raise_for_status()
        return response.json()

    def is_high_confidence(self, data: dict, threshold: float = 0.9) -> bool:
        """Check if data meets confidence threshold."""
        return data["consistency_score"] >= threshold

# Use in trading logic
fetcher = FinancialDataFetcher(os.getenv("FINSIGHT_KEY"))
revenue_data = fetcher.get_metric("AAPL", "revenue_ttm")

if fetcher.is_high_confidence(revenue_data):
    # Make trading decision based on verified data
    pass
```

---

## 🎨 Use Cases & Target Customers

### 1. **AI Chatbots** ($49-$199/mo)
- Financial Q&A bots
- Portfolio assistants
- Investment advisors

**Value:** Cited, verifiable answers (no hallucination risk)

### 2. **Financial Dashboards** ($199/mo)
- Company analysis tools
- Portfolio trackers
- Investment platforms

**Value:** Sub-300ms latency + SLA guarantee

### 3. **Trading Systems** ($199-$999/mo)
- Algorithmic trading
- Risk analysis
- Fundamental screening

**Value:** Consistency scores + multi-source validation

### 4. **Enterprise Analytics** ($999+/mo)
- Custom metrics
- Dedicated instances
- White-label options

**Value:** Custom SLA + dedicated support

---

## 📊 GTM Strategy

### Landing Page Messaging

**Hero:**
> "LLM-ready, cited financial answers in 300ms"
>
> Stop hallucinating. Start citing sources.

**Code Snippet (above the fold):**
```python
# One line to get verified financial data
response = cite-finance.get("AAPL", "revenue_ttm")
# ✅ Structured JSON
# ✅ SEC citations
# ✅ 0.96 consistency score
```

**CTA:** "Start Free Trial" → 50 free calls, upgrade to Starter in checkout

### Outreach Targets

1. **Indie Hackers** building financial chatbots
   - Reddit: r/SideProject, r/Entrepreneur
   - Twitter: #buildinpublic, #indiehackers

2. **Fintech Startups** needing reliable data
   - YC companies (finance vertical)
   - Product Hunt launches
   - Indie VC portfolio

3. **AI Companies** building financial agents
   - LangChain community
   - AutoGen users
   - ChatGPT plugin developers

### Success Metrics (7-14 day pilot)

- **Citation coverage:** % of responses with SEC URLs
- **Latency p95:** <300ms for /answers endpoint
- **Consistency:** >90% cross-source agreement
- **Developer NPS:** >50

---

## 🔐 Heroku Deployment

### Environment Variables

```bash
# Set on Heroku
heroku config:set \
  STRIPE_SECRET_KEY=sk_live_xxx \
  STRIPE_WEBHOOK_SECRET=whsec_xxx \
  SENTRY_DSN=https://xxx@sentry.io/xxx \
  STRIPE_PRICE_STARTER=price_xxx \
  STRIPE_PRICE_PRO=price_xxx \
  STRIPE_PRICE_ENTERPRISE=price_xxx \
  --app cite-finance-api-prod
```

### Health Check

```bash
curl https://cite-finance-api-prod.herokuapp.com/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "database": "ok",
  "redis": "ok",
  "version": "1.0.0"
}
```

---

## 📈 Revenue Projections

### Conservative (12 months)

| Month | Free Users | Starter | Pro | MRR |
|-------|-----------|---------|-----|-----|
| 1 | 50 | 2 | 0 | $98 |
| 3 | 200 | 10 | 2 | $888 |
| 6 | 500 | 30 | 8 | $3,062 |
| 12 | 1000 | 60 | 20 | $6,920 |

**12-Month ARR:** ~$83K

### Optimistic (12 months)

| Month | Free Users | Starter | Pro | MRR |
|-------|-----------|---------|-----|-----|
| 1 | 100 | 5 | 1 | $444 |
| 3 | 500 | 25 | 5 | $2,220 |
| 6 | 1500 | 75 | 15 | $6,660 |
| 12 | 3000 | 150 | 40 | $15,310 |

**12-Month ARR:** ~$184K

---

## ✅ Next Steps

1. **Deploy to Heroku** (with updated env vars)
2. **Test /answers endpoint** (AAPL, MSFT, NVDA)
3. **Create landing page** (1-page with code snippet)
4. **Launch on Product Hunt** (tag: finance, API, LLM)
5. **Outreach** (5-10 indie hackers building financial tools)
6. **Pilot program** (7-14 days, track success metrics)

---

**Status:** Ready to monetize ✅

Built for LLM-first financial applications.
