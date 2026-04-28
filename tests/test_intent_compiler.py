from __future__ import annotations

from agent.intent_compiler import CommandShape, IntentCompiler


def test_intent_compiler_corrects_typos_and_preserves_original_text():
    compiler = IntentCompiler()

    commands = compiler.compile("opn youutbe in chrme")

    assert len(commands) == 1
    assert commands[0].original_text == "opn youutbe in chrme"
    assert commands[0].normalized_text == "open youtube in chrome"
    assert commands[0].shape is CommandShape.SINGLE_ACTION


def test_intent_compiler_splits_compound_commands_and_preserves_quotes():
    compiler = IntentCompiler()

    commands = compiler.compile('open youtube and play "lofi beats" then message Rajaa on whatsapp')

    assert [command.normalized_text for command in commands] == [
        'open youtube',
        'play "lofi beats"',
        "message Rajaa on whatsapp",
    ]
    assert all(command.shape is CommandShape.SINGLE_ACTION for command in commands)


def test_intent_compiler_suppresses_near_exact_repeats_in_short_window():
    compiler = IntentCompiler()

    first = compiler.compile("open whatsapp")
    second = compiler.compile("open   whatsapp!!!")

    assert len(first) == 1
    assert second == []
