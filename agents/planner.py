"""Planner agent that generates checklists from specifications."""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.llm_client import LLMClient
from core.tools import Tools


class PlannerAgent:
    """Generates execution checklists from project specifications."""

    def __init__(self, workspace_dir: str, llm_client: LLMClient):
        """Initialize the planner agent.

        Args:
            workspace_dir: Workspace directory path
            llm_client: LLM client for interactions
        """
        self.tools = Tools(workspace_dir)
        self.llm = llm_client
        self.workspace_dir = Path(workspace_dir)

    def load_system_prompt(self) -> str:
        """Load the planner system prompt."""
        prompt_path = self.workspace_dir.parent / "planner_prompt.md"
        if not prompt_path.exists():
            raise FileNotFoundError("planner_prompt.md not found")
        return prompt_path.read_text()

    def get_tool_definitions(self) -> List[Dict]:
        """Get tool definitions for the planner.

        Returns:
            List of tool definition dicts
        """
        return [
            {
                "name": "write_file",
                "description": "Write or create a file in the workspace",
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
            else:
                return f"Error: Unknown tool '{tool_name}'"
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"

    def run(self) -> Dict:
        """Run the planner to generate a checklist.

        Returns:
            Dict with:
                - success: Whether planning succeeded
                - checklist_path: Path to generated checklist
                - error: Error message if failed
        """
        try:
            # Load system prompt
            system_prompt = self.load_system_prompt()

            # Read the spec
            spec_content = self.tools.read_file("spec.md")

            # Create user message
            user_message = f"""Please analyze the following specification and create a comprehensive checklist in `instructions/plan.md`.

The checklist should follow the format defined in the system prompt, with:
- Clear phases
- Concrete tasks with measurable proof requirements
- Sequential organization

Here is the specification:

{spec_content}

Please use the write_file tool to create the checklist now."""

            # Initialize conversation
            conversation_history = [{"role": "user", "content": user_message}]

            # Tool calling loop
            max_iterations = 10
            iteration = 0
            checklist_created = False

            while iteration < max_iterations:
                iteration += 1

                # Call LLM with tools
                response = self.llm.chat(
                    system_prompt=system_prompt,
                    messages=conversation_history,
                    max_tokens=8000,
                    tools=self.get_tool_definitions()
                )

                # Build assistant message
                assistant_content = []
                if response['content']:
                    assistant_content.append({
                        "type": "text",
                        "text": response['content']
                    })
                    print(f"\n[Planner] {response['content']}\n")

                # Handle tool uses
                if response['tool_uses']:
                    for tool_use in response['tool_uses']:
                        assistant_content.append({
                            "type": "tool_use",
                            "id": tool_use["id"],
                            "name": tool_use["name"],
                            "input": tool_use["input"]
                        })

                    conversation_history.append({
                        "role": "assistant",
                        "content": assistant_content
                    })

                    # Execute tools
                    tool_results = []
                    for tool_use in response['tool_uses']:
                        print(f"[Planner] Executing: {tool_use['name']}")
                        result = self.execute_tool(tool_use["name"], tool_use["input"])
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use["id"],
                            "content": str(result)
                        })

                        # Check if checklist was created
                        if tool_use["name"] == "write_file" and "instructions/plan.md" in tool_use["input"].get("path", ""):
                            checklist_created = True

                    # Add tool results to conversation
                    conversation_history.append({
                        "role": "user",
                        "content": tool_results
                    })

                    # Continue loop
                    continue

                else:
                    # No more tool uses
                    conversation_history.append({
                        "role": "assistant",
                        "content": response['content']
                    })
                    break

            # Calculate total tokens
            total_tokens = self.llm.get_total_tokens()
            print(f"[Planner] Tokens used: {total_tokens}")

            # Verify the checklist was created
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
                except FileNotFoundError:
                    return {
                        "success": False,
                        "error": "Checklist file was not found after tool execution"
                    }
            else:
                return {
                    "success": False,
                    "error": "Planner did not create the checklist file"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
