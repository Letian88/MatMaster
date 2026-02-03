def get_thinking_instruction(
    available_tools_with_info: str,
    session_file_summary: str,
    original_query: str,
    expanded_query: str,
) -> str:
    return f"""The assistant reasons about tool selection and ordering before creating an execution plan. The output is free-form reasoning only (no JSON). Use {{target_language}}. Include detour and reflection: re-check and revise when preconditions or cost suggest a change.

Begin the reasoning with a short meaningless token such as "OK," "Hmm," "嗯," "哦," according to the target language (e.g. "OK, let me parse what the user provided..." or "嗯, 先看用户给了什么..."). Then continue in plain text. Do not use markdown, bullets, or numbered sections; write short, natural sentences.

Output format: Do not copy section titles or tag names into the output; refer to the user's request and the task list in plain wording (e.g. "根据用户原始描述和本轮拆分出的任务" or "from the user message and the expanded task list"). When referring to the requester, always use "the user" or "用户"; do not use personal pronouns (e.g. they, their, he, she).

Distinguish two inputs below: "Original user message" is the raw user message; "Task after expansion (this round)" is the same request after expansion/splitting. Reason over both: parse entities from the original, and align tool choice with the expanded task list (no extra steps the user did not ask for).

Parse user input first: Before choosing tools, identify what the user has provided in the original message and in the expanded task list. Extract entities: (a) SMILES string — if the request contains a SMILES-like string (e.g. element symbols C, N, O, S, P; bonds #, =, -; parentheses; ring-closure digits; patterns like N#C, C#N, (C#N), Fe-2), treat it as SMILES and look for tools whose Prerequisites include "SMILES" or "SMILES string". (b) Chemical formula, file URL, space group, target properties, etc. Do not conclude "user has no input" or "no tool accepts user input" without first parsing. If a SMILES-like string appears, state explicitly "The user provided a SMILES string: ..." and then pick tools that accept SMILES.

CRITICAL — When the user provided SMILES: Search the entire <Available Tools With Info> for the exact strings "SMILES" or "SMILES string" (in tool names, "What it does", "Prerequisites / Inputs", or "When to use"). If any tool entry contains that text, that tool MUST be used for the step that builds structure from SMILES. Do not conclude "no tool accepts SMILES" until the list has been literally searched. If a matching tool is found (e.g. build_molecule_structures_from_smiles), use it as the first step; if none is found, state "The list was searched for 'SMILES' and no matching tool was found."

CRITICAL — Grounding: Only use tools that appear in <Available Tools With Info> below. When describing what a tool does or needs, use only the exact "What it does", "Prerequisites / Inputs", and "Outputs" from that tool's entry. Do not invent or paraphrase capabilities. If the list says a tool needs "Molecule file path", it does not accept SMILES unless the list says so.

Match user request to tool scope: Each tool's "What it does" and "When to use" must fit what the user has (after parsing) and what the user wants. Examples: (a) User has SMILES and needs a molecule/structure — pick a tool whose Prerequisites include "SMILES" or "SMILES string" (e.g. build_molecule_structures_from_smiles); do not pick a crystal-structure tool that needs "space groups" and "Target properties" for a single molecule from SMILES. (b) User has no uploaded file — do not start with a tool that needs "Molecule file path" unless a prior step provides it. (c) If after parsing no tool accepts the user's inputs, conclude clearly in {{target_language}} that the list has no tool for the parsed inputs and the user may need to supply something else (e.g. upload a file).

Do not add steps the user did not ask for: Only include steps the user explicitly requested (in the original message or the expanded task list) or that are strictly required by a tool's Prerequisites (e.g. a structure file is needed because the next tool requires it). Do not add "helpful" extra steps (e.g. structure optimization, relaxation) unless the user explicitly asked. If a step would be optional (e.g. optimize_structure when the user only asked to build a structure and generate Gaussian input), omit it or state that it is optional and the user did not request it.

<Available Tools With Info>
{available_tools_with_info}

<Session File Info>
{session_file_summary}

--- Original user message ---
{original_query}

--- Task after expansion (this round) ---
{expanded_query}

Reason in plain text ({{target_language}}): parse both, propose tools and order, check preconditions, briefly consider cost, and reflect or revise if needed. Do not repeat the section titles above in the output. When referring to the requester, always use "the user" or "用户"; do not use personal pronouns. No JSON, no markdown.
"""


def get_thinking_revision_instruction(
    available_tools_with_info: str,
    session_file_summary: str,
    original_query: str,
    expanded_query: str,
    previous_reasoning: str,
) -> str:
    return f"""Review and correct prior reasoning about tool choice and order. Output plain text only in {{target_language}}. Do not use markdown, bullets, or numbered sections.

<Available Tools With Info>
{available_tools_with_info}

<Session File Info>
{session_file_summary}

--- Original user message ---
{original_query}

--- Task after expansion (this round) ---
{expanded_query}

--- Previous reasoning ---
{previous_reasoning}

Check: wrong tool for user input? Wrong order so a prerequisite is not met? Tool that needs SMILES but user gave SMILES and we did not use a SMILES tool? Extra step the user did not ask for? Plans that ignore the original message or the expanded task list?

If a real error is found, output a short corrected reasoning in plain text. Do not copy the section titles above. When referring to the requester, always use "the user" or "用户"; do not use personal pronouns. If the previous reasoning is fine, output exactly: OK

No JSON, no markdown.
"""
