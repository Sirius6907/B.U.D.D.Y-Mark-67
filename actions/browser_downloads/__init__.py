from importlib import import_module

for module_name in (
    "actions.browser_downloads.tool_1",
    "actions.browser_downloads.tool_2",
    "actions.browser_downloads.tool_3",
    "actions.browser_downloads.tool_4",
    "actions.browser_downloads.tool_5",
    "actions.browser_downloads.tool_6",
    "actions.browser_downloads.tool_7",
    "actions.browser_downloads.tool_8",
    "actions.browser_downloads.tool_9",
    "actions.browser_downloads.tool_10",
    "actions.browser_downloads.tool_11",
    "actions.browser_downloads.tool_12",
    "actions.browser_downloads.tool_13",
    "actions.browser_downloads.tool_14",
    "actions.browser_downloads.tool_15",
):
    import_module(module_name)
