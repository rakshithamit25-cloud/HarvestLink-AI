import json
import logging
import httpx
from typing import Optional, Dict, Any, List
from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMClient:
    """
    Plain HTTPS client for OpenAI-compatible chat completion endpoints (e.g. Groq).
    Uses httpx directly without any external SDK.
    Timeout: 8 seconds. At most 1 retry.
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 8.0,
        max_retries: int = 1
    ):
        self.api_key = api_key if api_key is not None else settings.LLM_API_KEY
        self.base_url = (base_url or settings.LLM_BASE_URL).rstrip("/")
        self.model = model if model is not None else settings.LLM_MODEL
        self.timeout = timeout
        self.max_retries = max_retries

    def is_configured(self) -> bool:
        """Returns True only if both API key and model name are present."""
        return bool(self.api_key and self.api_key.strip() and self.model and self.model.strip())

    def chat_completion_json(self, messages: List[Dict[str, str]]) -> Optional[Dict[str, Any]]:
        """
        Sends chat completion request expecting a JSON object response.
        Retries at most once on network error/timeout.
        Returns parsed JSON dict if valid, else None.
        Never logs API keys or full payload.
        """
        if not self.is_configured():
            return None

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key.strip()}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model.strip(),
            "messages": messages,
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        }

        attempts = 0
        max_attempts = 1 + self.max_retries  # 1 initial + max 1 retry = 2

        while attempts < max_attempts:
            attempts += 1
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(url, json=payload, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        choices = data.get("choices", [])
                        if not choices:
                            logger.warning("LLM response had no choices.")
                            return None

                        content = choices[0].get("message", {}).get("content", "")
                        if not content:
                            return None

                        # Parse JSON content
                        try:
                            parsed_json = json.loads(content)
                            if isinstance(parsed_json, dict):
                                return parsed_json
                            else:
                                logger.warning("LLM output is not a JSON object.")
                                return None
                        except (json.JSONDecodeError, TypeError):
                            logger.warning("LLM output was not valid JSON.")
                            return None
                    else:
                        logger.warning(f"LLM request returned HTTP status {resp.status_code} (attempt {attempts}/{max_attempts})")
            except (httpx.TimeoutException, httpx.NetworkError) as e:
                logger.warning(f"LLM request encountered network error/timeout (attempt {attempts}/{max_attempts}): {type(e).__name__}")
            except Exception as e:
                logger.warning(f"LLM unexpected error during request: {type(e).__name__}")
                return None

        return None
