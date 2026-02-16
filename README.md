# Project Chimera: RALPH Loop Benchmark & Comparison

> **NVIDIA Golden Ticket Developer Contest Submission**
> Comparing NVIDIA Nemotron-3-Nano-30B-A3B vs Anthropic Claude Sonnet 4.5 on autonomous coding tasks

## What is Project Chimera?

Project Chimera is a **benchmark and comparison framework** for autonomous coding agents using the **RALPH Loop protocol** (Read-Analyze-Loop-Proof-Halt). It demonstrates how different LLMs perform on complex coding tasks by implementing the same JSON parser from a specification.

### Key Innovation: RALPH Loops

Unlike traditional chatbot-style agents that maintain long conversation histories, **RALPH Loops** are:

- **Context-Independent**: Each iteration reads fresh from structured files (AGENTS.md → conventions.md → checklist)
- **Stateless**: All progress stored in git commits and markdown checklists, not conversation memory
- **Proof-Based**: Every task requires verifiable evidence of completion before moving forward
- **Self-Correcting**: Agents document failures as "Signs" in conventions.md to avoid repeating mistakes

This design enables:
- **True long-running autonomy** (days/weeks) without context window limits
- **Seamless agent handoff** - any agent can continue from where another left off
- **Reproducible results** - git history provides complete audit trail
- **Provider comparison** - identical protocol across different LLMs

## Why This Matters for NVIDIA

Project Chimera showcases **NVIDIA Nemotron-3-Nano-30B-A3B** as a cost-effective alternative to larger proprietary models for autonomous coding:

1. **1M Token Context Window**: Handles massive codebases in a single context
2. **3.2B Active Parameters**: Efficient inference with Mixture-of-Experts architecture
3. **Native Tool Calling**: OpenAI-compatible function calling for file operations, shell commands, and git
4. **Benchmark Results**: Head-to-head comparison against Claude Sonnet 4.5 on JSON parser implementation

### Benchmark Task: JSON Parser

Both agents receive the same specification in `testing/spec.md` and must:
- Generate a complete implementation plan
- Write a pure Python JSON parser from scratch
- Handle all JSON types (objects, arrays, strings, numbers, booleans, null)
- Pass 60+ comprehensive unit tests
- Implement error handling and edge cases

**Metrics Tracked:**
- Number of iterations to completion
- Memory usage during execution
- Time elapsed (wall clock)
- Test pass rate (0-60+ tests)
- Lines of code generated
- Git commits created

## Overview: RALPH Loop Architecture

```
┌─────────────┐
│   Planner   │  Reads spec.md
│   Agent     │  → Generates instructions/plan.md checklist
└─────────────┘  (One-time planning phase)

       ↓

┌─────────────────────────────────────────────────┐
│              RALPH Loop (Worker)                │
│                                                 │
│  1. READ: AGENTS.md → conventions.md → plan.md │
│  2. ANALYZE: Find next unchecked task [ ]      │
│  3. LOOP: Execute task with tool calling       │
│     - read_file, write_file, str_replace_editor│
│     - run_command (tests, linters, etc.)       │
│     - git_commit (conventional commits)        │
│  4. PROOF: Update checklist with evidence [x]  │
│  5. HALT: Check if complete or rotate context  │
│                                                 │
│  → Repeat until all tasks marked [x]           │
└─────────────────────────────────────────────────┘
```

### Key Design Principles

1. **Context-Independent Design**: Agents don't rely on conversation history - all state is in git commits and markdown checklists
2. **Planner-Worker Architecture**: Separation between planning (checklist generation) and execution
3. **Configurable Context Rotation**: Automatic context refresh at configurable threshold (50% default for Nemotron's 1M window)
4. **Git-as-Memory**: All progress tracked through conventional commits
5. **Ralph Protocol**: Structured reading order ensures consistency across iterations and agents

## Architecture

```
┌─────────────┐
│   Planner   │  Reads spec.md
│   Agent     │  → Generates instructions/plan.md checklist
└─────────────┘

       ↓

┌─────────────┐
│   Worker    │  Reads: AGENTS.md → conventions.md → plan.md
│   Agent     │  → Executes tasks → Updates checklist → Commits
└─────────────┘  → Loop until complete or context rotation
```

## Key Features

1. **NVIDIA NeMo Agent Toolkit**: Built on NVIDIA's official agent framework
2. **Nemotron-3-Nano-30B-A3B**: 3.2B active parameters, 1M token context window
3. **Context Rotation**: Flushes context at configurable percentage (10% default = 100k tokens)
4. **Proof-Based Progress**: Every task requires proof of completion
5. **Self-Documenting**: Agents add "Signs" to conventions.md when learning patterns
6. **Benchmark Task**: JSON parser implementation to demonstrate capability

## Directory Structure

```
project-chimera/
├── agents/
│   ├── planner.py          # Claude planner
│   ├── worker.py           # Claude worker implementing Ralph Loop
│   ├── nemo_planner.py     # NeMo planner with Nemotron
│   └── nemo_worker.py      # NeMo worker implementing Ralph Loop
├── core/
│   ├── llm_client.py       # Anthropic Claude client
│   ├── tools.py            # Tool calling for Claude
│   ├── nemo_llm_client.py  # NVIDIA Nemotron-3-Nano client
│   ├── nemo_tools.py       # Tool calling for NeMo
│   └── context_guard.py    # Token tracking & rotation
├── configs/
│   ├── planner_config.yaml # Planner configuration (both providers)
│   └── worker_config.yaml  # Worker configuration (both providers)
├── testing/                # Benchmark workspace (git repo, clone this from https://github.com/praneelseth/testing)
│   ├── spec.md             # JSON parser specification
│   ├── AGENTS.md           # Operational rules for workers
│   ├── docs/conventions.md # Learned patterns and "Signs"
│   ├── instructions/       # Generated checklists (plan.md)
│   ├── src/                # Generated source code
│   └── tests/              # Unit tests
├── main.py                 # CLI entry point with --agent flag
├── prompt.md               # Worker system prompt (Ralph Loop protocol)
├── planner_prompt.md       # Planner system prompt
└── requirements.txt
```

## Installation

```bash
# Clone repository
git clone <repo-url>
cd project-chimera

git clone https://github.com/praneelseth/testing.git

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env and add your API key(s):
#   NVIDIA_API_KEY (for --agent nemo) from https://build.nvidia.com
#   ANTHROPIC_API_KEY (for --agent claude) from https://console.anthropic.com/settings/keys
```

## Agent Selection

Project Chimera supports multiple LLM providers via the `--agent` flag:

### Using NVIDIA Nemotron (Default)

```bash
python main.py --mode plan --agent nemo
python main.py --mode work --agent nemo

# Or omit --agent flag (defaults to nemo)
python main.py --mode plan
python main.py --mode work
```

**Requirements:**
- Set `NVIDIA_API_KEY` in `.env`
- Get your key from: https://build.nvidia.com

**Features:**
- 1M token context window
- 3.2B active parameters (31.6B total with MoE)
- Cost-effective for large codebases

### Using Claude (Anthropic)

```bash
python main.py --mode plan --agent claude
python main.py --mode work --agent claude
```

**Requirements:**
- Set `ANTHROPIC_API_KEY` in `.env`
- Get your key from: https://console.anthropic.com/settings/keys

**Features:**
- 200k token context window
- State-of-the-art reasoning and code generation
- Native tool calling support

### Feature Comparison

| Feature | NeMo (Nemotron) | Claude (Sonnet 4.5) |
|---------|-----------------|---------------------|
| Context Window | 1M tokens | 200k tokens |
| Tool Calling | OpenAI-compatible | Native Anthropic format |
| `str_replace_editor` | ✓ | ✓ |
| Cost | $ | $$ |
| Best For | Large codebases | Complex reasoning |

## Quick Start: Running the Benchmark

### Option 1: Automated Benchmark (Recommended)

Run the full benchmark comparing both agents:

```bash
python benchmark.py
```

This will:
1. Run NeMo planner → worker → tests
2. Capture metrics (iterations, memory, time, test results)
3. Clean workspace
4. Run Claude planner → worker → tests
5. Capture metrics
6. Display comparison results

### Option 2: Manual Step-by-Step

Choose your agent first (default is `nemo`):

#### Step 1: Run Planner (Once)

```bash
# Using NVIDIA Nemotron (default)
python main.py --mode plan --agent nemo

# OR using Claude
python main.py --mode plan --agent claude
```

**What happens:**
- Reads `testing/spec.md` (JSON parser specification)
- Generates `testing/instructions/plan.md` (structured checklist with phases and tasks)
- Output: Checklist location and token usage

#### Step 2: Run Worker (Once or until complete)

```bash
# Using NVIDIA Nemotron
python main.py --mode work --agent nemo

# OR using Claude
python main.py --mode work --agent claude
```

**What happens:**
- Executes RALPH Loop protocol
- Reads AGENTS.md → conventions.md → plan.md each iteration
- Executes next unchecked task with tool calling
- Updates checklist with proof [x]
- Creates git commits
- Repeats until complete or max iterations reached

**Output:**
```
--- Iteration 1 ---
  [Tool] read_file(['path'])
  [Tool] str_replace_editor(['command', 'path'])
  [Tool] git_commit(['message'])
  Tokens: 65,931, Usage: 13.2%

--- Iteration 2 ---
  ...
```

#### Step 3: Check Results

```bash
# Run the test suite
cd testing
python -m pytest tests/test_json_parser.py -v

# Check git history
git log --oneline

# View generated code
cat src/json_parser.py
```

### Comparing Agents

#### Automated Benchmark (Recommended)

Use the benchmark script to automatically compare both agents:

```bash
python benchmark.py
```

**What it does:**
1. Runs NeMo planner → worker
2. Executes pytest and captures results
3. Records metrics: iterations, memory usage, time, test pass rate
4. Cleans workspace (removes plan.md, resets git, clears src/)
5. Runs Claude planner → worker
6. Executes pytest and captures results
7. Displays comparison table with winner determination
8. Saves results to `benchmark_results.json`

**Sample Output:**
```
============================================================
BENCHMARK RESULTS
============================================================

| Metric                  | NeMo (Nemotron)     | Claude (Sonnet 4.5) |
|-------------------------|---------------------|---------------------|
| **Iterations**          | 5                   | 8                   |
| **Time Elapsed**        | 145.2s              | 210.5s              |
| **Memory Usage (Peak)** | 85.3 MB             | 120.7 MB            |
| **Tests Passing**       | 45/60 (75%)         | 58/60 (97%)         |
| **Lines of Code**       | 171                 | 245                 |
| **Git Commits**         | 8                   | 12                  |
| **Tokens Used**         | 346,375             | 125,423             |

🏆 Winner: Claude (more tests passing)

📊 Results saved to benchmark_results.json
```

#### Manual Comparison

To manually compare both agents:

```bash
# 1. Run NeMo
python main.py --mode plan --agent nemo
python main.py --mode work --agent nemo
cd testing && python -m pytest tests/ -v && cd ..

# 2. Clean workspace
rm testing/instructions/plan.md
rm -rf testing/src/*
cd testing && git reset --hard HEAD~10 && cd ..

# 3. Run Claude
python main.py --mode plan --agent claude
python main.py --mode work --agent claude
cd testing && python -m pytest tests/ -v && cd ..
```

### Configuration

Edit `configs/worker_config.yaml` to adjust:

```yaml
context:
  threshold_percentage: 10.0  # Rotate at 10% of max context
  max_context: 200000         # Claude Sonnet 4.5 context window

execution:
  max_iterations: 50          # Safety limit
```

## Ralph Protocol

The worker follows this structured reading order every iteration:

1. **AGENTS.md**: Operational rules and available commands
2. **docs/conventions.md**: Learned patterns and failure recovery "Signs"
3. **instructions/plan.md**: Task checklist with proof requirements

This ensures context-independent operation - each iteration can start fresh.

## Benchmark Task

The system is demonstrated with a **JSON Parser** implementation:

- **Spec**: `testing/spec.md` - Requirements for a pure Python JSON parser
- **Tests**: `testing/tests/test_json_parser.py` - Comprehensive test suite
- **Success**: All tests pass, parser handles all JSON types

## Context Rotation

Unlike traditional chatbot-style agents, Project Chimera is designed for **context independence**:

- Context rotates at configurable threshold (10% default)
- All state preserved in git commits and checklist files
- New worker instance picks up exactly where previous left off
- No context required beyond the protocol files

## Benchmark Results

### Sample Comparison: JSON Parser Implementation

| Metric | NVIDIA Nemotron-3-Nano | Claude Sonnet 4.5 |
|--------|------------------------|-------------------|
| **Iterations** | 5 | TBD |
| **Time Elapsed** | ~2.5 min | TBD |
| **Memory Usage (Peak)** | ~250 MB | TBD |
| **Tests Passing** | 45/60 (75%) | TBD |
| **Lines of Code** | 171 | TBD |
| **Git Commits** | 8 | TBD |
| **Context Used** | 346k tokens (69% of 500k threshold) | TBD |
| **Tool Calls** | 95 | TBD |

**Cost Comparison:**
- Nemotron: ~350k tokens ≈ $0.XX
- Claude: TBD tokens ≈ $X.XX

_Run `python benchmark.py` to generate updated results._

## Example Output

```
============================================================
PROJECT CHIMERA - PLANNER MODE
NeMo Agent Toolkit + NVIDIA Nemotron-3-Nano-30B-A3B
============================================================

Workspace: testing
Agent: nemo
Model: nvidia/nemotron-3-nano-30b-a3b

[Planner] Starting checklist generation with Nemotron-3-Nano

✓ Checklist generated successfully!
  Location: testing/instructions/plan.md
  Tokens used: 7563

============================================================
PROJECT CHIMERA - WORKER MODE
NeMo Agent Toolkit + NVIDIA Nemotron-3-Nano-30B-A3B
============================================================

Workspace: testing
Agent: nemo
Model: nvidia/nemotron-3-nano-30b-a3b
Context: 1,000,000 tokens (1M token window!)
Rotation threshold: 50.0%

[Worker] Starting Ralph Loop with Nemotron-3-Nano-30B-A3B

--- Iteration 1 ---
  [DEBUG] Tool: read_file
  [DEBUG] Tool: run_command
  [DEBUG] Tool: str_replace_editor
  [DEBUG] Tool: git_commit
  [Worker] Step completed. Tokens: 65,931, Usage: 13.2%

--- Iteration 2 ---
  [Worker] Step completed. Tokens: 83,844, Usage: 16.8%

--- Iteration 3 ---
  [DEBUG] Tool: str_replace_editor (15 calls - incremental editing!)
  [DEBUG] Tool: update_checklist
  [DEBUG] Tool: git_commit
  [Worker] Step completed. Tokens: 316,284, Usage: 63.3%

...

============================================================
EXECUTION SUMMARY
============================================================
Iterations: 5
Total tokens: 346,375
Completed: ✗ No (partial implementation, see test results)
```

## Implemented Features

- ✅ **NVIDIA NeMo Agent Toolkit integration** with Nemotron-3-Nano-30B-A3B
- ✅ **Dual agent support**: Switch between Nemotron and Claude
- ✅ **Tool calling**: Native function calling for both providers
- ✅ **str_replace_editor**: Incremental file editing (prevents regeneration bug)
- ✅ **RALPH Loop protocol**: Context-independent execution
- ✅ **Benchmark framework**: Automated comparison script
- ✅ **1M token context** support for Nemotron
- ✅ **Configurable context rotation** (50% default)

## Future Enhancements

- [ ] Multi-worker parallelization for sub-tasks
- [ ] Web UI for real-time monitoring
- [ ] Extended benchmark suite (multiple coding tasks)
- [ ] Streaming output for live progress tracking
- [ ] Cost tracking per API call

## Contributing

This is a demonstration project for NVIDIA GTC. Contributions welcome!

## License

MIT License
