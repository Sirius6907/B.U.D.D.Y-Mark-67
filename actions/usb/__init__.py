from importlib import import_module

for module_name in (
    "actions.usb.usb_tool_1",
    "actions.usb.usb_tool_2",
    "actions.usb.usb_tool_3",
    "actions.usb.usb_tool_4",
    "actions.usb.usb_tool_5",
    "actions.usb.usb_tool_6",
):
    import_module(module_name)
