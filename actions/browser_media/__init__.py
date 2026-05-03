from importlib import import_module

for module_name in (
    "actions.browser_media.tool_1",
    "actions.browser_media.tool_2",
    "actions.browser_media.tool_3",
    "actions.browser_media.tool_4",
    "actions.browser_media.tool_5",
    "actions.browser_media.tool_6",
    "actions.browser_media.tool_7",
    "actions.browser_media.tool_8",
    "actions.browser_media.tool_9",
    "actions.browser_media.tool_10",
    "actions.browser_media.tool_11",
    "actions.browser_media.tool_12",
    "actions.browser_media.tool_13",
    "actions.browser_media.tool_14",
    "actions.browser_media.tool_15",
    "actions.browser_media.tool_16",
    "actions.browser_media.tool_17",
    "actions.browser_media.tool_18",
    "actions.browser_media.tool_19",
    "actions.browser_media.tool_20",
):
    import_module(module_name)
