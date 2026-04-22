import subprocess
import os
import shutil
from actions.base import Action, ActionRegistry

def privacy_manager(parameters: dict, player=None, speak=None, **kwargs) -> str:
    action = parameters.get("action", "clear_all").lower()
    
    if action == "clear_all":
        results = [
            _empty_recycle_bin(),
            _clear_temp_files(),
            _clear_browser_cache()
        ]
        return "🧹 Privacy Sweep Results:\n" + "\n".join(results)
        
    if action == "empty_recycle_bin":
        return _empty_recycle_bin()
    if action == "clear_temp_files":
        return _clear_temp_files()
    if action == "clear_browser_cache":
        return _clear_browser_cache()
        
    return f"Unknown privacy_manager action: {action}"


def _empty_recycle_bin() -> str:
    try:
        cmd = ["powershell", "-Command", "Clear-RecycleBin -Force"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            return "✅ Recycle Bin emptied successfully."
        return f"Failed to empty Recycle Bin: {result.stderr.strip()}"
    except Exception as e:
        return f"Error emptying Recycle Bin: {e}"


def _clear_temp_files() -> str:
    temp_paths = [
        os.environ.get("TEMP"),
        os.environ.get("TMP"),
        r"C:\Windows\Temp",
        r"C:\Windows\Prefetch"
    ]
    
    deleted_count = 0
    failed_count = 0
    
    for path in temp_paths:
        if not path or not os.path.exists(path):
            continue
            
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                try:
                    os.remove(os.path.join(root, name))
                    deleted_count += 1
                except Exception:
                    failed_count += 1
                    
            for name in dirs:
                try:
                    os.rmdir(os.path.join(root, name))
                except Exception:
                    # Usually fails if directory is not empty or in use
                    pass

    return f"✅ Cleared {deleted_count} temporary files. ({failed_count} files were in use and skipped)."


def _clear_browser_cache() -> str:
    # A robust browser cache clear usually requires killing the browser first, which we won't do automatically.
    # Instead, we will attempt to delete cache directories for Chrome and Edge if they exist.
    
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if not local_app_data:
        return "LOCALAPPDATA environment variable not found."
        
    cache_paths = [
        os.path.join(local_app_data, r"Google\Chrome\User Data\Default\Cache"),
        os.path.join(local_app_data, r"Google\Chrome\User Data\Default\Code Cache"),
        os.path.join(local_app_data, r"Microsoft\Edge\User Data\Default\Cache"),
        os.path.join(local_app_data, r"Microsoft\Edge\User Data\Default\Code Cache")
    ]
    
    deleted_bytes = 0
    for cache_dir in cache_paths:
        if os.path.exists(cache_dir):
            try:
                for item in os.listdir(cache_dir):
                    item_path = os.path.join(cache_dir, item)
                    try:
                        if os.path.isfile(item_path):
                            size = os.path.getsize(item_path)
                            os.remove(item_path)
                            deleted_bytes += size
                        elif os.path.isdir(item_path):
                            # simplistic size accumulation
                            shutil.rmtree(item_path, ignore_errors=True)
                    except Exception:
                        pass
            except Exception:
                pass

    if deleted_bytes > 0:
        return f"✅ Cleared approx {deleted_bytes / (1024*1024):.2f} MB of browser cache."
    return "✅ Browser cache clear attempted (Note: files might be locked if the browser is running)."


class PrivacyManagerAction(Action):
    @property
    def name(self) -> str:
        return "privacy_manager"

    @property
    def description(self) -> str:
        return (
            "Manages and protects user privacy. "
            "Can clear temporary files, empty the recycle bin, and clear common browser caches."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "action": {
                    "type": "STRING", 
                    "description": "clear_all | empty_recycle_bin | clear_temp_files | clear_browser_cache"
                }
            },
            "required": ["action"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs) -> str:
        return privacy_manager(parameters=parameters, player=player, speak=speak)


ActionRegistry.register(PrivacyManagerAction)
