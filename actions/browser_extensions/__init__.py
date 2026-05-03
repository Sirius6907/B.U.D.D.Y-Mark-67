from importlib import import_module

for module_name in (
    "actions.browser_extensions.tool_1",
    "actions.browser_extensions.tool_2",
    "actions.browser_extensions.tool_3",
    "actions.browser_extensions.tool_4",
    "actions.browser_extensions.tool_5",
    "actions.browser_extensions.tool_6",
    "actions.browser_extensions.tool_7",
    "actions.browser_extensions.tool_8",
    "actions.browser_extensions.tool_9",
    "actions.browser_extensions.tool_10",
    "actions.browser_extensions.tool_11",
    "actions.browser_extensions.tool_12",
    "actions.browser_extensions.tool_13",
    "actions.browser_extensions.tool_14",
    "actions.browser_extensions.tool_15",
):
    import_module(module_name)
