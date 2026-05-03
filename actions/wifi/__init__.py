from importlib import import_module

for module_name in (
    "actions.wifi.wifi_tool_1",
    "actions.wifi.wifi_tool_2",
    "actions.wifi.wifi_tool_3",
    "actions.wifi.wifi_tool_4",
    "actions.wifi.wifi_tool_5",
    "actions.wifi.wifi_tool_6",
    "actions.wifi.wifi_tool_7",
    "actions.wifi.wifi_tool_8",
):
    import_module(module_name)
