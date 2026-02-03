import logging
from typing import Any, AsyncGenerator, Optional, override

from google.adk.agents import InvocationContext
from google.adk.events import Event

from agents.matmaster_agent.constant import MATMASTER_AGENT_NAME
from agents.matmaster_agent.core_agents.comp_agents.dntransfer_climit_agent import (
    DisallowTransferAndContentLimitLlmAgent,
)
from agents.matmaster_agent.flow_agents.thinking_agent.constant import (
    FIRST_ROUND_NEED_REVISION,
    FIRST_ROUND_READY,
    REVISION_OK,
)
from agents.matmaster_agent.flow_agents.thinking_agent.prompt import (
    get_thinking_instruction,
    get_thinking_revision_instruction,
)
from agents.matmaster_agent.logger import PrefixFilter

logger = logging.getLogger(__name__)
logger.addFilter(PrefixFilter(MATMASTER_AGENT_NAME))
logger.setLevel(logging.INFO)


def _collect_text_from_event(event: Event) -> str:
    if getattr(event, 'partial', True) or not getattr(event, 'content', None):
        return ''
    parts = getattr(event.content, 'parts', None) or []
    return ''.join(
        getattr(p, 'text', None) or ''
        for p in parts
        if getattr(p, 'text', None) is not None
    ).strip()


def _last_line(s: str) -> str:
    """Last non-empty line, stripped."""
    lines = [ln.strip() for ln in s.strip().splitlines() if ln.strip()]
    return lines[-1] if lines else ''


def _strip_first_round_marker(text: str) -> str:
    """Remove trailing READY or NEED_REVISION line so downstream only sees reasoning."""
    if not text:
        return text
    lines = text.strip().splitlines()
    while lines:
        last = lines[-1].strip().upper()
        if (
            last == FIRST_ROUND_READY.upper()
            or last == FIRST_ROUND_NEED_REVISION.upper()
        ):
            lines.pop()
            continue
        break
    return '\n'.join(lines).strip()


def _model_wants_revision(thinking_text: str) -> bool:
    """True iff the model ended with NEED_REVISION (model decides, no hardcoded hints)."""
    return _last_line(thinking_text).upper() == FIRST_ROUND_NEED_REVISION.upper()


class ThinkingAgent(DisallowTransferAndContentLimitLlmAgent):
    """Agent that produces free-form reasoning about tool selection and order before planning.
    When _thinking_params is set, runs an internal loop: first round, then a revision round
    only if the model ended its first reply with NEED_REVISION (model decides, no keyword lists).
    """

    _thinking_params: Optional[dict[str, Any]] = None

    def set_thinking_params(
        self,
        available_tools_with_info: str,
        session_file_summary: str,
        original_query: str,
        expanded_query: str,
    ) -> None:
        """Set params for self-contained loop mode. Cleared after run_async."""
        self._thinking_params = {
            'available_tools_with_info': available_tools_with_info,
            'session_file_summary': session_file_summary,
            'original_query': original_query,
            'expanded_query': expanded_query,
        }

    @override
    async def _run_events(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        params = self._thinking_params
        if params is None:
            async for event in super()._run_events(ctx):
                yield event
            return

        try:
            self.instruction = get_thinking_instruction(
                params['available_tools_with_info'],
                params['session_file_summary'],
                params['original_query'],
                params['expanded_query'],
            )
            last_full_text = ''
            async for event in super()._run_events(ctx):
                yield event
                t = _collect_text_from_event(event)
                if t:
                    last_full_text = t
            thinking_text = last_full_text.strip()

            # Loop: only run revision if the model asked for it (last line NEED_REVISION)
            if thinking_text and _model_wants_revision(thinking_text):
                previous_reasoning = _strip_first_round_marker(thinking_text)
                self.instruction = get_thinking_revision_instruction(
                    params['available_tools_with_info'],
                    params['session_file_summary'],
                    params['original_query'],
                    params['expanded_query'],
                    previous_reasoning=previous_reasoning,
                )
                last_full_text = ''
                async for event in super()._run_events(ctx):
                    yield event
                    t = _collect_text_from_event(event)
                    if t:
                        last_full_text = t
                round_text = last_full_text.strip()
                if round_text.upper().strip() != REVISION_OK:
                    thinking_text = round_text
                else:
                    thinking_text = previous_reasoning or thinking_text

            # Downstream gets reasoning only (no READY/NEED_REVISION marker)
            self._last_thinking_text = _strip_first_round_marker(thinking_text)
        except Exception:
            self._last_thinking_text = None
            raise
        finally:
            self._thinking_params = None
