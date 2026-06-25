import httpx
import pytest
import respx

from backend.config import Settings
from backend.llm.factory import get_llm_client
from backend.llm.azure_client import AzureFoundryClient
from backend.llm.anthropic_client import AnthropicClient


def test_factory_selects_azure():
    s = Settings(
        llm_provider="azure",
        azure_foundry_endpoint="https://x.openai.azure.com",
        azure_foundry_api_key="k",
        azure_foundry_deployment="gpt",
    )
    client = get_llm_client(s)
    assert isinstance(client, AzureFoundryClient)
    assert client.name == "azure"


def test_factory_selects_anthropic():
    s = Settings(llm_provider="anthropic", anthropic_api_key="k")
    client = get_llm_client(s)
    assert isinstance(client, AnthropicClient)
    assert client.name == "anthropic"


def test_factory_unknown_provider_raises():
    s = Settings(llm_provider="bogus")
    with pytest.raises(ValueError):
        get_llm_client(s)


def test_azure_requires_config():
    with pytest.raises(ValueError):
        AzureFoundryClient(endpoint="", api_key="", deployment="", api_version="v")


@respx.mock
async def test_azure_complete_parses_response():
    route = respx.post(url__regex=r".*/chat/completions.*").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "1",
                "model": "gpt",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": '{"ok": true}'},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 11, "completion_tokens": 7, "total_tokens": 18},
            },
        )
    )
    client = AzureFoundryClient(
        endpoint="https://x.openai.azure.com",
        api_key="k",
        deployment="gpt",
        api_version="2024-10-21",
    )
    resp = await client.complete("sys", "user", json_mode=True)
    assert route.called
    assert resp.text == '{"ok": true}'
    assert resp.input_tokens == 11
    assert resp.output_tokens == 7


@respx.mock
async def test_anthropic_complete_prefills_json():
    route = respx.post("https://api.anthropic.com/v1/messages").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "msg",
                "type": "message",
                "role": "assistant",
                "model": "claude",
                "content": [{"type": "text", "text": '"ok": true}'}],
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 9, "output_tokens": 4},
            },
        )
    )
    client = AnthropicClient(api_key="k", model="claude-opus-4-8")
    resp = await client.complete("sys", "user", json_mode=True)
    assert route.called
    # prefilled "{" is re-attached -> valid JSON object string
    assert resp.text == '{"ok": true}'
    assert resp.input_tokens == 9
    assert resp.output_tokens == 4
