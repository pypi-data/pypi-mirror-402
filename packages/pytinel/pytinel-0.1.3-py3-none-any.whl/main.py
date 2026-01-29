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
    "standards": "Output ONLY executable Python code—no explanations. Use local libs or the requests library. The user's system is {os}. For file, network, subprocess, or system tasks: prepend code that prompts 'Are you sure you want to [ACTION]? (Y/N):' via input(), and exits if the response is not 'y'. Replace [ACTION] with a short, literal English description. If the request risks public safety, national security, or enables illegal harm: output EXACTLY: print(\"Operation denied.\"); exit()",
    "sandbox": "Output ONLY executable Python code—no explanations. Use only built-in modules or the requests library if absolutely necessary, but DO NOT perform any file, network, subprocess, or system operations. If the request involves ANY interaction with the operating system (including reading/writing files, making network calls, running commands, or accessing environment info), output EXACTLY: print(\"Operation denied.\"); exit(). Otherwise, perform ONLY pure computation.",
    "trusted": "Output ONLY executable Python code—no explanations. Use local libs or the requests library. The user's system is {os}. Execute ALL requested operations directly—do NOT prompt for confirmation, do NOT add safety checks, and do NOT restrict file, network, subprocess, or system tasks. If the request risks public safety, national security, or enables illegal harm: output EXACTLY: print(\"Operation denied.\"); exit()."
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
    print("Version 0.1.3")

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