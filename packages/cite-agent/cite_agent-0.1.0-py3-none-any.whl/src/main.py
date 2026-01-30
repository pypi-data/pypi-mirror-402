import os
import time
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from src.api import auth, answers, metrics, subscriptions, companies, intelligence
from src.billing.lemonsqueezy_integration import LemonSqueezyManager
from src.data_sources import register_source
from src.data_sources.aggregator import init_aggregator, DataPriority
from src.data_sources.yfinance_source import YFinanceSource
from src.data_sources.sec_edgar import SECEdgarSource
from src.data_sources.polygon_source import PolygonSource
from src.data_sources.alphavantage_source import AlphaVantageSource
from src.data_sources.finnhub_source import FinnhubSource
from src.models.user import APIKey, PricingTier, User, UserStatus

# Sentry Init
SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    sentry_sdk.init(dsn=SENTRY_DSN, traces_sample_rate=0.1)

# Lemon Squeezy Manager Global
ls_manager = LemonSqueezyManager(
    api_key=os.getenv("LS_API_KEY", ""),
    webhook_secret=os.getenv("LS_WEBHOOK_SECRET", "")
)


def _dev_no_auth_enabled() -> bool:
    return (os.getenv("CITE_FINANCE_DEV_NO_AUTH") or "").strip().lower() in {"1", "true", "yes", "y"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load Billing, Database, etc.
    print("🚀 Cite-Finance API starting up...")

    # Initialize data source aggregator (runs even without premium keys; YFinance/SEC still work).
    aggregator = init_aggregator(redis_client=None)
    aggregator.register_source(YFinanceSource({}), priority=DataPriority.FALLBACK)

    sec_user_agent = os.getenv("SEC_USER_AGENT", "Cite-Finance/1.0 (contact: local@example.com)")
    sec_source = SECEdgarSource({"user_agent": sec_user_agent})
    aggregator.register_source(sec_source, priority=DataPriority.SECONDARY)
    # Also register plugins into the capability registry used by /metrics and /companies.
    register_source(sec_source)
    register_source(YFinanceSource({}))

    polygon_key = os.getenv("POLYGON_API_KEY") or os.getenv("POLYGON_KEY")
    if polygon_key:
        aggregator.register_source(PolygonSource({"api_key": polygon_key}), priority=DataPriority.PRIMARY)

    av_key = os.getenv("ALPHA_VANTAGE_API_KEY") or os.getenv("ALPHAVANTAGE_API_KEY")
    if av_key:
        aggregator.register_source(AlphaVantageSource({"api_key": av_key}), priority=DataPriority.SECONDARY)

    finnhub_key = os.getenv("FINNHUB_API_KEY")
    if finnhub_key:
        aggregator.register_source(FinnhubSource({"api_key": finnhub_key}), priority=DataPriority.SECONDARY)
    
    # Inject LS Manager into subscriptions dependency
    subscriptions.set_dependencies(ls_manager)
    
    yield
    # Shutdown
    print("🛑 Cite-Finance API shutting down...")

app = FastAPI(
    title="Cite-Finance API",
    description="LLM-ready financial data with compliance-grade citations.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

if _dev_no_auth_enabled():
    # Dev helper: run without DB/API keys by injecting a synthetic user into request.state.
    # This makes /metrics + /companies + /intelligence usable for local demos.
    @app.middleware("http")
    async def _dev_no_auth_user_injector(request: Request, call_next):
        request.state.user = User(
            user_id="dev_no_auth",
            email="dev-no-auth@example.com",
            tier=PricingTier.PROFESSIONAL,
            status=UserStatus.ACTIVE,
            api_calls_this_month=0,
            api_calls_limit=10_000,
        )
        request.state.api_key = APIKey(
            key_id="dev_no_auth_key",
            user_id="dev_no_auth",
            key_hash="dev_no_auth",
            key_prefix="dev_no_auth",
            name="Dev No-Auth Key",
            is_active=True,
            is_test_mode=True,
            total_calls=0,
        )
        return await call_next(request)

# CORS (Allow all for now to support diverse clients/MCP)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instrument Prometheus
Instrumentator().instrument(app).expose(app)

# --- MCP Server Mount ---
# Mount the MCP server as a sub-application
# Agents will connect to /mcp/sse and /mcp/messages
try:
    from src.mcp_server import starlette_app as mcp_app
    app.mount("/mcp", mcp_app)
    print("✅ MCP Server mounted at /mcp")
except ImportError as e:
    print(f"⚠️ Failed to mount MCP Server: {e}")

# Include Routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(answers.router, prefix="/api/v1/answers", tags=["Answers (Core)"])
app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["Metrics"])
app.include_router(subscriptions.router, prefix="/api/v1/subscriptions", tags=["Billing"])
app.include_router(companies.router, prefix="/api/v1/companies", tags=["Companies"])
app.include_router(intelligence.router, prefix="/api/v1/intelligence", tags=["Intelligence"])

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": time.time(),
        "billing_configured": bool(os.getenv("LS_API_KEY"))
    }

@app.get("/")
async def root():
    return {
        "message": "Welcome to Cite-Finance API. Documentation at /docs",
        "mcp_server": "Use the MCP server wrapper to connect AI agents."
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
