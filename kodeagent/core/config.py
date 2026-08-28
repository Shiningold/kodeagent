"""全局配置 —— 3 层覆盖：Global / Project / Session。"""

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """从 .env + 环境变量读取配置。字段名大写即环境变量名。"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_provider: str = "ollama"

    openai_api_key: SecretStr | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    anthropic_api_key: SecretStr | None = None
    anthropic_model: str = "claude-haiku-4-5-20251001"

    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "qwen2.5:7b"

    log_level: str = "INFO"
    data_dir: str = Field(default=".kodeagent", description="session / memory 存储根目录")


settings = Settings()
