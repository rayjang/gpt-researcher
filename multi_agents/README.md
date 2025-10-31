# LangGraph x GPT Researcher
[LangGraph](https://python.langchain.com/docs/langgraph) is a library for building stateful, multi-actor applications with LLMs. 
This example uses Langgraph to automate the process of an in depth research on any given topic.

## Use case
By using Langgraph, the research process can be significantly improved in depth and quality by leveraging multiple agents with specialized skills. 
Inspired by the recent [STORM](https://arxiv.org/abs/2402.14207) paper, this example showcases how a team of AI agents can work together to conduct research on a given topic, from planning to publication.

An average run generates a 5-6 page research report in multiple formats such as PDF, Docx and Markdown.

Please note: Multi-agents are utilizing the same configuration of models like GPT-Researcher does. However, only the SMART_LLM is used for the time being. Please refer to the [LLM config pages](https://docs.gptr.dev/docs/gpt-researcher/llms/llms).

## The Multi Agent Team
The research team is made up of 8 agents:
- **Human** - The human in the loop that oversees the process and provides feedback to the agents.
- **Chief Editor** - Oversees the research process and manages the team. This is the "master" agent that coordinates the other agents using Langgraph.
- **Researcher** (gpt-researcher) - A specialized autonomous agent that conducts in depth research on a given topic.
- **Editor** - Responsible for planning the research outline and structure.
- **Reviewer** - Validates the correctness of the research results given a set of criteria.
- **Revisor** - Revises the research results based on the feedback from the reviewer.
- **Writer** - Responsible for compiling and writing the final report.
- **Publisher** - Responsible for publishing the final report in various formats.

## How it works
Generally, the process is based on the following stages: 
1. Planning stage
2. Data collection and analysis
3. Review and revision
4. Writing and submission
5. Publication

### Architecture
<div align="center">
<img align="center" height="600" src="https://github.com/user-attachments/assets/ef561295-05f4-40a8-a57d-8178be687b18">
</div>
<br clear="all"/>

### Steps
More specifically (as seen in the architecture diagram) the process is as follows:
- Browser (gpt-researcher) - Browses the internet for initial research based on the given research task.
- Editor - Plans the report outline and structure based on the initial research.
- For each outline topic (in parallel):
  - Researcher (gpt-researcher) - Runs an in depth research on the subtopics and writes a draft.
  - Reviewer - Validates the correctness of the draft given a set of criteria and provides feedback.
  - Revisor - Revises the draft until it is satisfactory based on the reviewer feedback.
- Writer - Compiles and writes the final report including an introduction, conclusion and references section from the given research findings.
- Publisher - Publishes the final report to multi formats such as PDF, Docx, Markdown, etc.

## Prerequisites
1. Install the Python dependencies (LangGraph and GPT-Researcher ships in `requirements.txt`):
    ```bash
    pip install -r requirements.txt
    ```
2. Install the [kisti-mcp](https://github.com/ansua79/kisti-mcp) client so the MCP retriever can launch it:
    ```bash
    pip install kisti-mcp
    ```
3. (Optional) Install [LangSmith](https://docs.smith.langchain.com/) CLI support if you plan to stream traces by exporting `LANGCHAIN_API_KEY`.

### Configure environment variables
1. Copy the example environment file and fill in your credentials:
    ```bash
    cp multi_agents/.env.example .env
    ```
2. Open `.env` and provide the following values:
    - `OPENAI_API_KEY` (required) – the default LLM for all agents.
    - `TAVILY_API_KEY` (required when the Tavily retriever is enabled).
    - `KISTI_API_KEY` and `KISTI_API_SECRET` (required for the MCP bridge).
    - `KISTI_MCP_BASE_URL` (optional) – override the default MCP endpoint if your deployment differs.
    - `DOC_PATH` (optional) – location of your local reference documents, defaults to `./my-docs`.
    - `STRATEGIC_LLM` or `SMART_LLM` (optional) – override the OpenAI model used by the LangGraph agents.
3. Any variables defined in `.env` are automatically loaded by `multi_agents/main.py`. You can also export them directly in your shell instead of using a file.

4. Place your local reference material under `./my-docs` (or set the `DOC_PATH` environment variable to point elsewhere).

## How to run
1. Ensure the `kisti-mcp` executable is on your `$PATH`. The default `task.json` will spawn the MCP server automatically using the command listed in its `mcp_configs` section.
2. Run the multi-agent workflow from the repository root:
    ```bash
    python multi_agents/main.py
    ```
3. Monitor the console for progress logs. When the run completes, the generated report and artifacts are saved under `./outputs/`.

### Verify the setup
Use these checks whenever you change configuration or upgrade dependencies:

- Compile-time sanity check:
  ```bash
  python -m compileall multi_agents
  ```
- End-to-end smoke test with the provided `task.json`:
  ```bash
  python multi_agents/main.py
  ```
  Inspect the latest folder in `./outputs/` to confirm the hybrid retrieval summary was produced.

## Usage
To change the research query and customize the report, edit the `task.json` file in the main directory.
#### Task.json contains the following fields:
- `query` - The research query or task.
- `source` - The location from which to conduct the research. Options: `web`, `local`, or `hybrid` (combine web and local documents).
- `retrievers` - Optional list of retrievers to use. When omitted GPT Researcher defaults to Tavily. Provide multiple values (e.g. `["tavily", "arxiv", "mcp"]`) to fan out to several knowledge sources.
- `model` - The OpenAI LLM to use for the agents.
- `max_sections` - The maximum number of sections in the report. Each section is a subtopic of the research query.
- `include_human_feedback` - If true, the user can provide feedback to the agents. If false, the agents will work autonomously.
- `publish_formats` - The formats to publish the report in. The reports will be written in the `output` directory.
- `follow_guidelines` - If true, the research report will follow the guidelines below. It will take longer to complete. If false, the report will be generated faster but may not follow the guidelines.
- `guidelines` - A list of guidelines that the report must follow.
- `verbose` - If true, the application will print detailed logs to the console.

#### For example:
```json
{
  "query": "Is AI in a hype cycle?",
  "model": "gpt-4o",
  "max_sections": 3, 
  "publish_formats": {
    "markdown": true,
    "pdf": true,
    "docx": true
  },
  "include_human_feedback": false,
  "source": "web",
  "follow_guidelines": true,
  "guidelines": [
    "The report MUST fully answer the original question",
    "The report MUST be written in apa format",
    "The report MUST be written in english"
  ],
  "verbose": true
}
```

### Hybrid research with local documents, Tavily, arXiv and KISTI MCP

The example `task.json` in this directory is pre-configured for hybrid research:

- `source` is set to `"hybrid"` so the researcher blends local documents from `./my-docs` with the configured web retrievers.
- `retrievers` enumerates the engines the agents will call (`tavily`, `arxiv`, and the MCP retriever).
- `mcp_configs` starts the [kisti-mcp](https://github.com/ansua79/kisti-mcp) server so the MCP retriever can query the institute's APIs. The sample configuration uses environment placeholders such as `${KISTI_API_KEY}` which are resolved automatically when the task file is loaded.

To get up and running:

1. Install and configure the `kisti-mcp` package following the repository instructions. Ensure the CLI command (`kisti-mcp` by default) is on your `$PATH`.
2. Provide the required credentials in `.env` or your shell (`KISTI_API_KEY`, `KISTI_API_SECRET`, and optionally `KISTI_MCP_BASE_URL`).
3. Place your local reference material under `./my-docs` (or set the `DOC_PATH` environment variable to point elsewhere).
4. Run `python multi_agents/main.py` to launch the multi-agent pipeline.

During execution each research agent will:

- index local files for relevant passages,
- pull web data through Tavily and arXiv,
- and query KISTI knowledge through the MCP server.

The reviewer, writer, and publisher agents then collaborate on the final Korean APA-style report that merges all of these sources.

## To Deploy

```shell
pip install langgraph-cli
langgraph up
```

From there, see documentation [here](https://github.com/langchain-ai/langgraph-example) on how to use the streaming and async endpoints, as well as the playground.
