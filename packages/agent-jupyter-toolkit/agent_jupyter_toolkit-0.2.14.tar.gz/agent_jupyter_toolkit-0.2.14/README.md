# Agent Jupyter Toolkit

A Python toolkit for building agent tools that interact with Jupyter kernels and the Jupyter protocol. This package provides high-level wrappers and abstractions around [jupyter_client](https://pypi.org/project/jupyter-client/), making it easy to manage kernels, execute code, and build agent-driven workflows for automation, orchestration, and integration with Model Context Protocol (MCP) servers.

## Features
- Async-first kernel and notebook orchestration with multiple transport options:
  - Local file transport for filesystem-backed notebooks
  - Contents API transport for Jupyter Server-managed notebooks
  - Collaboration transport for real-time, multi-client editing
- Session, variables, and notebook editing utilities geared for agent workflows
- In-memory notebook buffer for staged edits with explicit commit
- Local notebook autosave with optional debounced writes
- Extensible hooks and integration points for custom workflows

## Use Cases
- Build agent tools that execute code in Jupyter kernels
- Integrate Jupyter kernel execution into MCP servers or other orchestration systems
- Automate notebook and code execution for data science, ML, and automation pipelines

## Installation

You can install the package and its dependencies from PyPI or set up a development environment using pip or [uv](https://github.com/astral-sh/uv).

### Install from PyPI

```sh
# Using pip
pip install agent-jupyter-toolkit

# Or using uv
uv pip install agent-jupyter-toolkit
```

### Environment Setup

### Development Environment (contributors)

#### Option 1: Using pip

```sh
# Create a virtual environment (Python 3.10+ recommended)
python3 -m venv .venv

# Activate the virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install the package in editable mode with dev dependencies
pip install -e '.[dev]'
```

#### Option 2: Using uv

```sh
# Create and activate a virtual environment
uv venv .venv
source .venv/bin/activate

# Install the package in editable mode with dev dependencies
uv pip install '.[dev]'
```

## Quickstart

Local kernel execution does not require a Jupyter Server. The library starts a
local kernel process for you (via `jupyter_client`) and connects over ZMQ. The
snippet below can be saved as a script and run with your preferred Python
runner.

Example (same as `quickstarts/01_local_kernel.py`):

```python
import asyncio

from agent_jupyter_toolkit.kernel import SessionConfig, create_session


async def main() -> None:
    session = create_session(SessionConfig(mode="local", kernel_name="python3"))
    async with session:
        result = await session.execute(
            "import os\n"
            "from platform import node\n"
            "user = os.environ.get('USER', 'friend')\n"
            "print(f'Hello {user} from {node()}')\n"
        )

    print("status:", result.status)
    print("execution_count:", result.execution_count)
    print("stdout:", result.stdout.strip())
    print("outputs:", result.outputs)


if __name__ == "__main__":
    asyncio.run(main())
```

For server-backed and notebook scenarios, see `quickstarts/README.md` and the
other scripts under `quickstarts/`.

## Reference: jupyter_client

[jupyter_client](https://pypi.org/project/jupyter-client/) is the reference implementation of the Jupyter protocol, providing client and kernel management APIs. This toolkit builds on top of jupyter_client to provide a more ergonomic, agent-oriented interface for automation and integration.

## Release Process

See `docs/RELEASE.md` for the full release checklist.

---
 
Contributions and feedback are welcome!