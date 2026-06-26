"""Azure AI Foundry client.

Supports both Foundry endpoint styles:
- OpenAI-compatible v1 endpoint (".../openai/v1" or "*.services.ai.azure.com")
  -> plain ``AsyncOpenAI`` with ``base_url`` (model = deployment, no api-version).
- Classic Azure OpenAI endpoint ("*.openai.azure.com")
  -> ``AsyncAzureOpenAI`` with deployment + api-version.

Reasoning-family models (gpt-5*, o1/o3/o4*) require ``max_completion_tokens``
instead of ``max_tokens`` and only support the default temperature, so those
params are adapted per model.
"""
from __future__ import annotations

from .base import LLMResponse

_REASONING_HINTS = ("gpt-5", "o1", "o3", "o4")


def _is_reasoning_model(deployment: str) -> bool:
    d = deployment.lower()
    return any(h in d for h in _REASONING_HINTS)


class AzureFoundryClient:
    name = "azure"

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        deployment: str,
        api_version: str,
    ) -> None:
        if not (endpoint and api_key and deployment):
            raise ValueError(
                "Azure Foundry is not configured: set AZURE_FOUNDRY_ENDPOINT, "
                "AZURE_FOUNDRY_API_KEY and AZURE_FOUNDRY_DEPLOYMENT."
            )
        self._deployment = deployment.strip()
        self._endpoint = endpoint.strip().strip('"').strip("'")
        if "/openai/deployments/" in self._endpoint:
            self._endpoint = self._endpoint.split("/openai/deployments/", 1)[0]
        self._api_key = api_key.strip()
        self._api_version = (api_version or "2024-10-21").strip()
        self._client = None  # lazy
        ep = self._endpoint.lower()
        self._use_v1 = "/openai/v1" in ep

    def _ensure_client(self):
        if self._client is None:
            if self._use_v1:
                from openai import AsyncOpenAI

                self._client = AsyncOpenAI(
                    base_url=self._endpoint.rstrip("/"),
                    api_key=self._api_key,
                )
            else:
                from openai import AsyncAzureOpenAI

                self._client = AsyncAzureOpenAI(
                    azure_endpoint=self._endpoint,
                    api_key=self._api_key,
                    api_version=self._api_version,
                )
        return self._client

    async def complete(
        self,
        system: str,
        user: str,
        *,
        json_mode: bool = False,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> LLMResponse:
        client = self._ensure_client()
        kwargs = {
            "model": self._deployment,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if _is_reasoning_model(self._deployment):
            kwargs["max_completion_tokens"] = max_tokens
            # reasoning models only accept the default temperature -> omit it
        else:
            kwargs["max_tokens"] = max_tokens
            kwargs["temperature"] = temperature
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        resp = await client.chat.completions.create(**kwargs)
        text = resp.choices[0].message.content or ""
        usage = resp.usage
        return LLMResponse(
            text=text,
            input_tokens=getattr(usage, "prompt_tokens", 0) or 0,
            output_tokens=getattr(usage, "completion_tokens", 0) or 0,
        )
