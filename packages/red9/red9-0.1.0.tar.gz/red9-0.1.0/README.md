# RED9

Enterprise Multi-Agent Coding System powered by Stabilize, IssueDB, and Ragit.

## Installation

```bash
pip install red9
```

## Quick Start

```bash
# Initialize RED9 in your project
red9 init

# Execute a coding task
red9 task "Add user authentication"

# Ask a question about the codebase
red9 ask "How does the auth system work?"

# Check status
red9 status
```

## Features

- **Multi-Agent Parallelism**: Coordinate multiple specialized agents working simultaneously
- **Persistent Memory**: Context and guidelines stored in IssueDB
- **Intelligent Code Understanding**: RAG-based codebase search via Ragit
- **Enterprise Workflow**: DAG-based execution with Stabilize

## Commands

| Command | Description |
|---------|-------------|
| `red9 init` | Initialize RED9 in current directory |
| `red9 task "request"` | Execute a coding task |
| `red9 ask "question"` | Ask about the codebase |
| `red9 status` | Show workflow status |
| `red9 todos` | List pending issues |
| `red9 memory add KEY VALUE` | Store agent guideline |
| `red9 lessons` | Show lessons learned |

## Architecture

RED9 follows the principle: **Agents ARE Stabilize Tasks**.

```
User Request → IssueDB Issue → Stabilize Workflow → Agent Tasks → Result
```

## License

Apache 2.0
