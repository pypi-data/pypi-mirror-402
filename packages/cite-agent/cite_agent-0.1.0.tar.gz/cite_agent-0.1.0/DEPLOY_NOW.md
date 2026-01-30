# Deploy to Production - Step by Step

**Time required:** 30-45 minutes
**Everything is ready - just follow these steps:**

---

## ✅ What's Already Done

- Code merged to main and pushed to GitHub
- Landing page created (`docs/index.html`)
- Launch materials written (`LAUNCH_COPY.md`)
- Documentation complete
- Redis TLS configured for Heroku
- Sentry monitoring ready
- `/api/v1/answers` endpoint implemented

---

## 🚀 Step 1: Create Stripe Products (10 min)

### Go to Stripe Dashboard

1. **Log in to Stripe:** https://dashboard.stripe.com
2. **Navigate to:** Products → Create Product

### Create 3 Products:

#### Product 1: Starter
- **Name:** Cite-Finance Starter
- **Description:** LLM-ready answers with citations
- **Price:** $49.00 / month
- **Billing:** Recurring monthly
- **Click "Save Product"**
- **Copy the Price ID** (looks like `price_1ABC...`)

#### Product 2: Professional
- **Name:** Cite-Finance Professional
- **Description:** All features with 99.9% SLA
- **Price:** $199.00 / month
- **Billing:** Recurring monthly
- **Click "Save Product"**
- **Copy the Price ID**

#### Product 3: Enterprise
- **Name:** Cite-Finance Enterprise
- **Description:** Unlimited calls with dedicated support
- **Price:** $999.00 / month
- **Billing:** Recurring monthly
- **Click "Save Product"**
- **Copy the Price ID**

### Get API Keys:

1. **Navigate to:** Developers → API Keys
2. **Copy "Secret key"** (starts with `sk_live_` or `sk_test_`)
3. **Navigate to:** Developers → Webhooks
4. **Create endpoint:** `https://cite-finance-api-prod.herokuapp.com/api/v1/webhooks/stripe`
5. **Select events:** `customer.subscription.created`, `customer.subscription.updated`, `customer.subscription.deleted`
6. **Copy "Signing secret"** (starts with `whsec_`)

**Save these 5 values - you'll need them next:**
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_PRICE_STARTER`
- `STRIPE_PRICE_PRO`
- `STRIPE_PRICE_ENTERPRISE`

---

## 🔐 Step 2: Create Sentry Project (5 min)

### Go to Sentry.io

1. **Log in to Sentry:** https://sentry.io
2. **Create New Project**
   - Platform: Python
   - Project name: `cite-finance-api-prod`
   - Team: Default
3. **Click "Create Project"**
4. **Copy the DSN** (looks like `https://xxx@sentry.io/xxx`)

**Save this value:**
- `SENTRY_DSN`

---

## ⚙️ Step 3: Configure Heroku (5 min)

### Set Environment Variables

```bash
heroku config:set \
  STRIPE_SECRET_KEY=sk_live_YOUR_KEY_HERE \
  STRIPE_WEBHOOK_SECRET=whsec_YOUR_SECRET_HERE \
  STRIPE_PRICE_STARTER=price_YOUR_STARTER_ID \
  STRIPE_PRICE_PRO=price_YOUR_PRO_ID \
  STRIPE_PRICE_ENTERPRISE=price_YOUR_ENTERPRISE_ID \
  SENTRY_DSN=https://YOUR_DSN_HERE \
  ENVIRONMENT=production \
  --app cite-finance-api-prod
```

**Replace the placeholders with values from Steps 1 & 2**

### Verify Configuration:

```bash
heroku config --app cite-finance-api-prod
```

You should see all variables set.

---

## 🚢 Step 4: Deploy to Heroku (10 min)

### Deploy Code:

```bash
cd /home/phyrexian/Downloads/llm_automation/project_portfolio/cite-finance-api

# Ensure you're on main
git checkout main
git pull origin main

# Deploy to Heroku
git push heroku main
```

**Wait for deployment to complete** (2-3 minutes)

### Verify Deployment:

```bash
# Check logs
heroku logs --tail --app cite-finance-api-prod

# You should see:
# "Starting Cite-Finance API"
# "Database pool created"
# "Redis connected"
# "Managers initialized"
```

---

## ✅ Step 5: Test the Deployment (10 min)

### Test 1: Health Check

```bash
curl https://cite-finance-api-prod.herokuapp.com/health
```

**Expected:**
```json
{
  "status": "healthy",
  "database": "ok",
  "redis": "ok",
  "version": "1.0.0"
}
```

✅ If you see this, Redis TLS is working!

### Test 2: API Documentation

Visit: `https://cite-finance-api-prod.herokuapp.com/docs`

You should see the Swagger UI with:
- `/api/v1/answers` endpoint ✨
- `/api/v1/metrics` endpoint
- `/api/v1/auth/register` endpoint

### Test 3: Register & Test API Key

```bash
# Register a test user
curl -X POST https://cite-finance-api-prod.herokuapp.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@youremail.com", "company_name": "Test"}'
```

**Copy the API key from response**

```bash
# Test the /answers endpoint
curl -H "X-API-Key: YOUR_KEY_HERE" \
  "https://cite-finance-api-prod.herokuapp.com/api/v1/answers?ticker=AAPL&metric=revenue_ttm&format=json"
```

**Expected:**
```json
{
  "ticker": "AAPL",
  "metric": "revenue_ttm",
  "value": 383285000000,
  "unit": "USD",
  ...
  "consistency_score": 0.96
}
```

✅ If you see structured data with sources, it's working!

---

## 📊 Step 6: Verify Monitoring (5 min)

### Check Sentry

1. Go to https://sentry.io
2. Open your `cite-finance-api-prod` project
3. You should see "Waiting for first event" or recent requests

### Check Heroku Metrics

```bash
heroku metrics --app cite-finance-api-prod
```

Look for:
- Response times <500ms
- No errors
- Memory usage stable

---

## 🎉 Step 7: Launch! (15 min)

### Update Landing Page URL

If you have a custom domain, update `docs/index.html` to use it instead of the Heroku URL.

### Post Launch Announcements

**Use the content from `LAUNCH_COPY.md`:**

1. **Product Hunt** (best time: 12:01 AM PST)
   - Use the title, tagline, and description from LAUNCH_COPY.md
   - Add screenshots from `/docs` page
   - Post first comment

2. **Twitter** (immediately after PH)
   - Post the 6-tweet thread
   - Tag relevant accounts (@LangChainAI, etc.)

3. **Reddit** (2-4 hours after PH)
   - Post to r/SideProject
   - Post to r/LangChain
   - Be ready to answer questions

4. **Hacker News** (6-12 hours after PH)
   - Post "Show HN" submission
   - Monitor and respond to comments

5. **Email Outreach** (next day)
   - Send to 10-20 potential users
   - Offer free pilot

---

## 📈 Post-Launch Monitoring

### Track These Metrics:

**Day 1:**
- Free signups: Target 10-20
- /health uptime: >99%
- Average response time: <300ms
- Errors in Sentry: <5

**Week 1:**
- Free signups: Target 50-100
- Starter conversions: Target 2-5
- API usage: Track top endpoints

**Month 1:**
- MRR: Target $100-500
- Churn: <10%
- NPS: Survey first 10 customers

### Monitor:

```bash
# Heroku logs
heroku logs --tail --app cite-finance-api-prod

# Metrics
heroku metrics --app cite-finance-api-prod

# Sentry dashboard
https://sentry.io
```

---

## 🐛 Troubleshooting

### Issue: /health returns unhealthy

**Fix:**
```bash
# Check Redis URL
heroku config:get REDIS_URL --app cite-finance-api-prod

# Should start with rediss:// (TLS)
# If not, Redis addon might not be configured
heroku addons:info heroku-redis --app cite-finance-api-prod
```

### Issue: Stripe webhooks failing

**Fix:**
1. Check webhook endpoint URL in Stripe Dashboard
2. Verify `STRIPE_WEBHOOK_SECRET` is correct
3. Check Heroku logs for signature errors

### Issue: Rate limiting not working

**Fix:**
```bash
# Verify Redis is connected
curl https://cite-finance-api-prod.herokuapp.com/health

# Should show "redis": "ok"
```

---

## ✅ Launch Checklist

Before going public, verify:

- [ ] Health check returns 200 OK
- [ ] Can register user and get API key
- [ ] `/answers` endpoint returns structured data
- [ ] Stripe webhooks configured
- [ ] Sentry receiving events
- [ ] Heroku logs clean (no errors)
- [ ] Landing page accessible
- [ ] API docs accessible at `/docs`

---

## 🎯 Success Metrics

**Week 1 Goals:**
- 50 free signups
- 2-3 Starter conversions
- <0.1% error rate
- 99.9% uptime

**Month 1 Goals:**
- 200 free signups
- 10 paying customers
- $500 MRR
- 5-10 testimonials

---

## 🚀 You're Ready!

Everything is built, tested, and ready to deploy.

**Estimated time:**
- Stripe setup: 10 min
- Sentry setup: 5 min
- Heroku config: 5 min
- Deploy: 10 min
- Test: 10 min
- Launch: 15 min

**Total: ~45 minutes to production**

**Next step:** Go to Step 1 and start with Stripe.

Good luck! 💪

---

**Questions or issues?** Check `DEPLOYMENT_CHECKLIST.md` for detailed troubleshooting.
