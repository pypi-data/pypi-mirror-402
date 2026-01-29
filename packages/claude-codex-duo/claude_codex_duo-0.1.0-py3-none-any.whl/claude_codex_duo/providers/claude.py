"""
Claude Code CLI Provider

Wrapper for interacting with the Claude Code CLI.
"""

import shutil
import subprocess
from pathlib import Path


class ClaudeProvider:
    """
    Provider for Claude Code CLI interactions.

    Wraps the `claude` CLI to execute prompts and get responses.
    """

    def __init__(
        self,
        workspace: str = None,
        model: str = "claude-sonnet-4-20250514",
    ):
        """
        Initialize Claude provider.

        Args:
            workspace: Working directory for Claude
            model: Claude model to use (default: claude-sonnet-4)
        """
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.model = model
        self._verify_cli()

    def _verify_cli(self) -> None:
        """Verify Claude CLI is available."""
        if not shutil.which("claude"):
            raise RuntimeError(
                "Claude Code CLI not found. Install from: "
                "https://docs.anthropic.com/claude-code"
            )

    def execute(
        self,
        prompt: str,
        timeout: int = 300,
        print_output: bool = False,
    ) -> str:
        """
        Execute a prompt with Claude Code CLI.

        Args:
            prompt: The prompt to send to Claude
            timeout: Maximum seconds to wait
            print_output: Whether to print output in real-time

        Returns:
            Claude's response text
        """
        cmd = [
            "claude",
            "-p", prompt,  # Print mode (non-interactive)
            "--model", self.model,
        ]

        try:
            if print_output:
                # Stream output
                result = subprocess.run(
                    cmd,
                    cwd=self.workspace,
                    capture_output=False,
                    text=True,
                    timeout=timeout,
                )
                return ""  # Output was printed
            else:
                result = subprocess.run(
                    cmd,
                    cwd=self.workspace,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
                return result.stdout

        except subprocess.TimeoutExpired as exc:
            raise TimeoutError(
                f"Claude command timed out after {timeout}s"
            ) from exc
        except FileNotFoundError as exc:
            raise RuntimeError("Claude CLI not found") from exc

    def code_review_prompt(
        self,
        code: str,
        task: str,
        feedback: str = None
    ) -> str:
        """
        Generate a prompt for Claude to process review feedback.

        Args:
            code: The current code
            task: The task description
            feedback: Previous review feedback to address

        Returns:
            Formatted prompt string
        """
        if feedback:
            return f"""You are working on: {task}

Your current code:
```
{code}
```

Codex has reviewed your code and provided this feedback:
{feedback}

Please address the feedback and provide updated code."""
        else:
            return f"""You are working on: {task}

Please write the code to accomplish this task. Be thorough and follow best practices."""

    @staticmethod
    def is_available() -> bool:
        """Check if Claude CLI is available."""
        return shutil.which("claude") is not None
