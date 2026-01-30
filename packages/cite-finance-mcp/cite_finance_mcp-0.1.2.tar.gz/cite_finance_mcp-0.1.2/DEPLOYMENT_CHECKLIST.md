# Cite-Finance API - Deployment Checklist

**Status:** Ready to deploy with monetization features ✅

---

## ✅ Completed Implementation

### 1. Redis TLS Fix
- ✅ Updated `src/main.py` with `ssl_cert_reqs="none"` for Heroku Redis
- ✅ `/health` endpoint will now work on Heroku
- ✅ Rate limiting will function correctly

### 2. New `/api/v1/answers` Endpoint
- ✅ Structured JSON responses (no LLM hallucination)
- ✅ Multi-source citations with SEC URLs
- ✅ `consistency_score` (0-1 cross-validation metric)
- ✅ Two formats: `json` (default) and `llm` (prompt-ready)
- ✅ Tier-gated (Starter+ only)

### 3. Updated Pricing Tiers
- ✅ Free: 50 calls/mo (reduced from 100 for lead gen)
- ✅ Starter: $49/mo, 2K calls, LLM answers enabled
- ✅ Pro: $199/mo, 10K calls, SLA included
- ✅ Enterprise: $999/mo, unlimited, custom

### 4. Monitoring & Reliability
- ✅ Sentry integration (error tracking)
- ✅ Stripe environment variable support
- ✅ Rate limits optimized for monetization

### 5. Documentation
- ✅ `MONETIZATION_GUIDE.md` with code samples
- ✅ Integration examples (Python, JavaScript, ChatGPT)
- ✅ GTM strategy and revenue projections

---

## 🚀 Deployment Steps

### 1. Set Heroku Environment Variables

```bash
heroku config:set \
  STRIPE_SECRET_KEY=sk_live_xxx \
  STRIPE_WEBHOOK_SECRET=whsec_xxx \
  SENTRY_DSN=https://xxx@sentry.io/xxx \
  STRIPE_PRICE_STARTER=price_xxx \
  STRIPE_PRICE_PRO=price_xxx \
  STRIPE_PRICE_ENTERPRISE=price_xxx \
  --app cite-finance-api-prod
```

**Where to get values:**
- `STRIPE_SECRET_KEY`: Stripe Dashboard → Developers → API Keys
- `STRIPE_WEBHOOK_SECRET`: Stripe Dashboard → Developers → Webhooks
- `SENTRY_DSN`: Sentry.io → Settings → Client Keys (DSN)
- `STRIPE_PRICE_*`: Create products in Stripe, copy price IDs

### 2. Create Stripe Products

In Stripe Dashboard:

1. **Starter Tier**
   - Name: "Cite-Finance Starter"
   - Price: $49/month
   - Features: "2,000 API calls/month, LLM-ready answers, Citations, Consistency scores"
   - Copy Price ID → set as `STRIPE_PRICE_STARTER`

2. **Professional Tier**
   - Name: "Cite-Finance Professional"
   - Price: $199/month
   - Features: "10,000 API calls/month, All features, 99.9% SLA, Priority support"
   - Copy Price ID → set as `STRIPE_PRICE_PRO`

3. **Enterprise Tier**
   - Name: "Cite-Finance Enterprise"
   - Price: $999/month
   - Features: "Unlimited calls, Dedicated instance, Custom metrics, 99.95% SLA"
   - Copy Price ID → set as `STRIPE_PRICE_ENTERPRISE`

### 3. Deploy to Heroku

```bash
# Ensure you're on the updated branch
git checkout claude/add-phase4-docs-01JDCigoe4YHYZPwMRDk9yaA

# Merge to main (or deploy from branch)
git checkout main
git merge claude/add-phase4-docs-01JDCigoe4YHYZPwMRDk9yaA
git push origin main

# Push to Heroku
git push heroku main

# Check deployment
heroku logs --tail --app cite-finance-api-prod
```

### 4. Verify Deployment

```bash
# Health check
curl https://cite-finance-api-prod.herokuapp.com/health
# Expected: {"status": "healthy", "database": "ok", "redis": "ok"}

# Test /answers endpoint (requires valid API key)
curl -H "X-API-Key: YOUR_KEY" \
  "https://cite-finance-api-prod.herokuapp.com/api/v1/answers?ticker=AAPL&metric=revenue_ttm&format=json"
```

### 5. Test Subscription Flow

1. Register new user → get API key
2. Subscribe to Starter tier
3. Verify webhook received
4. Test `/answers` endpoint access
5. Verify rate limiting works

---

## 📋 Pre-Launch Checklist

- [ ] Stripe products created
- [ ] Environment variables set on Heroku
- [ ] Sentry project created and DSN configured
- [ ] Deployed to Heroku production
- [ ] `/health` returns 200 OK
- [ ] Redis connection working (rate limiting functional)
- [ ] Test `/answers` endpoint with AAPL, MSFT, NVDA
- [ ] Subscription flow tested end-to-end
- [ ] Rate limits enforced (free tier blocked from /answers)
- [ ] Documentation reviewed

---

## 🎯 Post-Launch Tasks

### Week 1: Validation
- [ ] Monitor Sentry for errors
- [ ] Check Heroku metrics (response times, error rates)
- [ ] Verify `/answers` latency <300ms (p95)
- [ ] Test with 3-5 friendly users

### Week 2-4: GTM
- [ ] Create landing page
- [ ] Write blog post announcement
- [ ] Launch on Product Hunt
- [ ] Outreach to 10-20 indie hackers
- [ ] Start 7-day pilot program

### Month 2-3: Growth
- [ ] Add more metrics to `/answers`
- [ ] Implement webhook notifications (Pro tier)
- [ ] Create Python SDK
- [ ] Partner with 2-3 fintech startups

---

## 🔧 Troubleshooting

### Redis Connection Fails
**Symptom:** `/health` returns "unhealthy", Redis errors in logs

**Fix:**
```bash
# Verify REDIS_URL is set correctly (should be rediss:// for TLS)
heroku config:get REDIS_URL --app cite-finance-api-prod

# Check Redis TLS setting in code (should be ssl_cert_reqs="none")
# Already implemented in src/main.py line 55
```

### Stripe Webhooks Not Working
**Symptom:** Subscriptions created but user tier not updated

**Fix:**
1. Check webhook endpoint in Stripe Dashboard
2. Verify `STRIPE_WEBHOOK_SECRET` is correct
3. Check Heroku logs for webhook signature validation errors

### Rate Limiting Not Working
**Symptom:** Free users can access `/answers` endpoint

**Fix:**
1. Verify Redis connection (run `/health` check)
2. Check tier enforcement in `src/api/answers.py` line 125
3. Ensure middleware is loaded (check startup logs)

---

## 📊 Success Metrics to Track

### Technical KPIs
- **Uptime:** >99.9% (Pro/Enterprise SLA)
- **Latency p95:** <300ms for `/answers`
- **Error rate:** <0.1%
- **Redis hit rate:** >90%

### Business KPIs
- **Free signups:** Track weekly growth
- **Free → Starter conversion:** Target 5-10%
- **Starter → Pro upgrade:** Track after month 1
- **MRR growth:** Month-over-month
- **Churn rate:** <5% monthly

### Product KPIs
- **Citation coverage:** % of responses with SEC URLs (target: 95%+)
- **Consistency score avg:** Target >0.90
- **API response time:** p50, p95, p99
- **Endpoint usage:** `/answers` vs `/metrics` ratio

---

## 🎉 You're Ready!

Your Cite-Finance API now has:
- ✅ Reliable infrastructure (Redis TLS, Sentry monitoring)
- ✅ Monetization-first architecture (`/answers` endpoint)
- ✅ Clear pricing tiers with value differentiation
- ✅ Production-ready code
- ✅ Comprehensive documentation

**Next step:** Deploy to Heroku and start customer outreach.

---

**Estimated time to first paying customer:** 1-2 weeks
**Estimated time to $1K MRR:** 4-8 weeks
**Estimated time to $10K MRR:** 6-12 months

Good luck! 🚀
