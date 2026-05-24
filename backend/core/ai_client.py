"""Multi-provider AI client with response caching."""
from __future__ import annotations

import hashlib
import logging
import time
from pathlib import Path

from core.config import get_config

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent.parent / "data" / "ai_cache"


class AIClient:
    def __init__(self, model: str | None = None) -> None:
        self._config = get_config()
        self.provider = self._config.ai_provider
        self.model = model or self._config.ai_model
        self._client = None
        self._cache_enabled = self._config.get("ai.cache_responses", True)
        if self._cache_enabled:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)

    @property
    def is_available(self) -> bool:
        return self._config.ai_api_key is not None

    def _get_client(self):
        if self._client is not None:
            return self._client
        api_key = self._config.ai_api_key
        if not api_key:
            return None
        try:
            from openai import OpenAI
        except ImportError:
            logger.warning("openai package not installed — run: pip install openai")
            return None
        base_url = self._config.ai_base_url if self.provider == "deepseek" else None
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        logger.info("AI client ready: provider=%s model=%s", self.provider, self.model)
        return self._client

    def send(
        self,
        prompt: str,
        system: str = "",
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        if temperature is None:
            temperature = self._config.get("ai.temperature_generation", 0.3)
        if max_tokens is None:
            max_tokens = self._config.get("ai.max_tokens", 4096)

        cache_key = self._cache_key(prompt, system, temperature)
        if self._cache_enabled:
            cached = self._read_cache(cache_key)
            if cached is not None:
                return cached

        if not self.is_available:
            logger.warning("AI API key not set — returning empty")
            return ""

        client = self._get_client()
        if client is None:
            return ""

        start = time.monotonic()
        try:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            resp = client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            choice = resp.choices[0] if resp.choices else None
            text = choice.message.content if choice and choice.message else ""

            latency = int((time.monotonic() - start) * 1000)
            logger.info("AI call: provider=%s latency=%dms", self.provider, latency)

            if self._cache_enabled and text:
                self._write_cache(cache_key, text)
            return text
        except Exception as e:
            logger.error("AI call failed: %s", e)
            return ""

    def send_json(
        self,
        prompt: str,
        system: str = "",
        temperature: float | None = None,
    ) -> dict:
        """Send a prompt expecting JSON response. Returns parsed dict or {} on failure."""
        import json

        text = self.send(prompt, system=system, temperature=temperature or 0.0)
        if not text:
            return {}
        try:
            text = text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning("AI returned non-JSON response")
            return {"raw": text}

    def _cache_key(self, prompt: str, system: str, temperature: float) -> str:
        data = f"{self.provider}:{self.model}:{temperature}:{system}:{prompt}"
        return hashlib.sha256(data.encode()).hexdigest()

    def _read_cache(self, key: str) -> str | None:
        cache_file = CACHE_DIR / f"{key}.txt"
        if cache_file.exists():
            try:
                return cache_file.read_text(encoding="utf-8")
            except Exception:
                return None
        return None

    def _write_cache(self, key: str, text: str) -> None:
        try:
            (CACHE_DIR / f"{key}.txt").write_text(text, encoding="utf-8")
        except Exception:
            pass


_ai_client: AIClient | None = None


def get_ai_client() -> AIClient:
    global _ai_client
    if _ai_client is None:
        _ai_client = AIClient()
    return _ai_client
