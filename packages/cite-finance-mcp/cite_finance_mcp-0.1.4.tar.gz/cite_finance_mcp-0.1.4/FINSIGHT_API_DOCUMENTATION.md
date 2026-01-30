# Cite-Finance API - Complete Documentation

**Version:** 1.0.0
**Production URL:** https://cite-finance-api-prod-a25c5600ed94.herokuapp.com
**Status:** Live & Accepting Users
**Last Updated:** 2025-10-26

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [API Endpoints](#api-endpoints)
4. [Authentication](#authentication)
5. [Pricing & Tiers](#pricing--tiers)
6. [Code Examples](#code-examples)
7. [Database Schema](#database-schema)
8. [Deployment Info](#deployment-info)
9. [Troubleshooting](#troubleshooting)

---

## Overview

Cite-Finance API provides financial data from SEC EDGAR filings with built-in citations, usage tracking, and Stripe billing integration.

### Key Features

- **SEC EDGAR Data:** 10,000+ public companies, 100+ metrics
- **Citations Included:** Every data point links back to SEC filing
- **4-Tier Pricing:** Free to Enterprise ($0-999/month)
- **API Key Auth:** Secure SHA256 hashed keys
- **Rate Limiting:** Redis-backed tier enforcement
- **Stripe Billing:** Automated subscriptions & webhooks

### Tech Stack

- **Backend:** Python 3.11 + FastAPI + uvicorn
- **Database:** PostgreSQL (Heroku essential-0)
- **Cache:** Redis (Heroku mini)
- **Payments:** Stripe
- **Hosting:** Heroku
- **Monitoring:** Prometheus + structlog

---

## Quick Start

### 1. Register for Free Account

```bash
curl -X POST https://cite-finance-api-prod-a25c5600ed94.herokuapp.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@example.com",
    "company_name": "Your Company"
  }'
```

**Response:**
```json
{
  "user_id": "user_xxx",
  "email": "your-email@example.com",
  "tier": "free",
  "api_key": "fsk_xxxxxxxxxxxxxxxxxxxxxxxxx",
  "key_prefix": "fsk_xxxxxxxx",
  "message": "Account created successfully. Save your API key - it won't be shown again!"
}
```

**⚠️ SAVE YOUR API KEY - It's only shown once!**

### 2. Make Your First API Call

```bash
curl -H "X-API-Key: fsk_xxxxxxxxxxxxxxxxxxxxxxxxx" \
  "https://cite-finance-api-prod-a25c5600ed94.herokuapp.com/api/v1/companies/search?q=Apple"
```

**Response:**
```json
{
  "results": [
    {
      "ticker": "AAPL",
      "name": "Apple Inc.",
      "cik": "0000320193"
    }
  ],
  "count": 1
}
```

### 3. Get Financial Data with Citations

```bash
curl -H "X-API-Key: fsk_xxxxxxxxxxxxxxxxxxxxxxxxx" \
  "https://cite-finance-api-prod-a25c5600ed94.herokuapp.com/api/v1/metrics?ticker=AAPL&metrics=revenue"
```

**Response:**
```json
[
  {
    "ticker": "AAPL",
    "metric": "revenue",
    "value": 394328000000,
    "unit": "USD",
    "period": "2023-09-30",
    "citation": {
      "source": "SEC EDGAR",
      "form": "10-K",
      "filing_date": "2023-11-03",
      "accession": "0000320193-23-000077",
      "url": "https://www.sec.gov/cgi-bin/viewer?action=view&cik=0000320193&accession_number=0000320193-23-000077"
    },
    "source": "sec_edgar"
  }
]
```

---

## API Endpoints

### Authentication

#### Register User
```
POST /api/v1/auth/register
```

**Body:**
```json
{
  "email": "user@example.com",
  "company_name": "Optional Company Name",
  "website": "https://optional-website.com"
}
```

**Response:** User object + API key (shown once)

---

#### Create API Key
```
POST /api/v1/auth/keys
Authorization: Bearer {your-api-key}
```

**Body:**
```json
{
  "name": "Production Key",
  "test_mode": false,
  "expires_days": null
}
```

**Response:** New API key (shown once)

---

#### List API Keys
```
GET /api/v1/auth/keys
Authorization: Bearer {your-api-key}
```

**Response:** Array of your API keys (prefixes only, not full keys)

---

#### Revoke API Key
```
DELETE /api/v1/auth/keys/{key_id}
Authorization: Bearer {your-api-key}
```

**Response:** Success/failure message

---

#### Get Current User Info
```
GET /api/v1/auth/me
Authorization: Bearer {your-api-key}
```

**Response:**
```json
{
  "user_id": "user_xxx",
  "email": "user@example.com",
  "tier": "free",
  "status": "active",
  "usage": {
    "api_calls_this_month": 42,
    "api_calls_limit": 100,
    "remaining": 58
  },
  "limits": {
    "rate_limit_per_minute": 10,
    "max_api_keys": 1,
    "data_sources": ["sec"],
    "features": ["basic_metrics"]
  },
  "current_key": {
    "key_prefix": "fsk_xxxxxxxx",
    "name": "Default Key",
    "total_calls": 42
  }
}
```

---

### Financial Data

#### Get Metrics
```
GET /api/v1/metrics?ticker={TICKER}&metrics={METRICS}&period={PERIOD}
Authorization: Bearer {your-api-key}
```

**Parameters:**
- `ticker` (required): Company ticker symbol (e.g., AAPL, MSFT, GOOGL)
- `metrics` (required): Comma-separated list of metrics
- `period` (optional): Specific period (e.g., "2023-Q4")

**Available Metrics:**
- `revenue` - Total revenue
- `netIncome` - Net income
- `totalAssets` - Total assets
- `currentAssets` - Current assets
- `currentLiabilities` - Current liabilities
- `shareholdersEquity` - Shareholders' equity
- `totalDebt` - Total debt
- `cashAndEquivalents` - Cash and equivalents
- `cfo` - Cash from operations
- `cfi` - Cash from investing
- `cff` - Cash from financing
- `grossProfit` - Gross profit
- `operatingIncome` - Operating income

**Example:**
```bash
GET /api/v1/metrics?ticker=AAPL&metrics=revenue,netIncome,totalAssets
```

---

#### List Available Metrics
```
GET /api/v1/metrics/available
```

**Response:**
```json
{
  "metrics": [
    {
      "name": "revenue",
      "description": "Total revenue",
      "unit": "USD"
    },
    ...
  ],
  "periods": [
    "Latest quarter",
    "Specific period (e.g., 2023-Q4)",
    "ttm (Trailing Twelve Months)"
  ]
}
```

---

### Companies

#### Search Companies
```
GET /api/v1/companies/search?q={QUERY}
```

**Parameters:**
- `q` (required): Search query (company name or ticker)

**Example:**
```bash
GET /api/v1/companies/search?q=apple
```

**Response:**
```json
{
  "results": [
    {
      "ticker": "AAPL",
      "name": "Apple Inc.",
      "cik": "0000320193"
    }
  ],
  "count": 1
}
```

---

#### Get Company Info
```
GET /api/v1/companies/{ticker}
```

**Response:**
```json
{
  "ticker": "AAPL",
  "name": "Apple Inc.",
  "cik": "0000320193",
  "data_sources": ["sec_edgar"],
  "available_metrics": ["revenue", "netIncome", ...]
}
```

---

### Billing

#### Get Pricing Info (Public)
```
GET /api/v1/pricing
```

**Response:**
```json
{
  "tiers": {
    "free": {
      "price": "$0/month",
      "limits": {
        "api_calls_per_month": 100,
        "rate_limit_per_minute": 10,
        "max_api_keys": 1,
        "data_sources": ["sec"],
        "features": ["basic_metrics"]
      }
    },
    "starter": {
      "price": "$49/month",
      "limits": {
        "api_calls_per_month": 1000,
        "rate_limit_per_minute": 50,
        "max_api_keys": 3,
        "data_sources": ["sec", "yahoo"],
        "features": ["basic_metrics", "calculations", "ttm"]
      }
    },
    "professional": {
      "price": "$199/month",
      "limits": {
        "api_calls_per_month": 10000,
        "rate_limit_per_minute": 200,
        "max_api_keys": 10,
        "data_sources": ["sec", "yahoo", "alpha_vantage"],
        "features": ["all_metrics", "calculations", "ai_synthesis", "webhooks"]
      }
    },
    "enterprise": {
      "price": "$999/month",
      "limits": {
        "api_calls_per_month": -1,
        "rate_limit_per_minute": 1000,
        "max_api_keys": -1,
        "data_sources": ["all"],
        "features": ["all", "priority_support", "sla", "custom_metrics"]
      }
    }
  }
}
```

---

#### Get Subscription Status
```
GET /api/v1/subscription
Authorization: Bearer {your-api-key}
```

**Response:**
```json
{
  "user_id": "user_xxx",
  "tier": "free",
  "status": "active",
  "api_calls_this_month": 42,
  "api_calls_limit": 100,
  "stripe_subscription_id": null,
  "billing_period_start": null,
  "billing_period_end": null
}
```

---

#### Create Stripe Checkout (Upgrade)
```
POST /api/v1/subscription/checkout
Authorization: Bearer {your-api-key}
```

**Body:**
```json
{
  "tier": "starter",
  "success_url": "https://yoursite.com/success",
  "cancel_url": "https://yoursite.com/cancel"
}
```

**Response:**
```json
{
  "checkout_url": "https://checkout.stripe.com/c/pay/cs_xxx",
  "session_id": "cs_xxx"
}
```

---

#### Cancel Subscription
```
POST /api/v1/subscription/cancel
Authorization: Bearer {your-api-key}
```

**Response:**
```json
{
  "success": true,
  "message": "Subscription will be cancelled at end of billing period"
}
```

---

### Health & Status

#### Health Check
```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "database": "ok",
  "redis": "ok",
  "version": "1.0.0"
}
```

---

#### API Info
```
GET /
```

**Response:**
```json
{
  "name": "Cite-Finance API",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health",
  "pricing": "https://cite-finance.io/pricing"
}
```

---

## Authentication

### API Key Format

API keys use the format: `fsk_` + 32 random characters

Example: `fsk_5UZLE3bBACIodRyp0nAiPwEbEP0vBJ6Y-rQsOtN-haY`

### How to Authenticate

Include your API key in requests using one of these methods:

**Method 1: X-API-Key Header (Recommended)**
```bash
curl -H "X-API-Key: fsk_xxx" https://api.cite-finance.io/v1/metrics?ticker=AAPL
```

**Method 2: Authorization Bearer Header**
```bash
curl -H "Authorization: Bearer fsk_xxx" https://api.cite-finance.io/v1/metrics?ticker=AAPL
```

### Security

- API keys are hashed with SHA256 before storage
- Only the first 12 characters (prefix) are stored in plaintext for display
- Keys cannot be recovered - if lost, create a new one
- Revoked keys are immediately invalidated

---

## Pricing & Tiers

### Tier Comparison

| Feature | Free | Starter | Professional | Enterprise |
|---------|------|---------|--------------|------------|
| **Price** | $0/mo | $49/mo | $199/mo | $999/mo |
| **API Calls/Month** | 100 | 1,000 | 10,000 | Unlimited |
| **Rate Limit** | 10/min | 50/min | 200/min | 1000/min |
| **API Keys** | 1 | 3 | 10 | Unlimited |
| **Data Sources** | SEC only | SEC + Yahoo | SEC + Yahoo + Alpha Vantage | All |
| **Features** | Basic metrics | + TTM, calculations | + AI synthesis, webhooks | + Priority support, SLA |

### Rate Limiting

**Per-Minute Limits:**
- Free: 10 requests/minute
- Starter: 50 requests/minute
- Professional: 200 requests/minute
- Enterprise: 1000 requests/minute

**Monthly Limits:**
- Free: 100 API calls
- Starter: 1,000 API calls
- Professional: 10,000 API calls
- Enterprise: Unlimited

**Rate Limit Headers:**
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 42
X-Monthly-Limit: 100
X-Monthly-Remaining: 58
```

**When Exceeded:**
```json
{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded. Max 10 requests/minute for free tier.",
  "retry_after": 42,
  "upgrade_url": "https://cite-finance.io/pricing"
}
```

---

## Code Examples

### Python

```python
import httpx

API_KEY = "fsk_your_key_here"
BASE_URL = "https://cite-finance-api-prod-a25c5600ed94.herokuapp.com"

# Search for a company
response = httpx.get(
    f"{BASE_URL}/api/v1/companies/search",
    params={"q": "Apple"},
    headers={"X-API-Key": API_KEY}
)
companies = response.json()
print(companies)

# Get financial metrics
response = httpx.get(
    f"{BASE_URL}/api/v1/metrics",
    params={
        "ticker": "AAPL",
        "metrics": "revenue,netIncome,totalAssets"
    },
    headers={"X-API-Key": API_KEY}
)
metrics = response.json()

for metric in metrics:
    print(f"{metric['metric']}: ${metric['value']:,.0f}")
    print(f"  Source: {metric['citation']['form']} filed {metric['citation']['filing_date']}")
    print(f"  URL: {metric['citation']['url']}")
```

---

### JavaScript (Node.js)

```javascript
const axios = require('axios');

const API_KEY = 'fsk_your_key_here';
const BASE_URL = 'https://cite-finance-api-prod-a25c5600ed94.herokuapp.com';

async function getFinancialData(ticker, metrics) {
  const response = await axios.get(`${BASE_URL}/api/v1/metrics`, {
    params: { ticker, metrics: metrics.join(',') },
    headers: { 'X-API-Key': API_KEY }
  });

  return response.data;
}

// Usage
getFinancialData('AAPL', ['revenue', 'netIncome']).then(data => {
  data.forEach(metric => {
    console.log(`${metric.metric}: $${metric.value.toLocaleString()}`);
    console.log(`  Filed: ${metric.citation.filing_date}`);
  });
});
```

---

### cURL

```bash
# Register
curl -X POST https://cite-finance-api-prod-a25c5600ed94.herokuapp.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com"}'

# Search companies
curl -H "X-API-Key: fsk_xxx" \
  "https://cite-finance-api-prod-a25c5600ed94.herokuapp.com/api/v1/companies/search?q=apple"

# Get metrics
curl -H "X-API-Key: fsk_xxx" \
  "https://cite-finance-api-prod-a25c5600ed94.herokuapp.com/api/v1/metrics?ticker=AAPL&metrics=revenue,netIncome"

# Check usage
curl -H "X-API-Key: fsk_xxx" \
  "https://cite-finance-api-prod-a25c5600ed94.herokuapp.com/api/v1/auth/me"
```

---

## Database Schema

### Tables

**users** - User accounts
- `user_id` (PK)
- `email` (unique)
- `tier` (free/starter/professional/enterprise)
- `status` (active/suspended/cancelled/trial)
- `api_calls_this_month`
- `api_calls_limit`
- `stripe_customer_id`
- `stripe_subscription_id`
- `billing_period_start`
- `billing_period_end`

**api_keys** - API authentication keys
- `key_id` (PK)
- `user_id` (FK → users)
- `key_hash` (SHA256, unique)
- `key_prefix` (first 12 chars for display)
- `name`
- `is_active`
- `is_test_mode`
- `total_calls`
- `calls_this_month`
- `last_used_at`
- `expires_at`

**usage_records** - API call logs
- `record_id` (PK)
- `user_id` (FK → users)
- `key_id` (FK → api_keys)
- `endpoint`
- `method`
- `status_code`
- `credits_used`
- `response_time_ms`
- `timestamp`
- `ip_address`
- `user_agent`

**subscription_history** - Audit log
- `id` (PK)
- `user_id` (FK → users)
- `old_tier`
- `new_tier`
- `stripe_subscription_id`
- `stripe_event_id`
- `change_reason` (upgrade/downgrade/cancelled/trial_ended)
- `changed_at`

**webhook_events** - Stripe webhooks
- `id` (PK)
- `event_id` (Stripe event ID, unique)
- `event_type` (subscription.created, etc.)
- `payload` (JSONB)
- `processed`
- `processing_error`
- `received_at`
- `processed_at`

**feature_flags** - Feature access control
- `feature_name` (PK)
- `description`
- `free_tier` (boolean)
- `starter_tier` (boolean)
- `professional_tier` (boolean)
- `enterprise_tier` (boolean)
- `enabled` (global toggle)

---

## Deployment Info

### Production Environment

**Hosting:** Heroku
**App Name:** `cite-finance-api-prod`
**URL:** https://cite-finance-api-prod-a25c5600ed94.herokuapp.com

**Infrastructure:**
- PostgreSQL: Heroku essential-0 (~$5/month)
- Redis: Heroku mini (~$3/month)
- Web Dyno: 1x eco (free tier, 1000 hours/month)

**Total Cost:** ~$8/month

### Environment Variables

```bash
DATABASE_URL=postgres://...  # Auto-set by Heroku
REDIS_URL=rediss://...       # Auto-set by Heroku
SEC_USER_AGENT=Cite-Finance-API/1.0 (cite-finance@production.app)
ALLOWED_ORIGINS=*
DEBUG=false
LOG_LEVEL=INFO
STRIPE_SECRET_KEY=sk_live_xxx  # Optional, for billing
STRIPE_WEBHOOK_SECRET=whsec_xxx  # Optional, for webhooks
```

### Health Status

Check API health:
```bash
curl https://cite-finance-api-prod-a25c5600ed94.herokuapp.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "ok",
  "redis": "ok",
  "version": "1.0.0"
}
```

---

## Troubleshooting

### Common Issues

**Q: My API key doesn't work**
A: Ensure you're including the full key (starts with `fsk_`) in the `X-API-Key` header.

**Q: Getting 429 Rate Limit errors**
A: You've exceeded your tier's rate limit. Check headers for reset time or upgrade tier.

**Q: No data returned for a ticker**
A: Company may not be in SEC database or ticker is incorrect. Use `/companies/search` first.

**Q: Getting 503 Service Unavailable**
A: Database or Redis connection issue. Check `/health` endpoint or contact support.

**Q: Subscription not updating after Stripe payment**
A: Webhook may not have been processed. Check Stripe dashboard for webhook delivery status.

### Error Codes

- `400` - Bad request (missing parameters)
- `401` - Authentication required (missing or invalid API key)
- `403` - Forbidden (feature not available in your tier)
- `404` - Not found (ticker or resource doesn't exist)
- `429` - Rate limit exceeded
- `500` - Internal server error
- `503` - Service unavailable (database/Redis down)

### Support

**Email:** support@cite-finance.io
**GitHub Issues:** (not public yet)
**Status Page:** https://cite-finance-api-prod-a25c5600ed94.herokuapp.com/health

---

## Appendix

### Data Sources

**SEC EDGAR**
- 10,000+ US public companies
- 100+ financial metrics
- Quarterly (10-Q) and annual (10-K) filings
- Real-time filing updates
- Free data source (no licensing costs)

### Roadmap

**Coming Soon:**
- Yahoo Finance integration (market data, prices)
- Alpha Vantage integration (real-time quotes)
- AI-powered financial analysis
- Webhook notifications for new filings
- Custom metric formulas
- GraphQL API endpoint

### Changelog

**v1.0.0** (2025-10-26)
- Initial production release
- SEC EDGAR data source
- 4-tier pricing
- Stripe integration
- API key authentication
- Rate limiting
- Usage tracking
- PostgreSQL + Redis infrastructure

---

**End of Documentation**

For latest updates, visit: https://cite-finance-api-prod-a25c5600ed94.herokuapp.com/docs
