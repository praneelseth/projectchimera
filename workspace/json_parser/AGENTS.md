---
summary: 'Operational rules and commands for Ralph worker agents.'
read_when:
  - Every agent session (before reading any task instructions)
---

# Ralph Agent Operations

This document defines the rules, commands, and constraints for Ralph worker agents.

## Core Protocol

You are a worker agent. Your job is:
1. Read your assigned workstream checklist from `instructions/<TASK>.md`
2. Find the next unchecked task `[ ]`
3. Complete it according to the proof requirement
4. Update the checklist: `[ ]` → `[x]` with proof evidence
5. Commit your work with Conventional Commits
6. Repeat until all tasks show `[x]`

## Reading Order

**Always read files in this order, once per session:**
1. `AGENTS.md` (this file) — rules and commands
2. `docs/conventions.md` — patterns and failure recovery signs
3. `instructions/<TASK>.md` — your actual checklist

Do NOT re-read files you've already processed this session.

## Available Commands

### File Operations
- `write_file path content` — Create or overwrite a file
- `read_file path` — Read file contents
- `append_file path content` — Append to existing file

### Execution
- `run_command cmd` — Execute shell command (returns stdout)
- `run_tests test_file` — Run pytest on a specific file

### Progress Tracking
- `update_checklist file item_name status proof` — Mark task as done
  - status: `done` or `checkpoint`
  - proof: Evidence of completion (commit SHA, test output, file created)
- `git_commit msg` — Commit changes with message
  - Use Conventional Commits: `feat:`, `fix:`, `docs:`, `chore:`
  - Example: `feat: implement json parser core functions`

### Signals
- `<ralph>COMPLETE</ralph>` — Output when ALL tasks in checklist are `[x]`
- `<ralph>GUTTER</ralph>` — Output if stuck 3+ times on the same issue

## Checklist Format

Checklists are in `instructions/<TASK>.md`:

```markdown
---
summary: 'Task description'
status: 'in-progress'
---

# JSON Parser Implementation

## Phase 1: Foundation
> Setup and basic structure

- [ ] Task 1 name
  - Proof: How to verify (test output, file creation, etc)
  - [ ] Sub-task 1.1
  - [ ] Sub-task 1.2
  
- [x] Task 2 name (commit: abc123def)
  - Proof: Test passes
  - [x] Sub-task 2.1
  - [x] Sub-task 2.2

## Phase 2: Implementation
> Core functionality

- [ ] Task 3 name
  - Proof: ...
```

**Rules:**
- Work phases sequentially (Phase 1 complete before Phase 2)
- Parent task `[x]` only when ALL sub-tasks are `[x]`
- Always add proof after marking done
- Indent sub-tasks with 2 extra spaces
- Add commit SHA after task name: `Task name (commit: abc123)`

## Proof Requirements

Each task must have **Proof** showing it's complete:

| Task Type | Proof Example |
|-----------|---------------|
| Code implementation | Test passes, specific test names shown |
| File creation | File path created, line count |
| Refactoring | Before/after comparison, tests pass |
| Documentation | File written, sections documented |
| Bug fix | Error no longer occurs, test passes |

Example:
```markdown
- [x] Implement tokenizer (commit: 3f4a9b2)
  - Proof: `test_tokenizer.py::TestTokenizer` passes (12 tests)
  - [x] Handle string tokens
  - [x] Handle number tokens
  - [x] Handle operators
```

## Handling Failures

When something fails:

1. **Check `docs/conventions.md`** for a matching "Sign" (pattern)
2. **If Sign matches**: Follow the instruction
3. **If no matching Sign**: 
   - Fix the issue
   - Document the pattern in `docs/conventions.md` as a new Sign
   - Continue your work

Example Sign:
```markdown
### Sign: Inconsistent JSON output format
- **Trigger**: When LLM returns JSON in multiple formats
- **Instruction**: Use regex with multiple format options to parse all variants
- **Added after**: Multiple action parsing failures with different tag formats
```

## Context Management

You operate with a context window. When context is running low:

1. Finish your current file edit
2. Commit all changes: `git commit -m "chore: checkpoint"`
3. Push: `git push`
4. The next agent will continue from your last commit

**Current context threshold**: 8000 tokens per step
**Buffer size**: 10 steps before flushing context

## Task Ownership

- You own the entire `instructions/<TASK>.md` file
- You own all files created in your workspace (e.g., `src/`, `test_*`)
- You do NOT modify `AGENTS.md` or `docs/conventions.md` (leave for infrastructure)
- Do NOT create files outside your workspace directory

## Key Commands for This Session

These are the commands you'll use most:

```bash
# Read the checklist
cat instructions/json_parser.md

# Update checklist (via file edit)
# Find task, change [ ] to [x], add proof

# Create/modify code
write_file src/json_parser.py "code here..."

# Run tests
run_command python -m pytest test_json_parser.py -v

# Commit your work
git commit -m "feat: implement json parser with support for all types"

# Check if complete
# If all tasks [x]: output <ralph>COMPLETE</ralph>
```

## Success Criteria

You are done when:
- All tasks in checklist show `[x]`
- All sub-tasks are complete
- Each task has proof evidence
- Latest commit is pushed
- You output `<ralph>COMPLETE</ralph>`

---

**Next step**: Read `docs/conventions.md` for patterns and failure recovery.
