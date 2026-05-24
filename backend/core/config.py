"""Configuration loader from config.yaml."""
from pathlib import Path
from typing import Any

import yaml


class Config:
    _instance: "Config | None" = None

    def __init__(self, config_path: str | Path | None = None) -> None:
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config.yaml"
        self._path = Path(config_path)
        self._data: dict[str, Any] = {}
        self.reload()

    def reload(self) -> None:
        if self._path.exists():
            with open(self._path, "r", encoding="utf-8") as f:
                self._data = yaml.safe_load(f) or {}

    @property
    def app_name(self) -> str:
        return self._data.get("app", {}).get("name", "CPA Tutor")

    @property
    def ai_provider(self) -> str:
        return self._data.get("ai", {}).get("provider", "deepseek")

    @property
    def ai_model(self) -> str:
        return self._data.get("ai", {}).get("model", "deepseek-chat")

    @property
    def ai_base_url(self) -> str:
        return self._data.get("ai", {}).get("base_url", "https://api.deepseek.com")

    @property
    def ai_api_key(self) -> str | None:
        import os

        ai_cfg = self._data.get("ai", {})
        direct_key = ai_cfg.get("api_key", "")
        if direct_key:
            return direct_key
        env_var = ai_cfg.get("api_key_env", "DEEPSEEK_API_KEY")
        return os.environ.get(env_var)

    @property
    def db_url(self) -> str:
        return self._data.get("database", {}).get("url", "sqlite:///./data/cpa_tutor.db")

    @property
    def scraping_sources(self) -> dict[str, Any]:
        return self._data.get("scraping", {}).get("sources", {})

    @property
    def scraping_user_agent(self) -> str:
        return self._data.get("scraping", {}).get("user_agent", "")

    @property
    def scraping_request_delay(self) -> int:
        return self._data.get("scraping", {}).get("request_delay", 2)

    @property
    def subjects(self) -> list[dict[str, str]]:
        return self._data.get("subjects", [])

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split(".")
        node = self._data
        for k in keys:
            if isinstance(node, dict):
                node = node.get(k)
            else:
                return default
            if node is None:
                return default
        return node


_config_singleton: Config | None = None


def get_config() -> Config:
    global _config_singleton
    if _config_singleton is None:
        _config_singleton = Config()
    return _config_singleton
