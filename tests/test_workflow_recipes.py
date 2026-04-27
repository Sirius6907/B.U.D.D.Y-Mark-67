from agent.workflow_recipes import match_workflow_recipe


def test_match_workflow_recipe_routes_whatsapp_open_chat_requests():
    recipe = match_workflow_recipe("open whatsapp and search for contact Rajaa and open the chat")

    assert recipe is not None
    assert recipe.intent_family == "open_chat"
    assert recipe.steps[0].action == "send_message"
    assert recipe.steps[0].parameters["mode"] == "open_chat"
    assert recipe.steps[0].parameters["receiver"] == "Rajaa"


def test_match_workflow_recipe_routes_whatsapp_message_requests():
    recipe = match_workflow_recipe("open whatsapp.web in chrome and search for the contact name Rajaa then message him Hii how are you")

    assert recipe is not None
    assert recipe.intent_family == "send_message"
    assert recipe.requires_approval is True
    assert recipe.steps[0].parameters["mode"] == "send"
    assert recipe.steps[0].parameters["message_text"] == "Hii how are you"


def test_match_workflow_recipe_routes_admin_launch_requests():
    recipe = match_workflow_recipe("run command prompt as administrator")

    assert recipe is not None
    assert recipe.intent_family == "open_app_admin"
    assert recipe.requires_approval is True
    assert recipe.steps[0].parameters["run_as_admin"] is True


def test_match_workflow_recipe_routes_bluetooth_process_and_settings_requests():
    bluetooth = match_workflow_recipe("open bluetooth settings")
    processes = match_workflow_recipe("show top running processes by memory")
    settings = match_workflow_recipe("open settings")

    assert bluetooth is not None and bluetooth.intent_family == "bluetooth_control"
    assert processes is not None and processes.intent_family == "process_view"
    assert settings is not None and settings.intent_family == "settings_open"

