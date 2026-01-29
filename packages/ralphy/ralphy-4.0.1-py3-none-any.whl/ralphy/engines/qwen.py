"""Qwen-Code AI engine implementation."""

import json
import subprocess
import sys

from ralphy.engines.base import AIEngine, AIResult
from ralphy.utils import command_exists


class QwenEngine(AIEngine):
    """Qwen-Code AI engine."""

    name = "qwen"
    cli_command = "qwen"

    def check_available(self) -> bool:
        """Check if Qwen-Code CLI is available."""
        return command_exists(self.cli_command)

    def get_install_instructions(self) -> str:
        """Return instructions for installing Qwen-Code CLI."""
        return "Make sure 'qwen' is in your PATH."

    def run(self, prompt: str, verbose: bool = False) -> AIResult:
        """Run Qwen-Code with the given prompt."""
        cmd = [
            self.cli_command,
            "--output-format",
            "stream-json",
            "--approval-mode",
            "yolo",
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
            result_data = None

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
            input_tokens = 0
            output_tokens = 0

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

        except FileNotFoundError:
            return AIResult(
                response="",
                error=f"Qwen-Code CLI not found. {self.get_install_instructions()}",
            )
        except Exception as e:
            return AIResult(response="", error=str(e))

    def run_simple(self, prompt: str) -> AIResult:
        """Run Qwen-Code in simple mode for brownfield tasks."""
        return self.run(prompt, verbose=False)
