import os
import subprocess
import requests
import platform
import sys
import tempfile
import re
from pt_config import initialize_key, ensure_config
from pt_init import init

config = None
api_key = None
api_url = None
model_name = None
SYSTEM_PROMPT = {
    "standards": "Output ONLY executable Python code—no explanations; use only stdlib or requests; for ANY file/network/subprocess/system operation, prepend: import sys; a=input('Are you sure you want to [ACTION]? (Y/N): '); sys.exit() if a.lower()!='y' else None (replace [ACTION] with a short literal English description); if request risks public safety, national security, or enables illegal harm, output EXACTLY: print(\"User-generated content is too dangerous, execution terminated.\"); exit()",
    "sandbox": "Output ONLY executable Python code—no explanations; use only pure stdlib with NO file/network/subprocess/system access (e.g., no os, sys, subprocess, shutil, pathlib, urllib, requests, socket, etc.); if ANY operation could read/write files, access network, run commands, or affect the system, treat it as dangerous and output EXACTLY: print(\"User-generated content is too dangerous, execution terminated.\"); exit()",
    "trusted": "Output ONLY executable Python code—no explanations; use only stdlib or requests; DO NOT add any confirmation prompts for file/network/subprocess/system operations; if request risks public safety, national security, or enables illegal harm, output EXACTLY: print(\"User-generated content is too dangerous, execution terminated.\"); exit()"
}

def get_user_system():
    system = platform.system()
    if system == "Windows":
        return "Windows"
    elif system == "Darwin":
        return "macOS"
    elif system == "Linux":
        return "Linux"
    else:
        return "Unix-like"


def get_python_code_from_llm(prompt):
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": model_name,
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT["standards"].format(os=get_user_system())
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 1000,
        }
        
        response = requests.post(api_url, headers=headers, json=payload, timeout=600)
        response.raise_for_status()
        
        result = response.json()
        code = result["choices"][0]["message"]["content"].strip()
        
        code_block_match = re.search(r"```python\n(.*?)```", code, re.DOTALL)
        if code_block_match:
            code = code_block_match.group(1).strip()
        
        return code
    except Exception as e:
        return f"{e}"

def execute_python_code(code):
    temp_file = None
    
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            delete=False,
            encoding="utf-8",
            dir="."
        ) as f:
            f.write(code)
            temp_file=f.name
        
        result = subprocess.run(
            [sys.executable, temp_file],
            stdin=None,
            stdout=None,
            stderr=None
        )
            
    except Exception as e:
        print(f"{e}")
    finally:
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)

def update_config(enforce: bool = False):
    global config, api_key, api_url, model_name
    config = ensure_config(enforce)
    api_key = config["api_key"]
    api_url = config["base_url"]
    model_name = config["model"]

def main():
    initialize_key()
    init()
    update_config()

    print("Python Terminal in Natural Executable Language")
    print("Version 0.1.1")

    while True:
        try:
            prompt = input(">>> ")
            
            if prompt.lower() in ["exit", "quit", "exit()", "quit()"]:
                break
            elif prompt.lower() in ["setting", "config", "setting()", "config()"]:
                update_config(True)
                continue
            if not prompt.strip():
                continue
            code = get_python_code_from_llm(prompt)
            execute_python_code(code)
            print()
            
        except KeyboardInterrupt:
            print("")
            break
        except Exception as e:
            print(f"Error: {e}")
            print()

if __name__ == "__main__":
    main()