"""
Memory: all operations go through the remote FastAPI memory service (HTTP).

Server (e.g. 101.126.90.82:8002): POST /api/v1/memory/write, /retrieve, /list.
This module is the HTTP client; on error we log and fallback (no raise), same pattern as icl.py.
"""

import logging
from typing import Any, Optional

import requests

from agents.matmaster_agent.constant import MEMORY_SERVICE_URL

logger = logging.getLogger(__name__)

DEFAULT_RETRIEVE_N_RESULTS = 5
MEMORY_REQUEST_TIMEOUT = (3, 3)  # (connect, read)


def _base_url(host_port: Optional[str] = None) -> str:
    """Normalize to http://host:port (no trailing slash)."""
    h = host_port or MEMORY_SERVICE_URL
    if "://" in h:
        return h.rstrip("/")
    return f"http://{h}".rstrip("/")


def memory_write(
    session_id: str,
    text: str,
    metadata: Optional[dict[str, Any]] = None,
    base_url: Optional[str] = None,
) -> None:
    """Write one piece of text to session memory via FastAPI. No-op on error (logged)."""
    url = f"{_base_url(base_url)}/api/v1/memory/write"
    try:
        resp = requests.post(
            url=url,
            json={
                "session_id": session_id,
                "text": text,
                "metadata": metadata or {},
            },
            timeout=MEMORY_REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
    except Exception as e:
        logger.info("memory_write fallback due to error: %s", e)


def memory_retrieve(
    session_id: str,
    query_text: str,
    n_results: int = DEFAULT_RETRIEVE_N_RESULTS,
    base_url: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Retrieve relevant chunks for session via FastAPI. Returns [] on error."""
    url = f"{_base_url(base_url)}/api/v1/memory/retrieve"
    try:
        resp = requests.post(
            url=url,
            json={
                "session_id": session_id,
                "query_text": query_text,
                "n_results": n_results,
            },
            timeout=MEMORY_REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json().get("data") or []
    except Exception as e:
        logger.info("memory_retrieve fallback due to error: %s", e)
        return []


def memory_list(
    session_id: Optional[str] = None,
    limit: Optional[int] = None,
    base_url: Optional[str] = None,
) -> list[dict[str, Any]]:
    """List documents via FastAPI (for scripts). Returns [] on error."""
    url = f"{_base_url(base_url)}/api/v1/memory/list"
    try:
        resp = requests.post(
            url=url,
            json={"session_id": session_id, "limit": limit},
            timeout=MEMORY_REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json().get("data") or []
    except Exception as e:
        logger.info("memory_list fallback due to error: %s", e)
        return []


def format_short_term_memory(
    query_text: str,
    session_id: str,
    n_results: int = DEFAULT_RETRIEVE_N_RESULTS,
) -> str:
    """Format retrieved session memory for prompts. Empty string on error or no results."""
    data = memory_retrieve(
        session_id=session_id,
        query_text=query_text or " ",
        n_results=n_results,
    )
    if not data:
        return ""
    lines = []
    for item in data:
        doc = item.get("document") or item.get("text", "")
        if doc:
            lines.append(doc.strip())
    return "\n".join(lines) if lines else ""
