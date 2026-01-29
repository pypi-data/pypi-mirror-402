# Claude-Codex Duo

**Claude codes. Codex reviews. Better code together.**

A simple library for duo peer programming between [Claude Code](https://docs.anthropic.com/claude-code) and [Codex](https://github.com/openai/codex). Two AI coding assistants working together to write better code.

## Why Use Both?

| Claude | Codex |
|--------|-------|
| Superior tool calling & code generation | Excellent at catching bugs & edge cases |
| Great at understanding context | Strong code review capabilities |
| Creative problem solving | Thorough analysis |

Together, they create a peer programming experience that's greater than either alone.

## Quick Start

### Prerequisites

- Python 3.10+
- [Claude Code CLI](https://docs.anthropic.com/claude-code) installed
- [Codex CLI](https://github.com/openai/codex) installed

### Installation

```bash
pip install claude-codex-duo
```

Or install from source:

```bash
git clone https://github.com/Sigma5C-Corp/claude-codex-duo
cd claude-codex-duo
pip install -e .
```

### Basic Usage

```python
from claude_codex_duo import create_session, Verdict

# Create a peer programming session
session = create_session("auth_feature", "Implement user authentication")

# Claude submits code for review
session.submit_code("""
def authenticate(username: str, password: str) -> bool:
    user = get_user(username)
    if user and verify_password(password, user.password_hash):
        return True
    return False
""")

# Wait for Codex's review
exchange = session.wait_for_review(timeout=120)

if exchange and exchange.verdict == Verdict.APPROVED:
    print("Consensus reached! Code approved.")
else:
    print(f"Feedback: {exchange.codex_review}")
```

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│    ┌──────────┐                           ┌──────────┐         │
│    │  Claude  │  ───── submits code ────► │  Codex   │         │
│    │  (coder) │                           │(reviewer)│         │
│    └──────────┘  ◄──── sends review ───── └──────────┘         │
│         │                                       │               │
│         │          ┌─────────────┐              │               │
│         └─────────►│   Session   │◄─────────────┘               │
│                    │   (files)   │                              │
│                    └─────────────┘                              │
│                                                                 │
│    Round 1: Claude writes → Codex reviews → Feedback           │
│    Round 2: Claude fixes  → Codex reviews → Approved!          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

1. **Claude writes code** - Implements the task
2. **Codex reviews** - Checks for bugs, edge cases, best practices
3. **Iterate** - Claude addresses feedback, Codex re-reviews
4. **Consensus** - When Codex approves, the code is ready

All communication happens via file-based messaging (no database needed).

## API Reference

### `create_session(session_id, task, workspace=None, max_rounds=10)`

Create a new peer programming session.

```python
session = create_session(
    "my_session",           # Unique session ID
    "Build a REST API",     # Task description
    workspace="/path/to/project",
    max_rounds=5
)
```

### `DuoSession.submit_code(content, files_modified=None)`

Submit code from Claude for Codex review.

```python
session.submit_code(
    "def hello(): return 'world'",
    files_modified=["src/utils.py"]
)
```

### `DuoSession.wait_for_review(timeout=300)`

Wait for Codex's review response.

```python
exchange = session.wait_for_review(timeout=120)
if exchange:
    print(f"Verdict: {exchange.verdict}")
    print(f"Feedback: {exchange.codex_review}")
```

### Session Status

```python
session.status        # SessionStatus.ACTIVE, REVIEWING, CONSENSUS, etc.
session.has_consensus # True if approved
session.is_complete   # True if done (approved or max rounds)
session.current_round # Current review round number
```

## Configuration

Set the data directory via environment variable:

```bash
export CLAUDE_CODEX_DUO_DATA=~/.my-duo-data
```

Default: `~/.claude-codex-duo/`

Session files are stored in:
```
~/.claude-codex-duo/
└── sessions/
    └── my_session/
        ├── session.json       # Session state
        ├── claude_inbox.json  # Messages for Claude
        ├── codex_inbox.json   # Messages for Codex
        └── conversation.jsonl # Full history
```

## Advanced Usage

### Manual Provider Control

```python
from claude_codex_duo import ClaudeProvider, CodexProvider

# Direct Claude interaction
claude = ClaudeProvider(workspace="/my/project")
response = claude.execute("Write a function to validate emails")

# Direct Codex interaction
codex = CodexProvider(model="o3", reasoning_effort="high")
review = codex.execute(codex.review_prompt(code, task))
verdict = codex.extract_verdict(review)
```

### Load Existing Session

```python
from claude_codex_duo import load_session

session = load_session("my_session")
print(f"Round {session.current_round} of {session.max_rounds}")
```

## Requirements

- Python 3.10+
- Unix-like OS (uses `fcntl` for file locking)
- Claude Code CLI
- Codex CLI

## License

MIT License - see [LICENSE](LICENSE)

## Contributing

Contributions welcome! Please read our contributing guidelines.

## About

Built by [Sigma5C](https://sigma5c.com) - Leaders in multi-agent AI systems.

We believe AI tools work better together. Claude's superior reasoning and tool-calling combined with Codex's bug-catching creates a peer programming experience that's greater than either alone.

---

*"Two AIs are better than one."*
