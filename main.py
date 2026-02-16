#!/usr/bin/env python3
"""Main entry point for Project Chimera - NeMo Agent Toolkit + Nemotron."""

import argparse
import os
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

from core.context_guard import ContextGuard


def load_agents(agent_type: str):
    """Dynamically load agent classes based on agent type.

    Args:
        agent_type: 'claude' or 'nemo'

    Returns:
        Tuple of (PlannerClass, WorkerClass, LLMClientClass)
    """
    if agent_type == 'claude':
        from agents.planner import PlannerAgent
        from agents.worker import WorkerAgent
        from core.llm_client import LLMClient
        return PlannerAgent, WorkerAgent, LLMClient
    elif agent_type == 'nemo':
        from agents.nemo_planner import NeMoPlannerAgent
        from agents.nemo_worker import NeMoWorkerAgent
        return NeMoPlannerAgent, NeMoWorkerAgent, None
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def run_planner(config: dict, agent_type: str):
    """Run the planner agent to generate checklist.

    Args:
        config: Configuration dictionary
        agent_type: 'claude' or 'nemo'
    """
    print("=" * 60)
    print("PROJECT CHIMERA - PLANNER MODE")

    if agent_type == 'claude':
        print("Claude (Anthropic) - Sonnet 4.5")
    else:
        print("NeMo Agent Toolkit + NVIDIA Nemotron-3-Nano-30B-A3B")

    print("=" * 60)

    workspace = config['workspace']['directory']
    print(f"\nWorkspace: {workspace}")
    print(f"Agent: {agent_type}")
    print(f"Model: {config['llm']['model']}\n")

    # Load agent classes
    PlannerClass, _, LLMClientClass = load_agents(agent_type)

    # Initialize planner
    if agent_type == 'claude':
        llm_client = LLMClientClass(
            model=config['llm'].get('model', 'claude-sonnet-4-5-20250929'),
            api_key=os.getenv('ANTHROPIC_API_KEY')
        )
        planner = PlannerClass(workspace, llm_client)
    else:
        planner = PlannerClass(workspace)

    # Run planner
    result = planner.run()

    if result['success']:
        print(f"\n✓ Checklist generated successfully!")
        print(f"  Location: {workspace}/{result['checklist_path']}")
        print(f"  Tokens used: {result['token_usage']}")
    else:
        print(f"\n✗ Planning failed: {result['error']}")
        sys.exit(1)


def run_worker(config: dict, agent_type: str):
    """Run the worker agent with Ralph Loop.

    Args:
        config: Configuration dictionary
        agent_type: 'claude' or 'nemo'
    """
    print("=" * 60)
    print("PROJECT CHIMERA - WORKER MODE")

    if agent_type == 'claude':
        print("Claude (Anthropic) - Sonnet 4.5")
    else:
        print("NeMo Agent Toolkit + NVIDIA Nemotron-3-Nano-30B-A3B")

    print("=" * 60)

    # Initialize context guard
    context_guard = ContextGuard(
        threshold_percentage=config['context']['threshold_percentage'],
        max_context=config['context']['max_context']
    )

    workspace = config['workspace']['directory']
    print(f"\nWorkspace: {workspace}")
    print(f"Agent: {agent_type}")
    print(f"Model: {config['llm']['model']}")
    print(f"Context: {config['context']['max_context']:,} tokens")
    print(f"Rotation threshold: {config['context']['threshold_percentage']}%")

    # Load agent classes
    _, WorkerClass, LLMClientClass = load_agents(agent_type)

    # Initialize worker
    if agent_type == 'claude':
        llm_client = LLMClientClass(
            model=config['llm'].get('model', 'claude-sonnet-4-5-20250929'),
            api_key=os.getenv('ANTHROPIC_API_KEY')
        )
        worker = WorkerClass(workspace, llm_client, context_guard)
    else:
        worker = WorkerClass(workspace, context_guard)

    # Run worker loop
    result = worker.run_loop(
        checklist_path="instructions/plan.md",
        max_iterations=config['execution']['max_iterations']
    )

    print("\n" + "=" * 60)
    print("EXECUTION SUMMARY")
    print("=" * 60)
    print(f"Iterations: {result['iterations']}")
    print(f"Total tokens: {result['total_tokens']:,}")
    print(f"Completed: {'✓ Yes' if result['completed'] else '✗ No'}")


def main():
    """Main entry point."""
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Project Chimera - Ralph Loop with Multiple Agent Providers"
    )
    parser.add_argument(
        '--mode',
        choices=['plan', 'work'],
        required=True,
        help='Mode: plan (generate checklist) or work (execute tasks)'
    )
    parser.add_argument(
        '--agent',
        choices=['claude', 'nemo'],
        default='nemo',
        help='Agent provider: claude (Anthropic) or nemo (NVIDIA Nemotron) [default: nemo]'
    )
    parser.add_argument(
        '--config',
        help='Custom config file (optional, defaults based on mode)'
    )

    args = parser.parse_args()

    # Check for appropriate API key
    if args.agent == 'claude':
        if not os.getenv('ANTHROPIC_API_KEY'):
            print("Error: ANTHROPIC_API_KEY environment variable not set")
            print("Get your key from: https://console.anthropic.com/settings/keys")
            print("")
            print("Add it to .env file:")
            print("  ANTHROPIC_API_KEY=sk-ant-xxxxx")
            sys.exit(1)
    elif args.agent == 'nemo':
        if not os.getenv('NVIDIA_API_KEY'):
            print("Error: NVIDIA_API_KEY environment variable not set")
            print("Get your key from: https://build.nvidia.com")
            print("")
            print("Add it to .env file:")
            print("  NVIDIA_API_KEY=nvapi-xxxxx")
            sys.exit(1)

    # Load config
    if args.config:
        config_path = args.config
    else:
        config_path = f"configs/{'planner' if args.mode == 'plan' else 'worker'}_config.yaml"

    try:
        config = load_config(config_path)
    except FileNotFoundError:
        print(f"Error: Config file not found: {config_path}")
        sys.exit(1)

    # Run mode
    try:
        if args.mode == 'plan':
            run_planner(config, args.agent)
        else:
            run_worker(config, args.agent)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
