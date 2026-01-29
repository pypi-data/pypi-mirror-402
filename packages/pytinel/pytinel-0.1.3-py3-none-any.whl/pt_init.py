from pathlib import Path
from platformdirs import user_config_dir
from pt_config import ensure_config

FIRST_RUN_DISCLAIMER = """Welcome to Pytinel

Pytinel (Python Terminal in Natural Executable Language) is an intelligent, in-process Python REPL that interprets natural-language prompts and executes the corresponding Python code directly within your runtime environment—without displaying intermediate code generation.

Execution Model:
- Generated code executes silently by default.
- High-risk operations—including but not limited to file system modifications, network requests, subprocess invocations, and environment variable alterations—require explicit user authorization prior to execution.

Credential Management:
- LLM API credentials are stored locally using platform-adaptive key derivation and AES-based encryption at rest.
- No credentials, prompts, generated code, or execution results are transmitted off-device. Pytinel collects no telemetry, logs no session data, and performs no external communication.

Security Notice:
- Code synthesized by large language models may contain logical errors, security vulnerabilities, or unintended side effects.
- Pytinel implements prompt-level risk filtering but does not perform static or dynamic analysis of the generated code.
- By using this tool, you acknowledge full responsibility for the safety, correctness, and consequences of all executed instructions.
"""
def init():
    APP_NAME = "pytinel"
    APP_AUTHOR = "pytinel"
    CONFIG_DIR = Path(user_config_dir(APP_NAME, APP_AUTHOR))
    CONFIG_FILE = CONFIG_DIR / "config.json"
    if not CONFIG_FILE.exists():
        print(FIRST_RUN_DISCLAIMER)
        input("Press Enter to continue…")
        ensure_config()

    