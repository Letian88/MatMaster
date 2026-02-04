"""
HTTP client for the remote MatMaster memory service (FastAPI).

Provides: memory_write, memory_retrieve, memory_list, format_short_term_memory.
Base URL is from constant (101.126.90.82:8002); scripts can override via base_url.
Timeouts: connect 3s, read 10s.
"""

import logging
from typing import Any, Optional

import requests

from agents.matmaster_agent.constant import MEMORY_SERVICE_URL

logger = logging.getLogger(__name__)

_CONNECT_TIMEOUT = 3
_READ_TIMEOUT = 10


def _base(base_url: Optional[str] = None) -> str:
    url = (base_url or MEMORY_SERVICE_URL).strip()
    if not url.startswith('http'):
        url = f'http://{url}'
    return url.rstrip('/')


def memory_write(
    session_id: str,
    text: str,
    metadata: Optional[dict[str, Any]] = None,
    base_url: Optional[str] = None,
) -> None:
    """Write one insight to the memory service for the given session."""
    payload = {
        'session_id': session_id,
        'text': text,
        'metadata': metadata or {},
    }
    try:
        r = requests.post(
            f'{_base(base_url)}/write',
            json=payload,
            timeout=(_CONNECT_TIMEOUT, _READ_TIMEOUT),
        )
        r.raise_for_status()
    except Exception as e:
        logger.warning('memory_write failed: %s', e)


def memory_retrieve(
    session_id: str,
    query: str,
    limit: int = 10,
    base_url: Optional[str] = None,
) -> list[str]:
    """Retrieve relevant memory texts for the session and query. Returns list of text snippets."""
    payload = {
        'session_id': session_id,
        'query': query,
        'limit': limit,
    }
    try:
        r = requests.post(
            f'{_base(base_url)}/retrieve',
            json=payload,
            timeout=(_CONNECT_TIMEOUT, _READ_TIMEOUT),
        )
        r.raise_for_status()
        data = r.json()
        docs = data.get('documents') or data.get('results') or []
        if isinstance(docs, list):
            return [d.get('text', d) if isinstance(d, dict) else str(d) for d in docs]
        return []
    except Exception as e:
        logger.debug('memory_retrieve failed: %s', e)
        return []


def memory_list(
    session_id: Optional[str] = None,
    limit: Optional[int] = None,
    base_url: Optional[str] = None,
) -> list[dict[str, Any]]:
    """List stored documents, optionally filtered by session_id and limit."""
    params: dict[str, Any] = {}
    if session_id is not None:
        params['session_id'] = session_id
    if limit is not None:
        params['limit'] = limit
    try:
        r = requests.get(
            f'{_base(base_url)}/list',
            params=params or None,
            timeout=(_CONNECT_TIMEOUT, _READ_TIMEOUT),
        )
        r.raise_for_status()
        data = r.json()
        return data.get('documents') or data.get('data') or data if isinstance(data, list) else []
    except Exception as e:
        logger.warning('memory_list failed: %s', e)
        return []


def format_short_term_memory(
    query_text: str,
    session_id: str,
    base_url: Optional[str] = None,
    limit: int = 10,
) -> str:
    """
    Retrieve session memory for the given query and format as a single block
    for injection into prompts. Returns empty string if no memory or on error.
    """
    texts = memory_retrieve(
        session_id=session_id,
        query=query_text or 'general',
        limit=limit,
        base_url=base_url,
    )
    if not texts:
        return ''
    lines = [f'- {t.strip()}' for t in texts if (t and isinstance(t, str))]
    if not lines:
        return ''
    return 'Session Memory (relevant):\n' + '\n'.join(lines)
