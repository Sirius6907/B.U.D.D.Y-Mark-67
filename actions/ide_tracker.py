import os
import json
import sqlite3
import subprocess
import urllib.parse
from datetime import datetime
from actions.base import ActionRegistry, Action

def get_vscode_recent():
    try:
        appdata = os.getenv('APPDATA')
        if not appdata:
            return "VS Code: APPDATA environment variable not found."
        
        db_path = os.path.join(appdata, 'Code', 'User', 'globalStorage', 'state.vscdb')
        if not os.path.exists(db_path):
            return "VS Code: No recent history found."
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM ItemTable WHERE key='history.recentlyOpenedPathsList'")
        row = cursor.fetchone()
        conn.close()
        
        if row:
            data = json.loads(row[0])
            entries = data.get("entries", [])
            recent_paths = []
            for entry in entries[:5]:
                uri = entry.get("folderUri", "")
                if uri.startswith("file:///"):
                    # Unquote the URI to get actual Windows path
                    path = urllib.parse.unquote(uri[8:])
                    recent_paths.append(path)
            
            if recent_paths:
                return "VS Code Recent Projects:\n" + "\n".join(f"- {p}" for p in recent_paths)
        
        return "VS Code: No recent folders found."
    except Exception as e:
        return f"VS Code: Error reading history ({e})"

def get_antigravity_recent():
    try:
        brain_path = os.path.expanduser("~/.gemini/antigravity/brain")
        if not os.path.exists(brain_path):
            return "Antigravity: No recent brain history found."
            
        subdirs = [os.path.join(brain_path, d) for d in os.listdir(brain_path) if os.path.isdir(os.path.join(brain_path, d))]
        if not subdirs:
            return "Antigravity: No active sessions."
            
        subdirs.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        recent_sessions = []
        for s in subdirs[:3]:
            session_id = os.path.basename(s)
            mod_time = datetime.fromtimestamp(os.path.getmtime(s)).strftime("%Y-%m-%d %H:%M:%S")
            recent_sessions.append(f"Session {session_id} (Updated: {mod_time})")
            
        return "Antigravity Recent Sessions:\n" + "\n".join(f"- {s}" for s in recent_sessions)
    except Exception as e:
        return f"Antigravity: Error reading history ({e})"

def get_codex_recent():
    try:
        index_path = os.path.expanduser("~/.codex/session_index.jsonl")
        if not os.path.exists(index_path):
            return "Codex: No recent sessions found."
            
        sessions = []
        with open(index_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in reversed(lines[-5:]): # Last 5
                data = json.loads(line)
                thread_name = data.get("thread_name", "Unknown Thread")
                updated_at = data.get("updated_at", "")
                sessions.append(f"Thread: {thread_name} (Updated: {updated_at})")
                
        if sessions:
            return "Codex Recent Threads:\n" + "\n".join(f"- {s}" for s in sessions)
        return "Codex: No recent threads."
    except Exception as e:
        return f"Codex: Error reading history ({e})"

def get_hermes_wsl_recent():
    try:
        result = subprocess.run(
            ["wsl", "-d", "kali-linux", "--", "bash", "-c", "ls -l /home/sirius/.hermes/state.db-shm 2>/dev/null"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return "Hermes Agent (WSL): State Database is active and recently updated."
        return "Hermes Agent (WSL): Installed, but recent state not available."
    except Exception as e:
        return f"Hermes Agent (WSL): Error ({e})"

class GetRecentIdeProjectsAction(Action):
    @property
    def name(self) -> str:
        return "get_recent_ide_projects"
        
    @property
    def description(self) -> str:
        return "Retrieves a list of recently opened projects from multiple IDEs (VS Code, Antigravity, Codex, Hermes, OpenCode, Gemini CLI) to understand what the user was working on."
        
    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {},
            "required": []
        }
        
    def execute(self, parameters: dict, player=None, speak=None, **kwargs) -> str:
        results = [
            get_vscode_recent(),
            get_antigravity_recent(),
            get_codex_recent(),
            get_hermes_wsl_recent(),
            "OpenCode/Gemini CLI: Activity tracked externally or not recently updated."
        ]
        return "\n\n".join(results)

ActionRegistry.register(GetRecentIdeProjectsAction)


class LaunchIdeProjectAction(Action):
    @property
    def name(self) -> str:
        return "launch_ide_project"
        
    @property
    def description(self) -> str:
        return "Launches an IDE and optionally opens a specific project path."
        
    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "ide": {
                    "type": "string",
                    "description": "The name of the IDE/agent to launch (e.g. 'vscode', 'antigravity', 'codex', 'hermes', 'opencode', 'gemini')"
                },
                "path": {
                    "type": "string",
                    "description": "The specific path to open inside the IDE. Optional."
                },
                "new_window": {
                    "type": "boolean",
                    "description": "If true, forces opening in a new window. Default is false (reuses recent working window)."
                }
            },
            "required": ["ide"]
        }
        
    def execute(self, parameters: dict, player=None, speak=None, **kwargs) -> str:
        ide = parameters.get("ide", "").lower()
        path = parameters.get("path")
        new_window = parameters.get("new_window", False)
        
        try:
            if ide in ["vscode", "code"]:
                cmd_args = ["code"]
                if new_window:
                    cmd_args.append("-n")
                else:
                    cmd_args.append("-r")
                    
                if path and os.path.exists(path):
                    cmd_args.append(path)
                    subprocess.Popen(" ".join(cmd_args), shell=True)
                    return f"Launched VS Code at {path} (new_window={new_window})"
                
                subprocess.Popen(" ".join(cmd_args), shell=True)
                return f"Launched VS Code (new_window={new_window})"
                
            elif ide in ["antigravity", "gemini"]:
                cmd = "antigravity" if ide == "antigravity" else "gemini"
                subprocess.Popen(["start", "cmd", "/K", cmd], shell=True)
                return f"Launched {cmd} in new terminal."
                
            elif ide == "codex":
                subprocess.Popen(["start", "cmd", "/K", "codex"], shell=True)
                return "Launched Codex CLI."
                
            elif ide == "opencode":
                subprocess.Popen(["start", "cmd", "/K", "opencode"], shell=True)
                return "Launched OpenCode CLI."
                
            elif ide == "hermes":
                subprocess.Popen(["start", "cmd", "/K", "wsl -d kali-linux -- bash -lc 'hermes start'"], shell=True)
                return "Launched Hermes Agent in WSL."
                
            else:
                return f"Unknown IDE or software: {ide}"
                
        except Exception as e:
            return f"Failed to launch {ide}: {e}"

ActionRegistry.register(LaunchIdeProjectAction)

if __name__ == "__main__":
    action = GetRecentIdeProjectsAction()
    print(action.execute({}))
