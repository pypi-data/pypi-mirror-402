import json
import sys
from pathlib import Path

CONFIG_FILE = Path.home() / ".cmdify_config.json"

def to_bool(value):
    if isinstance(value, bool): return value
    return str(value).lower() in ("true", "1", "yes", "on")

def load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load config file: {e}", file=sys.stderr)
    return {}

def save_config(config):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
        print(f"Configuration saved to {CONFIG_FILE}")
    except Exception as e:
        print(f"Error saving config: {e}", file=sys.stderr)

def print_config_help():
    print("Configuration Options for --set-config:")
    print("  -local_endpoint=<url>    Set the URL for a local LLM endpoint (e.g., http://localhost:8000/v1)")
    print("  -model=<name>            Set the model name to use (e.g., openai/gpt-4o, hosted_vllm/llama-3)")
    print("  -command_history=<n>     Number of recent shell commands to include in context (default: 3)")
    print("  -prefer-local=<bool>     If true, use local endpoint even if OPENAI_API_KEY is present (default: false)")
    print("  -api_key=<key>           (Optional) Set OpenAI API key directly in config")
    print("\nUsage Example:")
    print("  cmdify --set-config -local_endpoint=http://127.0.0.1:1234/v1 -prefer-local=true")
