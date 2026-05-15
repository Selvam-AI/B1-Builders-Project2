from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool | None = Field(default=None, alias="DEBUG")
    database_url: str = Field(default="sqlite:///./data/fithub_ai.db", alias="DATABASE_URL")
    youtube_api_key: str = Field(default="", alias="YOUTUBE_API_KEY")
    ai_llm_provider: str = Field(default="ollama", alias="AI_LLM_PROVIDER")
    ai_recommender_mode: str = Field(default="llm", alias="AI_RECOMMENDER_MODE")
    ai_allow_mock_fallback: bool = Field(default=True, alias="AI_ALLOW_MOCK_FALLBACK")
    model: str = Field(default="ollama/llama3", alias="MODEL")
    base_url: str = Field(default="http://localhost:11434", alias="BASE_URL")
    secret_key: str = Field(default="replace-with-local-dev-secret", alias="SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    seed_admin: bool = Field(default=True, alias="SEED_ADMIN")
    admin_email: str = Field(default="admin@example.com", alias="ADMIN_EMAIL")
    admin_password: str = Field(default="admin123", alias="ADMIN_PASSWORD")
    video_curator_enabled: bool = Field(default=True, alias="VIDEO_CURATOR_ENABLED")
    video_cache_target_per_category: int = Field(default=5, alias="VIDEO_CACHE_TARGET_PER_CATEGORY")
    video_cache_max_play_count: int = Field(default=3, alias="VIDEO_CACHE_MAX_PLAY_COUNT")
    video_curator_interval_hours: int = Field(default=24, alias="VIDEO_CURATOR_INTERVAL_HOURS")

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug_flag(cls, value: object) -> bool | None:
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "debug", "development"}:
                return True
            if normalized in {"0", "false", "no", "off", "quiet", "production"}:
                return False
            return None
        return None

    @model_validator(mode="after")
    def default_debug_for_development(self) -> "Settings":
        if self.debug is None:
            self.debug = self.app_env.lower() == "development"
        return self


settings = Settings()
