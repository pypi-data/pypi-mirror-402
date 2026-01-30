# Cite-Finance-MCP: Execution Masterplan to $10k/mo

**Product:** Python MCP Server for financial data with citations  
**Status:** Live on PyPI v0.1.0, Gumroad logic added (not pushed)  
**Competitor:** Financial Datasets MCP (735 stars)  
**Constraints:** No Ads, No Community Building, No Hosting Costs  
**Goal:** $10,000/mo in 90 days

---

## 🎯 Strategic Positioning: "Zero Hallucination Financial Data"

### Core Value Proposition
> "The only MCP server that **proves** every number with SEC citations. Built for Claude Desktop users who refuse to trust AI guesses with their money."

### Competitive Advantage vs Financial Datasets MCP
| Factor | Financial Datasets MCP | Cite-Finance-MCP | Winner |
|--------|----------------------|------------------|---------|
| **Data Coverage** | 735 stars, broad | Focused (SEC + citations) | Them (breadth) |
| **Hallucination Risk** | Unknown/High | Zero (provenance) | **Us** |
| **Trust Layer** | Missing | SEC URLs + consistency score | **Us** |
| **MCP Native** | Yes | Yes | Tie |
| **Monetization** | Unknown | Gumroad (serverless) | **Us** |

**Wedge Strategy:** Position as "Premium Alternative" - they're Walmart, we're Whole Foods.

---

## 🏗️ Technical Architecture: Serverless Monetization

### Problem: No Backend, No Hosting Budget
**Solution:** Hybrid Static + Spectator tunnel architecture

### Architecture: 3-Tier Data Serving

```
┌─────────────────────────────────────────────────────────────┐
│ TIER 1: Demo Data (FREE - Built into MCP Package)          │
├─────────────────────────────────────────────────────────────┤
│ • Static JSON embedded in mcp_server.py                    │
│ • 5-10 tickers (AAPL, MSFT, NVDA, TSLA, GOOGL)            │
│ • Last 2 years of quarterly data                           │
│ • Purpose: Hook users, showcase citations                   │
│ • Cost: $0 (bundled in PyPI package)                       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ TIER 2: Extended Cache (PAID - Gumroad $29 one-time)      │
├─────────────────────────────────────────────────────────────┤
│ • Static parquet file (~50MB) downloaded post-purchase     │
│ • 500 tickers x 5 years of data                            │
│ • Delivered via Gumroad file delivery                       │
│ • User stores locally, MCP reads from disk                  │
│ • Update: New file every quarter ($9 update fee)           │
│ • Cost: $0 hosting (user-side storage)                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ TIER 3: Live API (PAID - Gumroad $99/mo subscription)     │
├─────────────────────────────────────────────────────────────┤
│ • SSH tunnel to Spectator node (100.96.62.97)             │
│ • Real-time SEC scraping on-demand                          │
│ • Unlimited tickers, latest filings                         │
│ • User provides SSH key, we provision Spectator access      │
│ • Cost: $0 (Spectator already running 24/7)                │
└─────────────────────────────────────────────────────────────┘
```

### Implementation Details

#### Tier 1: Demo Data (Already Built)
```python
# mcp_server.py (current)
DEMO_DATA = {
    "AAPL": {"revenue_ttm": 383285000000, "source": "SEC 10-K", "url": "..."},
    "TSLA": {"revenue_ttm": 96770000000, "source": "SEC 10-K", "url": "..."}
}
```

**Enhancement:** Expand to 10 tickers, add more metrics (net_income, cash, debt).

#### Tier 2: Extended Static Cache (NEW)
```python
# mcp_server.py (add)
CACHE_PATH = os.path.expanduser("~/.cite-finance/financial_data.parquet")

def load_cache():
    if os.path.exists(CACHE_PATH):
        return pd.read_parquet(CACHE_PATH)
    return None

# On first paid user request
if not API_KEY and not os.path.exists(CACHE_PATH):
    return "Buy Extended Cache: https://gumroad.com/l/cite-finance-cache"
```

**Delivery Workflow:**
1. User buys on Gumroad ($29)
2. Gumroad emails download link (financial_data.parquet)
3. User downloads, places in `~/.cite-finance/`
4. MCP auto-detects and uses local cache
5. Zero server cost

#### Tier 3: Live Spectator Tunnel (NEW)
```python
# mcp_server.py (add)
SPECTATOR_ENABLED = os.getenv("CITE_SPECTATOR_KEY") is not None

async def fetch_from_spectator(ticker: str, metric: str) -> dict:
    """SSH into Spectator, scrape SEC on-demand."""
    ssh_key = os.getenv("CITE_SPECTATOR_KEY")
    
    # SSH to spectator
    result = subprocess.run([
        "ssh", "-i", ssh_key, 
        "spectator@100.96.62.97",
        f"python3 /home/spectator/scrapers/sec_query.py {ticker} {metric}"
    ], capture_output=True, timeout=30)
    
    return json.loads(result.stdout)
```

**Provisioning Workflow:**
1. User buys $99/mo subscription on Gumroad
2. Gumroad webhook → Lambda → Generate SSH key for user
3. Email user: "Set CITE_SPECTATOR_KEY=/path/to/key.pem"
4. MCP detects key, enables live mode
5. Cost: $0 (Spectator capacity already exists)

---

## 💰 Monetization: Gumroad-Only (Serverless)

### Why Gumroad (not Stripe/Paddle)
- ✅ No webhook server needed (email-based delivery)
- ✅ Handles VAT/sales tax automatically
- ✅ File delivery built-in (for Tier 2 cache)
- ✅ Subscription support (for Tier 3)
- ✅ 10% fee (vs Stripe 2.9% + $0.30 + webhook infra)

### Pricing Strategy

| Tier | Price | Value | Target |
|------|-------|-------|--------|
| **Demo** | Free | 10 tickers, 2 years | Hook users |
| **Extended Cache** | $29 one-time | 500 tickers, 5 years | Indie devs |
| **Cache Updates** | $9/quarter | Latest filings | Retention |
| **Live API** | $99/mo | Unlimited, real-time | Pro users |
| **Enterprise** | $499/mo | White-label + support | Companies |

### Revenue Model Math

**Conservative (90 Days):**
```
Month 1: 1000 installs → 20 cache ($580) + 2 live ($198) = $778
Month 2: 2000 installs → 40 cache ($1160) + 5 live ($495) = $1655
Month 3: 3500 installs → 70 cache ($2030) + 10 live ($990) = $3020

Total Revenue: $5,453 (54% of goal)
```

**Aggressive (90 Days):**
```
Month 1: 2000 installs → 40 cache ($1160) + 4 live ($396) = $1556
Month 2: 5000 installs → 100 cache ($2900) + 12 live ($1188) = $4088
Month 3: 10000 installs → 200 cache ($5800) + 25 live ($2475) = $8275

Total Revenue: $13,919 (139% of goal) ✅
```

**Key Assumption:** 2% conversion to paid (industry standard for dev tools).

---

## 🚀 Traffic Strategy: Zero Community Building

### Constraint Interpretation
"No community building" = No Discord, No Twitter replies, No support forums.

**Allowed:** SEO, Documentation, Registry optimization, One-way content.

### Traffic Sources (Ranked by ROI)

#### 1. Smithery Registry Optimization (Week 1)
**Current:** Basic listing  
**Goal:** Feature placement

**Actions:**
- [ ] Enhance `smithery.yaml` with rich metadata
- [ ] Add tags: `finance`, `sec`, `compliance`, `zero-hallucination`
- [ ] Request "Featured" badge (email Smithery team)
- [ ] Add demo GIF showing SEC citation flow

**Expected Impact:** 500-1000 installs/month from featured placement.

#### 2. PyPI SEO (Week 1-2)
**Current:** v0.1.0 published, minimal README  
**Goal:** First result for "mcp financial data"

**Actions:**
- [ ] Expand PyPI README to 2000+ words
- [ ] Add keywords: `mcp-server`, `financial-data`, `sec-edgar`, `citations`
- [ ] Include code examples with output screenshots
- [ ] Add "Alternatives" section comparing to Financial Datasets MCP
- [ ] Link to GitHub repo (creates backlink for SEO)

**Expected Impact:** 200-500 organic installs/month.

#### 3. MCP Official Directory (Week 2)
**Repo:** https://github.com/modelcontextprotocol/servers

**Actions:**
- [ ] Submit PR to add cite-finance-mcp to directory
- [ ] Follow their template (name, description, install command)
- [ ] Highlight unique feature: "Only MCP with SEC provenance"

**Expected Impact:** 1000-2000 installs from official endorsement.

#### 4. Documentation SEO (Week 2-3)
**Create:** `docs.cite-finance.io` (GitHub Pages, free)

**Target Keywords:**
- "claude desktop financial data"
- "mcp server sec filings"
- "zero hallucination financial api"
- "ai financial assistant without errors"

**Content:**
- Installation guide
- Usage examples (with Claude Desktop screenshots)
- "Why Citations Matter" (thought leadership)
- Comparison table (vs Financial Datasets MCP)

**Expected Impact:** 500-1000 installs/month from Google.

#### 5. "Show HN" Launch (Week 3)
**Title:** "Show HN: MCP Server for Financial Data with SEC Citations"

**Body:**
```
I built cite-finance-mcp because I was tired of Claude making up 
financial numbers. Every figure includes a direct link to the 
SEC filing. Zero hallucination.

Try it free (10 tickers), upgrade to 500 tickers for $29.

Feedback welcome on the citation UX - still refining how to 
surface provenance without cluttering the response.
```

**Expected Impact:** 2000-5000 installs in 48 hours.

#### 6. Reddit (Strategic Posts, Not Community)
**Subreddits:** r/ClaudeAI, r/LocalLLaMA, r/MachineLearning

**Post Type:** "I made a thing" (not engagement farming)

**Example Title (r/ClaudeAI):**  
"MCP Server that cites every financial number (SEC URLs included)"

**Expected Impact:** 500-1000 installs per successful post.

---

## 📊 Traffic Funnel Metrics

### Installation Journey
```
1000 Registry Views
  ↓ (30% CTR)
300 PyPI Page Views
  ↓ (20% install rate)
60 Installations
  ↓ (50% activation)
30 Active Users
  ↓ (2% conversion)
1 Paid Customer ($29 or $99)
```

**To hit $10k/mo:**
- Need ~100 paid customers (mix of $29 and $99)
- Need ~5,000 active users
- Need ~10,000 installations
- Need ~50,000 registry views

**Timeline:** 90 days = Aggressive but achievable with featured placement.

---

## 🛠️ Technical Roadmap

### Week 1: Foundation
- [ ] Expand demo data to 10 tickers (5 → 10)
- [ ] Add 5 more metrics (revenue, net_income, cash, debt, equity)
- [ ] Create `financial_data.parquet` (500 tickers, 5 years)
- [ ] Test local cache loading in MCP
- [ ] Update `smithery.yaml` with rich metadata
- [ ] Enhance PyPI README (2000+ words)

### Week 2: Monetization
- [ ] Create Gumroad products:
  - [ ] Extended Cache ($29 one-time)
  - [ ] Cache Updates ($9/quarter subscription)
  - [ ] Live API ($99/mo subscription)
- [ ] Test Gumroad file delivery workflow
- [ ] Write provisioning script for Spectator SSH keys
- [ ] Add license key validation to `mcp_server.py`
- [ ] Create "Upgrade" prompts in demo mode responses

### Week 3: Distribution
- [ ] Submit to MCP official directory (PR)
- [ ] Launch GitHub Pages docs site
- [ ] Write 5 SEO-optimized documentation pages
- [ ] Post "Show HN" on Hacker News
- [ ] Post to r/ClaudeAI
- [ ] Email Smithery for featured placement

### Week 4-8: Iteration
- [ ] Monitor conversion funnel (installs → paid)
- [ ] Add most-requested metrics (P/E, EPS, margins)
- [ ] Optimize cache file size (compression)
- [ ] Add SQLite option (alternative to parquet)
- [ ] Create video demo (Loom, 2 min)
- [ ] Add testimonials from early users

### Week 9-12: Scale
- [ ] Launch Enterprise tier ($499/mo)
- [ ] Add Paddle as payment option (lower fees at scale)
- [ ] Create affiliate program (20% commission)
- [ ] Optimize for "claude desktop plugins" keyword
- [ ] Expand demo data to 20 tickers
- [ ] Add caching layer for Spectator queries (Redis)

---

## 🏁 Success Metrics

### Leading Indicators (Weekly)
- **Installs:** 100 → 500 → 1000 → 2000/week
- **Activation Rate:** >50% (user runs first query)
- **Demo → Paid CTR:** >2%
- **PyPI Daily Downloads:** 50 → 200 → 500/day

### Lagging Indicators (Monthly)
- **MRR:** $500 → $2000 → $5000 → $10,000
- **Paid Users:** 5 → 20 → 50 → 100
- **Churn Rate:** <5% monthly
- **Spectator Uptime:** >99%

### Red Flags (Act Immediately)
- ⚠️ Activation rate <30% (UX problem)
- ⚠️ Conversion rate <1% (pricing problem)
- ⚠️ Churn rate >10% (quality problem)
- ⚠️ Spectator downtime >1% (reliability problem)

---

## 🎯 Competitive Response Plan

### If Financial Datasets MCP Adds Citations
**Response:** Position as "Compliance-First" alternative.
- Emphasize: SEC-specific, regulatory-grade provenance
- Add: Audit trail export (for compliance teams)
- Target: Financial institutions, not indie devs

### If They Launch Paid Tier
**Response:** Undercut on price (they'll go SaaS, we're static).
- Our $29 = lifetime access to 500 tickers
- Their $X/mo = recurring cost
- Marketing: "Own your data, don't rent it"

### If They Copy Our Model
**Response:** We're 3 months ahead, focus on execution.
- By then: 10k installs, 100 paid customers, SEO dominance
- Leverage: First-mover advantage in MCP ecosystem

---

## 💡 Contingency Plans

### Plan B: If Spectator Dies
**Fallback:** Use free SEC API (sec-api.io free tier).
- Tier 3 becomes "Premium SEC API" (we're just wrapper)
- Cost: $0 (within free tier limits)
- Trade-off: Slower, less flexible

### Plan C: If Gumroad Sucks
**Migrate to:** Paddle (lower fees, better automation).
- Wait until $5k/mo to justify migration effort
- Use Paddle's webhook → CloudFlare Worker (serverless)

### Plan D: If MCP Ecosystem Fails
**Pivot:** Convert to Obsidian plugin (similar architecture).
- Market: Knowledge workers, researchers
- Same value prop: Zero hallucination financial notes
- Estimated market: 100k+ Obsidian users interested in finance

---

## 🚨 Critical Blockers

### 1. PyPI Package Broken?
**Test:** `pip install cite-finance-mcp` in fresh env
**Fix:** If broken, republish with `hatch build && twine upload dist/*`

### 2. Spectator SSH Access
**Verify:** Can we SSH to 100.96.62.97 from external client?
**Fix:** If no, use Tailscale tunnel (user installs Tailscale)

### 3. Demo Data Stale
**Check:** Are AAPL/TSLA numbers still current?
**Fix:** Update with Q4 2024 or Q1 2025 data

---

## 📈 Revenue Milestones

### $1k/mo (Month 1)
- 5,000 total installs
- 30 Extended Cache sales ($870)
- 2 Live API subs ($198)
- **Unlock:** Validate product-market fit

### $5k/mo (Month 2)
- 15,000 total installs
- 100 cache sales ($2,900)
- 20 Live API subs ($1,980)
- **Unlock:** Quit side projects, focus here

### $10k/mo (Month 3)
- 30,000 total installs
- 200 cache sales ($5,800)
- 40 Live API subs ($3,960)
- 2 Enterprise deals ($998)
- **Unlock:** Sustainable income, consider full-time

---

## ✅ Immediate Action Plan (Next 7 Days)

### Day 1 (Today)
- [ ] Test current PyPI package (install + run)
- [ ] Audit demo data (ensure accuracy)
- [ ] Create Gumroad account (if not exists)

### Day 2
- [ ] Generate `financial_data.parquet` (500 tickers)
- [ ] Test local cache loading logic
- [ ] Write Extended Cache product page on Gumroad

### Day 3
- [ ] Enhance `smithery.yaml` (rich metadata)
- [ ] Rewrite PyPI README (2000+ words)
- [ ] Create demo GIF (30 sec, shows citation)

### Day 4
- [ ] Submit to MCP official directory (PR)
- [ ] Email Smithery for featured placement
- [ ] Set up GitHub Pages (docs site)

### Day 5
- [ ] Write 3 documentation pages (install, usage, comparison)
- [ ] Add license key validation to `mcp_server.py`
- [ ] Create upgrade prompts (demo → paid)

### Day 6
- [ ] Publish Gumroad products (Extended Cache, Live API)
- [ ] Test end-to-end purchase flow
- [ ] Create provisioning script for Spectator keys

### Day 7
- [ ] Post to Hacker News ("Show HN")
- [ ] Post to r/ClaudeAI
- [ ] Monitor installs + feedback

---

## 📚 Appendix: Technical Specs

### Extended Cache File Structure
```
financial_data.parquet (50MB compressed)
├─ Schema:
│  ├─ ticker (string)
│  ├─ metric (string) 
│  ├─ value (float64)
│  ├─ period (string)
│  ├─ filing_type (string)
│  ├─ filing_url (string)
│  ├─ consistency_score (float32)
│  └─ as_of (datetime64)
├─ Rows: ~250,000 (500 tickers × 10 metrics × 5 years × 4 quarters)
├─ Compression: Snappy (parquet native)
└─ Update Frequency: Quarterly
```

### Spectator Query API
```python
# sec_query.py (on Spectator)
import sys
import json
from sec_scraper import SECEdgar

ticker = sys.argv[1]
metric = sys.argv[2]

scraper = SECEdgar()
result = scraper.get_metric(ticker, metric)
print(json.dumps(result))
```

**Response Format:**
```json
{
  "ticker": "AAPL",
  "metric": "revenue_ttm",
  "value": 383285000000,
  "unit": "USD",
  "period": "TTM",
  "as_of": "2024-09-30",
  "sources": [{
    "type": "sec_filing",
    "filing": "10-K",
    "url": "https://www.sec.gov/...",
    "excerpt": "Total net sales: $383,285 million"
  }],
  "consistency_score": 0.96,
  "retrieved_at": "2026-01-21T11:00:00Z"
}
```

---

## 🎬 Closing

**This is your path to $10k/mo:**

1. **Week 1-2:** Build cache, polish product, optimize listings
2. **Week 3-4:** Launch on Hacker News, MCP directory, r/ClaudeAI
3. **Week 5-8:** Ride the install wave, iterate on conversion funnel
4. **Week 9-12:** Scale with SEO, affiliates, enterprise outreach

**No servers. No community management. Just product + distribution.**

The architecture is serverless (Gumroad + Spectator), the moat is citations, and the market is every Claude Desktop user who needs financial data.

**Execute. Ship. Scale.**

---

**Masterplan Version:** 1.0  
**Created:** 2026-01-21  
**Owner:** Christopher Ongko  
**Next Review:** 2026-02-21 (30 days)
