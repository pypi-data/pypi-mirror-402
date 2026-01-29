# cmdify

Cmdify - A tool to translate natural language to shell commands using LLMs.

## Installation

```bash
pip install cmdify
```

## Usage

You can use `cmdify` (or the short alias `ctr` if installed):

```bash
cmdify "Remove everything under the directory foo/"
# or
ctr "Remove everything under the directory foo/"
```

The command will be printed to the console and copied to your clipboard.

## Configuration

Set your OpenAI API key:
```bash
export OPENAI_API_KEY=sk-...
```

Or configure a local endpoint (e.g., vLLM, LMStudio). You can set this via the command line:

```bash
cmdify --set-config -local_endpoint=http://127.0.0.1:1234/v1 -model=openai/qwen3-30b-a3b
```

To see all available configuration options, run:

```bash
cmdify --set-config -h
```

Common options:
*   `local_endpoint`: URL for your local LLM server.
*   `model`: Model name to use.
*   `command_history`: Number of recent shell commands to include in context (default: 3).
*   `prefer-local`: If set to `true`, forces use of the local endpoint even if `OPENAI_API_KEY` is set.

Example of setting command history size:
```bash
cmdify --set-config -command_history=5
```

Alternatively, you can manually edit `~/.cmdify_config.json`:
```json
{
  "local_endpoint": "http://localhost:8000/v1",
  "model": "hosted_vllm/...",
  "command_history": 5
}
```
