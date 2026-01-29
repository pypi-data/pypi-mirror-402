"""Shell execution tools for CC Python."""

import asyncio
import os
import shlex
import subprocess
import sys
from pathlib import Path

from .base import Tool, ToolParameter, ToolResult


class BashTool(Tool):
    """Tool for executing shell commands."""

    name = "bash"
    description = "Execute a shell command and return the output. Use this for running system commands, scripts, or any terminal operations."
    category = "execute"
    requires_approval = True

    parameters = [
        ToolParameter(
            name="command",
            type="string",
            description="The shell command to execute",
        ),
        ToolParameter(
            name="working_directory",
            type="string",
            description="The working directory to run the command in",
            required=False,
            default=None,
        ),
        ToolParameter(
            name="timeout",
            type="integer",
            description="Timeout in seconds (default: 30)",
            required=False,
            default=30,
        ),
    ]

    async def execute(
        self,
        command: str,
        working_directory: str | None = None,
        timeout: int = 30,
    ) -> ToolResult:
        """Execute a shell command."""
        try:
            cwd = Path(working_directory).resolve() if working_directory else Path.cwd()

            if not cwd.exists():
                return ToolResult(
                    output=f"Working directory not found: {working_directory}",
                    is_error=True,
                )

            # Determine shell based on platform
            if sys.platform == "win32":
                # Use PowerShell on Windows
                shell_cmd = ["powershell", "-Command", command]
            else:
                # Use bash on Unix-like systems
                shell_cmd = ["bash", "-c", command]

            # Run the command
            process = await asyncio.create_subprocess_exec(
                *shell_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(cwd),
                env={**os.environ},
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolResult(
                    output=f"Command timed out after {timeout} seconds",
                    is_error=True,
                )

            # Decode output
            stdout_str = stdout.decode("utf-8", errors="replace").strip()
            stderr_str = stderr.decode("utf-8", errors="replace").strip()

            # Build output
            output_parts = []
            if stdout_str:
                output_parts.append(stdout_str)
            if stderr_str:
                output_parts.append(f"[stderr]\n{stderr_str}")

            output = "\n".join(output_parts) if output_parts else "(no output)"

            # Check exit code
            is_error = process.returncode != 0

            if is_error:
                output = f"Exit code: {process.returncode}\n{output}"

            return ToolResult(
                output=output,
                is_error=is_error,
                data={
                    "exit_code": process.returncode,
                    "cwd": str(cwd),
                },
            )

        except FileNotFoundError:
            return ToolResult(
                output="Shell not found. Please ensure bash/powershell is installed.",
                is_error=True,
            )
        except Exception as e:
            return ToolResult(
                output=f"Error executing command: {e}",
                is_error=True,
            )


class PythonTool(Tool):
    """Tool for executing Python code."""

    name = "python"
    description = "Execute Python code and return the output."
    category = "execute"
    requires_approval = True

    parameters = [
        ToolParameter(
            name="code",
            type="string",
            description="The Python code to execute",
        ),
        ToolParameter(
            name="timeout",
            type="integer",
            description="Timeout in seconds (default: 30)",
            required=False,
            default=30,
        ),
    ]

    async def execute(
        self,
        code: str,
        timeout: int = 30,
    ) -> ToolResult:
        """Execute Python code."""
        try:
            # Create a temporary script
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".py",
                delete=False,
                encoding="utf-8",
            ) as f:
                f.write(code)
                script_path = f.name

            try:
                process = await asyncio.create_subprocess_exec(
                    sys.executable,
                    script_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=timeout,
                    )
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
                    return ToolResult(
                        output=f"Execution timed out after {timeout} seconds",
                        is_error=True,
                    )

                stdout_str = stdout.decode("utf-8", errors="replace").strip()
                stderr_str = stderr.decode("utf-8", errors="replace").strip()

                output_parts = []
                if stdout_str:
                    output_parts.append(stdout_str)
                if stderr_str:
                    output_parts.append(f"[stderr]\n{stderr_str}")

                output = "\n".join(output_parts) if output_parts else "(no output)"
                is_error = process.returncode != 0

                return ToolResult(
                    output=output,
                    is_error=is_error,
                    data={"exit_code": process.returncode},
                )

            finally:
                # Clean up temp file
                os.unlink(script_path)

        except Exception as e:
            return ToolResult(
                output=f"Error executing Python code: {e}",
                is_error=True,
            )
