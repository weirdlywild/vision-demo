from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration using environment variables."""

    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"  # Much faster than gpt-4o
    openai_max_tokens: int = 800  # Increased for detailed instructions
    openai_temperature: float = 0.3

    # Image Processing
    max_image_size_mb: int = 10
    min_image_dimension: int = 100
    max_image_dimension: int = 4096
    resize_max_dimension: int = 384  # Aggressive reduction for speed (was 512)
    blur_threshold: int = 30  # Very permissive - only catch truly blurry images
    min_brightness: int = 40
    max_brightness: int = 240

    # Caching
    cache_ttl_seconds: int = 3600
    perceptual_cache_ttl_seconds: int = 86400
    max_cache_entries: int = 1000

    # Session Management
    session_ttl_minutes: int = 30
    max_session_history: int = 3
    cleanup_interval_minutes: int = 10

    # API Configuration
    api_timeout_seconds: int = 30
    max_retries: int = 3
    backoff_factor: int = 2

    # Performance
    uvicorn_workers: int = 2
    uvicorn_timeout: int = 60

    # Security
    allowed_origins: str = "*"
    api_key_required: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


# Global settings instance
settings = Settings()
