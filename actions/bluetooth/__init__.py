from importlib import import_module

for module_name in (
    "actions.bluetooth.bluetooth_tool_1",
    "actions.bluetooth.bluetooth_tool_2",
    "actions.bluetooth.bluetooth_tool_3",
    "actions.bluetooth.bluetooth_tool_4",
    "actions.bluetooth.bluetooth_tool_5",
    "actions.bluetooth.bluetooth_tool_6",
    "actions.bluetooth.bluetooth_tool_7",
    "actions.bluetooth.bluetooth_tool_8",
):
    import_module(module_name)
