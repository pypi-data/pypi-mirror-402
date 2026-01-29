"""File operation tools for CC Python."""

import fnmatch
import os
from pathlib import Path

import aiofiles

from .base import Tool, ToolParameter, ToolResult


class ReadFileTool(Tool):
    """Tool for reading file contents."""

    name = "read_file"
    description = "Read the contents of a file at the specified path. Use this to examine existing files."
    category = "read"
    requires_approval = False  # Reading is generally safe

    parameters = [
        ToolParameter(
            name="path",
            type="string",
            description="The absolute or relative path to the file to read",
        ),
        ToolParameter(
            name="offset",
            type="integer",
            description="Line number to start reading from (1-indexed)",
            required=False,
            default=1,
        ),
        ToolParameter(
            name="limit",
            type="integer",
            description="Maximum number of lines to read",
            required=False,
            default=None,
        ),
    ]

    async def execute(
        self,
        path: str,
        offset: int = 1,
        limit: int | None = None,
    ) -> ToolResult:
        """Read file contents."""
        try:
            file_path = Path(path).resolve()

            if not file_path.exists():
                return ToolResult(
                    output=f"File not found: {path}",
                    is_error=True,
                )

            if not file_path.is_file():
                return ToolResult(
                    output=f"Not a file: {path}",
                    is_error=True,
                )

            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                lines = await f.readlines()

            # Apply offset and limit
            start_idx = max(0, offset - 1)
            if limit:
                end_idx = start_idx + limit
                lines = lines[start_idx:end_idx]
            else:
                lines = lines[start_idx:]

            # Format with line numbers
            output_lines = []
            for i, line in enumerate(lines, start=start_idx + 1):
                output_lines.append(f"{i:6}|{line.rstrip()}")

            content = "\n".join(output_lines)

            return ToolResult(
                output=content if content else "File is empty.",
                data={"path": str(file_path), "lines": len(lines)},
            )

        except UnicodeDecodeError:
            return ToolResult(
                output=f"Cannot read file (binary or encoding issue): {path}",
                is_error=True,
            )
        except PermissionError:
            return ToolResult(
                output=f"Permission denied: {path}",
                is_error=True,
            )
        except Exception as e:
            return ToolResult(
                output=f"Error reading file: {e}",
                is_error=True,
            )


class WriteFileTool(Tool):
    """Tool for writing file contents."""

    name = "write_file"
    description = "Write content to a file. Creates the file if it doesn't exist, or overwrites if it does."
    category = "write"
    requires_approval = True

    parameters = [
        ToolParameter(
            name="path",
            type="string",
            description="The absolute or relative path to the file to write",
        ),
        ToolParameter(
            name="content",
            type="string",
            description="The content to write to the file",
        ),
    ]

    async def execute(self, path: str, content: str) -> ToolResult:
        """Write content to file."""
        try:
            file_path = Path(path).resolve()

            # Create parent directories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)

            async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                await f.write(content)

            return ToolResult(
                output=f"Successfully wrote to {path}",
                data={"path": str(file_path), "bytes": len(content)},
            )

        except PermissionError:
            return ToolResult(
                output=f"Permission denied: {path}",
                is_error=True,
            )
        except Exception as e:
            return ToolResult(
                output=f"Error writing file: {e}",
                is_error=True,
            )


class EditFileTool(Tool):
    """Tool for editing file contents with string replacement."""

    name = "edit_file"
    description = "Edit a file by replacing a specific string with another. The old_string must match exactly."
    category = "write"
    requires_approval = True

    parameters = [
        ToolParameter(
            name="path",
            type="string",
            description="The path to the file to edit",
        ),
        ToolParameter(
            name="old_string",
            type="string",
            description="The exact string to replace (must be unique in the file)",
        ),
        ToolParameter(
            name="new_string",
            type="string",
            description="The string to replace it with",
        ),
    ]

    async def execute(
        self,
        path: str,
        old_string: str,
        new_string: str,
    ) -> ToolResult:
        """Edit file by string replacement."""
        try:
            file_path = Path(path).resolve()

            if not file_path.exists():
                return ToolResult(
                    output=f"File not found: {path}",
                    is_error=True,
                )

            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                content = await f.read()

            # Check if old_string exists
            count = content.count(old_string)
            if count == 0:
                return ToolResult(
                    output=f"String not found in file: {old_string[:50]}...",
                    is_error=True,
                )
            if count > 1:
                return ToolResult(
                    output=f"String found {count} times. Please provide a more specific string.",
                    is_error=True,
                )

            # Replace
            new_content = content.replace(old_string, new_string)

            async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                await f.write(new_content)

            return ToolResult(
                output=f"Successfully edited {path}",
                data={"path": str(file_path)},
            )

        except Exception as e:
            return ToolResult(
                output=f"Error editing file: {e}",
                is_error=True,
            )


class ListDirectoryTool(Tool):
    """Tool for listing directory contents."""

    name = "list_directory"
    description = "List the contents of a directory."
    category = "read"
    requires_approval = False

    parameters = [
        ToolParameter(
            name="path",
            type="string",
            description="The path to the directory to list",
        ),
        ToolParameter(
            name="recursive",
            type="boolean",
            description="Whether to list recursively",
            required=False,
            default=False,
        ),
        ToolParameter(
            name="max_depth",
            type="integer",
            description="Maximum depth for recursive listing",
            required=False,
            default=3,
        ),
    ]

    async def execute(
        self,
        path: str,
        recursive: bool = False,
        max_depth: int = 3,
    ) -> ToolResult:
        """List directory contents."""
        try:
            dir_path = Path(path).resolve()

            if not dir_path.exists():
                return ToolResult(
                    output=f"Directory not found: {path}",
                    is_error=True,
                )

            if not dir_path.is_dir():
                return ToolResult(
                    output=f"Not a directory: {path}",
                    is_error=True,
                )

            entries = []

            def list_dir(p: Path, depth: int = 0, prefix: str = "") -> None:
                if depth > max_depth:
                    return

                try:
                    items = sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name))
                except PermissionError:
                    entries.append(f"{prefix}[Permission denied]")
                    return

                for item in items:
                    # Skip hidden files and common ignore patterns
                    if item.name.startswith(".") or item.name in {
                        "__pycache__",
                        "node_modules",
                        ".git",
                        "venv",
                        ".venv",
                    }:
                        continue

                    if item.is_dir():
                        entries.append(f"{prefix}{item.name}/")
                        if recursive:
                            list_dir(item, depth + 1, prefix + "  ")
                    else:
                        entries.append(f"{prefix}{item.name}")

            list_dir(dir_path)

            output = f"{dir_path}/\n" + "\n".join(entries)
            return ToolResult(
                output=output,
                data={"path": str(dir_path), "count": len(entries)},
            )

        except Exception as e:
            return ToolResult(
                output=f"Error listing directory: {e}",
                is_error=True,
            )


class SearchFilesTool(Tool):
    """Tool for searching file contents."""

    name = "search_files"
    description = "Search for a pattern in files within a directory."
    category = "read"
    requires_approval = False

    parameters = [
        ToolParameter(
            name="pattern",
            type="string",
            description="The search pattern (supports regex)",
        ),
        ToolParameter(
            name="path",
            type="string",
            description="The directory to search in",
            required=False,
            default=".",
        ),
        ToolParameter(
            name="file_pattern",
            type="string",
            description="Glob pattern for files to search (e.g., '*.py')",
            required=False,
            default="*",
        ),
        ToolParameter(
            name="max_results",
            type="integer",
            description="Maximum number of results to return",
            required=False,
            default=50,
        ),
    ]

    async def execute(
        self,
        pattern: str,
        path: str = ".",
        file_pattern: str = "*",
        max_results: int = 50,
    ) -> ToolResult:
        """Search for pattern in files."""
        import re

        try:
            search_path = Path(path).resolve()

            if not search_path.exists():
                return ToolResult(
                    output=f"Path not found: {path}",
                    is_error=True,
                )

            try:
                regex = re.compile(pattern)
            except re.error as e:
                return ToolResult(
                    output=f"Invalid regex pattern: {e}",
                    is_error=True,
                )

            results = []
            files_searched = 0

            for file_path in search_path.rglob(file_pattern):
                if not file_path.is_file():
                    continue

                # Skip binary and large files
                if file_path.suffix in {".pyc", ".exe", ".dll", ".so", ".bin"}:
                    continue

                try:
                    async with aiofiles.open(
                        file_path, "r", encoding="utf-8", errors="ignore"
                    ) as f:
                        content = await f.read()

                    files_searched += 1

                    for i, line in enumerate(content.splitlines(), 1):
                        if regex.search(line):
                            rel_path = file_path.relative_to(search_path)
                            results.append(f"{rel_path}:{i}: {line.strip()}")

                            if len(results) >= max_results:
                                break

                except (PermissionError, UnicodeDecodeError):
                    continue

                if len(results) >= max_results:
                    break

            if not results:
                return ToolResult(
                    output=f"No matches found for '{pattern}' in {files_searched} files",
                    data={"matches": 0, "files_searched": files_searched},
                )

            output = "\n".join(results)
            if len(results) >= max_results:
                output += f"\n\n(Results limited to {max_results})"

            return ToolResult(
                output=output,
                data={"matches": len(results), "files_searched": files_searched},
            )

        except Exception as e:
            return ToolResult(
                output=f"Error searching files: {e}",
                is_error=True,
            )


class GlobTool(Tool):
    """Tool for finding files by glob pattern."""

    name = "glob"
    description = "Find files matching a glob pattern."
    category = "read"
    requires_approval = False

    parameters = [
        ToolParameter(
            name="pattern",
            type="string",
            description="Glob pattern (e.g., '**/*.py' for all Python files)",
        ),
        ToolParameter(
            name="path",
            type="string",
            description="Base directory to search from",
            required=False,
            default=".",
        ),
        ToolParameter(
            name="max_results",
            type="integer",
            description="Maximum number of results",
            required=False,
            default=100,
        ),
    ]

    async def execute(
        self,
        pattern: str,
        path: str = ".",
        max_results: int = 100,
    ) -> ToolResult:
        """Find files matching glob pattern."""
        try:
            base_path = Path(path).resolve()

            if not base_path.exists():
                return ToolResult(
                    output=f"Path not found: {path}",
                    is_error=True,
                )

            # Handle patterns that don't start with **
            if not pattern.startswith("**/"):
                pattern = f"**/{pattern}"

            matches = []
            for match in base_path.glob(pattern):
                # Skip hidden and common ignore patterns
                parts = match.parts
                if any(
                    p.startswith(".") or p in {"__pycache__", "node_modules", "venv"}
                    for p in parts
                ):
                    continue

                try:
                    rel_path = match.relative_to(base_path)
                    matches.append(str(rel_path))
                except ValueError:
                    matches.append(str(match))

                if len(matches) >= max_results:
                    break

            if not matches:
                return ToolResult(
                    output=f"No files found matching '{pattern}'",
                    data={"count": 0},
                )

            # Sort by modification time (newest first)
            matches.sort()

            output = "\n".join(matches)
            if len(matches) >= max_results:
                output += f"\n\n(Results limited to {max_results})"

            return ToolResult(
                output=output,
                data={"count": len(matches)},
            )

        except Exception as e:
            return ToolResult(
                output=f"Error finding files: {e}",
                is_error=True,
            )
