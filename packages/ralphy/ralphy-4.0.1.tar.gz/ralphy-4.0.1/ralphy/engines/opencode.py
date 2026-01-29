"""OpenCode AI engine implementation."""

import json
import os
import subprocess
import sys

from ralphy.engines.base import AIEngine, AIResult
from ralphy.utils import command_exists


class OpenCodeEngine(AIEngine):
    """OpenCode AI engine."""

    name = "opencode"
    cli_command = "opencode"

    def check_available(self) -> bool:
        """Check if OpenCode CLI is available."""
        return command_exists(self.cli_command)

    def get_install_instructions(self) -> str:
        """Return instructions for installing OpenCode CLI."""
        return "Install from: https://opencode.ai/docs/"

    def run(self, prompt: str, verbose: bool = False) -> AIResult:
        """Run OpenCode with the given prompt."""
        cmd = [self.cli_command, "run", "--format", "json", prompt]

        # Set permission environment variable
        env = os.environ.copy()
        env["OPENCODE_PERMISSION"] = '{"*":"allow"}'

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
            )

            output_lines = []
            step_finish_data = None

            for line in process.stdout:
                output_lines.append(line)
                sys.stdout.write(line)
                sys.stdout.flush()

                line = line.strip()
                if '"type":"step_finish"' in line:
                    try:
                        step_finish_data = json.loads(line)
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
            input_tokens = 0
            output_tokens = 0
            actual_cost = None

            if step_finish_data:
                part = step_finish_data.get("part", {})
                tokens = part.get("tokens", {})
                input_tokens = tokens.get("input", 0)
                output_tokens = tokens.get("output", 0)
                actual_cost = part.get("cost", None)

            # Get text response from text events
            response = ""
            for line in output_lines:
                if '"type":"text"' in line:
                    try:
                        text_data = json.loads(line.strip())
                        response += text_data.get("part", {}).get("text", "")
                    except json.JSONDecodeError:
                        pass

            if not response:
                response = "Task completed"

            return AIResult(
                response=response,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                actual_cost=actual_cost,
            )

        except FileNotFoundError:
            return AIResult(
                response="",
                error=f"OpenCode CLI not found. {self.get_install_instructions()}",
            )
        except Exception as e:
            return AIResult(response="", error=str(e))

    def run_simple(self, prompt: str) -> AIResult:
        """Run OpenCode in simple mode for brownfield tasks."""
        return self.run(prompt, verbose=False)
