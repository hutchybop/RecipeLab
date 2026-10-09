from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class AppConfig:
    secret_key: str
    mongo_uri: str
    mongo_db_name: str
    log_level: str
    llm_provider: str
    llm_endpoint: str
    llm_api_key: str
    llm_model: str

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            secret_key=os.getenv("SECRET_KEY", ""),
            mongo_uri=os.getenv("MONGO_URI", ""),
            mongo_db_name=os.getenv("MONGO_DB_NAME", "RecipeLab"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            llm_provider=os.getenv("LLM_PROVIDER", "openai_compatible"),
            llm_endpoint=os.getenv("LLM_ENDPOINT", ""),
            llm_api_key=os.getenv("LLM_API_KEY", ""),
            llm_model=os.getenv("LLM_MODEL", ""),
        )

    def validate(self) -> list[str]:
        missing: list[str] = []
        if not self.secret_key:
            missing.append("SECRET_KEY")
        if not self.mongo_uri:
            missing.append("MONGO_URI")
        return missing

    def to_flask_dict(self) -> dict[str, str]:
        return {
            "SECRET_KEY": self.secret_key,
            "MONGO_URI": self.mongo_uri,
            "MONGO_DB_NAME": self.mongo_db_name,
            "LOG_LEVEL": self.log_level,
            "LLM_PROVIDER": self.llm_provider,
            "LLM_ENDPOINT": self.llm_endpoint,
            "LLM_API_KEY": self.llm_api_key,
            "LLM_MODEL": self.llm_model,
        }
