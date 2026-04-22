from agent.voice import VoiceOrchestrator


def test_voice_orchestrator_can_interrupt_active_response():
    orchestrator = VoiceOrchestrator()
    orchestrator.start_response("Working on it")
    assert orchestrator.is_speaking is True
    orchestrator.interrupt()
    assert orchestrator.is_speaking is False
