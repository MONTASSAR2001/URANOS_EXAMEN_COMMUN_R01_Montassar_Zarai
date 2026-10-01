import sys

PY_PATH = 'apps/uranos_project_os/uranos_project_os/services/ai_synthesis.py'

with open(PY_PATH, 'r', encoding='utf-8') as f:
    lines = f.readlines()

content = "".join(lines)

# 1. Update call_cloud_llm_synthesis signature
old_sig = "def call_cloud_llm_synthesis(\n    project: str,\n    open_blockers: List[Dict[str, Any]],\n    closed_blockers: List[Dict[str, Any]],\n    api_key: Optional[str] = None,\n    endpoint: Optional[str] = None,\n    model: Optional[str] = None,\n    timeout_seconds: float = 12.0,\n    lang: Optional[str] = None,\n) -> str:"
new_sig = "def call_cloud_llm_synthesis(\n    project: str,\n    open_blockers: List[Dict[str, Any]],\n    closed_blockers: List[Dict[str, Any]],\n    api_key: Optional[str] = None,\n    endpoint: Optional[str] = None,\n    model: Optional[str] = None,\n    timeout_seconds: float = 12.0,\n    lang: Optional[str] = None,\n    completed_work: Optional[Dict[str, Any]] = None,\n    remaining_work: Optional[Dict[str, Any]] = None,\n    active_defects_blockers: Optional[Dict[str, Any]] = None,\n) -> str:"

if old_sig in content:
    content = content.replace(old_sig, new_sig, 1)
    print("1. Updated call_cloud_llm_synthesis signature")

# 2. Inject Anti-Hallucination and holistic context in call_cloud_llm_synthesis
old_sys = '    system_prompt = (\n        "You are an expert Utility-Scale Photovoltaic Construction & Executive Project Management Advisor for URANOS Group.\\n"'
new_sys = '''    anti_hallucination_directive = (
        "ANTI-HALLUCINATION DIRECTIVE: Base your summary and answers STRICTLY on the provided database context. "
        "Do not invent or simulate project data. If a metric, work package, or record is not in the context, "
        "state clearly that it is not recorded in the database."
    )

    system_prompt = (
        "You are an expert Utility-Scale Photovoltaic Construction & Executive Project Management Advisor for URANOS Group.\\n"
        "Analyze the provided holistic project data covering Completed Work, Remaining Work, and Active Defects/Blockers, then deliver an executive synthesis.\\n"'''

if old_sys in content:
    content = content.replace(old_sys, new_sys, 1)
    print("2. Added anti_hallucination_directive to call_cloud_llm_synthesis")

old_user = '    user_prompt = (\n        f"Project: {project}\\n\\n"\n        f"ACTIVE BLOCKERS ({len(open_context)}):\\n{json.dumps(open_context, indent=2)}\\n\\n"\n        f"HISTORICAL RESOLUTION PRECEDENTS ({len(closed_context)}):\\n{json.dumps(closed_context, indent=2)}\\n\\n"\n        f"{instruction}"\n    )'
new_user = '''    holistic_context = {
        "Project": project,
        "Completed Work": completed_work or {},
        "Remaining Work": remaining_work or {},
        "Active Defects/Blockers": active_defects_blockers or {
            "total_active_count": len(open_blockers),
            "items": open_context,
            "historical_resolutions": closed_context,
        },
    }

    user_prompt = (
        f"Project: {project}\\n\\n"
        f"HOLISTIC PROJECT DATABASE CONTEXT (Completed Work, Remaining Work, Active Defects/Blockers):\\n"
        f"{json.dumps(holistic_context, indent=2)}\\n\\n"
        f"{instruction}"
    )'''

if old_user in content:
    content = content.replace(old_user, new_user, 1)
    print("3. Updated user_prompt in call_cloud_llm_synthesis with holistic context")

# 3. Update build_deterministic_chat_reply signature and handlers
old_chat_sig = "def build_deterministic_chat_reply(\n    project: str,\n    message: str,\n    open_blockers: List[Dict[str, Any]],\n    closed_blockers: List[Dict[str, Any]],\n    lang: str = \"en\",\n) -> str:"
new_chat_sig = "def build_deterministic_chat_reply(\n    project: str,\n    message: str,\n    open_blockers: List[Dict[str, Any]],\n    closed_blockers: List[Dict[str, Any]],\n    lang: str = \"en\",\n    completed_work: Optional[Dict[str, Any]] = None,\n    remaining_work: Optional[Dict[str, Any]] = None,\n) -> str:"

if old_chat_sig in content:
    content = content.replace(old_chat_sig, new_chat_sig, 1)
    print("4. Updated build_deterministic_chat_reply signature")

old_en = '        # Default: English\n        if any(k in msg_lower for k in ("material", "supply", "delivery", "custom")):'
new_en = '''        # Default: English
        if any(k in msg_lower for k in ("progress", "advance", "work", "complete", "remain", "plan", "status", "execut")):
            lines = [f"**Project Progress & Execution Status for {project}**:"]
            if completed_work and completed_work.get("summary"):
                lines.append(f"- **Completed Work**: {completed_work['summary']}.")
            else:
                lines.append(f"- **Completed Work**: No verified field progress entries recorded in database to date.")
            if remaining_work and remaining_work.get("summary"):
                lines.append(f"- **Remaining Work**: {remaining_work['summary']}.")
            lines.append(f"- **Active Defects/Blockers**: **{open_count}** active obstacle(s) recorded ({len(critical_blockers)} Critical/High).")
            return "\\n".join(lines)

        if any(k in msg_lower for k in ("material", "supply", "delivery", "custom")):'''

if old_en in content:
    content = content.replace(old_en, new_en, 1)
    print("5. Added EN progress check in build_deterministic_chat_reply")

# 4. In generate_blocker_synthesis, use fetch_holistic_project_context
old_gen_call = '''        if api_key and str(api_key).strip():
            try:
                summary_text = call_cloud_llm_synthesis(
                    project=project,
                    open_blockers=open_blockers,
                    closed_blockers=closed_blockers,
                    api_key=api_key,
                    endpoint=GROQ_COMPLETIONS_URL,
                    model=GROQ_MODEL,
                    timeout_seconds=12.0,
                    lang=target_lang,
                )'''

new_gen_call = '''        if api_key and str(api_key).strip():
            try:
                summary_text = call_cloud_llm_synthesis(
                    project=project,
                    open_blockers=open_blockers,
                    closed_blockers=closed_blockers,
                    api_key=api_key,
                    endpoint=GROQ_COMPLETIONS_URL,
                    model=GROQ_MODEL,
                    timeout_seconds=12.0,
                    lang=target_lang,
                    completed_work=completed_work,
                    remaining_work=remaining_work,
                    active_defects_blockers=active_defects_blockers,
                )'''

if old_gen_call in content:
    content = content.replace(old_gen_call, new_gen_call, 1)
    print("6. Updated call_cloud_llm_synthesis invocation in generate_blocker_synthesis")

# Also inject holistic fetch into generate_blocker_synthesis
old_gen_retrieval = '''    # 1. Retrieval Phase (Frappe ORM scoped to project)
    open_blockers = frappe.get_all('''

new_gen_retrieval = '''    # 1. Retrieval Phase (Holistic project context from MariaDB)
    holistic = fetch_holistic_project_context(project)
    open_blockers = holistic["open_blockers"]
    closed_blockers = holistic["closed_blockers"]
    completed_work = holistic["completed_work"]
    remaining_work = holistic["remaining_work"]
    active_defects_blockers = holistic["active_defects_blockers"]

    # Legacy open_blockers query fallback if needed
    if False:
        open_blockers = frappe.get_all('''

if old_gen_retrieval in content:
    content = content.replace(old_gen_retrieval, new_gen_retrieval, 1)
    print("7. Injected holistic context retrieval into generate_blocker_synthesis")

# 5. In chat_with_project_ai, inject holistic fetch and updated system prompt
old_chat_retrieval = '''    # 1. Retrieval Phase (live project blockers)
    open_blockers = frappe.get_all('''

new_chat_retrieval = '''    # 1. Retrieval Phase (Holistic project context: Completed Work, Remaining Work, Active Defects/Blockers)
    holistic = fetch_holistic_project_context(project)
    open_blockers = holistic["open_blockers"]
    closed_blockers = holistic["closed_blockers"]
    completed_work = holistic["completed_work"]
    remaining_work = holistic["remaining_work"]
    active_defects_blockers = holistic["active_defects_blockers"]

    if False:
        open_blockers = frappe.get_all('''

if old_chat_retrieval in content:
    content = content.replace(old_chat_retrieval, new_chat_retrieval, 1)
    print("8. Injected holistic context retrieval into chat_with_project_ai")

old_chat_sys = '''        system_prompt = (
            f"You are the URANOS AI Project Copilot for utility-scale photovoltaic project '{project}'.\\n"
            f"Live Project Facts:\\n"
            f"- Total Open Blockers: {len(open_blockers)}\\n"
            f"- Critical / High Severity: {critical_count}\\n"
            f"- Cumulative Lost Hours: {total_lost:.1f}h\\n"
            f"- Active Blockers Context: {json.dumps(open_context)}\\n"
            f"- Historical Resolutions Context: {json.dumps(closed_context)}\\n\\n"
            f"Instructions:\\n"
            f"1. Answer the user's inquiry accurately, directly, and specifically citing blocker IDs, categories, and metrics where relevant.\\n"
            f"2. Use clean, chic Markdown with bullet points and bold highlights.\\n"
            f"3. Be concise, punchy, and operational (max 180 words).\\n"
            f"4. {lang_prompt}\\n"
            f"5. If the user asks about something not in the project data, state clearly that it is not recorded for this project."
        )'''

new_chat_sys = '''        anti_hallucination_directive = (
            "ANTI-HALLUCINATION DIRECTIVE: Base your summary and answers STRICTLY on the provided database context. "
            "Do not invent or simulate project data. If a metric or record is absent or zero, "
            "state clearly that it is not recorded in the database."
        )

        system_prompt = (
            f"You are the URANOS AI Project Copilot for utility-scale photovoltaic project '{project}'.\\n"
            f"Live Holistic Project Context:\\n"
            f"- Completed Work: {json.dumps(completed_work)}\\n"
            f"- Remaining Work: {json.dumps(remaining_work)}\\n"
            f"- Active Defects/Blockers: {json.dumps(active_defects_blockers)}\\n\\n"
            f"Instructions:\\n"
            f"1. Answer the user's inquiry accurately, directly, and specifically citing blocker IDs, work packages, quantities, and metrics from the provided context.\\n"
            f"2. Use clean, chic Markdown with bullet points and bold highlights.\\n"
            f"3. Be concise, punchy, and operational (max 180 words).\\n"
            f"4. {anti_hallucination_directive}\\n"
            f"5. {lang_prompt}\\n"
            f"6. Base your answers STRICTLY on the provided database context."
        )'''

if old_chat_sys in content:
    content = content.replace(old_chat_sys, new_chat_sys, 1)
    print("9. Injected Anti-Hallucination and holistic context into chat_with_project_ai system_prompt")

old_chat_fb = '''    # 3. Fallback Generation if AI call failed or offline
    if not is_ai_generated:
        reply_text = build_deterministic_chat_reply(
            project=project,
            message=message,
            open_blockers=open_blockers,
            closed_blockers=closed_blockers,
            lang=target_lang,
        )'''

new_chat_fb = '''    # 3. Fallback Generation if AI call failed or offline
    if not is_ai_generated:
        reply_text = build_deterministic_chat_reply(
            project=project,
            message=message,
            open_blockers=open_blockers,
            closed_blockers=closed_blockers,
            lang=target_lang,
            completed_work=completed_work,
            remaining_work=remaining_work,
        )'''

if old_chat_fb in content:
    content = content.replace(old_chat_fb, new_chat_fb, 1)
    print("10. Updated fallback invocation in chat_with_project_ai with completed_work and remaining_work")

with open(PY_PATH, 'w', encoding='utf-8') as f:
    f.write(content)

print("Finished patching ai_synthesis.py successfully!")
