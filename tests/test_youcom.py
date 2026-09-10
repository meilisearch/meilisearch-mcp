from src.meilisearch_mcp.server import create_server
from src.meilisearch_mcp.youcom import format_youcom_results, YouComSearchClient




def test_format_youcom_results():
    payload = {
        "results": {
            "web": [
                {
                    "title": "Example",
                    "url": "https://example.com",
                    "description": "A result",
                }
            ],
            "news": [],
        }
    }

    text = format_youcom_results(payload, "example query")

    assert "You.com results for 'example query':" in text
    assert "Example" in text
    assert "https://example.com" in text
    assert "A result" in text


def test_youcom_client_defaults_to_disabled(monkeypatch):
    monkeypatch.delenv("YDC_API_KEY", raising=False)
    server = create_server()
    assert isinstance(server.youcom_client, YouComSearchClient)
    assert not server.youcom_client.is_enabled()
