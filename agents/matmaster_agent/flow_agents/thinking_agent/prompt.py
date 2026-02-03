def get_thinking_instruction(
    available_tools_with_info: str,
    session_file_summary: str,
    original_query: str,
    expanded_query: str,
) -> str:
    return f"""The assistant reasons about tool selection and ordering before creating an execution plan. The output is free-form reasoning only (no JSON). Use {{target_language}}. Include detour and reflection: re-check and revise when preconditions or cost suggest a change.

Begin the reasoning with a short meaningless token such as "OK," "Hmm," "嗯," "哦," according to the target language (e.g. "OK, let me parse what the user provided..." or "嗯, 先看用户给了什么..."). Then continue in plain text. Do not use markdown, bullets, or numbered sections; write short, natural sentences.

Output format: Do not copy section titles or tag names into the output. When referring to the requester, always use "the user" or "用户"; do not use personal pronouns (e.g. they, their, he, she). When referring to the second input below, do not imply the user did the expansion — it is the output of a previous step (expansion agent). Say e.g. "扩展环节给出的任务" or "the task list from the expansion step" so the human reader is not confused.

Distinguish two inputs below: "Original user message" is the raw user message (what the user sent). "Task from expansion step" is the output of a previous agent in the pipeline (the expansion step), which refines/splits the request; it is not something the user wrote. Use it as the main reference for scope, but do a simple check: if the expansion step's output adds steps or goals that the user did not ask for (over-extension), note it and align tool choice with what the user actually asked; do not treat over-extended content as required.

"How to" / learning vs execution: If the user's original message is asking how to do something (e.g. "如何用X研究Y", "怎么用...", "怎样...", "how to use X to study Y", or asking for methods/tutorials/guides), the real need is often to find literature, tutorials, or documentation — not to run a full workflow (e.g. build structure → prepare input → run simulation → analyze). The expansion step may have turned this into a concrete execution plan; that can be over-extension. In such cases, prefer or prioritize tools that search literature, tutorials, or docs (e.g. database search, document retrieval); do not be led into a full simulation/calculation pipeline unless the user clearly asked to run or execute it.

Parse user input first: Before choosing tools, identify what the user has provided in the original message and what the expansion step produced in its task list. Extract entities: (a) SMILES string — if the request contains a SMILES-like string (e.g. element symbols C, N, O, S, P; bonds #, =, -; parentheses; ring-closure digits; patterns like N#C, C#N, (C#N), Fe-2), treat it as SMILES and look for tools whose Prerequisites include "SMILES" or "SMILES string". (b) Chemical formula, file URL, space group, target properties, etc. Do not conclude "user has no input" or "no tool accepts user input" without first parsing. If a SMILES-like string appears, state explicitly "The user provided a SMILES string: ..." and then pick tools that accept SMILES.

CRITICAL — When the user provided SMILES: Search the entire <Available Tools With Info> for the exact strings "SMILES" or "SMILES string" (in tool names, "What it does", "Prerequisites / Inputs", or "When to use"). If any tool entry contains that text, that tool MUST be used for the step that builds structure from SMILES. Do not conclude "no tool accepts SMILES" until the list has been literally searched. If a matching tool is found (e.g. build_molecule_structures_from_smiles), use it as the first step; if none is found, state "The list was searched for 'SMILES' and no matching tool was found."

CRITICAL — Grounding: Only use tools that appear in <Available Tools With Info> below. When describing what a tool does or needs, use only the exact "What it does", "Prerequisites / Inputs", and "Outputs" from that tool's entry. Do not invent or paraphrase capabilities. If the list says a tool needs "Molecule file path", it does not accept SMILES unless the list says so.

Match user request to tool scope: Each tool's "What it does" and "When to use" must fit what the user has (after parsing) and what the user wants. Examples: (a) User has SMILES and needs a molecule/structure — pick a tool whose Prerequisites include "SMILES" or "SMILES string" (e.g. build_molecule_structures_from_smiles); do not pick a crystal-structure tool that needs "space groups" and "Target properties" for a single molecule from SMILES. (b) User has no uploaded file — do not start with a tool that needs "Molecule file path" unless a prior step provides it. (c) If after parsing no tool accepts the user's inputs, conclude clearly in {{target_language}} that the list has no tool for the parsed inputs and the user may need to supply something else (e.g. upload a file).

Do not add steps the user did not ask for: Only include steps the user explicitly requested (in the original message or the expansion step's task list) or that are strictly required by a tool's Prerequisites (e.g. a structure file is needed because the next tool requires it). Do not add "helpful" extra steps (e.g. structure optimization, relaxation) unless the user explicitly asked. If a step would be optional (e.g. optimize_structure when the user only asked to build a structure and generate Gaussian input), omit it or state that it is optional and the user did not request it.

Conclusion: End with a definitive tool choice and order. Do not hedge (e.g. avoid "可能", "可以考虑", "might suggest"). If you have identified the right path (e.g. user needs literature/tutorial search → use search tool; user asked to run a simulation and provided inputs → use execution tools), state it clearly as the conclusion. If you are still uncertain, output NEED_REVISION so a revision round can re-check; output READY only when the reasoning is definitive and ready for the planner to use.

<Available Tools With Info>
{available_tools_with_info}

<Session File Info>
{session_file_summary}

--- Original user message ---
{original_query}

--- Task after expansion (this round) ---
{expanded_query}

Reason in plain text ({{target_language}}): parse both; check whether the user is asking "how to" / methods / tutorials (if so, consider literature/tutorial/search tools first, not a full execution workflow); briefly check whether the expansion step's output over-extends the user's actual need; then propose tools and order, check preconditions, briefly consider cost, and reflect or revise if needed. Do not repeat the section titles above in the output. When referring to the requester, always use "the user" or "用户"; do not use personal pronouns. No JSON, no markdown.

End your reply with exactly one line: READY or NEED_REVISION. Use READY only when your conclusion is definitive (clear tool choice and order; no hedging). Use NEED_REVISION when you are uncertain or want to re-check so the next round can correct.
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

--- Task from expansion step (output of previous agent, not from the user) ---
{expanded_query}

--- Previous reasoning ---
{previous_reasoning}

Check: wrong tool for user input? Wrong order so a prerequisite is not met? Tool that needs SMILES but user gave SMILES and we did not use a SMILES tool? Extra step the user did not ask for? Plans that ignore the original message or the expansion step's task list? Did the expansion step's output over-extend the user's need (if so, prior reasoning should have aligned with the user's actual request)? If the user asked "how to" / methods / tutorials, did the reasoning consider literature/tutorial/search instead of a full execution pipeline?

If a real error is found, output a short corrected reasoning in plain text. Do not copy the section titles above. When referring to the requester, always use "the user" or "用户"; do not use personal pronouns. If the previous reasoning is fine, output exactly: OK

No JSON, no markdown.
"""
