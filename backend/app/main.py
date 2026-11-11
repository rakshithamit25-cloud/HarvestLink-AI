from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.database.session import engine, Base, SessionLocal
from app.api.auth import router as auth_router
from app.api.listings import router as listings_router
from app.api.buyers import router as buyers_router
from app.api.matching import router as matching_router
from app.api.orders import router as orders_router
from app.api.payments import router as payments_router
from app.api.operator import router as operator_router
from app.api.impact import router as impact_router
from app.api.logs import router as logs_router
from app.api.demo import router as demo_router, seed_database

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        seed_database(session)
    yield

app = FastAPI(
    title="HarvestLink AI — Agentic Agricultural Commerce API",
    description="Multi-agent agricultural commerce API with Tamil voice processing, FPO operator proxy consent, and PayPal Sandbox settlement.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
]

cors_origins = list(DEFAULT_ALLOWED_ORIGINS)
for url in settings.FRONTEND_URL.split(","):
    clean_url = url.strip()
    if clean_url and clean_url not in cors_origins:
        cors_origins.append(clean_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth_router)
app.include_router(listings_router)
app.include_router(buyers_router)
app.include_router(matching_router)
app.include_router(orders_router)
app.include_router(payments_router)
app.include_router(operator_router)
app.include_router(impact_router)
app.include_router(logs_router)
app.include_router(demo_router)

@app.get("/")
def root():
    return {
        "message": "HarvestLink AI — Agentic Agricultural Commerce API is running.",
        "paypal_mode": settings.PAYPAL_MODE,
        "llm_provider": settings.LLM_PROVIDER,
        "currency": settings.PAYPAL_CURRENCY,
        "docs_url": "/docs"
    }

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "paypal_mode": settings.PAYPAL_MODE,
        "database": settings.DATABASE_URL.split(":///")[0]
    }
