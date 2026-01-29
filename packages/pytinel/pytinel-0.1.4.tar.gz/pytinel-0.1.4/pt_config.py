import json
import os
from pathlib import Path
from platformdirs import user_config_dir
from pt_crypto import derive_key, decrypt, encrypt

APP_NAME = "pytinel"
APP_AUTHOR = "pytinel"
CONFIG_DIR = Path(user_config_dir(APP_NAME, APP_AUTHOR))
CONFIG_FILE = CONFIG_DIR / "config.json"
_cached_key = None

DEFAULT_CONFIG = {
    "api_key": "",
    "base_url": "",
    "model": "",
    "policy": "standards"
}

def initialize_key():
    global _cached_key
    if _cached_key is None:
        _cached_key = derive_key(str(CONFIG_DIR), b"pytinel-salt")

def _get_key():
    global _cached_key
    if _cached_key is None:
        raise RuntimeError("Encryption key not initialized. Call initialize_key() at startup.")
    return _cached_key

def save_config(config_dict):
    to_save = config_dict.copy()
    if "api_key" in to_save and to_save["api_key"]:
        key = _get_key()
        encrypted = encrypt(to_save["api_key"], key)
        to_save["encrypted_api_key"] = encrypted
        del to_save["api_key"]
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(to_save, f, indent=4)

def load_config():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        config = DEFAULT_CONFIG.copy()
        config["api_key"] = ""
        return config
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    if "encrypted_api_key" in loaded:
        key = _get_key()
        plain_key = decrypt(loaded["encrypted_api_key"], key)
        if plain_key is None:
            raise RuntimeError("Failed to decrypt API key: invalid key or corrupted config.")
        loaded["api_key"] = plain_key
        del loaded["encrypted_api_key"]
    else:
        loaded["api_key"] = ""
    return loaded
    
def ensure_config(enforce: bool = False):
    config = load_config()
    modified = False
    if enforce or not config.get("api_key", "").strip() or not config.get("base_url", "").strip() or not config.get("model", "").strip():
        try:
            config = configure_api_url(config)
            config = configure_model(config)
            config = configure_api_key(config)
        except KeyboardInterrupt:
            return
        modified = True
    if modified:
        save_config(config)
        os.system('cls' if os.name == 'nt' else 'clear')
    return config

def configure_api_url(config):
    error_message = None
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\nSelect API Provider:")
        providers = [("1", "OpenAI (Default)", "https://api.openai.com/v1/chat/completions"), ("2", "DeepSeek", "https://api.deepseek.com/v1/chat/completions"), ("3", "Doubao", "https://api.doubao.com/v1/chat/completions"), ("4", "Kimi", "https://api.moonshot.cn/v1/chat/completions"), ("5", "Zhipu AI", "https://api.zhipuai.com/v1/chat/completions"), ("6", "Mistral AI", "https://api.mistral.ai/v1/chat/completions"), ("7", "Others (OpenAI)", "")]
        for num, name, url in providers:
            print(f"{num}. {name}")
        if error_message:
            print(error_message)
        choice = input("Enter your choice: ")
        if choice in ["1", "2", "3", "4", "5", "6", "7"]:
            break
        elif choice == "":
            choice = "1"
            break
        error_message = "Invalid choice. Please try again."
    if choice == "7":
        error_message = None
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            print("Please enter your custom base URL:")
            print("Example URL: https://api.example.com/v1/chat/completions")
            if error_message:
                print(error_message)
            custom_url = input("Enter base URL: ").strip().rstrip("/")
            if custom_url != "":
                break
            else:
                error_message = "Base URL cannot be empty."
        config["base_url"] = custom_url
    else:
        selected = providers[int(choice) - 1]
        config["base_url"] = selected[2]
    return config
        

def configure_model(config):
    error_message = None
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("Select Model:")
        print("Example: gpt-4o, deepseek-chat, doubao-seed-1.6...")
        if error_message:
            print(error_message)
        model_name = input("Enter model name: ").strip()
        if model_name != "":
            break
        else:
            error_message = "Model name cannot be empty."
    config["model"] = model_name
    return config

def configure_api_key(config):
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("Please enter your API key:")
        api_key = input("API key: ").strip()
        if api_key:
            break
        print("API key cannot be empty.")
    config["api_key"] = api_key
    return config

