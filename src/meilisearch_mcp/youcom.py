import os
from typing import Any, Dict, List, Optional

import httpx

YDC_SEARCH_URL = "https://ydc-index.io/v1/search"


class YouComSearchError(Exception):
    pass


class YouComSearchClient:
    def __init__(self, api_key: Optional[str] = None, timeout: float = 10.0):
        self.api_key = api_key or os.getenv("YDC_API_KEY")
        self.timeout = timeout

    def is_enabled(self) -> bool:
        return bool(self.api_key)

    def search(self, query: str, count: int = 5) -> Dict[str, Any]:
        if not self.api_key:
            raise YouComSearchError("YDC_API_KEY is not set")

        response = httpx.get(
            YDC_SEARCH_URL,
            params={"query": query, "count": count},
            headers={"X-API-Key": self.api_key},
            timeout=self.timeout,
        )
        if response.status_code >= 400:
            raise YouComSearchError(
                f"You.com search failed with status {response.status_code}: {response.text}"
            )
        return response.json()


def format_youcom_results(payload: Dict[str, Any], query: str) -> str:
    results = payload.get("results", {})
    web = results.get("web", []) or []
    news = results.get("news", []) or []
    lines: List[str] = [f"You.com results for '{query}':"]
    for section_name, section in (("web", web), ("news", news)):
        if not section:
            continue
        lines.append(f"\n{section_name.upper()} RESULTS")
        for item in section[:10]:
            title = item.get("title") or "Untitled"
            url = item.get("url") or ""
            description = item.get("description") or ""
            lines.append(f"- {title}")
            if url:
                lines.append(f"  {url}")
            if description:
                lines.append(f"  {description}")
    if len(lines) == 1:
        lines.append("No results found.")
    return "\n".join(lines)
