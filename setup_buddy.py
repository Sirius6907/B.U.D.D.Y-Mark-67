import os
import sys
import subprocess
import platform
import time
from pathlib import Path

def run_command(command, description):
    print(f"🚀 {description}...")
    try:
        subprocess.run(command, check=True, shell=True)
        print(f"✅ {description} completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during {description}: {e}")
        return False
    return True

def install_ollama():
    print("🔍 Checking for Ollama...")
    try:
        subprocess.run(["ollama", "--version"], capture_output=True, check=True)
        print("✅ Ollama is already installed.")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️ Ollama not found.")
        if platform.system().lower() == "windows":
            print("🌎 Please download and install Ollama from: https://ollama.com/download")
            print("After installation, restart this script.")
            # For a true 1-click, we could automate the download, but it requires handling UAC etc.
            # We'll at least open the link for them.
            import webbrowser
            webbrowser.open("https://ollama.com/download")
            return False
        elif platform.system().lower() == "linux":
            print("🔨 Attempting to install Ollama via curl...")
            return run_command("curl -fsSL https://ollama.com/install.sh | sh", "Ollama Installation")
        else:
            print("❌ Automatic installation not supported for this OS. Please install Ollama manually.")
            return False

def pull_models():
    # Phase 6/7/8/9: Using gemma:2b for fast reasoning and hermes3:8b for deep reasoning.
    models = ["hermes3:8b", "gemma:2b"]
    
    for model in models:
        run_command(f"ollama pull {model}", f"Pulling model {model}")

def install_playwright():
    # Use python -m playwright to ensure it uses the correct environment path
    # Added quotes around sys.executable to handle paths with spaces (e.g. C:\Program Files)
    run_command(f'"{sys.executable}" -m playwright install', "Playwright Browser Engine Installation")

def main():
    print("====================================================")
    print("   B.U.D.D.Y MARK LXVII - SYSTEM SETUP WIZARD")
    print("====================================================\n")

    # 1. Check/Install Ollama
    if not install_ollama():
        print("\n❌ Setup cannot proceed without Ollama. Please install it and try again.")
        sys.exit(1)

    # 2. Pull Models
    print("\n📦 Initializing Local Intelligence Models...")
    pull_models()

    # 3. Playwright
    print("\n🌐 Initializing Browser Automation...")
    install_playwright()

    # 4. Final Pip check (if running from source)
    if os.path.exists("requirements.txt"):
        print("\n🐍 Checking Python dependencies...")
        run_command("pip install -r requirements.txt", "Pip Dependencies")

    print("\n====================================================")
    print("   ✅ SYSTEM INITIALIZATION COMPLETE")
    print("   BUDDY IS READY FOR DEPLOYMENT")
    print("====================================================")
    print("You can now run 'python main.py' or build with PyInstaller.")

if __name__ == "__main__":
    main()
