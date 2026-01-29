import sys
import os
import argparse
import pyperclip

from cmdify.config import load_config, save_config, to_bool, print_config_help
from cmdify.sys_utils import get_os_info, get_shell_info, get_recent_history, inject_command_to_console
from cmdify.llm import query_llm

def main():
    # Check for config help
    if "--set-config" in sys.argv and ("-h" in sys.argv or "--help" in sys.argv):
        print_config_help()
        sys.exit(0)

    parser = argparse.ArgumentParser(description="cmdify: Cmdify - AI command helper")
    parser.add_argument("query", type=str, nargs='?', help="The natural language description of the command you need.")
    parser.add_argument("--no-copy", action="store_true", help="Do not copy the result to clipboard.")
    parser.add_argument("--set-config", action="store_true", help="Update configuration values (e.g., -local_endpoint=... -model=...).")
    
    args, unknown = parser.parse_known_args()
    
    if args.set_config:
        config = load_config()
        updated = False
        for arg in unknown:
            if arg.startswith("-"):
                clean_arg = arg.lstrip("-")
                if "=" in clean_arg:
                    key, val = clean_arg.split("=", 1)
                    if key == "prefer-local":
                        key = "prefer_local"
                    
                    if key == "prefer_local":
                        val = to_bool(val)
                    
                    config[key] = val
                    print(f"Updated configuration: {key} = {val}")
                    updated = True
                else:
                    print(f"Warning: Argument '{arg}' does not match expected format 'key=value'. Ignoring.", file=sys.stderr)
            else:
                print(f"Warning: Ignoring invalid argument '{arg}'. Expected -key=value.", file=sys.stderr)
        
        if updated:
            save_config(config)
            if to_bool(config.get("prefer_local")) and not config.get("local_endpoint"):
                print("Warning: prefer-local is True but no local_endpoint is configured. Please set local_endpoint.", file=sys.stderr)
        else:
            print("No configuration changes detected. Use format: cmdify --set-config -key=value")
        return

    if not args.query:
        parser.print_help()
        sys.exit(1)
    
    query = args.query
    os_info = get_os_info()
    shell_info = get_shell_info()
    
    config = load_config()
    
    # Determine model and base_url
    api_key = os.environ.get("OPENAI_API_KEY")
    local_endpoint = config.get("local_endpoint")
    prefer_local = to_bool(config.get("prefer_local", False))
    
    if prefer_local and not local_endpoint:
        print("Warning: prefer-local is True but no local_endpoint is configured. Please set local_endpoint or set prefer-local to False.", file=sys.stderr)
    
    model = "gpt-4o-mini" # Default for OpenAI
    api_base = None
    
    use_local = False
    
    if local_endpoint:
        if prefer_local:
            use_local = True
        elif not api_key:
            use_local = True
            
    if use_local:
        # Use local endpoint
        api_base = local_endpoint
        model = config.get("model", "openai/qwen3-30b-a3b") # User can override model name if needed for local
        api_key = "sk-xxxx" # Dummy key often needed for local servers
    elif api_key:
        # Use OpenAI
        pass # litellm handles this default if OPENAI_API_KEY is set
    else:
        print("Error: No OPENAI_API_KEY found in environment and no 'local_endpoint' specified in ~/.cmdify_config.json.", file=sys.stderr)
        sys.exit(1)
        
    # Load history
    try:
        history_size = int(config.get("command_history", 3))
    except ValueError:
        history_size = 3
        
    history_lines = get_recent_history(history_size)
    history_context = ""
    if history_lines:
        history_context = "Recent command history:\n" + "\n".join(history_lines) + "\n\n"
        
    system_prompt = (
        f"You are a command line helper. "
        f"The user needs a command for the following OS: {os_info} "
        f"running in shell: {shell_info}. "
        f"{history_context}"
        f"Output ONLY the command, no markdown (no backticks), no explanations. "
        f"If multiple commands are needed, chain them appropriately for the shell."
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query}
    ]
    
    try:
        command = query_llm(model, messages, api_base=api_base, api_key=api_key)
        
        print(command)
        
        # Inject into console input (Windows only)
        inject_command_to_console(command)
        
        if not args.no_copy:
            try:
                pyperclip.copy(command)
                print("(Copied to clipboard)", file=sys.stderr)
            except Exception as e:
                print(f"(Failed to copy to clipboard: {e})", file=sys.stderr)
                
    except Exception as e:
        print(f"Error calling LLM: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
