import os
from pathlib import Path

DOMAINS = {
    "browser_nav": {"count": 30, "start": 1},
    "browser_dom": {"count": 40, "start": 1},
    "browser_auth": {"count": 20, "start": 1},
    "browser_tabs": {"count": 20, "start": 1},
    "browser_cookies": {"count": 20, "start": 1},
    "browser_history": {"count": 20, "start": 1},
    "browser_media": {"count": 20, "start": 1},
    "browser_downloads": {"count": 15, "start": 1},
    "browser_extensions": {"count": 15, "start": 1},
}

TEMPLATE = """from actions.base import Action, ActionRegistry


class {class_name}Action(Action):
    @property
    def name(self) -> str:
        return "{domain}_tool_{operation}"

    @property
    def description(self) -> str:
        return "Dummy {domain} tool number {operation}"

    @property
    def parameters_schema(self) -> dict:
        return {{
            "type": "OBJECT",
            "properties": {{}},
            "required": [],
        }}

    def execute(self, parameters: dict, player=None, speak=None, **kwargs) -> str:
        from runtime.results.builder import build_tool_result
        return build_tool_result(
            tool_name=self.name,
            operation="dummy_operation",
            risk_level="LOW",
            status="success",
            summary="Dummy {domain} tool executed",
            structured_data={{}},
            idempotent=True,
            preconditions=[],
            postconditions=[],
        )

ActionRegistry.register({class_name}Action)
"""

INIT_TEMPLATE = """from importlib import import_module

for module_name in (
{imports}
):
    import_module(module_name)
"""

def generate_tools():
    actions_dir = Path("actions")
    
    for domain, info in DOMAINS.items():
        domain_dir = actions_dir / domain
        domain_dir.mkdir(parents=True, exist_ok=True)
        
        imports = []
        for i in range(info["start"], info["start"] + info["count"]):
            operation = f"{i}"
            class_name = f"{domain.title().replace('_', '')}Tool{i}"
            
            tool_content = TEMPLATE.format(
                class_name=class_name,
                domain=domain,
                operation=operation
            )
            
            file_name = f"tool_{operation}.py"
            file_path = domain_dir / file_name
            
            with open(file_path, "w") as f:
                f.write(tool_content)
                
            imports.append(f'    "actions.{domain}.tool_{operation}",')
            
        init_path = domain_dir / "__init__.py"
        with open(init_path, "w") as f:
            f.write(INIT_TEMPLATE.format(
                domain=domain,
                imports="\n".join(imports)
            ))

if __name__ == "__main__":
    generate_tools()
