"""Planner agent using NeMo/NVIDIA Nemotron with function calling."""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.nemo_llm_client import NeMoLLMClient
from core.nemo_tools import RalphTools


class NeMoPlannerAgent:
    """Planner agent using NVIDIA Nemotron-3-Nano with tool calling."""

    def __init__(self, workspace_dir: str):
        """Initialize the NeMo planner agent.

        Args:
            workspace_dir: Workspace directory path
        """
        self.workspace_dir = Path(workspace_dir)
        self.llm = NeMoLLMClient()
        self.tools = RalphTools(workspace_dir)

    def load_system_prompt(self) -> str:
        """Load the planner system prompt."""
        prompt_path = self.workspace_dir.parent / "planner_prompt.md"
        if not prompt_path.exists():
            raise FileNotFoundError("planner_prompt.md not found")
        return prompt_path.read_text()

    def run(self) -> Dict:
        """Run the planner to generate a checklist.

        Returns:
            Dict with:
                - success: Whether planning succeeded
                - checklist_path: Path to generated checklist
                - error: Error message if failed
                - token_usage: Total tokens used
        """
        try:
            # Load system prompt
            system_prompt = self.load_system_prompt()

            # Read spec
            spec_content = self.tools.read_file("spec.md")

            # Initialize conversation
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"""Please analyze the following specification and create a comprehensive checklist in `instructions/plan.md`.

The checklist should follow the format defined in the system prompt, with:
- Clear phases
- Concrete tasks with measurable proof requirements
- Sequential organization

Here is the specification:

{spec_content}

Please use the write_file tool to create the checklist now."""}
            ]

            # Tool calling loop
            max_iterations = 10
            iteration = 0
            checklist_created = False

            print("\n[Planner] Starting checklist generation with Nemotron-3-Nano")

            while iteration < max_iterations:
                iteration += 1

                # Call LLM with tools (planner only needs write_file)
                planner_tools = [t for t in self.tools.get_tool_definitions() if t['function']['name'] == 'write_file']

                response = self.llm.client.chat.completions.create(
                    model=self.llm.model,
                    messages=messages,
                    tools=planner_tools,
                    max_tokens=8000,
                    temperature=0.7
                )

                # Track tokens
                if hasattr(response, 'usage'):
                    self.llm.total_input_tokens += response.usage.prompt_tokens
                    self.llm.total_output_tokens += response.usage.completion_tokens

                assistant_message = response.choices[0].message

                # DEBUG: Print what we got back
                print(f"\n[DEBUG] Response stop_reason: {response.choices[0].finish_reason}")
                print(f"[DEBUG] Has tool_calls: {assistant_message.tool_calls is not None}")
                print(f"[DEBUG] Has content: {assistant_message.content is not None}")
                if assistant_message.tool_calls:
                    print(f"[DEBUG] Number of tool calls: {len(assistant_message.tool_calls)}")
                if assistant_message.content:
                    print(f"[DEBUG] Content length: {len(assistant_message.content)}")

                # Add assistant message to history
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": [tc.model_dump() for tc in assistant_message.tool_calls] if assistant_message.tool_calls else None
                })

                # Print assistant thinking
                if assistant_message.content:
                    print(f"\n[Planner] {assistant_message.content}\n")

                # Handle tool calls
                if assistant_message.tool_calls:
                    for tool_call in assistant_message.tool_calls:
                        tool_name = tool_call.function.name
                        tool_args = json.loads(tool_call.function.arguments)

                        print(f"[Planner] Executing tool: {tool_name}")

                        # Execute tool
                        result = self.tools.execute_tool(tool_name, tool_args)

                        # Add tool result to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result
                        })

                        # Check if checklist was created
                        if tool_name == "write_file" and "instructions/plan.md" in tool_args.get("path", ""):
                            checklist_created = True

                    # Continue loop to let LLM process results
                    continue

                else:
                    # No more tool calls, done
                    break

            # Calculate total tokens
            total_tokens = self.llm.get_total_tokens()
            print(f"\n[Planner] Total tokens used: {total_tokens}")

            # Verify checklist was created
            if checklist_created:
                checklist_path = "instructions/plan.md"
                try:
                    checklist = self.tools.read_file(checklist_path)
                    if len(checklist) < 100:
                        return {
                            "success": False,
                            "error": "Generated checklist is too short"
                        }

                    return {
                        "success": True,
                        "checklist_path": checklist_path,
                        "token_usage": total_tokens
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Checklist file error: {str(e)}"
                    }
            else:
                return {
                    "success": False,
                    "error": "Planner did not create the checklist file"
                }

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }
