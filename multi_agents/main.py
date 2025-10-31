from dotenv import load_dotenv
import sys
import os
import uuid
from pathlib import Path
from typing import Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from multi_agents.agents import ChiefEditorAgent
import asyncio
import json
from gpt_researcher.utils.enum import Tone

# Run with LangSmith if API key is set
if os.environ.get("LANGCHAIN_API_KEY"):
    os.environ["LANGCHAIN_TRACING_V2"] = "true"

# Load environment variables from common locations so the CLI works out of the box
_ROOT_DIR = Path(__file__).resolve().parent.parent
_MODULE_DIR = Path(__file__).resolve().parent

# Order matters: project root overrides module defaults, and shell env always wins
load_dotenv(_MODULE_DIR / ".env")
load_dotenv(_ROOT_DIR / ".env")
load_dotenv()


def _resolve_env_placeholders(value: Any) -> Any:
    """Recursively resolve environment variable placeholders in a task payload."""

    if isinstance(value, dict):
        return {k: _resolve_env_placeholders(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_env_placeholders(item) for item in value]
    if isinstance(value, str):
        # Support both ${VAR} and $VAR style placeholders
        if value.startswith("${") and value.endswith("}"):
            env_key = value[2:-1]
            return os.environ.get(env_key, value)
        if value.startswith("$") and len(value) > 1:
            env_key = value[1:]
            return os.environ.get(env_key, value)
    return value


def open_task():
    # Get the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Construct the absolute path to task.json
    task_json_path = os.path.join(current_dir, 'task.json')
    
    with open(task_json_path, 'r') as f:
        task = json.load(f)

    task = _resolve_env_placeholders(task)

    if not task:
        raise Exception("No task found. Please ensure a valid task.json file is present in the multi_agents directory and contains the necessary task information.")

    # Override model with STRATEGIC_LLM if defined in environment
    strategic_llm = os.environ.get("STRATEGIC_LLM")
    if strategic_llm:
        if ":" in strategic_llm:
            # Extract the model name (part after the first colon)
            model_name = strategic_llm.split(":", 1)[1]
            task["model"] = model_name
        else:
            task["model"] = strategic_llm

    return task

async def run_research_task(query, websocket=None, stream_output=None, tone=Tone.Objective, headers=None):
    task = open_task()
    task["query"] = query

    chief_editor = ChiefEditorAgent(task, websocket, stream_output, tone, headers)
    research_report = await chief_editor.run_research_task()

    if websocket and stream_output:
        await stream_output("logs", "research_report", research_report, websocket)

    return research_report

async def main():
    task = open_task()

    chief_editor = ChiefEditorAgent(task)
    research_report = await chief_editor.run_research_task(task_id=uuid.uuid4())

    return research_report

if __name__ == "__main__":
    asyncio.run(main())
