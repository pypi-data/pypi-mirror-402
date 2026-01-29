"""
Codex CLI Provider

Wrapper for interacting with the OpenAI Codex CLI.
"""

import shutil
import subprocess
from pathlib import Path


class CodexProvider:
    """
    Provider for Codex CLI interactions.

    Wraps the `codex` CLI to execute prompts and get responses.
    """

    def __init__(
        self,
        workspace: str = None,
        model: str = "o3",
        reasoning_effort: str = "medium",
    ):
        """
        Initialize Codex provider.

        Args:
            workspace: Working directory for Codex
            model: Codex model to use (default: o3)
            reasoning_effort: Reasoning effort level (low/medium/high)
        """
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.model = model
        self.reasoning_effort = reasoning_effort
        self._verify_cli()

    def _verify_cli(self) -> None:
        """Verify Codex CLI is available."""
        if not shutil.which("codex"):
            raise RuntimeError(
                "Codex CLI not found. Install from: "
                "https://github.com/openai/codex"
            )

    def execute(
        self,
        prompt: str,
        timeout: int = 300,
        sandbox: str = "read-only",
    ) -> str:
        """
        Execute a prompt with Codex CLI.

        Args:
            prompt: The prompt to send to Codex
            timeout: Maximum seconds to wait
            sandbox: Sandbox mode (read-only recommended for review)

        Returns:
            Codex's response text
        """
        cmd = [
            "codex",
            "-q",  # Quiet mode
            "-m", self.model,
            "-c", f'model_reasoning_effort="{self.reasoning_effort}"',
        ]

        if sandbox:
            cmd.extend(["--sandbox", sandbox])

        cmd.append(prompt)

        try:
            result = subprocess.run(
                cmd,
                cwd=self.workspace,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return result.stdout or result.stderr

        except subprocess.TimeoutExpired as exc:
            raise TimeoutError(
                f"Codex command timed out after {timeout}s"
            ) from exc
        except FileNotFoundError as exc:
            raise RuntimeError("Codex CLI not found") from exc

    def review_prompt(
        self,
        code: str,
        task: str,
    ) -> str:
        """
        Generate a code review prompt for Codex.

        Args:
            code: The code to review
            task: The task description

        Returns:
            Formatted review prompt
        """
        return f"""You are reviewing Claude Code's work in a peer programming session.

## Task
{task}

## Claude's Code
```
{code}
```

## Your Review
Please review this code and provide:

1. **Verdict**: APPROVED or NEEDS_CHANGES
2. **Summary**: Brief overall assessment
3. **Issues**: Specific problems found (if any)
4. **Suggestions**: Concrete improvements

Focus on:
- Correctness and bugs
- Security considerations
- Best practices
- Edge cases
- Performance

Be constructive and specific. If the code is good, say APPROVED."""

    def extract_verdict(self, response: str) -> str:
        """
        Extract verdict from Codex's review response.

        Args:
            response: Codex's full response text

        Returns:
            "APPROVED" or "NEEDS_CHANGES"
        """
        response_lower = response.lower()

        approved_indicators = [
            "verdict: approved",
            "**verdict**: approved",
            "verdict:** approved",
            "lgtm",
            "looks good to me",
            "approved",
            "ready to merge",
        ]

        for indicator in approved_indicators:
            if indicator in response_lower:
                return "APPROVED"

        return "NEEDS_CHANGES"

    @staticmethod
    def is_available() -> bool:
        """Check if Codex CLI is available."""
        return shutil.which("codex") is not None
