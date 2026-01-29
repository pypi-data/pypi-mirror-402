"""Claude Code AI engine implementation."""

import json
import subprocess
import sys
from typing import Optional

from ralphy.engines.base import AIEngine, AIResult
from ralphy.utils import command_exists


class ClaudeEngine(AIEngine):
    """Claude Code AI engine."""

    name = "claude"
    cli_command = "claude"

    def check_available(self) -> bool:
        """Check if Claude Code CLI is available."""
        return command_exists(self.cli_command)

    def get_install_instructions(self) -> str:
        """Return instructions for installing Claude Code CLI."""
        return "Install from: https://github.com/anthropics/claude-code"

    def run(self, prompt: str, verbose: bool = False) -> AIResult:
        """Run Claude Code with the given prompt."""
        cmd = [
            self.cli_command,
            "--dangerously-skip-permissions",
            "--output-format",
            "stream-json",
            "-p",
            prompt,
        ]

        if verbose:
            cmd.insert(1, "--verbose")

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )

            output_lines = []
            result_data = None

            # Stream output and collect for parsing
            for line in process.stdout:
                output_lines.append(line)
                # Also print to show progress (the shell version does this via tee)
                sys.stdout.write(line)
                sys.stdout.flush()

                # Try to parse result line
                line = line.strip()
                if '"type":"result"' in line:
                    try:
                        result_data = json.loads(line)
                    except json.JSONDecodeError:
                        pass

            process.wait()

            # Check for errors in output
            full_output = "".join(output_lines)
            if '"type":"error"' in full_output:
                for line in output_lines:
                    if '"type":"error"' in line:
                        try:
                            error_data = json.loads(line.strip())
                            error_msg = error_data.get("error", {}).get(
                                "message", error_data.get("message", "Unknown error")
                            )
                            return AIResult(response="", error=error_msg)
                        except json.JSONDecodeError:
                            pass
                return AIResult(response="", error="Unknown error occurred")

            # Parse result
            if result_data:
                response = result_data.get("result", "Task completed")
                usage = result_data.get("usage", {})
                input_tokens = usage.get("input_tokens", 0)
                output_tokens = usage.get("output_tokens", 0)

                return AIResult(
                    response=response,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )

            # No result found
            if process.returncode == 0:
                return AIResult(response="Task completed")
            else:
                return AIResult(response="", error="Command failed with no output")

        except FileNotFoundError:
            return AIResult(
                response="",
                error=f"Claude Code CLI not found. {self.get_install_instructions()}",
            )
        except Exception as e:
            return AIResult(response="", error=str(e))

    def run_simple(self, prompt: str) -> AIResult:
        """Run Claude Code in simple mode (for brownfield tasks) with live output."""
        cmd = [
            self.cli_command,
            "--dangerously-skip-permissions",
            "-p",
            prompt,
        ]

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )

            output_lines = []

            # Stream output in real-time
            for line in process.stdout:
                output_lines.append(line)
                sys.stdout.write(line)
                sys.stdout.flush()

            process.wait()

            return AIResult(
                response="".join(output_lines),
                error=None if process.returncode == 0 else "Command failed",
            )

        except FileNotFoundError:
            return AIResult(
                response="",
                error=f"Claude Code CLI not found. {self.get_install_instructions()}",
            )
        except Exception as e:
            return AIResult(response="", error=str(e))
