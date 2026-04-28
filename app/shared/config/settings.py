from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    app_name: str = "AgenTask Designer"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    app_debug: bool = True
    secret_key: str = "test-secret-key"
    llm_provider: str = "Qwen3-VL-235B-A22B-Instruct-AWQ"
    llm_model_name: str = "QuantTrio/Qwen3-VL-235B-A22B-Instruct-AWQ"
    llm_temperature: float = 0.0
    llm_base_url: str = "https://mozaik-ai-gateway.kube.uatisbank/isgpt/garden/v1/chat/completions"
    llm_timeout: int = 120
    llm_api_key: str = ""
    llm_auth_type: str = "bearer"
    llm_username: str = ""
    llm_password: str = ""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
@lru_cache
def get_settings() -> Settings:
    return Settings()