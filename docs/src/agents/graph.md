# Documentation for `src/agents/graph.py`

## Overview

`src/agents/graph.py` implements a **graph‑based coordination layer** for the FinBot project.  It wires together a set of specialised LangChain agents (documentation, release‑notes, issue‑management and code‑review) and exposes each sub‑agent as a LangChain **tool**.  The top‑level *coordinator* agent (`github_agent`) receives a high‑level user request, decides which sub‑agent should handle the work, and delegates the request via the tool wrappers.

The module provides:

* An `AgentName` enum for type‑safe dispatch.
* Four sub‑agents (`_documentation_agent`, `_release_notes_agent`, `_issue_agent`, `_code_review_agent`).
* Four tool wrappers (`call_documentation_agent`, `call_release_notes_agent`, `call_issue_agent`, `call_code_review_agent`).
* The main `github_agent` that orchestrates the workflow.
* A tiny CLI‑style entry point that demonstrates how to invoke the coordinator.

---

## Key Components

### 1. Imports & Global Objects
```python
from enum import Enum
from typing import Annotated

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool, InjectedToolCallId
from langchain_community.agent_toolkits.github.toolkit import GitHubToolkit
from langchain_community.utilities.github import GitHubAPIWrapper
from langchain_core.messages import ToolMessage
from langchain_groq import ChatGroq
from langgraph.types import Command

from .utils import (
    rename_tool,
    get_issue_tools,
    get_release_tools,
    get_code_review_tools,
    get_documentation_tools,
)
```
* Environment variables are loaded via `load_dotenv()`.
* `ChatGroq` (model `openai/gpt-oss-120b`) is used as the LLM for all agents.
* `GitHubAPIWrapper` together with `GitHubToolkit` provides the low‑level GitHub operations that the sub‑agents will call.

### 2. Sub‑Agents
Each sub‑agent is created with `create_agent`, a specific set of tools, a name and a system prompt that describes its responsibility.

```python
_documentation_agent = create_agent(
    model=llm,
    tools=get_documentation_tools(tools),
    name="documentation_agent",
    system_prompt="...",
)
```
The same pattern is repeated for:
* `_release_notes_agent`
* `_issue_agent`
* `_code_review_agent`

### 3. `AgentName` Enum
```python
class AgentName(str, Enum):
    DOCUMENTATION = "documentation_agent"
    RELEASE_NOTES = "release_notes_agent"
    ISSUE = "issue_agent"
    CODE_REVIEW = "code_review_agent"
```
Provides a clear, type‑safe way to reference agents.

### 4. Tool Wrappers
Each wrapper is decorated with `@tool` so that the coordinator can call it like any other LangChain tool.  The wrapper:
1. Calls the appropriate sub‑agent via `invoke`.
2. Extracts the final message from the sub‑agent’s response.
3. Returns a `Command` that injects a `ToolMessage` back into the graph.

Example – Documentation Agent:
```python
@tool(
    "documentation_agent",
    description=(
        "Handles project documentation tasks: writing/updating README files, API docs, and any "
        "other project documentation. Pass a clear description of the documentation task to perform."
    ),
)
def call_documentation_agent(
    task: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    result = _documentation_agent.invoke({"messages": [{"role": "user", "content": task}]})
    return Command(update={
        "messages": [ToolMessage(content=result["messages"][-1].content, tool_call_id=tool_call_id)]
    })
```
The other three wrappers follow the same structure.

### 5. Coordinator Agent (`github_agent`)
```python
github_agent = create_agent(
    model=llm,
    tools=[
        call_documentation_agent,
        call_release_notes_agent,
        call_issue_agent,
        call_code_review_agent,
    ],
    system_prompt=(
        "You are a GitHub project coordinator that delegates tasks to specialized subagents via tools. "
        "..."
    ),
)
```
The system prompt explicitly tells the agent to **only** use the provided tools and never perform GitHub actions directly.

### 6. CLI / Script Entry Point
When the file is executed directly, a simple demonstration request is sent to the coordinator:
```python
if __name__ == "__main__":
    res = github_agent.invoke({
        "messages": [{"role": "user", "content": "Create a markdown documentation for app/agents.py for the project finbot_repo and raise a PR for it."}]
    })
    print(res)
```
This showcases how a user can ask the system to generate documentation and open a PR – the coordinator will route the request to `documentation_agent`.

---

## Usage Example
Below is a minimal example of how another module could import and use the coordinator:

```python
from src.agents.graph import github_agent

# Define a user request – any natural‑language instruction.
request = "Update the README to include a quick‑start guide and create a PR targeting the 'main' branch."

# Invoke the graph.
response = github_agent.invoke({
    "messages": [{"role": "user", "content": request}]
})

# The response contains the final message from the sub‑agent.
print(response["messages"][-1].content)
```
The coordinator will:
1. Analyse the request.
2. Choose the `documentation_agent` tool.
3. The sub‑agent will use the `create_file`, `update_file`, `set_active_branch`, etc., tools to edit the README and open a PR.

---

## Extending the Graph
To add a new capability (e.g., a **security audit** agent):
1. Create a new sub‑agent with its own system prompt and relevant tools.
2. Write a wrapper function decorated with `@tool`.
3. Add the wrapper to the `tools` list when constructing `github_agent`.
4. (Optional) Extend `AgentName` enum.

---

## Related Files
| File | Purpose |
|------|---------|
| `src/agents/utils.py` | Helper functions for filtering the large GitHub toolkit into domain‑specific toolsets. |
| `app/agents.py` | Higher‑level entry point that may expose the coordinator to a FastAPI endpoint. |
| `src/workflow/main.py` | Example workflow that could orchestrate multiple graph runs. |

---

## License
This module is part of the **FinBot** repository and is licensed under the same terms as the rest of the project (see the repository root `LICENSE`).
