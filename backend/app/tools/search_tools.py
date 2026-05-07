
from __future__ import annotations
from typing import Any
import httpx
from langchain_core.tools import ToolException, tool
from langchain_tavily import TavilySearch
from app.config.settings import get_settings
from app.schema.search import SearchHit, SearchToolResponse

def _truncate(text: str, max_len: int = 12000) -> str:
    t = (text or "").strip()
    return t if len(t) <= max_len else t[: max_len - 24].rstrip() + "\n…(truncated)"


@tool
def tavily_web_search(query: str) -> str:
    """Search the public web using Tavily."""
    key = get_settings().agents.tavily_api_key
    q = (query or "").strip()
    if not key:
        return SearchToolResponse(provider="tavily", query=q, error="Tavily is not configured: set TAVILY_API_KEY in the environment.").to_agent_text()
    if not q:
        return SearchToolResponse(provider="tavily", query=q, error="Query is empty.").to_agent_text()
    client = TavilySearch(tavily_api_key=key, max_results=8, search_depth="basic", include_answer="basic", include_raw_content="markdown")
    try:
        raw = client.invoke({"query": q})
    except Exception as exc:
        return SearchToolResponse(provider="tavily", query=q, error=str(exc)).to_agent_text()
    if not isinstance(raw, dict):
        return SearchToolResponse(provider="tavily", query=q, error="Unexpected Tavily return type.").to_agent_text()
    err = raw.get("error")
    if err is not None:
        return SearchToolResponse(provider="tavily", query=q, error=str(err)).to_agent_text()
    overview = raw.get("answer")
    if overview is not None and not isinstance(overview, str):
        overview = str(overview)
    rows = raw.get("results")
    if not isinstance(rows, list):
        return SearchToolResponse(provider="tavily", query=q, overview=overview, error="Missing or invalid 'results' in Tavily response.").to_agent_text()
    hits = []
    for i, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            continue
        title = str(row.get("title", ""))
        url = str(row.get("url", ""))
        content = str(row.get("content", ""))
        raw_content = str(row.get("raw_content") or "")
        body = f"{content}\n\n### Page content (markdown)\n{raw_content}" if raw_content else content
        score = row.get("score")
        rel = float(score) if isinstance(score, (int, float)) else None
        meta = {"favicon": row.get("favicon")} if row.get("favicon") else {}
        hits.append(SearchHit(rank=i, title=title, url=url, summary=_truncate(body), source="tavily", relevance_score=rel, meta=meta))
    return SearchToolResponse(provider="tavily", query=q, overview=overview, hits=hits).to_agent_text()

@tool
def brave_web_search(query: str) -> str:
    """Search the public web using Brave LLM Context."""
    key = get_settings().agents.brave_search_api_key
    q = (query or "").strip()
    if not key:
        return SearchToolResponse(provider="brave", query=q, error="Brave Search is not configured: set BRAVE_SEARCH_API_KEY.").to_agent_text()
    if not q:
        return SearchToolResponse(provider="brave", query=q, error="Query is empty.").to_agent_text()
    try:
        with httpx.Client(timeout=45.0) as client:
            r = client.get(
                "https://api.search.brave.com/res/v1/llm/context",
                params={
                    "q": q,
                    "count": 15,
                    "maximum_number_of_urls": 15,
                    "maximum_number_of_tokens": 8192,
                    "context_threshold_mode": "balanced",
                },
                headers={
                    "Accept": "application/json",
                    "X-Subscription-Token": key,
                },
            )
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPError as exc:
        return SearchToolResponse(provider="brave", query=q, error=f"Brave LLM Context request failed: {exc}").to_agent_text()
    if not isinstance(data, dict):
        return SearchToolResponse(provider="brave", query=q, error="Unexpected Brave response type.").to_agent_text()
    grounding = data.get("grounding")
    if not isinstance(grounding, dict):
        return SearchToolResponse(provider="brave", query=q, error="Missing or invalid 'grounding' in Brave LLM Context response.").to_agent_text()
    sources_meta = data.get("sources") if isinstance(data.get("sources"), dict) else {}
    hits = []
    rank = 0
    def _append_block(block: dict[str, Any], kind: str):
        nonlocal rank
        url = str(block.get("url") or "").strip()
        title = str(block.get("title") or "").strip()
        snippets = block.get("snippets")
        summary = _truncate("\n\n".join([str(s).strip() for s in snippets if str(s).strip()]) if isinstance(snippets, list) else "")
        if not url and not summary:
            return
        rank += 1
        meta = {"brave_grounding": kind}
        src = sources_meta.get(url) if url else None
        if isinstance(src, dict):
            if src.get("hostname"):
                meta["site"] = src.get("hostname")
            if src.get("age") is not None:
                meta["age"] = src.get("age")
            if src.get("title") and not title:
                title = str(src["title"])
        hits.append(SearchHit(rank=rank, title=title or url or f"Source {rank}", url=url, summary=summary or "(no extracted snippets)", source="brave", relevance_score=None, meta=meta))
    for row in grounding.get("generic") or []:
        if isinstance(row, dict):
            _append_block(row, kind="generic")
    poi = grounding.get("poi")
    if isinstance(poi, dict):
        _append_block(poi, kind="poi")
    for row in grounding.get("map") or []:
        if isinstance(row, dict):
            _append_block(row, kind="map")
    if not hits:
        return SearchToolResponse(provider="brave", query=q, overview="Brave LLM Context returned no grounded excerpts for this query.", hits=[]).to_agent_text()
    overview_chunks = [h.summary[:500] for h in hits[:3] if h.summary and h.summary != "(no extracted snippets)"]
    if sum(len(x) for x in overview_chunks) > 1400:
        overview_chunks = overview_chunks[:1]
    overview = _truncate("\n---\n".join(overview_chunks), max_len=2000) if overview_chunks else None
    return SearchToolResponse(provider="brave", query=q, overview=overview, hits=hits).to_agent_text()

SEARCH_TOOLS = (tavily_web_search, brave_web_search)
