import os
import json
import sqlite3
import subprocess

def probe_path(*parts):
    p = os.path.join(*parts)
    print(f"{p}: {'[EXISTS]' if os.path.exists(p) else '[MISSING]'}")
    return p

appdata = os.getenv('APPDATA')
localappdata = os.getenv('LOCALAPPDATA')
home = os.path.expanduser('~')

print("--- VS Code ---")
probe_path(appdata, 'Code', 'User', 'globalStorage', 'state.vscdb')

print("\n--- Antigravity ---")
probe_path(home, '.gemini', 'antigravity', 'brain')

print("\n--- Codex ---")
probe_path(home, '.codex')
probe_path(appdata, 'codex')

print("\n--- OpenCode ---")
probe_path(home, '.opencode')
probe_path(appdata, 'opencode')

print("\n--- Gemini CLI ---")
probe_path(home, '.gemini')
probe_path(appdata, 'gemini')

print("\n--- Hermes (WSL) ---")
try:
    result = subprocess.run(["wsl", "-d", "kali-linux", "--", "bash", "-lc", "ls -la /home/sirius/.hermes"], capture_output=True, text=True, timeout=5)
    print("Hermes WSL output:\n", result.stdout[:500])
except Exception as e:
    print("WSL probe error:", e)
