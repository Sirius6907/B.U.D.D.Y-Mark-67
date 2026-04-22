import subprocess
import os
from actions.base import Action, ActionRegistry

MPCMD_PATH = r"C:\ProgramData\Microsoft\Windows Defender\Platform"

def get_mpcmd_exe():
    """Finds the most recent version of MpCmdRun.exe"""
    if not os.path.exists(MPCMD_PATH):
        # Fallback to the older path if platform path doesn't exist
        fallback = r"C:\Program Files\Windows Defender\MpCmdRun.exe"
        if os.path.exists(fallback):
            return fallback
        return None
        
    try:
        # Get the latest platform version folder
        versions = [d for d in os.listdir(MPCMD_PATH) if os.path.isdir(os.path.join(MPCMD_PATH, d))]
        if not versions:
            fallback = r"C:\Program Files\Windows Defender\MpCmdRun.exe"
            return fallback if os.path.exists(fallback) else None
            
        latest_version = sorted(versions)[-1]
        exe_path = os.path.join(MPCMD_PATH, latest_version, "MpCmdRun.exe")
        if os.path.exists(exe_path):
            return exe_path
    except Exception:
        pass
        
    fallback = r"C:\Program Files\Windows Defender\MpCmdRun.exe"
    return fallback if os.path.exists(fallback) else None


def antivirus_manager(parameters: dict, player=None, speak=None, **kwargs) -> str:
    action = parameters.get("action", "quick_scan").lower()
    
    mpcmd = get_mpcmd_exe()
    if not mpcmd:
        return "Windows Defender executable (MpCmdRun.exe) not found on this system."

    if action == "quick_scan":
        return _run_scan(mpcmd, scan_type=1)
    if action == "full_scan":
        return _run_scan(mpcmd, scan_type=2)
    if action == "update_signatures":
        return _update_signatures(mpcmd)
    if action == "status":
        return _get_status()
        
    return f"Unknown antivirus_manager action: {action}"


def _run_scan(mpcmd: str, scan_type: int) -> str:
    scan_name = "Quick Scan" if scan_type == 1 else "Full Scan"
    try:
        cmd = [mpcmd, "-Scan", "-ScanType", str(scan_type)]
        # This will block until the scan is complete, which for full scan might be a long time.
        # We'll set a timeout, but catch TimeoutExpired to notify it's running.
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600 if scan_type == 1 else 3600)
        
        if result.returncode == 0 or result.returncode == 2: 
            # 0=No threats, 2=Threats found
            return f"🛡️ {scan_name} completed.\nOutput: {result.stdout.strip()}"
        return f"Scan failed with return code {result.returncode}.\nOutput: {result.stdout.strip()}"
        
    except subprocess.TimeoutExpired:
        return f"🛡️ {scan_name} started and is running in the background. It may take some time to complete."
    except Exception as e:
        return f"Error running {scan_name}: {e}"


def _update_signatures(mpcmd: str) -> str:
    try:
        cmd = [mpcmd, "-SignatureUpdate"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            return "✅ Windows Defender signatures updated successfully."
        return f"Failed to update signatures. Error: {result.stdout.strip()}"
    except Exception as e:
        return f"Error updating signatures: {e}"


def _get_status() -> str:
    try:
        cmd = ["powershell", "-Command", "Get-MpComputerStatus | Select-Object AMServiceEnabled, AntivirusSignatureAge, RealTimeProtectionEnabled | Format-List"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            return f"🛡️ Antivirus Status:\n{result.stdout.strip()}"
        return f"Failed to get antivirus status: {result.stderr}"
    except Exception as e:
        return f"Error checking antivirus status: {e}"


class AntivirusManagerAction(Action):
    @property
    def name(self) -> str:
        return "antivirus_manager"

    @property
    def description(self) -> str:
        return (
            "Controls Windows Defender Antivirus. "
            "Can run quick scans, full scans, update threat signatures, and check real-time protection status."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "action": {
                    "type": "STRING", 
                    "description": "status | quick_scan | full_scan | update_signatures"
                }
            },
            "required": ["action"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs) -> str:
        return antivirus_manager(parameters=parameters, player=player, speak=speak)


ActionRegistry.register(AntivirusManagerAction)
