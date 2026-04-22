import re

with open('agent/error_handler.py', 'r', encoding='utf-8') as f:
    text = f.read()

def replace_all(text, target, rep):
    if target in text:
        return text.replace(target, rep)
    else:
        print(f"Warning: target not found:\n{target}")
        return text

# 1. analyze_error setup
analyze_import_target = '''    import google.generativeai as genai

    if attempt >= max_attempts:'''
analyze_import_rep = '''    from google import genai
    from google.genai import types

    if attempt >= max_attempts:'''
text = replace_all(text, analyze_import_target, analyze_import_rep)

analyze_model_target = '''    genai.configure(api_key=_get_api_key())
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash-lite",
        system_instruction=ERROR_ANALYST_PROMPT
    )'''
analyze_model_rep = '''    client = genai.Client(api_key=_get_api_key())'''
text = replace_all(text, analyze_model_target, analyze_model_rep)

analyze_generate_target = '''    try:
        response = model.generate_content(prompt)'''
analyze_generate_rep = '''    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=ERROR_ANALYST_PROMPT
            )
        )'''
text = replace_all(text, analyze_generate_target, analyze_generate_rep)

# 2. generate_fix
fix_target = '''    import google.generativeai as genai

    genai.configure(api_key=_get_api_key())
    model = genai.GenerativeModel(model_name="gemini-2.0-flash")'''

fix_rep = '''    from google import genai
    client = genai.Client(api_key=_get_api_key())'''
text = replace_all(text, fix_target, fix_rep)

fix_gen_target = '''    try:
        response = model.generate_content(prompt)'''
fix_gen_rep = '''    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )'''
text = replace_all(text, fix_gen_target, fix_gen_rep)

with open('agent/error_handler.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("done")
