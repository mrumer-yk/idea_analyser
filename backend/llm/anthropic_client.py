"""Anthropic / Claude client.

Used when ``LLM_PROVIDER=anthropic``. JSON mode is achieved by instructing the
model and prefilling the assistant turn with ``{`` so the entire reply is one
JSON object.
"""
from __future__ import annotations

from .base import LLMResponse


class AnthropicClient:
    name = "anthropic"

    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise ValueError("Anthropic is not configured: set ANTHROPIC_API_KEY.")
        self._api_key = api_key
        self._model = model
        self._client = None  # lazy

    def _ensure_client(self):
        if self._client is None:
            from anthropic import AsyncAnthropic

            self._client = AsyncAnthropic(api_key=self._api_key)
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
        messages = [{"role": "user", "content": user}]
        sys_prompt = system
        if json_mode:
            sys_prompt = (
                system
                + "\n\nReturn your entire response as a single valid JSON object. "
                "Do not include any prose, markdown fences, or commentary."
            )
            # Prefill forces the reply to start as JSON.
            messages.append({"role": "assistant", "content": "{"})

        resp = await client.messages.create(
            model=self._model,
            system=sys_prompt,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        text = "".join(
            block.text for block in resp.content if getattr(block, "type", "") == "text"
        )
        if json_mode:
            # Re-attach the prefilled opening brace.
            text = "{" + text
        return LLMResponse(
            text=text,
            input_tokens=resp.usage.input_tokens,
            output_tokens=resp.usage.output_tokens,
        )
