"""Git operation tools for CC Python."""

import asyncio
from pathlib import Path

from .base import Tool, ToolParameter, ToolResult


class GitStatusTool(Tool):
    """Tool for checking git status."""

    name = "git_status"
    description = "Show the working tree status. Lists staged, unstaged, and untracked files."
    category = "read"
    requires_approval = False

    parameters = [
        ToolParameter(
            name="path",
            type="string",
            description="The path to the git repository (defaults to current directory)",
            required=False,
            default=".",
        ),
    ]

    async def execute(self, path: str = ".") -> ToolResult:
        """Get git status."""
        try:
            repo_path = Path(path).resolve()

            process = await asyncio.create_subprocess_exec(
                "git",
                "status",
                "--porcelain=v2",
                "--branch",
                cwd=str(repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                return ToolResult(
                    output=f"Git error: {stderr.decode('utf-8', errors='replace')}",
                    is_error=True,
                )

            # Also get human-readable status
            process2 = await asyncio.create_subprocess_exec(
                "git",
                "status",
                cwd=str(repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout2, _ = await process2.communicate()

            return ToolResult(
                output=stdout2.decode("utf-8", errors="replace"),
                data={"porcelain": stdout.decode("utf-8", errors="replace")},
            )

        except FileNotFoundError:
            return ToolResult(
                output="Git is not installed or not in PATH",
                is_error=True,
            )
        except Exception as e:
            return ToolResult(
                output=f"Error getting git status: {e}",
                is_error=True,
            )


class GitDiffTool(Tool):
    """Tool for showing git diff."""

    name = "git_diff"
    description = "Show changes between commits, commit and working tree, etc."
    category = "read"
    requires_approval = False

    parameters = [
        ToolParameter(
            name="path",
            type="string",
            description="The path to the git repository",
            required=False,
            default=".",
        ),
        ToolParameter(
            name="staged",
            type="boolean",
            description="Show staged changes (--staged)",
            required=False,
            default=False,
        ),
        ToolParameter(
            name="file",
            type="string",
            description="Show diff for a specific file",
            required=False,
            default=None,
        ),
    ]

    async def execute(
        self,
        path: str = ".",
        staged: bool = False,
        file: str | None = None,
    ) -> ToolResult:
        """Get git diff."""
        try:
            repo_path = Path(path).resolve()

            cmd = ["git", "diff"]
            if staged:
                cmd.append("--staged")
            if file:
                cmd.extend(["--", file])

            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                return ToolResult(
                    output=f"Git error: {stderr.decode('utf-8', errors='replace')}",
                    is_error=True,
                )

            output = stdout.decode("utf-8", errors="replace")
            if not output:
                output = "No changes"

            return ToolResult(output=output)

        except FileNotFoundError:
            return ToolResult(
                output="Git is not installed or not in PATH",
                is_error=True,
            )
        except Exception as e:
            return ToolResult(
                output=f"Error getting git diff: {e}",
                is_error=True,
            )


class GitLogTool(Tool):
    """Tool for showing git log."""

    name = "git_log"
    description = "Show commit logs."
    category = "read"
    requires_approval = False

    parameters = [
        ToolParameter(
            name="path",
            type="string",
            description="The path to the git repository",
            required=False,
            default=".",
        ),
        ToolParameter(
            name="count",
            type="integer",
            description="Number of commits to show",
            required=False,
            default=10,
        ),
        ToolParameter(
            name="oneline",
            type="boolean",
            description="Show each commit on a single line",
            required=False,
            default=True,
        ),
    ]

    async def execute(
        self,
        path: str = ".",
        count: int = 10,
        oneline: bool = True,
    ) -> ToolResult:
        """Get git log."""
        try:
            repo_path = Path(path).resolve()

            cmd = ["git", "log", f"-{count}"]
            if oneline:
                cmd.append("--oneline")
            else:
                cmd.append("--format=medium")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                return ToolResult(
                    output=f"Git error: {stderr.decode('utf-8', errors='replace')}",
                    is_error=True,
                )

            return ToolResult(
                output=stdout.decode("utf-8", errors="replace"),
            )

        except FileNotFoundError:
            return ToolResult(
                output="Git is not installed or not in PATH",
                is_error=True,
            )
        except Exception as e:
            return ToolResult(
                output=f"Error getting git log: {e}",
                is_error=True,
            )


class GitCommitTool(Tool):
    """Tool for creating git commits."""

    name = "git_commit"
    description = "Record changes to the repository. Stages all changes and creates a commit."
    category = "write"
    requires_approval = True

    parameters = [
        ToolParameter(
            name="message",
            type="string",
            description="The commit message",
        ),
        ToolParameter(
            name="path",
            type="string",
            description="The path to the git repository",
            required=False,
            default=".",
        ),
        ToolParameter(
            name="add_all",
            type="boolean",
            description="Stage all changes before committing",
            required=False,
            default=True,
        ),
    ]

    async def execute(
        self,
        message: str,
        path: str = ".",
        add_all: bool = True,
    ) -> ToolResult:
        """Create a git commit."""
        try:
            repo_path = Path(path).resolve()

            # Stage changes if requested
            if add_all:
                add_process = await asyncio.create_subprocess_exec(
                    "git",
                    "add",
                    "-A",
                    cwd=str(repo_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                _, stderr = await add_process.communicate()

                if add_process.returncode != 0:
                    return ToolResult(
                        output=f"Git add error: {stderr.decode('utf-8', errors='replace')}",
                        is_error=True,
                    )

            # Create commit
            process = await asyncio.create_subprocess_exec(
                "git",
                "commit",
                "-m",
                message,
                cwd=str(repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode("utf-8", errors="replace")
                if "nothing to commit" in error_msg.lower() or "nothing to commit" in stdout.decode("utf-8", errors="replace").lower():
                    return ToolResult(
                        output="Nothing to commit, working tree clean",
                    )
                return ToolResult(
                    output=f"Git commit error: {error_msg}",
                    is_error=True,
                )

            return ToolResult(
                output=stdout.decode("utf-8", errors="replace"),
            )

        except FileNotFoundError:
            return ToolResult(
                output="Git is not installed or not in PATH",
                is_error=True,
            )
        except Exception as e:
            return ToolResult(
                output=f"Error creating git commit: {e}",
                is_error=True,
            )


class GitBranchTool(Tool):
    """Tool for listing and managing git branches."""

    name = "git_branch"
    description = "List, create, or delete branches."
    category = "read"
    requires_approval = False

    parameters = [
        ToolParameter(
            name="path",
            type="string",
            description="The path to the git repository",
            required=False,
            default=".",
        ),
        ToolParameter(
            name="create",
            type="string",
            description="Name of new branch to create",
            required=False,
            default=None,
        ),
        ToolParameter(
            name="all",
            type="boolean",
            description="List both remote and local branches",
            required=False,
            default=False,
        ),
    ]

    async def execute(
        self,
        path: str = ".",
        create: str | None = None,
        all: bool = False,
    ) -> ToolResult:
        """List or create git branches."""
        try:
            repo_path = Path(path).resolve()

            if create:
                # Create new branch
                cmd = ["git", "branch", create]
            else:
                # List branches
                cmd = ["git", "branch"]
                if all:
                    cmd.append("-a")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                return ToolResult(
                    output=f"Git error: {stderr.decode('utf-8', errors='replace')}",
                    is_error=True,
                )

            output = stdout.decode("utf-8", errors="replace")
            if create:
                output = f"Created branch: {create}"

            return ToolResult(output=output)

        except FileNotFoundError:
            return ToolResult(
                output="Git is not installed or not in PATH",
                is_error=True,
            )
        except Exception as e:
            return ToolResult(
                output=f"Error with git branch: {e}",
                is_error=True,
            )


class GitCheckoutTool(Tool):
    """Tool for switching branches or restoring files."""

    name = "git_checkout"
    description = "Switch branches or restore working tree files."
    category = "write"
    requires_approval = True

    parameters = [
        ToolParameter(
            name="target",
            type="string",
            description="Branch name or commit to checkout",
        ),
        ToolParameter(
            name="path",
            type="string",
            description="The path to the git repository",
            required=False,
            default=".",
        ),
        ToolParameter(
            name="create",
            type="boolean",
            description="Create a new branch (-b flag)",
            required=False,
            default=False,
        ),
    ]

    async def execute(
        self,
        target: str,
        path: str = ".",
        create: bool = False,
    ) -> ToolResult:
        """Checkout a branch or commit."""
        try:
            repo_path = Path(path).resolve()

            cmd = ["git", "checkout"]
            if create:
                cmd.append("-b")
            cmd.append(target)

            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                return ToolResult(
                    output=f"Git error: {stderr.decode('utf-8', errors='replace')}",
                    is_error=True,
                )

            # Git checkout outputs to stderr on success
            output = stderr.decode("utf-8", errors="replace") or stdout.decode(
                "utf-8", errors="replace"
            )
            return ToolResult(output=output)

        except FileNotFoundError:
            return ToolResult(
                output="Git is not installed or not in PATH",
                is_error=True,
            )
        except Exception as e:
            return ToolResult(
                output=f"Error with git checkout: {e}",
                is_error=True,
            )
