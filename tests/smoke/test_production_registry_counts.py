from actions import ActionRegistry


def test_registry_reaches_first_production_milestone():
    assert len(ActionRegistry._actions) >= 400
