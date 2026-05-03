from importlib import import_module

for module_name in (
    "actions.browser_tabs.tool_1",
    "actions.browser_tabs.tool_2",
    "actions.browser_tabs.tool_3",
    "actions.browser_tabs.tool_4",
    "actions.browser_tabs.tool_5",
    "actions.browser_tabs.tool_6",
    "actions.browser_tabs.tool_7",
    "actions.browser_tabs.tool_8",
    "actions.browser_tabs.tool_9",
    "actions.browser_tabs.tool_10",
    "actions.browser_tabs.tool_11",
    "actions.browser_tabs.tool_12",
    "actions.browser_tabs.tool_13",
    "actions.browser_tabs.tool_14",
    "actions.browser_tabs.tool_15",
    "actions.browser_tabs.tool_16",
    "actions.browser_tabs.tool_17",
    "actions.browser_tabs.tool_18",
    "actions.browser_tabs.tool_19",
    "actions.browser_tabs.tool_20",
):
    import_module(module_name)
