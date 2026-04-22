import re

with open('agent/executor.py', 'r', encoding='utf-8') as f:
    text = f.read()

def replace_all(text, target, rep):
    if target in text:
        return text.replace(target, rep)
    else:
        print(f"Warning: target not found:\n{target}")
        return text

# 1. _run_generated_code
target1 = '''def _run_generated_code(description: str, speak: Callable | None = None) -> str:
    import google.generativeai as genai

    if speak:
        speak("Writing custom code for this task, sir.")

    home = Path.home()
    desktop = home / "Desktop"
    downloads = home / "Downloads"
    documents = home / "Documents"

    genai.configure(api_key=_get_api_key())
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=(
            "You are an expert Python developer. "
            "Write clean, complete, working Python code. "
            "Use standard library + common packages. "
            "Return ONLY the Python code."
        ),
    )

    try:
        response = model.generate_content(
            f"Write Python code to accomplish this task:\n\n{description}\n\n"
            f"Paths:\nDesktop={desktop}\nDownloads={downloads}\nDocuments={documents}\nHome={home}"
        )'''
rep1 = '''def _run_generated_code(description: str, speak: Callable | None = None) -> str:
    from google import genai
    from google.genai import types

    if speak:
        speak("Writing custom code for this task, sir.")

    home = Path.home()
    desktop = home / "Desktop"
    downloads = home / "Downloads"
    documents = home / "Documents"

    client = genai.Client(api_key=_get_api_key())

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Write Python code to accomplish this task:\n\n{description}\n\n"
                     f"Paths:\nDesktop={desktop}\nDownloads={downloads}\nDocuments={documents}\nHome={home}",
            config=types.GenerateContentConfig(
                system_instruction=(
                    "You are an expert Python developer. "
                    "Write clean, complete, working Python code. "
                    "Use standard library + common packages. "
                    "Return ONLY the Python code."
                )
            )
        )'''
text = replace_all(text, target1, rep1)

# 2. _detect_language
target2 = '''def _detect_language(text: str) -> str:
    import google.generativeai as genai

    genai.configure(api_key=_get_api_key())
    model = genai.GenerativeModel("gemini-2.5-flash-lite")
    try:
        response = model.generate_content(
            "What language is this text written in? "
            "Reply with ONLY the language name in English.\n\n"
            f"Text: {text[:200]}"
        )'''
rep2 = '''def _detect_language(text: str) -> str:
    from google import genai

    client = genai.Client(api_key=_get_api_key())
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents="What language is this text written in? "
                     "Reply with ONLY the language name in English.\n\n"
                     f"Text: {text[:200]}"
        )'''
text = replace_all(text, target2, rep2)

# 3. _translate_to_goal_language
target3 = '''    try:
        import google.generativeai as genai

        genai.configure(api_key=_get_api_key())
        model = genai.GenerativeModel("gemini-2.5-flash")
        target_lang = _detect_language(goal)
        prompt = (
            f"Translate the following text into {target_lang}. Keep structure and facts intact. "
            "Return only the translated text.\n\n"
            f"{content[:4000]}"
        )
        response = model.generate_content(prompt)'''
rep3 = '''    try:
        from google import genai

        client = genai.Client(api_key=_get_api_key())
        target_lang = _detect_language(goal)
        prompt = (
            f"Translate the following text into {target_lang}. Keep structure and facts intact. "
            "Return only the translated text.\n\n"
            f"{content[:4000]}"
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )'''
text = replace_all(text, target3, rep3)

# 4. _summarize
target4 = '''        try:
            import google.generativeai as genai

            genai.configure(api_key=_get_api_key())
            model = genai.GenerativeModel(model_name="gemini-2.5-flash-lite")
            steps_str = "\\n".join(f"- {node.objective}" for node in completed_nodes)
            prompt = (
                f'User goal: "{goal}"\\n'
                f"Completed steps:\\n{steps_str}\\n\\n"
                "Write a single natural sentence summarizing what was accomplished. "
                "Address the user as 'sir'. Be direct and positive."
            )
            response = model.generate_content(prompt)'''
rep4 = '''        try:
            from google import genai

            client = genai.Client(api_key=_get_api_key())
            steps_str = "\\n".join(f"- {node.objective}" for node in completed_nodes)
            prompt = (
                f'User goal: "{goal}"\\n'
                f"Completed steps:\\n{steps_str}\\n\\n"
                "Write a single natural sentence summarizing what was accomplished. "
                "Address the user as 'sir'. Be direct and positive."
            )
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt
            )'''
text = replace_all(text, target4, rep4)

with open('agent/executor.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("done")
