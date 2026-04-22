import psutil
import subprocess
from actions.base import Action, ActionRegistry

def app_optimizer(parameters: dict, player=None, speak=None, **kwargs) -> str:
    action = parameters.get("action", "power_plan").lower()
    
    if action == "set_priority":
        target = parameters.get("target")
        level = parameters.get("level", "normal").lower()
        if not target: return "Error: 'target' (PID or name) required."
        return _set_process_priority(target, level)
    if action == "power_plan":
        plan = parameters.get("plan", "balanced").lower()
        return _set_power_plan(plan)
        
    return f"Unknown app_optimizer action: {action}"


def _set_process_priority(target: str, level: str) -> str:
    """Changes the OS priority of a process."""
    priorities = {
        "high": psutil.HIGH_PRIORITY_CLASS,
        "normal": psutil.NORMAL_PRIORITY_CLASS,
        "low": psutil.BELOW_NORMAL_PRIORITY_CLASS,
        "realtime": psutil.REALTIME_PRIORITY_CLASS
    }
    
    p_val = priorities.get(level, psutil.NORMAL_PRIORITY_CLASS)
    
    try:
        if target.isdigit():
            pid = int(target)
            proc = psutil.Process(pid)
            proc.nice(p_val)
            return f"🚀 Process (PID: {pid}) priority set to {level}."
        else:
            count = 0
            for proc in psutil.process_iter(['name']):
                if proc.info['name'].lower() == target.lower():
                    proc.nice(p_val)
                    count += 1
            if count > 0:
                return f"🚀 {count} instance(s) of '{target}' set to {level} priority."
            return f"❌ Process '{target}' not found."
    except Exception as e:
        return f"❌ Failed to set priority: {e}"


def _set_power_plan(plan: str) -> str:
    """Switch Windows power scheme."""
    # Common GUIDs for Windows power plans
    plans = {
        "performance": "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c",
        "balanced": "381b4222-f694-41f0-9685-ff5bb260df2e",
        "saver": "a1841308-3541-4fab-bc81-f71556f20b4a"
    }
    
    guid = plans.get(plan)
    if not guid: return f"Unknown plan: {plan}. Use performance | balanced | saver."
    
    try:
        subprocess.run(["powercfg", "/setactive", guid], check=True)
        return f"⚡ Power Plan set to {plan.upper()}."
    except Exception as e:
        return f"Error setting power plan: {e}"


class AppOptimizerAction(Action):
    @property
    def name(self) -> str:
        return "app_optimizer"

    @property
    def description(self) -> str:
        return (
            "Optimizes application and system performance. "
            "Can set process priorities (high/normal/low) and switch power plans (performance/balanced/saver)."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "action": {
                    "type": "STRING", 
                    "description": "set_priority | power_plan"
                },
                "target": {
                    "type": "STRING",
                    "description": "Process PID or name (for set_priority)"
                },
                "level": {
                    "type": "STRING",
                    "description": "high | normal | low | realtime (for set_priority)"
                },
                "plan": {
                    "type": "STRING",
                    "description": "performance | balanced | saver (for power_plan)"
                }
            },
            "required": ["action"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs) -> str:
        return app_optimizer(parameters=parameters, player=player, speak=speak)


ActionRegistry.register(AppOptimizerAction)
