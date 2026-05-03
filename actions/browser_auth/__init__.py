from importlib import import_module

for module_name in (
    "actions.browser_auth.tool_1",
    "actions.browser_auth.tool_2",
    "actions.browser_auth.tool_3",
    "actions.browser_auth.tool_4",
    "actions.browser_auth.tool_5",
    "actions.browser_auth.tool_6",
    "actions.browser_auth.tool_7",
    "actions.browser_auth.tool_8",
    "actions.browser_auth.tool_9",
    "actions.browser_auth.tool_10",
    "actions.browser_auth.tool_11",
    "actions.browser_auth.tool_12",
    "actions.browser_auth.tool_13",
    "actions.browser_auth.tool_14",
    "actions.browser_auth.tool_15",
    "actions.browser_auth.tool_16",
    "actions.browser_auth.tool_17",
    "actions.browser_auth.tool_18",
    "actions.browser_auth.tool_19",
    "actions.browser_auth.tool_20",
):
    import_module(module_name)
from actions.browser_auth.auth_gen import *  # noqa: F401,F403
