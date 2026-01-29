"""Codex CLI AI engine implementation."""

import os
import subprocess
import sys
import tempfile

from ralphy.engines.base import AIEngine, AIResult
from ralphy.utils import command_exists


class CodexEngine(AIEngine):
    """Codex CLI AI engine."""

    name = "codex"
    cli_command = "codex"

    def check_available(self) -> bool:
        """Check if Codex CLI is available."""
        return command_exists(self.cli_command)

    def get_install_instructions(self) -> str:
        """Return instructions for installing Codex CLI."""
        return "Make sure 'codex' is in your PATH."

    def run(self, prompt: str, verbose: bool = False) -> AIResult:
        """Run Codex with the given prompt."""
        # Create temp file for last message output
        last_message_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        )
        last_message_file.close()

        cmd = [
            self.cli_command,
            "exec",
            "--full-auto",
            "--json",
            "--output-last-message",
            last_message_file.name,
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

            # Check for errors
            full_output = "".join(output_lines)
            if '"type":"error"' in full_output:
                for line in output_lines:
                    if '"type":"error"' in line:
                        try:
                            import json

                            error_data = json.loads(line.strip())
                            error_msg = error_data.get("error", {}).get(
                                "message", error_data.get("message", "Unknown error")
                            )
                            return AIResult(response="", error=error_msg)
                        except Exception:
                            pass
                return AIResult(response="", error="Unknown error occurred")

            # Read last message from temp file
            response = ""
            if os.path.exists(last_message_file.name):
                with open(last_message_file.name) as f:
                    response = f.read()
                # Clean up the generic completion prefix if present
                if response.startswith("Task completed successfully."):
                    response = response.replace(
                        "Task completed successfully.", "", 1
                    ).strip()
                os.unlink(last_message_file.name)

            if not response:
                response = "Task completed"

            # Codex doesn't expose token counts
            return AIResult(
                response=response,
                input_tokens=0,
                output_tokens=0,
            )

        except FileNotFoundError:
            return AIResult(
                response="",
                error=f"Codex CLI not found. {self.get_install_instructions()}",
            )
        except Exception as e:
            # Clean up temp file on error
            if os.path.exists(last_message_file.name):
                os.unlink(last_message_file.name)
            return AIResult(response="", error=str(e))

    def run_simple(self, prompt: str) -> AIResult:
        """Run Codex in simple mode for brownfield tasks."""
        return self.run(prompt, verbose=False)
