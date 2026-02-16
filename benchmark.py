#!/usr/bin/env python3
"""
Benchmark script for comparing NVIDIA Nemotron vs Claude on JSON parser task.

This script:
1. Runs NeMo planner + worker
2. Captures metrics (iterations, memory, time, test results)
3. Cleans workspace
4. Runs Claude planner + worker
5. Captures metrics
6. Displays comparison results
"""

import os
import sys
import time
import subprocess
import json
import shutil
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional
import psutil


@dataclass
class BenchmarkResult:
    """Results from a single agent run."""
    agent: str
    success: bool
    iterations: int
    time_elapsed: float
    memory_peak_mb: float
    tokens_used: int
    tests_passing: int
    tests_total: int
    lines_of_code: int
    git_commits: int
    error: Optional[str] = None


def get_memory_usage() -> float:
    """Get current memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024


def count_lines_of_code(file_path: str) -> int:
    """Count non-empty lines in a Python file."""
    try:
        with open(file_path, 'r') as f:
            return len([line for line in f if line.strip() and not line.strip().startswith('#')])
    except FileNotFoundError:
        return 0


def count_git_commits(workspace: str) -> int:
    """Count git commits in workspace."""
    try:
        result = subprocess.run(
            ['git', 'rev-list', '--count', 'HEAD'],
            cwd=workspace,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return int(result.stdout.strip())
    except Exception:
        pass
    return 0


def run_tests(workspace: str) -> tuple[int, int]:
    """Run pytest and return (passing, total) test counts."""
    try:
        result = subprocess.run(
            ['python', '-m', 'pytest', 'tests/', '-v', '--tb=no', '--no-header'],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=60
        )

        # Parse pytest output for test counts
        output = result.stdout + result.stderr

        # Look for "X passed" or "X passed, Y failed"
        import re
        passed_match = re.search(r'(\d+) passed', output)
        failed_match = re.search(r'(\d+) failed', output)

        passed = int(passed_match.group(1)) if passed_match else 0
        failed = int(failed_match.group(1)) if failed_match else 0
        total = passed + failed

        return passed, total
    except Exception as e:
        print(f"  ⚠️  Error running tests: {e}")
        return 0, 0


def clean_workspace(workspace: str):
    """Clean workspace for next run."""
    print("  🧹 Cleaning workspace...")

    # Remove plan.md
    plan_path = Path(workspace) / "instructions" / "plan.md"
    if plan_path.exists():
        plan_path.unlink()

    # Remove src files
    src_dir = Path(workspace) / "src"
    if src_dir.exists():
        for file in src_dir.glob("*.py"):
            if file.name != "__init__.py":
                file.unlink()

    # Reset git (keep only initial commit)
    try:
        subprocess.run(
            ['git', 'reset', '--hard', 'HEAD~20'],
            cwd=workspace,
            capture_output=True,
            timeout=10
        )
        subprocess.run(
            ['git', 'clean', '-fd'],
            cwd=workspace,
            capture_output=True,
            timeout=10
        )
    except Exception:
        pass

    print("  ✓ Workspace cleaned")


def run_agent(agent: str, workspace: str) -> BenchmarkResult:
    """Run planner and worker for a specific agent."""
    print(f"\n{'='*60}")
    print(f"BENCHMARKING: {agent.upper()}")
    print(f"{'='*60}\n")

    start_time = time.time()
    start_memory = get_memory_usage()
    peak_memory = start_memory

    # Step 1: Run Planner
    print(f"  📋 Running {agent} planner...")
    try:
        planner_result = subprocess.run(
            ['python', 'main.py', '--mode', 'plan', '--agent', agent],
            capture_output=True,
            text=True,
            timeout=180
        )

        if planner_result.returncode != 0:
            return BenchmarkResult(
                agent=agent,
                success=False,
                iterations=0,
                time_elapsed=0,
                memory_peak_mb=0,
                tokens_used=0,
                tests_passing=0,
                tests_total=0,
                lines_of_code=0,
                git_commits=0,
                error=f"Planner failed: {planner_result.stderr}"
            )

        print("  ✓ Planner complete")

        # Update memory
        current_memory = get_memory_usage()
        peak_memory = max(peak_memory, current_memory)

    except subprocess.TimeoutExpired:
        return BenchmarkResult(
            agent=agent,
            success=False,
            iterations=0,
            time_elapsed=0,
            memory_peak_mb=0,
            tokens_used=0,
            tests_passing=0,
            tests_total=0,
            lines_of_code=0,
            git_commits=0,
            error="Planner timeout (>3 min)"
        )

    # Step 2: Run Worker
    print(f"  🔨 Running {agent} worker...")
    try:
        worker_result = subprocess.run(
            ['python', 'main.py', '--mode', 'work', '--agent', agent],
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )

        # Parse output for metrics
        output = worker_result.stdout + worker_result.stderr

        # Extract iterations
        import re
        iterations_match = re.search(r'Iterations:\s*(\d+)', output)
        iterations = int(iterations_match.group(1)) if iterations_match else 0

        # Extract tokens
        tokens_match = re.search(r'Total tokens:\s*([\d,]+)', output)
        tokens = int(tokens_match.group(1).replace(',', '')) if tokens_match else 0

        print(f"  ✓ Worker complete ({iterations} iterations, {tokens:,} tokens)")

        # Update memory
        current_memory = get_memory_usage()
        peak_memory = max(peak_memory, current_memory)

    except subprocess.TimeoutExpired:
        return BenchmarkResult(
            agent=agent,
            success=False,
            iterations=0,
            time_elapsed=0,
            memory_peak_mb=0,
            tokens_used=0,
            tests_passing=0,
            tests_total=0,
            lines_of_code=0,
            git_commits=0,
            error="Worker timeout (>10 min)"
        )

    # Step 3: Run Tests
    print(f"  🧪 Running tests...")
    passing, total = run_tests(workspace)
    print(f"  ✓ Tests complete: {passing}/{total} passing")

    # Step 4: Gather Metrics
    elapsed = time.time() - start_time
    loc = count_lines_of_code(f"{workspace}/src/json_parser.py")
    commits = count_git_commits(workspace)
    memory_used = peak_memory - start_memory

    return BenchmarkResult(
        agent=agent,
        success=passing > 0,
        iterations=iterations,
        time_elapsed=elapsed,
        memory_peak_mb=memory_used,
        tokens_used=tokens,
        tests_passing=passing,
        tests_total=total,
        lines_of_code=loc,
        git_commits=commits
    )


def display_results(results: list[BenchmarkResult]):
    """Display comparison results."""
    print(f"\n{'='*60}")
    print("BENCHMARK RESULTS")
    print(f"{'='*60}\n")

    # Create comparison table
    print("| Metric                  | NeMo (Nemotron)     | Claude (Sonnet 4.5) |")
    print("|-------------------------|---------------------|---------------------|")

    nemo_result = next((r for r in results if r.agent == 'nemo'), None)
    claude_result = next((r for r in results if r.agent == 'claude'), None)

    def format_value(result, attr, fmt=None):
        if not result:
            return "N/A"
        value = getattr(result, attr)
        if fmt == 'time':
            return f"{value:.1f}s"
        elif fmt == 'memory':
            return f"{value:.1f} MB"
        elif fmt == 'tokens':
            return f"{value:,}"
        elif fmt == 'tests':
            return f"{result.tests_passing}/{result.tests_total} ({result.tests_passing/max(result.tests_total,1)*100:.0f}%)"
        else:
            return str(value)

    print(f"| **Iterations**          | {format_value(nemo_result, 'iterations'):19} | {format_value(claude_result, 'iterations'):19} |")
    print(f"| **Time Elapsed**        | {format_value(nemo_result, 'time_elapsed', 'time'):19} | {format_value(claude_result, 'time_elapsed', 'time'):19} |")
    print(f"| **Memory Usage (Peak)** | {format_value(nemo_result, 'memory_peak_mb', 'memory'):19} | {format_value(claude_result, 'memory_peak_mb', 'memory'):19} |")
    print(f"| **Tests Passing**       | {format_value(nemo_result, 'tests_passing', 'tests'):19} | {format_value(claude_result, 'tests_passing', 'tests'):19} |")
    print(f"| **Lines of Code**       | {format_value(nemo_result, 'lines_of_code'):19} | {format_value(claude_result, 'lines_of_code'):19} |")
    print(f"| **Git Commits**         | {format_value(nemo_result, 'git_commits'):19} | {format_value(claude_result, 'git_commits'):19} |")
    print(f"| **Tokens Used**         | {format_value(nemo_result, 'tokens_used', 'tokens'):19} | {format_value(claude_result, 'tokens_used', 'tokens'):19} |")

    # Winner determination
    print(f"\n{'='*60}")
    print("COMPARISON")
    print(f"{'='*60}\n")

    if nemo_result and claude_result:
        if nemo_result.tests_passing > claude_result.tests_passing:
            print("🏆 Winner: NVIDIA Nemotron (more tests passing)")
        elif claude_result.tests_passing > nemo_result.tests_passing:
            print("🏆 Winner: Claude (more tests passing)")
        elif nemo_result.time_elapsed < claude_result.time_elapsed:
            print("🏆 Winner: NVIDIA Nemotron (faster execution)")
        else:
            print("🏆 Winner: Claude (faster execution)")

        print(f"\n✓ NeMo completed in {nemo_result.time_elapsed:.1f}s with {nemo_result.tests_passing}/{nemo_result.tests_total} tests passing")
        print(f"✓ Claude completed in {claude_result.time_elapsed:.1f}s with {claude_result.tests_passing}/{claude_result.tests_total} tests passing")

    # Save results to JSON
    results_file = "benchmark_results.json"
    with open(results_file, 'w') as f:
        json.dump([asdict(r) for r in results], f, indent=2)
    print(f"\n📊 Results saved to {results_file}")


def main():
    """Main benchmark execution."""
    print("="*60)
    print("PROJECT CHIMERA - BENCHMARK SUITE")
    print("Comparing NVIDIA Nemotron vs Claude on JSON Parser Task")
    print("="*60)

    workspace = "testing"

    # Check that workspace exists
    if not Path(workspace).exists():
        print(f"\n❌ Error: Workspace '{workspace}' not found")
        sys.exit(1)

    # Check API keys
    if not os.getenv('NVIDIA_API_KEY'):
        print("\n⚠️  Warning: NVIDIA_API_KEY not set, skipping NeMo benchmark")
        nemo_result = None
    else:
        nemo_result = run_agent('nemo', workspace)
        clean_workspace(workspace)

    if not os.getenv('ANTHROPIC_API_KEY'):
        print("\n⚠️  Warning: ANTHROPIC_API_KEY not set, skipping Claude benchmark")
        claude_result = None
    else:
        claude_result = run_agent('claude', workspace)

    # Display results
    results = [r for r in [nemo_result, claude_result] if r is not None]
    if results:
        display_results(results)
    else:
        print("\n❌ No benchmarks could be run. Check your API keys.")
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Benchmark interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Benchmark error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
