import re

with open('agent/planner.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix create_plan
create_plan_target = '''        print(f"[Planner] ?? Planning failed: {e}")
        return _fallback_plan(goal)'''

create_plan_replacement = '''        plan = TaskPlan(**data)
        print(f"[Planner] ? Plan created: {plan.plan_id} ({len(plan.nodes)} nodes)")
        return plan

    except Exception as e:
        print(f"[Planner] ?? Planning failed: {e}")
        return _fallback_plan(goal)'''

text = text.replace(create_plan_target, create_plan_replacement)


# Fix replan setup
replan_setup_target = '''def replan(goal: str, completed_nodes: list[TaskNode], failed_node: TaskNode, error: str) -> TaskPlan:
    import google.generativeai as genai

    genai.configure(api_key=_get_api_key())
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=PLANNER_PROMPT
    )'''

replan_setup_rep = '''def replan(goal: str, completed_nodes: list[TaskNode], failed_node: TaskNode, error: str) -> TaskPlan:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=_get_api_key())'''

text = text.replace(replan_setup_target, replan_setup_rep)


# Fix replan model call
replan_model_target = '''    try:
        response = model.generate_content(prompt)
        text     = response.text.strip()'''

replan_model_rep = '''    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=PLANNER_PROMPT
            )
        )
        text     = response.text.strip()'''

text = text.replace(replan_model_target, replan_model_rep)

with open('agent/planner.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("done")
