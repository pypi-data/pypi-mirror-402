import os
import sys
import warnings
import litellm

# Suppress Pydantic warnings from litellm/pydantic v2 compatibility issues
warnings.filterwarnings("ignore", message=".*Pydantic serializer warnings.*")

def query_llm(model, messages, api_base=None, api_key=None):
    """
    Calls the LLM using litellm and cleans up the response.
    """
    try:
        kwargs = {
            "model": model,
            "messages": messages,
        }
        if api_base:
            kwargs["api_base"] = api_base
        if api_key and not os.environ.get("OPENAI_API_KEY"):
             kwargs["api_key"] = api_key

        response = litellm.completion(**kwargs)
        
        command = response.choices[0].message.content.strip()
        
        # Strip potential markdown code blocks
        if command.startswith("```") and command.endswith("```"):
            lines = command.splitlines()
            if len(lines) >= 2:
                command = "\n".join(lines[1:-1])
            else:
                command = command.strip("`")
        elif command.startswith("`") and command.endswith("`"):
             command = command.strip("`")
             
        return command
        
    except Exception as e:
        # Re-raise to let caller handle or exit
        raise e
