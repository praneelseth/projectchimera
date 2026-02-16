"""Worker agent implementing Ralph Loop with NVIDIA Nemotron."""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.nemo_llm_client import NeMoLLMClient
from core.nemo_tools import RalphTools
from core.context_guard import ContextGuard


class NeMoWorkerAgent:
    """Worker agent implementing Ralph Loop with Nemotron-3-Nano-30B-A3B."""

    def __init__(self, workspace_dir: str, context_guard: ContextGuard):
        """Initialize the NeMo worker agent.

        Args:
            workspace_dir: Workspace directory path
            context_guard: Context monitor for rotation decisions
        """
        self.workspace_dir = Path(workspace_dir)
        self.llm = NeMoLLMClient()
        self.tools = RalphTools(workspace_dir)
        self.context_guard = context_guard
        self.rotation_count = 0

    def load_system_prompt(self) -> str:
        """Load the worker system prompt."""
        prompt_path = self.workspace_dir.parent / "prompt.md"
        if not prompt_path.exists():
            raise FileNotFoundError("prompt.md not found")
        return prompt_path.read_text()

    def _all_tasks_complete(self, checklist: str) -> bool:
        """Check if all tasks in checklist are complete.

        Args:
            checklist: Checklist content

        Returns:
            True if all tasks are marked [x]
        """
        lines = checklist.split("\n")
        for line in lines:
            # Look for unchecked tasks
            if line.strip().startswith("- [ ]"):
                return False
        return True

    def execute_step(self, checklist_path: str) -> Dict:
        """Execute one iteration of the Ralph Loop.

        Args:
            checklist_path: Path to checklist file

        Returns:
            Dict with step results
        """
        # Read Ralph Protocol files
        agents_md = self.tools.read_file("AGENTS.md")
        conventions_md = self.tools.read_file("docs/conventions.md")
        checklist_content = self.tools.read_file(checklist_path)

        # Check if complete
        if self._all_tasks_complete(checklist_content):
            return {
                "success": True,
                "action": "complete",
                "should_continue": False,
                "message": "<ralph>COMPLETE</ralph>"
            }

        # Load worker system prompt
        system_prompt = self.load_system_prompt()

        # Build user prompt with Ralph Protocol context
        user_prompt = f"""{system_prompt}

=== AGENTS.md ===
{agents_md}

=== docs/conventions.md ===
{conventions_md}

=== Current Checklist ({checklist_path}) ===
{checklist_content}

---

You are executing the Ralph Loop. Please:
1. Find the next unchecked [ ] task in the checklist
2. Complete the task and all its sub-tasks using the available tools
3. Run tests to verify your work matches the proof requirement
4. Update the checklist to mark tasks [x] with proof evidence
5. Commit your changes with a Conventional Commits message

Begin now with the next task."""

        # Initialize messages
        messages = [{"role": "user", "content": user_prompt}]

        # Tool calling loop for this step
        max_tool_iterations = 1000
        tool_iteration = 0

        while tool_iteration < max_tool_iterations:
            tool_iteration += 1

            try:
                # Call LLM with tools
                response = self.llm.client.chat.completions.create(
                    model=self.llm.model,
                    messages=messages,
                    tools=self.tools.get_tool_definitions(),
                    max_tokens=4096,
                    temperature=0.3
                )

                # Track tokens
                if hasattr(response, 'usage'):
                    tokens = response.usage.prompt_tokens + response.usage.completion_tokens
                    self.llm.total_input_tokens += response.usage.prompt_tokens
                    self.llm.total_output_tokens += response.usage.completion_tokens
                    self.context_guard.add_tokens(tokens)

                assistant_message = response.choices[0].message

                # DEBUG: Print what we got back
                print(f"  [DEBUG] Stop reason: {response.choices[0].finish_reason}")
                print(f"  [DEBUG] Has tool_calls: {assistant_message.tool_calls is not None}")
                if assistant_message.tool_calls:
                    print(f"  [DEBUG] Number of tool calls: {len(assistant_message.tool_calls)}")
                    for tc in assistant_message.tool_calls:
                        print(f"  [DEBUG] Tool: {tc.function.name}")

                # Add assistant message to history
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": [tc.model_dump() for tc in assistant_message.tool_calls] if assistant_message.tool_calls else None
                })

                # Check for completion signals
                if assistant_message.content:
                    if "<ralph>COMPLETE</ralph>" in assistant_message.content:
                        return {
                            "success": True,
                            "action": "complete",
                            "should_continue": False,
                            "message": "Worker signaled completion"
                        }
                    if "<ralph>GUTTER</ralph>" in assistant_message.content:
                        return {
                            "success": False,
                            "action": "gutter",
                            "should_continue": False,
                            "message": "Worker is stuck (gutter signal)"
                        }

                # Handle tool calls
                if assistant_message.tool_calls:
                    for tool_call in assistant_message.tool_calls:
                        tool_name = tool_call.function.name
                        tool_args = json.loads(tool_call.function.arguments)

                        print(f"  [Tool] {tool_name}({list(tool_args.keys())})")

                        # Execute tool
                        result = self.tools.execute_tool(tool_name, tool_args)

                        # Add tool result to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result
                        })

                    # Continue loop to let LLM process results
                    continue

                else:
                    # No more tool calls, step complete
                    return {
                        "success": True,
                        "action": "continue",
                        "should_continue": True,
                        "message": f"Step completed. Tokens: {self.llm.get_total_tokens()}, Usage: {self.context_guard.get_usage_percentage():.1f}%"
                    }

            except Exception as e:
                import traceback
                traceback.print_exc()
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

        print(f"\n[Worker] Starting Ralph Loop with Nemotron-3-Nano-30B-A3B")
        print(f"[Worker] Context: 1M tokens, threshold: {self.context_guard.threshold_percentage}%")
        print(f"[Worker] Context rotation at: {self.context_guard.threshold_tokens:,} tokens\n")

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
                self.rotation_count += 1
                print(f"\n[Worker] 🔄 Context rotation #{self.rotation_count} triggered")
                print(f"[Worker] Token usage before rotation: {self.context_guard.current_tokens:,} tokens ({self.context_guard.get_usage_percentage():.1f}%)")

                # Reset context state
                self.context_guard.reset()
                self.llm.reset_token_count()

                print(f"[Worker] ✓ Context reset complete. Continuing with fresh context...")
                print(f"[Worker] Progress persisted in: instructions/plan.md")
                # Continue the loop - do NOT break

        return {
            "iterations": iteration,
            "total_tokens": self.context_guard.current_tokens,
            "completed": iteration < max_iterations and result.get('action') == 'complete',
            "rotations": self.rotation_count
        }
