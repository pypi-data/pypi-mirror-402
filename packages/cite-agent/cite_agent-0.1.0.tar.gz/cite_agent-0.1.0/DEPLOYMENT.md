# Cite-Finance API - Deployment Guide

## Quick Deploy to Heroku

### Prerequisites
- Heroku CLI installed
- Heroku account
- Stripe account
- Domain name (optional)

### Step 1: Create Heroku App
```bash
heroku create cite-finance-api-prod
```

### Step 2: Add Add-ons
```bash
# PostgreSQL
heroku addons:create heroku-postgresql:mini --app cite-finance-api-prod

# Redis
heroku addons:create heroku-redis:mini --app cite-finance-api-prod

# Papertrail (logging)
heroku addons:create papertrail:choklad --app cite-finance-api-prod
```

### Step 3: Set Environment Variables
```bash
heroku config:set \
  STRIPE_SECRET_KEY=sk_live_xxx \
  STRIPE_WEBHOOK_SECRET=whsec_xxx \
  STRIPE_PUBLISHABLE_KEY=pk_live_xxx \
  SEC_USER_AGENT="Cite-Finance API/1.0 (contact@cite-finance.io)" \
  GROQ_API_KEY=gsk_xxx \
  JWT_SECRET_KEY=$(openssl rand -hex 32) \
  API_KEY_SALT=$(openssl rand -hex 16) \
  ENVIRONMENT=production \
  DEBUG=false \
  LOG_LEVEL=INFO \
  --app cite-finance-api-prod
```

### Step 4: Deploy
```bash
git push heroku main
```

### Step 5: Initialize Database
```bash
heroku run python -c "import asyncio; from src.utils.db_setup import init_database; asyncio.run(init_database())" --app cite-finance-api-prod
```

### Step 6: Scale Dynos
```bash
# Production: 2 web dynos + 1 worker
heroku ps:scale web=2 worker=1 --app cite-finance-api-prod
```

### Step 7: Configure Custom Domain (Optional)
```bash
heroku domains:add api.cite-finance.io --app cite-finance-api-prod
heroku certs:auto:enable --app cite-finance-api-prod
```

## Post-Deployment

### 1. Configure Stripe Webhooks
- Go to Stripe Dashboard → Webhooks
- Add endpoint: `https://api.cite-finance.io/api/v1/webhooks/stripe`
- Select events:
  - `customer.subscription.created`
  - `customer.subscription.updated`
  - `customer.subscription.deleted`
  - `invoice.payment_succeeded`
  - `invoice.payment_failed`

### 2. Create Stripe Products
```python
import stripe
stripe.api_key = "sk_live_xxx"

# Starter Tier
starter = stripe.Product.create(name="Cite-Finance Starter", description="1,000 API calls/month")
stripe.Price.create(product=starter.id, unit_amount=4900, currency="usd", recurring={"interval": "month"})

# Professional Tier
pro = stripe.Product.create(name="Cite-Finance Professional", description="10,000 API calls/month")
stripe.Price.create(product=pro.id, unit_amount=19900, currency="usd", recurring={"interval": "month"})

# Enterprise Tier
enterprise = stripe.Product.create(name="Cite-Finance Enterprise", description="Unlimited API calls")
stripe.Price.create(product=enterprise.id, unit_amount=99900, currency="usd", recurring={"interval": "month"})
```

### 3. Update Price IDs in Code
Edit `src/models/user.py`:
```python
STRIPE_PRICE_IDS = {
    PricingTier.STARTER: "price_xxx",  # From Stripe dashboard
    PricingTier.PROFESSIONAL: "price_yyy",
    PricingTier.ENTERPRISE: "price_zzz",
}
```

### 4. Monitor Logs
```bash
heroku logs --tail --app cite-finance-api-prod
```

### 5. Set Up Monitoring
- Sentry for error tracking
- Datadog/New Relic for APM
- Prometheus metrics exposed at `/metrics`

## Scaling

### Horizontal Scaling (More Dynos)
```bash
heroku ps:scale web=5 --app cite-finance-api-prod
```

### Vertical Scaling (Bigger Dynos)
```bash
heroku ps:resize web=standard-2x --app cite-finance-api-prod
```

### Database Scaling
```bash
heroku addons:upgrade heroku-postgresql:standard-0 --app cite-finance-api-prod
```

## Costs (Estimated)

| Component | Tier | Cost |
|-----------|------|------|
| Heroku Dyno | Standard-2x × 2 | $50/mo |
| PostgreSQL | Standard-0 | $50/mo |
| Redis | Premium-0 | $15/mo |
| Papertrail | Choklad | $7/mo |
| **Total** | | **$122/mo** |

## Rollback

```bash
# Rollback to previous release
heroku rollback --app cite-finance-api-prod

# Rollback to specific version
heroku rollback v123 --app cite-finance-api-prod
```

## Backup & Restore

```bash
# Create backup
heroku pg:backups:capture --app cite-finance-api-prod

# Download backup
heroku pg:backups:download --app cite-finance-api-prod

# Restore from backup
heroku pg:backups:restore b001 --app cite-finance-api-prod
```

## CI/CD with GitHub Actions

See `.github/workflows/deploy.yml` for automated deployment on push to `main` branch.

## Troubleshooting

### Database Connection Issues
```bash
heroku pg:info --app cite-finance-api-prod
heroku pg:ps --app cite-finance-api-prod
```

### Redis Connection Issues
```bash
heroku redis:info --app cite-finance-api-prod
heroku redis:cli --app cite-finance-api-prod
```

### Application Logs
```bash
heroku logs --tail --ps web --app cite-finance-api-prod
```

## Support

- Documentation: https://docs.cite-finance.io
- Status Page: https://status.cite-finance.io
- Contact: support@cite-finance.io
