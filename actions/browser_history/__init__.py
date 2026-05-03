from importlib import import_module

for module_name in (
    "actions.browser_history.tool_1",
    "actions.browser_history.tool_2",
    "actions.browser_history.tool_3",
    "actions.browser_history.tool_4",
    "actions.browser_history.tool_5",
    "actions.browser_history.tool_6",
    "actions.browser_history.tool_7",
    "actions.browser_history.tool_8",
    "actions.browser_history.tool_9",
    "actions.browser_history.tool_10",
    "actions.browser_history.tool_11",
    "actions.browser_history.tool_12",
    "actions.browser_history.tool_13",
    "actions.browser_history.tool_14",
    "actions.browser_history.tool_15",
    "actions.browser_history.tool_16",
    "actions.browser_history.tool_17",
    "actions.browser_history.tool_18",
    "actions.browser_history.tool_19",
    "actions.browser_history.tool_20",
):
    import_module(module_name)
