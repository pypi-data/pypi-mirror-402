"""MCP server for AgentHotspot OSS connector search.

Exposes tools: `search_connectors`.
Uses the public API endpoint to search connectors.
"""

from typing import Any

import httpx
from fastmcp import FastMCP

mcp = FastMCP("AgentHotspot OSS Search")

# Public API endpoint
CONNECTORS_API_URL = "https://agenthotspot.com/api/public/search"
DEFAULT_LIMIT = 10
HTTP_TIMEOUT_S = 30.0


def _as_str(value: Any) -> str:
    """Convert any value to a string safely."""
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    return str(value)


def _as_str_list(value: Any) -> list[str]:
    """Convert any value to a list of strings safely."""
    if isinstance(value, list):
        return [s for s in (_as_str(v).strip() for v in value) if s]
    s = _as_str(value).strip()
    return [s] if s else []


@mcp.tool()
async def search_connectors(query: str = "") -> list[dict[str, Any]]:
    """Search AgentHotspot OSS connectors.
    
    Searches the AgentHotspot marketplace for MCP connectors matching
    the specified query. Returns a list of connectors with their names,
    descriptions, tags, and URLs.
    
    Args:
        query: Search query string. Leave empty to browse all connectors.
        
    Returns:
        List of connector dictionaries containing:
        - name: The connector name
        - url: Direct link to the connector on AgentHotspot
        - description: Brief description of the connector
        - tags: List of relevant tags
        
    Example:
        >>> await search_connectors("github")
        [{"name": "GitHub MCP", "url": "...", "description": "...", "tags": [...]}]
    """
    params: dict[str, Any] = {"limit": DEFAULT_LIMIT}
    q = query.strip()
    if q:
        params["search"] = q

    timeout = httpx.Timeout(HTTP_TIMEOUT_S)
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(
                CONNECTORS_API_URL,
                params=params,
                headers={"User-Agent": "agenthotspot-mcp/1.0"},
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.TimeoutException:
        raise RuntimeError(f"Request timed out after {HTTP_TIMEOUT_S}s")
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(f"HTTP {exc.response.status_code}: {exc.response.text[:100]}")
    except Exception as exc:
        raise RuntimeError(f"Failed to fetch connectors: {exc}")

    # Public API returns { results: [...], total, limit, offset, hasMore }
    if isinstance(data, dict):
        items = data.get("results") or data.get("connectors") or []
    elif isinstance(data, list):
        items = data
    else:
        raise RuntimeError("Unexpected JSON shape from API")

    results: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue

        connector_id = _as_str(item.get("id")).strip()
        name = _as_str(item.get("name") or item.get("title")).strip()
        description = _as_str(item.get("description") or item.get("summary")).strip()
        tags = _as_str_list(item.get("tags"))
        url = f"https://agenthotspot.com/connectors/{connector_id}?t=oss" if connector_id else ""

        results.append(
            {
                "name": name,
                "url": url,
                "description": description,
                "tags": tags,
            }
        )

    return results


def main() -> None:
    """Run the MCP server with stdio transport."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
