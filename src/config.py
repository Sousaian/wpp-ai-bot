from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    
    # Evolution API
    evolution_api_url: str
    evolution_api_key: str
    evolution_instance_name: str
    
    # Application
    app_host: str = "0.0.0.0"
    app_port: int = 5000
    debug: bool = False
    
    # ngrok (optional)
    use_ngrok: bool = False
    ngrok_auth_token: str | None = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Convenience
settings = get_settings()