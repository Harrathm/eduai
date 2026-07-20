import os
import secrets
from typing import Any, Optional
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, ConfigDict


class Settings(BaseSettings):
    """Application settings with validation."""
    
    # Database
    database_url: str = Field(default="", description="PostgreSQL connection string")
    
    # JWT Security
    jwt_secret: str = Field(default="", description="JWT signing secret key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expire_minutes: int = Field(default=1440, description="Token expiration in minutes")
    
    # OpenAI
    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_org_id: Optional[str] = Field(default=None, description="OpenAI organization ID")

    # Groq
    groq_api_key: str = Field(default="", description="Groq API key")

    # OpenRouter
    openrouter_api_key: str = Field(default="", description="OpenRouter API key")

    # MiniMax (OpenAI-compatible)
    minimax_api_key: str = Field(default="", description="MiniMax API key")
    minimax_base_url: str = Field(default="https://inference.dahl.global/v1", description="MiniMax API base URL")
    
    # Stripe
    stripe_secret_key: str = Field(default="", description="Stripe secret key")
    stripe_webhook_secret: str = Field(default="", description="Stripe webhook secret")
    stripe_price_pro: str = Field(default="price_teacher_pro", description="Stripe price ID for Pro plan")
    stripe_price_school: str = Field(default="price_school", description="Stripe price ID for School plan")
    stripe_price_institution: str = Field(default="price_institution", description="Stripe price ID for Institution plan")
    
    # CORS
    cors_origins: str = Field(default="http://localhost:5173", description="Allowed CORS origins (comma-separated)")
    
    # Environment
    environment: str = Field(default="development", description="Environment: development|staging|production")
    
    # Course marketplace
    max_independent_course_price: float = Field(default=500.0, description="Plafond de prix pour un cours d'enseignant indépendant (TND)")
    refund_max_progress_percent: float = Field(default=20.0, description="Progression max (%) pour autoriser un remboursement")
    default_commission_rate: float = Field(default=30.0, description="Taux de commission EDUAI par défaut sur cours indépendant (%)")
    
    model_config = ConfigDict(env_file=".env", case_sensitive=False, extra="ignore")
    
    @field_validator("jwt_secret", mode="before")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """Fail if JWT secret is not set in production."""
        env = os.getenv("ENVIRONMENT", "development")
        if not v:
            if env == "production":
                raise ValueError("JWT_SECRET must be set in production")
            # Use a stable dev secret to avoid invalidating tokens on restart
            return "dev-only-jwt-secret-not-for-production-use-32+chars"
        if env == "production" and len(v) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters in production")
        return v
    
    @field_validator("database_url", mode="after")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Fail if database URL is not set."""
        if not v:
            raise ValueError("DATABASE_URL must be set")
        return v
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
    
    @property
    def allowed_hosts(self) -> list[str]:
        """Get allowed hosts for production."""
        if self.is_production:
            # In production, only allow HTTPS origins
            return [origin.replace("http://", "https://") for origin in self.cors_origins_list]
        return self.cors_origins_list


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def validate_environment() -> None:
    """Validate required environment at startup.
    
    Raises:
        ValueError: If critical environment variables are missing in production.
    """
    settings = get_settings()
    
    if settings.is_production:
        # Check required production variables
        if not settings.jwt_secret or len(settings.jwt_secret) < 32:
            raise ValueError("CRITICAL: JWT_SECRET must be at least 32 characters in production")
        
        if not settings.database_url:
            raise ValueError("CRITICAL: DATABASE_URL must be set in production")
        
        # Warn about missing Stripe in production
        if not settings.stripe_secret_key:
            import warnings
            warnings.warn("WARNING: STRIPE_SECRET_KEY not set - payments will not work")
        
        # Warn about missing OpenAI in production
        if not settings.openai_api_key:
            import warnings
            warnings.warn("WARNING: OPENAI_API_KEY not set - AI features will not work")