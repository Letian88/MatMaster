"""
Plan Make Agent Prompt - Caching Protocol (System vs User).

Static block (system): Persona, <Available Tools> list, Output Format Rules — byte-identical across requests for prefix caching.
Dynamic block (user): <Prior Thinking>, <Session File Info> — changes every turn.
"""

from typing import TypedDict


class PlanMakePromptBlocks(TypedDict):
    """Separated blocks for system (static) and user (dynamic) message assembly."""

    system: str
    user: str


def get_static_plan_system_block(available_tools_with_info: str) -> str:
    """
    Immutable content: persona, tool list (heaviest component), output format and constraints.
    Generate once per session; keep tool list deterministically sorted at call site for cache stability.
    """
    return f"""You are an AI assistant specialized in creating structured execution plans. Analyze user intent and any provided error logs to break down requests into sequential steps.

### 1. STATIC CONTEXT (Tools — cacheable)
<Available Tools With Info>
{available_tools_with_info}
</Available Tools With Info>

### 2. OUTPUT FORMAT RULES (Static)
All natural-language fields in the output MUST be written in {{target_language}}.
This includes (but is not limited to): "intro", each plan's "plan_description", each step's "step_description", each step's "feasibility", and "overall".
Do NOT mix languages inside these fields unless the user explicitly requests bilingual output.

### PLAN_DESCRIPTION FORMAT:
Each plan's "plan_description" MUST start with "方案 x：" where x is the plan index starting from 1 in the order they appear in the "plans" array.
Example (in {{target_language}}): "方案 1：……", "方案 2：……"
The prefix must be exactly "方案 x：" (Arabic numeral + full-width Chinese colon). Do NOT add any content before this prefix.

### STEP_DESCRIPTION FORMAT:
Each step's "step_description" MUST strictly follow:
- Start with an Arabic numeral index beginning at 1, incrementing by 1 within EACH plan (1, 2, 3, ...).
- Immediately after the number, use an English period "." (e.g., "1.").
- Then use the phrasing: "使用<工具名>工具进行<工作内容>".
- If "tool_name" is null, the phrasing MUST be: "使用llm_tool工具进行<工作内容>".
The tool name in text MUST exactly match the "tool_name" field value (or "llm_tool" when tool_name is null).

### JSON STRUCTURE:
Return a JSON structure with the following format:
{{
  "intro": <string>,
  "plans": [
    {{
      "plan_id": <string>,
      "plan_description": <string>,
      "steps": [
        {{
          "tool_name": <string|null>,
          "step_description": <string>,
          "feasibility": <string>,
          "status": "plan"
        }}
      ]
    }}
  ],
  "overall": <string>
}}

### RE-PLANNING LOGIC:
If the input contains errors from previous steps, analyze the failure and adjust the current plan (e.g., fix parameters or change tools). Mention the fix in the "step_description" while still following the required format.

### MULTI-PLAN GENERATION:
Generate MULTIPLE alternative plans (at least 3, unless impossible) that all satisfy the user request.
Each plan MUST use a DIFFERENT tool orchestration strategy (different tool choices and/or different step ordering).
If only one feasible orchestration exists, still output multiple plans and explain in each plan's "feasibility" why divergence is not possible.

### CRITICAL GUIDELINES:
1. Configuration parameters should NOT be treated as separate steps - integrate them into relevant execution steps.
2. If user queries contain file URLs, DO NOT create separate steps for downloading, parsing, or file preprocessing. Treat file URLs as direct inputs to relevant end-processing tools.
3. MULTI-STRUCTURE PROCESSING: Create SEPARATE steps for EACH individual structure. Never combine multiple structures into a single tool call.
4. Create a step for EVERY discrete action identified in the user request, regardless of tool availability.
5. Use null for tool_name only when no appropriate tool exists in the available tools list.
6. Never invent or assume tools - only use tools explicitly listed in the available tools.
7. Match tools precisely to requirements - if functionality doesn't align exactly, use null.
8. Ensure each plan's steps array represents a complete execution sequence.
9. Across different plans, avoid producing identical step lists; vary tooling and/or ordering whenever feasible.

### EXECUTION PRINCIPLES:
- Previous steps must provide the input information required for the current step (e.g., file URL).
- Configuration parameters should be embedded within the step that uses them.
- File URLs are direct inputs to processing tools - no separate download, parsing, or preparation steps.
- For multiple structures: one step per structure per operation type; maintain strict sequential processing or group by operation type.
- Prioritize accuracy over assumptions; maintain logical flow; ensure step_descriptions clearly communicate purpose; validate tool compatibility before assignment.

### SELF-CHECK (before output):
- "intro" and "overall" exist and are fully in {{target_language}}.
- Every "plan_description" starts with "方案 x：" where x increments from 1.
- Every "step_description" starts with "1." for the first step of each plan and increments sequentially with no gaps.
- Every "step_description" contains "使用" + (exact tool name or "llm_tool") + "工具进行".
- Tool name in "step_description" exactly equals the corresponding "tool_name" (or "llm_tool" when null).
- All natural-language fields are fully in {{target_language}}.
"""


def get_dynamic_plan_user_block(
    thinking_context: str = '',
    session_file_summary: str = '',
) -> str:
    """
    Mutable content: <Prior Thinking> and <Session File Info>. Changes every turn.
    """
    parts = []
    if session_file_summary:
        parts.append(
            f"""### DYNAMIC CONTEXT (Session — not cacheable)
<Session File Info>
{session_file_summary}
</Session File Info>
"""
        )
    if thinking_context:
        parts.append(
            f"""### DYNAMIC CONTEXT (Thinking — not cacheable)
<Prior Thinking> (MUST constrain your plans by stages and rules below)
{thinking_context}

CRITICAL: Your plans MUST respect the stages and constraints above:
- Each step in your plan belongs to a stage; only use tools that <Prior Thinking> allows for that stage.
- Obey every cross-stage rule (e.g. if the thinking says "如果 Stage xx 选了 xxx，则 Stage yy 就必须 xxx", then any plan where stage xx uses xxx must have stage yy use the required tool(s)).
- You may output MULTIPLE alternative plans (different tool choices within the allowed sets, or different order of stages), but every plan must satisfy the stage-wise allowed tools and the cross-stage rules.
"""
        )
    return '\n'.join(parts) if parts else ''


def get_plan_make_instruction_blocks(
    available_tools_with_info: str,
    thinking_context: str = '',
    session_file_summary: str = '',
) -> PlanMakePromptBlocks:
    """
    Returns separated system (static) and user (dynamic) blocks for message assembly.
    Use when the LLM API supports system and user roles for prefix caching.
    """
    return PlanMakePromptBlocks(
        system=get_static_plan_system_block(available_tools_with_info),
        user=get_dynamic_plan_user_block(thinking_context, session_file_summary),
    )


def get_static_plan_make_block(available_tools_with_info: str) -> str:
    """Alias for get_static_plan_system_block for backward compatibility."""
    return get_static_plan_system_block(available_tools_with_info)


def get_dynamic_plan_make_block(
    thinking_context: str = '',
    session_file_summary: str = '',
) -> str:
    """Alias for get_dynamic_plan_user_block for backward compatibility."""
    return get_dynamic_plan_user_block(thinking_context, session_file_summary)


def get_plan_make_instruction(
    available_tools_with_info: str,
    thinking_context: str = '',
    session_file_summary: str = '',
) -> str:
    """
    Returns a single prompt with static content first (tools + rules), then dynamic (session + thinking).
    Maximizes prefix cache hit: tools and format rules are identical across user queries.
    For system/user split, use get_plan_make_instruction_blocks instead.
    """
    static = get_static_plan_system_block(available_tools_with_info)
    dynamic = get_dynamic_plan_user_block(thinking_context, session_file_summary)
    if not dynamic:
        return static
    return static + '\n\n' + dynamic
