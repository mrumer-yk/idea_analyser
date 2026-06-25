"""Provider-agnostic LLM client interface.

Every concrete provider (Azure AI Foundry now, Anthropic later) implements the
same ``complete`` coroutine so the rest of the system never imports a vendor
SDK directly. Switch providers via the ``LLM_PROVIDER`` env var.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class LLMResponse:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0


@runtime_checkable
class LLMClient(Protocol):
    name: str

    async def complete(
        self,
        system: str,
        user: str,
        *,
        json_mode: bool = False,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> LLMResponse:
        """Run a single-turn completion.

        When ``json_mode`` is True the provider is instructed to return a single
        JSON object as its entire output.
        """
        ...
