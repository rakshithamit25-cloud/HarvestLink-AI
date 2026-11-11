import os
from dotenv import load_dotenv

# Load local .env if present
load_dotenv()

class Settings:
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "local-dev-secret-key-32-chars-harvestlink-2026")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./harvestlink.db")
    
    # PayPal Sandbox
    PAYPAL_MODE: str = os.getenv("PAYPAL_MODE", "mock").lower()  # 'sandbox' or 'mock'
    PAYPAL_CLIENT_ID: str = os.getenv("PAYPAL_CLIENT_ID", "")
    PAYPAL_CLIENT_SECRET: str = os.getenv("PAYPAL_CLIENT_SECRET", "")
    PAYPAL_API_BASE_URL: str = os.getenv("PAYPAL_API_BASE_URL", "https://api-m.sandbox.paypal.com")
    PAYPAL_CURRENCY: str = os.getenv("PAYPAL_CURRENCY", "USD")
    
    # AI Agents
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "heuristic").lower()
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
    
    # Demo Mode
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "false").lower() == "true"
    
    # URLs
    FRONTEND_URL: str = os.getenv(
        "FRONTEND_URL",
        "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174"
    )
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")

settings = Settings()
