"""Tool system for agent file operations, shell commands, and checklist management."""

import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class Tools:
    """Provides file I/O, shell execution, and git operations for agents."""

    def __init__(self, workspace_dir: str):
        """Initialize tools with a workspace directory.

        Args:
            workspace_dir: Root directory for all file operations
        """
        self.workspace_dir = Path(workspace_dir).resolve()
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, path: str) -> Path:
        """Resolve path relative to workspace."""
        resolved = (self.workspace_dir / path).resolve()
        # Security check: ensure path is within workspace
        if not str(resolved).startswith(str(self.workspace_dir)):
            raise ValueError(f"Path {path} is outside workspace")
        return resolved

    def read_file(self, path: str) -> str:
        """Read file contents.

        Args:
            path: Path relative to workspace

        Returns:
            File contents as string
        """
        file_path = self._resolve_path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        return file_path.read_text()

    def write_file(self, path: str, content: str) -> str:
        """Write or overwrite file.

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

    def append_file(self, path: str, content: str) -> str:
        """Append to existing file.

        Args:
            path: Path relative to workspace
            content: Content to append

        Returns:
            Success message
        """
        file_path = self._resolve_path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        with file_path.open("a") as f:
            f.write(content)
        return f"Content appended to: {path}"

    def run_command(self, command: str, cwd: Optional[str] = None) -> Dict[str, any]:
        """Execute shell command.

        Args:
            command: Shell command to execute
            cwd: Working directory (relative to workspace)

        Returns:
            Dict with stdout, stderr, return_code
        """
        work_dir = self.workspace_dir
        if cwd:
            work_dir = self._resolve_path(cwd)

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "success": result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": "Command timed out after 30 seconds",
                "return_code": -1,
                "success": False
            }

    def git_commit(self, message: str) -> Dict[str, any]:
        """Create a git commit.

        Args:
            message: Commit message (should follow Conventional Commits)

        Returns:
            Dict with commit SHA and success status
        """
        # Stage all changes
        self.run_command("git add -A")

        # Commit
        result = self.run_command(f'git commit -m "{message}"')

        # Get commit SHA if successful
        sha = None
        if result["success"]:
            sha_result = self.run_command("git rev-parse --short HEAD")
            if sha_result["success"]:
                sha = sha_result["stdout"].strip()

        return {
            "success": result["success"],
            "sha": sha,
            "message": message
        }

    def parse_checklist(self, checklist_path: str) -> Dict:
        """Parse a checklist file to find tasks.

        Args:
            checklist_path: Path to checklist markdown file

        Returns:
            Dict with:
                - status: Status from frontmatter
                - phases: List of phases with tasks
                - next_task: Next unchecked task or None
        """
        content = self.read_file(checklist_path)

        # Parse frontmatter
        frontmatter_match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
        status = "incomplete"
        if frontmatter_match:
            fm = frontmatter_match.group(1)
            status_match = re.search(r"status:\s*(\w+)", fm)
            if status_match:
                status = status_match.group(1)

        # Parse phases and tasks
        phases = []
        current_phase = None

        lines = content.split("\n")
        for i, line in enumerate(lines):
            # Phase header: ### Phase N: Name
            if line.startswith("### Phase"):
                if current_phase:
                    phases.append(current_phase)
                phase_match = re.match(r"###\s+Phase\s+(\d+):\s+(.+)", line)
                if phase_match:
                    current_phase = {
                        "number": int(phase_match.group(1)),
                        "name": phase_match.group(2),
                        "description": "",
                        "tasks": []
                    }
                    # Next line might be description (>)
                    if i + 1 < len(lines) and lines[i + 1].startswith(">"):
                        current_phase["description"] = lines[i + 1][1:].strip()

            # Task line: - [ ] or - [x]
            elif line.strip().startswith("- ["):
                task_match = re.match(r"^(\s*)- \[([ x])\]\s+(.+)", line)
                if task_match and current_phase:
                    indent = len(task_match.group(1))
                    is_complete = task_match.group(2) == "x"
                    description = task_match.group(3)

                    task = {
                        "description": description,
                        "is_complete": is_complete,
                        "indent": indent,
                        "line_number": i
                    }
                    current_phase["tasks"].append(task)

        if current_phase:
            phases.append(current_phase)

        # Find next unchecked task
        next_task = None
        for phase in phases:
            for task in phase["tasks"]:
                if not task["is_complete"] and task["indent"] == 0:
                    next_task = {
                        "phase": phase["name"],
                        "description": task["description"],
                        "line_number": task["line_number"]
                    }
                    break
            if next_task:
                break

        return {
            "status": status,
            "phases": phases,
            "next_task": next_task
        }

    def update_checklist(self, checklist_path: str, task_description: str,
                         mark_complete: bool = True, proof: Optional[str] = None,
                         commit_sha: Optional[str] = None) -> str:
        """Update a task in the checklist.

        Args:
            checklist_path: Path to checklist file
            task_description: Description of task to update
            mark_complete: Whether to mark as complete
            proof: Proof evidence to add
            commit_sha: Commit SHA to add

        Returns:
            Success message
        """
        content = self.read_file(checklist_path)
        lines = content.split("\n")

        # Find the task line
        task_line_idx = None
        for i, line in enumerate(lines):
            if task_description in line and line.strip().startswith("- ["):
                task_line_idx = i
                break

        if task_line_idx is None:
            raise ValueError(f"Task not found: {task_description}")

        # Update the task line
        task_line = lines[task_line_idx]
        if mark_complete:
            # Change [ ] to [x]
            task_line = task_line.replace("- [ ]", "- [x]", 1)

            # Add commit SHA if provided
            if commit_sha and "(commit:" not in task_line:
                # Insert before any existing parenthetical
                task_line = task_line.rstrip() + f" (commit: {commit_sha})"

            lines[task_line_idx] = task_line

            # Add proof on next line if provided
            if proof:
                indent = len(task_line) - len(task_line.lstrip())
                proof_line = " " * (indent + 2) + f"- Proof: {proof}"

                # Check if proof line already exists
                if task_line_idx + 1 < len(lines) and "Proof:" in lines[task_line_idx + 1]:
                    lines[task_line_idx + 1] = proof_line
                else:
                    lines.insert(task_line_idx + 1, proof_line)

        # Write back
        updated_content = "\n".join(lines)
        self.write_file(checklist_path, updated_content)

        return f"Checklist updated: {task_description}"

    def check_all_tasks_complete(self, checklist_path: str) -> bool:
        """Check if all tasks in checklist are complete.

        Args:
            checklist_path: Path to checklist file

        Returns:
            True if all tasks are marked [x]
        """
        parsed = self.parse_checklist(checklist_path)
        for phase in parsed["phases"]:
            for task in phase["tasks"]:
                if not task["is_complete"]:
                    return False
        return True
