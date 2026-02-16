"""Custom tools for Ralph Loop using NeMo Agent Toolkit patterns."""

import json
import re
import subprocess
from pathlib import Path
from typing import Any, Dict


class RalphTools:
    """Custom tools for Ralph Loop compatible with NAT."""

    def __init__(self, workspace_dir: str):
        """Initialize tools with workspace directory.

        Args:
            workspace_dir: Root directory for all file operations
        """
        self.workspace_dir = Path(workspace_dir).resolve()
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, path: str) -> Path:
        """Resolve path relative to workspace."""
        resolved = (self.workspace_dir / path).resolve()
        if not str(resolved).startswith(str(self.workspace_dir)):
            raise ValueError(f"Path {path} is outside workspace")
        return resolved

    def read_file(self, path: str) -> str:
        """Read file contents from workspace.

        Args:
            path: Path relative to workspace

        Returns:
            File contents as string
        """
        file_path = self._resolve_path(path)
        if not file_path.exists():
            return f"Error: File not found: {path}"
        if file_path.is_dir():
            return f"Error: '{path}' is a directory, not a file. Use list_directory or specify a file path."
        return file_path.read_text()

    def write_file(self, path: str, content: str) -> str:
        """Write or overwrite a file in workspace.

        Args:
            path: Path relative to workspace
            content: File contents

        Returns:
            Success message
        """
        file_path = self._resolve_path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return f"File written: {path}"

    def run_command(self, command: str) -> str:
        """Execute a shell command in workspace.

        Args:
            command: Shell command to execute

        Returns:
            JSON string with stdout, stderr, return_code
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.workspace_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            return json.dumps({
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "success": result.returncode == 0
            }, indent=2)
        except subprocess.TimeoutExpired:
            return json.dumps({
                "stdout": "",
                "stderr": "Command timed out after 30 seconds",
                "return_code": -1,
                "success": False
            }, indent=2)

    def git_commit(self, message: str) -> str:
        """Create a git commit with all changes.

        Args:
            message: Commit message (use Conventional Commits format)

        Returns:
            JSON string with commit details
        """
        # Stage all changes
        subprocess.run("git add -A", shell=True, cwd=self.workspace_dir, capture_output=True)

        # Commit
        result = subprocess.run(
            f'git commit -m "{message}"',
            shell=True,
            cwd=self.workspace_dir,
            capture_output=True,
            text=True
        )

        # Get commit SHA
        sha = None
        if result.returncode == 0:
            sha_result = subprocess.run(
                "git rev-parse --short HEAD",
                shell=True,
                cwd=self.workspace_dir,
                capture_output=True,
                text=True
            )
            if sha_result.returncode == 0:
                sha = sha_result.stdout.strip()

        return json.dumps({
            "success": result.returncode == 0,
            "sha": sha,
            "message": message,
            "stdout": result.stdout,
            "stderr": result.stderr
        }, indent=2)

    def str_replace_editor(self, command: str, path: str,
                          old_str: str = None, new_str: str = None) -> str:
        """Edit a file using string replacement (like Aider/Claude Code).

        Args:
            command: "str_replace" to replace text, "create" to create new file
            path: Path relative to workspace
            old_str: Text to find and replace (for str_replace)
            new_str: Text to replace with (for str_replace)

        Returns:
            Success message or error
        """
        file_path = self._resolve_path(path)

        if command == "create":
            if file_path.exists():
                return f"Error: File already exists: {path}. Use str_replace to modify it."
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(new_str if new_str else "")
            return f"File created: {path}"

        elif command == "str_replace":
            if not file_path.exists():
                return f"Error: File not found: {path}. Use create command for new files."

            if not old_str:
                return "Error: old_str is required for str_replace command"

            content = file_path.read_text()

            # Check if old_str exists in file
            if old_str not in content:
                return f"Error: old_str not found in {path}. Make sure to copy the exact text."

            # Count occurrences
            count = content.count(old_str)
            if count > 1:
                return f"Error: old_str appears {count} times in {path}. Make it more specific to match exactly once."

            # Replace
            new_content = content.replace(old_str, new_str if new_str else "", 1)
            file_path.write_text(new_content)
            return f"File edited: {path} (replaced {len(old_str)} chars with {len(new_str or '')} chars)"

        else:
            return f"Error: Unknown command '{command}'. Available: 'str_replace', 'create'"

    def update_checklist(self, checklist_path: str, task_description: str,
                         proof: str, commit_sha: str = None) -> str:
        """Mark a task complete in the checklist with proof.

        Args:
            checklist_path: Path to checklist file (e.g., 'instructions/plan.md')
            task_description: Description of task to mark complete
            proof: Evidence that task is complete
            commit_sha: Optional git commit SHA

        Returns:
            Success message
        """
        try:
            file_path = self._resolve_path(checklist_path)
            content = file_path.read_text()
            lines = content.split("\n")

            # Find the task line
            task_line_idx = None
            for i, line in enumerate(lines):
                if task_description in line and "- [ ]" in line:
                    task_line_idx = i
                    break

            if task_line_idx is None:
                return f"Error: Task not found: {task_description}"

            # Update the task line
            task_line = lines[task_line_idx]
            task_line = task_line.replace("- [ ]", "- [x]", 1)

            # Add commit SHA if provided
            if commit_sha and "(commit:" not in task_line:
                task_line = task_line.rstrip() + f" (commit: {commit_sha})"

            lines[task_line_idx] = task_line

            # Add proof on next line
            indent = len(task_line) - len(task_line.lstrip())
            proof_line = " " * (indent + 2) + f"- Proof: {proof}"

            # Check if proof line already exists
            if task_line_idx + 1 < len(lines) and "Proof:" in lines[task_line_idx + 1]:
                lines[task_line_idx + 1] = proof_line
            else:
                lines.insert(task_line_idx + 1, proof_line)

            # Write back
            file_path.write_text("\n".join(lines))
            return f"Checklist updated: {task_description}"

        except Exception as e:
            return f"Error updating checklist: {str(e)}"

    def get_tool_definitions(self) -> list:
        """Get tool definitions in OpenAI function calling format.

        Returns:
            List of tool definition dicts for function calling
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read contents of a file in the workspace",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Path to file relative to workspace directory"
                            }
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Write or overwrite a file in the workspace",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Path to file relative to workspace directory"
                            },
                            "content": {
                                "type": "string",
                                "description": "Content to write to the file"
                            }
                        },
                        "required": ["path", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_command",
                    "description": "Execute a shell command in the workspace directory",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "Shell command to execute"
                            }
                        },
                        "required": ["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "git_commit",
                    "description": "Create a git commit with all current changes",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "Commit message (use Conventional Commits format)"
                            }
                        },
                        "required": ["message"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "str_replace_editor",
                    "description": "Edit a file by replacing exact text matches (safer than full file rewrites)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "Command to execute: 'str_replace' (replace text) or 'create' (new file)",
                                "enum": ["str_replace", "create"]
                            },
                            "path": {
                                "type": "string",
                                "description": "Path to file relative to workspace directory"
                            },
                            "old_str": {
                                "type": "string",
                                "description": "Exact text to find and replace (required for str_replace, must match exactly once)"
                            },
                            "new_str": {
                                "type": "string",
                                "description": "Text to replace with (for str_replace) or file content (for create)"
                            }
                        },
                        "required": ["command", "path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_checklist",
                    "description": "Mark a task as complete in the checklist with proof",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "checklist_path": {
                                "type": "string",
                                "description": "Path to checklist file (e.g., 'instructions/plan.md')"
                            },
                            "task_description": {
                                "type": "string",
                                "description": "Description of the task to mark complete (must match task text)"
                            },
                            "proof": {
                                "type": "string",
                                "description": "Evidence that task is complete (test output, file created, etc.)"
                            },
                            "commit_sha": {
                                "type": "string",
                                "description": "Git commit SHA for this task (optional)"
                            }
                        },
                        "required": ["checklist_path", "task_description", "proof"]
                    }
                }
            }
        ]

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool by name with arguments.

        Args:
            tool_name: Name of the tool to execute
            arguments: Dictionary of arguments

        Returns:
            Tool execution result as string
        """
        if tool_name == "read_file":
            return self.read_file(arguments["path"])
        elif tool_name == "write_file":
            return self.write_file(arguments["path"], arguments["content"])
        elif tool_name == "str_replace_editor":
            return self.str_replace_editor(
                arguments["command"],
                arguments["path"],
                arguments.get("old_str"),
                arguments.get("new_str")
            )
        elif tool_name == "run_command":
            return self.run_command(arguments["command"])
        elif tool_name == "git_commit":
            return self.git_commit(arguments["message"])
        elif tool_name == "update_checklist":
            return self.update_checklist(
                arguments["checklist_path"],
                arguments["task_description"],
                arguments["proof"],
                arguments.get("commit_sha")
            )
        else:
            available_tools = ["read_file", "write_file", "str_replace_editor", "run_command", "git_commit", "update_checklist"]
            return f"Error: Unknown tool '{tool_name}'. Available tools: {', '.join(available_tools)}"
