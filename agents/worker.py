"""Worker agent that executes tasks following the Ralph Loop protocol."""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.llm_client import LLMClient
from core.context_guard import ContextGuard
from core.tools import Tools


class WorkerAgent:
    """Executes tasks from checklist using Ralph Loop protocol with tool calling."""

    def __init__(self, workspace_dir: str, llm_client: LLMClient, context_guard: ContextGuard):
        """Initialize the worker agent.

        Args:
            workspace_dir: Workspace directory path
            llm_client: LLM client for interactions
            context_guard: Context monitor for rotation decisions
        """
        self.tools = Tools(workspace_dir)
        self.llm = llm_client
        self.context_guard = context_guard
        self.workspace_dir = Path(workspace_dir)
        self.conversation_history: List[Dict[str, Any]] = []
        self.files_read_this_session = set()

    def load_system_prompt(self) -> str:
        """Load the worker system prompt."""
        prompt_path = self.workspace_dir.parent / "prompt.md"
        if not prompt_path.exists():
            raise FileNotFoundError("prompt.md not found")
        return prompt_path.read_text()

    def get_tool_definitions(self) -> List[Dict]:
        """Get tool definitions for Claude API.

        Returns:
            List of tool definition dicts
        """
        return [
            {
                "name": "read_file",
                "description": "Read contents of a file in the workspace",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to file relative to workspace directory"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "write_file",
                "description": "Write or overwrite a file in the workspace",
                "input_schema": {
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
            },
            {
                "name": "run_command",
                "description": "Execute a shell command in the workspace directory",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "Shell command to execute"
                        }
                    },
                    "required": ["command"]
                }
            },
            {
                "name": "git_commit",
                "description": "Create a git commit with all current changes",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Commit message (use Conventional Commits format)"
                        }
                    },
                    "required": ["message"]
                }
            },
            {
                "name": "str_replace_editor",
                "description": "Edit a file by replacing exact text matches (safer than full file rewrites)",
                "input_schema": {
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
            },
            {
                "name": "update_checklist",
                "description": "Mark a task as complete in the checklist with proof",
                "input_schema": {
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
                            "description": "Git commit SHA for this task"
                        }
                    },
                    "required": ["checklist_path", "task_description", "proof"]
                }
            }
        ]

    def execute_tool(self, tool_name: str, tool_input: Dict) -> Any:
        """Execute a tool call.

        Args:
            tool_name: Name of the tool
            tool_input: Input parameters for the tool

        Returns:
            Tool execution result
        """
        try:
            if tool_name == "read_file":
                return self.tools.read_file(tool_input["path"])

            elif tool_name == "write_file":
                return self.tools.write_file(tool_input["path"], tool_input["content"])

            elif tool_name == "run_command":
                result = self.tools.run_command(tool_input["command"])
                return json.dumps(result, indent=2)

            elif tool_name == "git_commit":
                result = self.tools.git_commit(tool_input["message"])
                return json.dumps(result, indent=2)

            elif tool_name == "str_replace_editor":
                return self.tools.str_replace_editor(
                    command=tool_input["command"],
                    path=tool_input["path"],
                    old_str=tool_input.get("old_str"),
                    new_str=tool_input.get("new_str")
                )

            elif tool_name == "update_checklist":
                return self.tools.update_checklist(
                    checklist_path=tool_input["checklist_path"],
                    task_description=tool_input["task_description"],
                    mark_complete=True,
                    proof=tool_input.get("proof"),
                    commit_sha=tool_input.get("commit_sha")
                )

            else:
                available_tools = ["read_file", "write_file", "str_replace_editor", "run_command", "git_commit", "update_checklist"]
                return f"Error: Unknown tool '{tool_name}'. Available tools: {', '.join(available_tools)}"

        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"

    def read_protocol_files(self) -> str:
        """Read AGENTS.md and conventions.md as per Ralph protocol.

        Returns:
            Formatted string with both files' contents
        """
        protocol_text = ""

        # Read AGENTS.md
        if "AGENTS.md" not in self.files_read_this_session:
            try:
                agents_content = self.tools.read_file("AGENTS.md")
                protocol_text += f"=== AGENTS.md ===\n{agents_content}\n\n"
                self.files_read_this_session.add("AGENTS.md")
            except FileNotFoundError:
                pass

        # Read conventions.md
        if "docs/conventions.md" not in self.files_read_this_session:
            try:
                conventions = self.tools.read_file("docs/conventions.md")
                protocol_text += f"=== docs/conventions.md ===\n{conventions}\n\n"
                self.files_read_this_session.add("docs/conventions.md")
            except FileNotFoundError:
                pass

        return protocol_text

    def execute_step(self, checklist_path: str) -> Dict:
        """Execute one step of the Ralph Loop with tool calling.

        Args:
            checklist_path: Path to checklist file

        Returns:
            Dict with:
                - success: Whether step succeeded
                - action: What action was taken
                - should_continue: Whether to continue looping
                - message: Status message
        """
        # Check if all tasks are complete
        if self.tools.check_all_tasks_complete(checklist_path):
            return {
                "success": True,
                "action": "complete",
                "should_continue": False,
                "message": "<ralph>COMPLETE</ralph>"
            }

        # Build initial user message
        if not self.conversation_history:
            protocol_docs = self.read_protocol_files()
            checklist_content = self.tools.read_file(checklist_path)

            user_message = f"""{protocol_docs}

=== Current Checklist ({checklist_path}) ===
{checklist_content}

---

You are starting a new Ralph Loop session. You have access to tools to read/write files, run commands, commit changes, and update the checklist.

Please:
1. Identify the next unchecked [ ] task
2. Complete the task and all its sub-tasks using the available tools
3. Run tests to verify your work matches the proof requirement
4. Update the checklist to mark tasks [x] with proof evidence
5. Commit your changes with a Conventional Commits message

Begin now with the next task."""

            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })

        # Tool use loop
        max_iterations = 1000
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            # Call LLM with tools
            try:
                response = self.llm.chat(
                    system_prompt=self.load_system_prompt(),
                    messages=self.conversation_history,
                    max_tokens=8000,
                    tools=self.get_tool_definitions()
                )

                # Track tokens
                total_tokens = response['input_tokens'] + response['output_tokens']
                self.context_guard.add_tokens(total_tokens)

                # Add assistant response to history
                assistant_content = []
                if response['content']:
                    assistant_content.append({
                        "type": "text",
                        "text": response['content']
                    })

                # Check for completion signals in text
                if "<ralph>COMPLETE</ralph>" in response['content']:
                    return {
                        "success": True,
                        "action": "complete",
                        "should_continue": False,
                        "message": "Worker signaled completion"
                    }

                if "<ralph>GUTTER</ralph>" in response['content']:
                    return {
                        "success": False,
                        "action": "gutter",
                        "should_continue": False,
                        "message": "Worker is stuck (gutter signal)"
                    }

                # Handle tool uses
                if response['tool_uses']:
                    for tool_use in response['tool_uses']:
                        assistant_content.append({
                            "type": "tool_use",
                            "id": tool_use["id"],
                            "name": tool_use["name"],
                            "input": tool_use["input"]
                        })

                    self.conversation_history.append({
                        "role": "assistant",
                        "content": assistant_content
                    })

                    # Execute tools and collect results
                    tool_results = []
                    for tool_use in response['tool_uses']:
                        print(f"  [Tool] {tool_use['name']}({json.dumps(tool_use['input'], indent=2)[:100]}...)")
                        result = self.execute_tool(tool_use["name"], tool_use["input"])
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use["id"],
                            "content": str(result)
                        })

                    # Add tool results to conversation
                    self.conversation_history.append({
                        "role": "user",
                        "content": tool_results
                    })

                    # Continue loop to let LLM process results
                    continue

                else:
                    # No tool use, just text response
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": response['content']
                    })

                    # Ask LLM to continue if needed
                    if response['stop_reason'] == 'end_turn':
                        # Check if task is actually done
                        if self.tools.check_all_tasks_complete(checklist_path):
                            return {
                                "success": True,
                                "action": "complete",
                                "should_continue": False,
                                "message": "All tasks complete"
                            }

                        # Otherwise, prompt for next task
                        checklist_content = self.tools.read_file(checklist_path)
                        self.conversation_history.append({
                            "role": "user",
                            "content": f"Current checklist:\n{checklist_content}\n\nPlease continue with the next task."
                        })

                        return {
                            "success": True,
                            "action": "continue",
                            "should_continue": not self.context_guard.should_rotate(),
                            "message": f"Step completed. Tokens: {total_tokens}, Usage: {self.context_guard.get_usage_percentage():.1f}%"
                        }

            except Exception as e:
                return {
                    "success": False,
                    "action": "error",
                    "should_continue": False,
                    "message": f"Error: {str(e)}"
                }

        return {
            "success": False,
            "action": "error",
            "should_continue": False,
            "message": "Max tool iterations reached"
        }

    def run_loop(self, checklist_path: str = "instructions/plan.md", max_iterations: int = 50) -> Dict:
        """Run the full Ralph Loop until completion or context rotation.

        Args:
            checklist_path: Path to checklist file
            max_iterations: Maximum iterations before stopping

        Returns:
            Dict with run statistics
        """
        iteration = 0
        total_tokens = 0

        print(f"\n[Worker] Starting Ralph Loop")
        print(f"[Worker] Context threshold: {self.context_guard.threshold_tokens} tokens ({self.context_guard.threshold_percentage}%)\n")

        while iteration < max_iterations:
            iteration += 1
            print(f"\n--- Iteration {iteration} ---")

            result = self.execute_step(checklist_path)

            print(f"[Worker] {result['message']}")

            if not result['should_continue']:
                if result['action'] == 'complete':
                    print(f"\n[Worker] ✓ All tasks complete!")
                elif result['action'] == 'gutter':
                    print(f"\n[Worker] ✗ Worker is stuck (gutter signal)")
                elif result['action'] == 'error':
                    print(f"\n[Worker] ✗ Error occurred")

                break

            # Check if rotation needed
            if self.context_guard.should_rotate():
                print(f"\n[Worker] ⚠ Context rotation threshold reached ({self.context_guard.get_usage_percentage():.1f}%)")
                print(f"[Worker] Total tokens: {self.context_guard.current_tokens}")
                print(f"[Worker] Checkpoint: Ensure work is committed before rotation")
                break

        return {
            "iterations": iteration,
            "total_tokens": self.context_guard.current_tokens,
            "completed": iteration < max_iterations and result.get('action') == 'complete'
        }
