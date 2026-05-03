from importlib import import_module

for module_name in (
    "actions.serial.serial_tool_1",
    "actions.serial.serial_tool_2",
    "actions.serial.serial_tool_3",
    "actions.serial.serial_tool_4",
):
    import_module(module_name)
