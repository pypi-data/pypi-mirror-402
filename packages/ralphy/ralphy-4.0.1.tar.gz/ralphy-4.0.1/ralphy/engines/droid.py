"""Factory Droid AI engine implementation."""

import json
import subprocess
import sys

from ralphy.engines.base import AIEngine, AIResult
from ralphy.utils import command_exists


class DroidEngine(AIEngine):
    """Factory Droid AI engine."""

    name = "droid"
    cli_command = "droid"

    def check_available(self) -> bool:
        """Check if Factory Droid CLI is available."""
        return command_exists(self.cli_command)

    def get_install_instructions(self) -> str:
        """Return instructions for installing Factory Droid CLI."""
        return "Install from: https://docs.factory.ai/cli/getting-started/quickstart"

    def run(self, prompt: str, verbose: bool = False) -> AIResult:
        """Run Factory Droid with the given prompt."""
        cmd = [
            self.cli_command,
            "exec",
            "--output-format",
            "stream-json",
            "--auto",
            "medium",
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
            completion_data = None

            for line in process.stdout:
                output_lines.append(line)
                sys.stdout.write(line)
                sys.stdout.flush()

                line = line.strip()
                if '"type":"completion"' in line:
                    try:
                        completion_data = json.loads(line)
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

            if completion_data:
                response = completion_data.get("finalText", "Task completed")
                duration_ms = completion_data.get("durationMs")

            # Droid doesn't expose token counts in exec mode
            return AIResult(
                response=response,
                input_tokens=0,
                output_tokens=0,
                duration_ms=duration_ms,
            )

        except FileNotFoundError:
            return AIResult(
                response="",
                error=f"Factory Droid CLI not found. {self.get_install_instructions()}",
            )
        except Exception as e:
            return AIResult(response="", error=str(e))

    def run_simple(self, prompt: str) -> AIResult:
        """Run Factory Droid in simple mode for brownfield tasks."""
        return self.run(prompt, verbose=False)
