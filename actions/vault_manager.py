import os
from cryptography.fernet import Fernet
from actions.base import Action, ActionRegistry

# Path to the encryption key
KEY_FILE = os.path.join(os.getcwd(), ".buddy_vault.key")

def vault_manager(parameters: dict, player=None, speak=None, **kwargs) -> str:
    action = parameters.get("action", "encrypt").lower()
    file_path = parameters.get("file_path")
    
    if not file_path: return "Error: 'file_path' required."
    
    # Initialize or load key
    key = _get_or_create_key()
    fernet = Fernet(key)
    
    if action == "encrypt":
        return _encrypt_file(file_path, fernet)
    if action == "decrypt":
        return _decrypt_file(file_path, fernet)
    if action == "gen_key":
        return f"🔑 Key already exists at {KEY_FILE}. Keep it safe!"
        
    return f"Unknown vault_manager action: {action}"


def _get_or_create_key():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
        return key
    with open(KEY_FILE, "rb") as f:
        return f.read()


def _encrypt_file(file_path: str, fernet: Fernet) -> str:
    try:
        if not os.path.exists(file_path): return f"❌ File not found: {file_path}"
        if file_path.endswith(".locked"): return "⚠️ File is already encrypted."
        
        with open(file_path, "rb") as f:
            data = f.read()
            
        encrypted_data = fernet.encrypt(data)
        
        new_path = file_path + ".locked"
        with open(new_path, "wb") as f:
            f.write(encrypted_data)
            
        # Optional: Delete original
        # os.remove(file_path)
        
        return f"🔒 File encrypted successfully: {new_path}"
    except Exception as e:
        return f"❌ Encryption failed: {e}"


def _decrypt_file(file_path: str, fernet: Fernet) -> str:
    try:
        if not os.path.exists(file_path): return f"❌ File not found: {file_path}"
        if not file_path.endswith(".locked"): return "⚠️ This does not appear to be a .locked file."
        
        with open(file_path, "rb") as f:
            encrypted_data = f.read()
            
        decrypted_data = fernet.decrypt(encrypted_data)
        
        new_path = file_path.replace(".locked", "")
        if os.path.exists(new_path):
            new_path = new_path.replace(".", f"_decrypted_{int(os.path.getmtime(file_path))}.")
            
        with open(new_path, "wb") as f:
            f.write(decrypted_data)
            
        return f"🔓 File decrypted successfully: {new_path}"
    except Exception as e:
        return f"❌ Decryption failed (Incorrect key or corrupted file): {e}"


class VaultManagerAction(Action):
    @property
    def name(self) -> str:
        return "vault_manager"

    @property
    def description(self) -> str:
        return (
            "Manages encrypted file storage (Vault). "
            "Can encrypt files to a .locked format or decrypt them back. "
            "Uses AES-256 (Fernet). THE KEY IS STORED LOCALLY IN .buddy_vault.key."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "action": {
                    "type": "STRING", 
                    "description": "encrypt | decrypt | gen_key"
                },
                "file_path": {
                    "type": "STRING",
                    "description": "Path to the file to process"
                }
            },
            "required": ["action"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs) -> str:
        return vault_manager(parameters=parameters, player=player, speak=speak)


ActionRegistry.register(VaultManagerAction)
