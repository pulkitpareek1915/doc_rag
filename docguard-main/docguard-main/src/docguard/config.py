from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    openai_api_key: str = ""
    anthropic_api_key: str = ""

    database_url: str = (
        "postgresql://docguard:docguard_dev_password@localhost:5432/docguard"
    )
    redis_url: str = "redis://localhost:6379/0"

    embedding_model: str = "text-embedding-3-small"
    embedding_dims: int = 1536
    llm_model: str = "claude-3-5-sonnet-20241022"

    retrieval_top_k: int = 8
    retrieval_min_score: float = 0.35
    min_relevant_docs: int = 2
    max_rewrites: int = 2
    generation_max_context_docs: int = 5

    environment: str = "development"
    log_level: str = "INFO"

    max_document_size_mb: int = 10
    max_query_length: int = 500
    enable_security_scan: bool = True

    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600

    auth_enabled: bool = True
    api_auth_token: str = ""

    rate_limit_enabled: bool = True
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60

    cors_origins: list[str] = ["*"]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def langfuse_enabled(self) -> bool:
        return bool(
            self.langfuse_public_key
            and self.langfuse_secret_key
        )


settings = Settings()
