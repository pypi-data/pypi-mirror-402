# Cite-Finance API - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### 1. Clone & Install
```bash
cd /path/to/cite-finance-api
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your credentials
```

**Minimum Required:**
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis connection
- `STRIPE_SECRET_KEY` - Stripe API key

### 3. Initialize Database
```bash
# Start PostgreSQL and Redis (via Docker Compose)
docker-compose up -d db redis

# Apply schema
psql $DATABASE_URL < config/database_schema.sql
```

### 4. Run API
```bash
uvicorn src.main:app --reload
```

**API will be available at:** http://localhost:8000

### 5. Test API
```bash
# View API docs
open http://localhost:8000/docs

# Health check
curl http://localhost:8000/health

# Example: Get Apple's revenue
curl -H "X-API-Key: your-test-key" \
  "http://localhost:8000/api/v1/metrics?ticker=AAPL&metrics=revenue"
```

## 📊 Example Usage

### Create API Key
```python
import asyncio
import asyncpg
from src.auth.api_keys import APIKeyManager

async def create_key():
    pool = await asyncpg.create_pool("postgresql://localhost/cite-finance")
    manager = APIKeyManager(pool)
    
    # Create demo user first (manual SQL)
    key, api_key_obj = await manager.create_api_key(
        user_id="demo_user_123",
        name="Development Key"
    )
    
    print(f"API Key: {key}")  # Save this, won't be shown again!
    print(f"Prefix: {api_key_obj.key_prefix}")

asyncio.run(create_key())
```

### Fetch Financial Data
```python
import httpx

API_KEY = "fsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
API_URL = "http://localhost:8000"

# Get multiple metrics
response = httpx.get(
    f"{API_URL}/api/v1/metrics",
    params={
        "ticker": "AAPL",
        "metrics": "revenue,netIncome,totalAssets"
    },
    headers={"X-API-Key": API_KEY}
)

data = response.json()
for metric in data:
    print(f"{metric['metric']}: ${metric['value']:,.0f} ({metric['period']})")
```

## 🔑 API Key Tiers

| Tier | Calls/Month | Rate Limit | Price |
|------|-------------|------------|-------|
| Free | 100 | 10/min | $0 |
| Starter | 1,000 | 50/min | $49/mo |
| Professional | 10,000 | 200/min | $199/mo |
| Enterprise | Unlimited | 1000/min | $999/mo |

## 📚 Available Endpoints

### Metrics API
- `GET /api/v1/metrics` - Get financial metrics
- `GET /api/v1/metrics/available` - List available metrics

### Companies API
- `GET /api/v1/companies/search` - Search companies
- `GET /api/v1/companies/{ticker}` - Company details

### Subscriptions API
- `POST /api/v1/subscriptions/create` - Create subscription
- `POST /api/v1/subscriptions/cancel` - Cancel subscription
- `GET /api/v1/subscriptions/status` - Get subscription status

### Auth API
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/keys` - Create API key
- `GET /api/v1/auth/keys` - List API keys
- `DELETE /api/v1/auth/keys/{key_id}` - Revoke API key

## 🎯 Next Steps

1. **Set up Stripe** - Configure products and webhooks
2. **Add data sources** - Extend with Yahoo Finance, Alpha Vantage
3. **Deploy** - Follow DEPLOYMENT.md for production setup
4. **Monitor** - Set up Sentry, Datadog, or Prometheus

## 🆘 Troubleshooting

**Database connection failed:**
```bash
# Check PostgreSQL is running
docker-compose ps
docker-compose logs db
```

**Redis connection failed:**
```bash
# Check Redis is running
redis-cli ping
```

**API key invalid:**
```bash
# Verify key in database
psql $DATABASE_URL -c "SELECT key_prefix, is_active FROM api_keys;"
```

## 📖 Documentation

- **API Docs:** http://localhost:8000/docs
- **Deployment Guide:** DEPLOYMENT.md
- **Architecture:** README.md
- **Database Schema:** config/database_schema.sql

## 💰 Monetization Checklist

- [ ] Configure Stripe products & prices
- [ ] Set up webhook endpoint
- [ ] Create pricing page
- [ ] Add Stripe Checkout
- [ ] Test subscription flow
- [ ] Monitor revenue in Stripe Dashboard

## 🎉 You're Ready!

Your Cite-Finance API is now running. Start monetizing your financial data!

Questions? Email: support@cite-finance.io
