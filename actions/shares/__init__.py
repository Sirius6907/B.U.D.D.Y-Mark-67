from importlib import import_module

for module_name in (
    "actions.shares.shares_tool_1",
    "actions.shares.shares_tool_2",
    "actions.shares.shares_tool_3",
    "actions.shares.shares_tool_4",
):
    import_module(module_name)
