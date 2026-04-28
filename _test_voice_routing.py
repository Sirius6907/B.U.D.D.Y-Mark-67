import asyncio
from agent.voice import VoiceOrchestrator
from agent.kernel import kernel

async def test_routing():
    print("============================================================")
    print("BUDDY Voice Routing Integration Test")
    print("============================================================")
    
    # We will provide a dummy speak_fn
    speak_out = []
    def dummy_speak(text):
        speak_out.append(text)
        print(f"[SPEAKER] {text}")
        
    orchestrator = VoiceOrchestrator(speak_fn=dummy_speak)
    
    print("\n[Test 1] Chat Intent Routing")
    text_chat = "Hello BUDDY, who are you?"
    print(f"Command: {text_chat}")
    
    # Call handle_user_command
    await orchestrator.handle_user_command(text_chat)
    
    if len(speak_out) > 0:
        print("[PASS] Chat intent successfully routed to conversational memory.")
    else:
        print("[FAIL] No speech output detected for chat intent.")
        
    speak_out.clear()
    
    print("\n[Test 2] Action Intent Routing")
    text_action = "Take a screenshot of the browser."
    print(f"Command: {text_action}")
    
    # We don't want to actually execute the plan for real, maybe?
    # Actually wait, handle_user_command will call create_plan and runtime.execute_plan.
    # To prevent it from taking too long or doing things, we can mock `create_plan`.
    
    # Mocking create_plan and runtime.execute_plan
    import agent.voice
    
    original_create_plan = agent.voice.create_plan
    async def mock_execute_plan(*args, **kwargs):
        print(f"[MOCK] Executing plan...")
        
    def mock_create_plan(*args, **kwargs):
        print(f"[MOCK] Creating plan for: {args[0]}")
        from agent.models import TaskPlan, TaskNode, RiskTier
        return TaskPlan(
            plan_id="mock-plan",
            goal=args[0],
            nodes=[
                TaskNode(
                    node_id="mock-node",
                    objective="Mock Step",
                    tool="mock_tool",
                    parameters={},
                    expected_outcome="Mock outcome"
                )
            ]
        )
        
    agent.voice.create_plan = mock_create_plan
    orchestrator.runtime.execute_plan = mock_execute_plan
    
    # Observe active agent before
    print(f"Active Agent Before: {kernel.agents.active_agent.name if kernel.agents.active_agent else 'None'}")
    
    await orchestrator.handle_user_command(text_action)
    
    print(f"Active Agent After: {kernel.agents.active_agent.name if kernel.agents.active_agent else 'None'}")
    
    if kernel.agents.active_agent and kernel.agents.active_agent.name == "screen_agent":
        print("[PASS] Action intent successfully routed to screen_agent.")
    else:
        print("[FAIL] Action intent was not routed to screen_agent.")
        
    # Restore mock
    agent.voice.create_plan = original_create_plan
    
    print("\n[Test 3] General Action Intent Routing")
    text_action_2 = "Can you help me check my running processes?"
    print(f"Command: {text_action_2}")
    
    await orchestrator.handle_user_command(text_action_2)
    
    print(f"Active Agent After: {kernel.agents.active_agent.name if kernel.agents.active_agent else 'None'}")
    
    if kernel.agents.active_agent and kernel.agents.active_agent.name == "system_agent":
        print("[PASS] Action intent successfully routed to system_agent.")
    else:
        print("[FAIL] Action intent was not routed to system_agent.")

if __name__ == "__main__":
    asyncio.run(test_routing())
