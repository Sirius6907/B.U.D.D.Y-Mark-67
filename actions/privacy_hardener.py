import subprocess
from actions.base import Action, ActionRegistry

def privacy_hardener(parameters: dict, player=None, speak=None, **kwargs) -> str:
    action = parameters.get("action", "audit").lower()
    
    if action == "audit":
        return _audit_privacy_settings()
    if action == "harden":
        return _harden_privacy()
        
    return f"Unknown privacy_hardener action: {action}"


def _audit_privacy_settings() -> str:
    """Checks the status of common Windows privacy risks."""
    checks = {
        "Telemetry": r"HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection /v AllowTelemetry",
        "AdvertisingID": r"HKCU\Software\Microsoft\Windows\CurrentVersion\AdvertisingInfo /v Enabled",
        "Location": r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\location /v Value"
    }
    
    report = "🔍 Privacy Audit Report:\n"
    for name, path in checks.items():
        try:
            res = subprocess.run(["reg", "query"] + path.split(), capture_output=True, text=True)
            if res.returncode == 0:
                report += f"❌ {name}: Active/Enabled (Consider hardening)\n"
            else:
                report += f"✅ {name}: Disabled/Protected\n"
        except Exception:
            report += f"⚠️ {name}: Could not verify\n"
            
    return report


def _harden_privacy() -> str:
    """Disables telemetry and advertising ID via registry. Requires Admin."""
    commands = [
        # Disable Telemetry
        ["reg", "add", r"HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection", "/v", "AllowTelemetry", "/t", "REG_DWORD", "/d", "0", "/f"],
        # Disable Advertising ID
        ["reg", "add", r"HKCU\Software\Microsoft\Windows\CurrentVersion\AdvertisingInfo", "/v", "Enabled", "/t", "REG_DWORD", "/d", "0", "/f"]
    ]
    
    results = []
    for cmd in commands:
        try:
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                results.append(f"✅ Executed: {' '.join(cmd[:3])}...")
            else:
                results.append(f"❌ Failed (Admin needed): {' '.join(cmd[:3])}...")
        except Exception as e:
            results.append(f"⚠️ Error: {e}")
            
    return "🛡️ Privacy Hardening Status:\n" + "\n".join(results)


class PrivacyHardenerAction(Action):
    @property
    def name(self) -> str:
        return "privacy_hardener"

    @property
    def description(self) -> str:
        return (
            "Audits and hardens system privacy settings. "
            "Can disable Windows Telemetry and Advertising ID to reduce data leakage."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "action": {
                    "type": "STRING", 
                    "description": "audit | harden"
                }
            },
            "required": ["action"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs) -> str:
        return privacy_hardener(parameters=parameters, player=player, speak=speak)


ActionRegistry.register(PrivacyHardenerAction)
