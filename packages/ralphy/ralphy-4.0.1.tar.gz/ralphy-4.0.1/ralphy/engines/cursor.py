"""Cursor agent AI engine implementation."""

import json
import subprocess
import sys

from ralphy.engines.base import AIEngine, AIResult
from ralphy.utils import command_exists


class CursorEngine(AIEngine):
    """Cursor agent AI engine."""

    name = "cursor"
    cli_command = "agent"

    def check_available(self) -> bool:
        """Check if Cursor agent CLI is available."""
        return command_exists(self.cli_command)

    def get_install_instructions(self) -> str:
        """Return instructions for installing Cursor agent CLI."""
        return "Make sure Cursor is installed and 'agent' is in your PATH."

    def run(self, prompt: str, verbose: bool = False) -> AIResult:
        """Run Cursor agent with the given prompt."""
        cmd = [
            self.cli_command,
            "--print",
            "--force",
            "--output-format",
            "stream-json",
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
            result_data = None
            assistant_data = None

            for line in process.stdout:
                output_lines.append(line)
                sys.stdout.write(line)
                sys.stdout.flush()

                line = line.strip()
                if '"type":"result"' in line:
                    try:
                        result_data = json.loads(line)
                    except json.JSONDecodeError:
                        pass
                elif '"type":"assistant"' in line:
                    try:
                        assistant_data = json.loads(line)
                    except json.JSONDecodeError:
                        pass

            process.wait()

            # Check for errors
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
            response = "Task completed"
            duration_ms = None

            if result_data:
                response = result_data.get("result", "Task completed")
                duration_ms = result_data.get("duration_ms")

            # Fallback to assistant message if no result
            if response == "Task completed" and assistant_data:
                msg = assistant_data.get("message", {})
                content = msg.get("content", [])
                if content and isinstance(content, list) and len(content) > 0:
                    if isinstance(content[0], dict):
                        response = content[0].get("text", response)
                    else:
                        response = str(content)

            # Cursor doesn't provide token counts
            return AIResult(
                response=response,
                input_tokens=0,
                output_tokens=0,
                duration_ms=duration_ms,
            )

        except FileNotFoundError:
            return AIResult(
                response="",
                error=f"Cursor agent CLI not found. {self.get_install_instructions()}",
            )
        except Exception as e:
            return AIResult(response="", error=str(e))

    def run_simple(self, prompt: str) -> AIResult:
        """Run Cursor agent in simple mode for brownfield tasks."""
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
                error=f"Cursor agent CLI not found. {self.get_install_instructions()}",
            )
        except Exception as e:
            return AIResult(response="", error=str(e))
