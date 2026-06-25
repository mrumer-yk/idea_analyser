import httpx
import pytest
import respx

from backend.research.tavily import TavilyProvider
from backend.research.fetcher import PageFetcher


@respx.mock
async def test_tavily_maps_results():
    respx.post("https://api.tavily.com/search").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "title": "Razorpay Pricing",
                        "url": "https://razorpay.com/pricing/",
                        "content": "2% per transaction",
                        "raw_content": "full page text",
                    }
                ]
            },
        )
    )
    provider = TavilyProvider(api_key="k")
    results = await provider.search("razorpay pricing india", max_results=3)
    assert len(results) == 1
    assert results[0].url == "https://razorpay.com/pricing/"
    assert results[0].snippet == "2% per transaction"
    assert results[0].raw_content == "full page text"


def test_tavily_requires_key():
    with pytest.raises(ValueError):
        TavilyProvider(api_key="")


@respx.mock
async def test_page_fetcher_extracts_text():
    html = """
    <html><head><title>Acme Pricing</title></head>
    <body><nav>menu</nav>
    <article><h1>Plans</h1><p>Our pro plan costs 999 rupees per month.</p></article>
    <footer>copyright</footer></body></html>
    """
    respx.get("https://acme.in/pricing").mock(
        return_value=httpx.Response(200, text=html)
    )
    fetcher = PageFetcher()
    page = await fetcher.fetch("https://acme.in/pricing")
    assert page.ok
    assert "999 rupees" in page.text  # main content extracted
    assert "<article>" not in page.text  # html stripped to readable text


@respx.mock
async def test_page_fetcher_handles_error():
    respx.get("https://broken.in").mock(return_value=httpx.Response(500))
    fetcher = PageFetcher()
    page = await fetcher.fetch("https://broken.in")
    assert not page.ok
    assert page.error
