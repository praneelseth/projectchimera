---
summary: 'Initial planner agent - reads task specification and creates workspace structure.'
status: 'in-progress'
mode: 'planner'
read_when:
  - First agent session only
  - When starting a new major task
---

# Task Planner: Create Workspaces

**Your Role**: You are the initial planner agent. Your job is to:
1. Read the task specification (spec.md)
2. Break the task into logical subtasks/phases
3. Create multiple workspace directories
4. For each workspace, create a checklist (instructions/<name>.md)
5. When complete, output: `<ralph>WORKSPACES_CREATED</ralph>`

---

## Phase 1: Read & Analyze Specification

- [ ] Read spec.md completely
  - Proof: Can summarize all requirements
  - [ ] Understand overall objective
  - [ ] Identify all requirements
  - [ ] List test cases/validation criteria
  - [ ] Note any constraints (size limits, dependencies, etc.)

- [ ] Break task into logical subtasks
  - Proof: List of 3-5 focused subtasks
  - [ ] Each subtask is independent or has clear dependencies
  - [ ] Each subtask has a specific deliverable
  - [ ] Subtasks together complete the full task
  - [ ] Example: "tokenizer" → "parser" → "error handling" → "testing"

---

## Phase 2: Create Workspace Structure

- [ ] Create workspace directory for each subtask
  - Proof: Directory structure created with proper names
  - [ ] Directory created: `workspaces/subtask1/`
  - [ ] Directory created: `workspaces/subtask2/`
  - [ ] Directory created: `workspaces/subtask3/`
  - [ ] Each has: `src/`, `tests/`, `instructions/`

- [ ] Copy shared files to each workspace
  - Proof: Files present in all workspaces
  - [ ] Copy `spec.md` to each workspace
  - [ ] Copy test files to each workspace
  - [ ] Copy `AGENTS.md` to each workspace
  - [ ] Copy `docs/conventions.md` to each workspace

---

## Phase 3: Create Individual Checklists

- [ ] Create instructions/subtask1.md
  - Proof: File created with checklist
  - [ ] Phases clearly defined
  - [ ] Tasks with proof requirements
  - [ ] Sub-tasks nested and clear
  - [ ] README or Quick Reference section

- [ ] Create instructions/subtask2.md
  - Proof: File created with checklist
  - [ ] Build on previous subtask if needed
  - [ ] Clear dependencies listed
  - [ ] Proof requirements specified

- [ ] Create instructions/subtask3.md
  - Proof: File created with checklist
  - [ ] Integration/final validation phase
  - [ ] All tests verified
  - [ ] Code quality checks

- [ ] (Repeat for additional subtasks if needed)
  - Proof: All checklists created
  - [ ] Each file: `instructions/<subtask>.md`
  - [ ] All have same structure and format

---

## Phase 4: Initialization

- [ ] Create workspace initialization file
  - Proof: File created with metadata
  - [ ] File: `workspaces/README.md`
  - [ ] Lists all subtasks
  - [ ] Explains dependencies
  - [ ] Instructions for running agents on each

- [ ] Create workspace manifest
  - Proof: Manifest shows all workspaces
  - [ ] File: `workspaces/MANIFEST.md`
  - [ ] Lists subtask order
  - [ ] Shows dependencies between tasks
  - [ ] Indicates which agents work on which tasks

---

## Phase 5: Completion

- [ ] Verify all workspaces created and ready
  - Proof: All directories and files present
  - [ ] Each workspace has instructions/<name>.md
  - [ ] Each workspace has src/ directory
  - [ ] Shared files (spec, tests) are copied
  - [ ] AGENTS.md and docs/ are in each workspace

- [ ] Commit workspace structure
  - Proof: Git commit with message
  - [ ] Command: `git commit -m "feat: create workspace structure with N subtasks"`
  - [ ] All files staged and committed
  - [ ] Ready for worker agents to begin

---

## How Workspaces Should Be Organized

```
workspaces/
├── subtask1/
│   ├── AGENTS.md (symlink or copy)
│   ├── docs/conventions.md (copy)
│   ├── instructions/subtask1.md (checklist - you create)
│   ├── spec.md (copy from root)
│   ├── test_*.py (copy from root)
│   └── src/ (created by worker agents)
│
├── subtask2/
│   ├── AGENTS.md
│   ├── docs/conventions.md
│   ├── instructions/subtask2.md (checklist - you create)
│   ├── spec.md
│   ├── test_*.py
│   └── src/
│
├── subtask3/
│   └── ...
│
├── README.md (you create - overview of workspaces)
└── MANIFEST.md (you create - dependency graph)
```

---

## Example: JSON Parser Task Breakdown

If breaking down the JSON parser task, you might create:

**Subtask 1: Tokenizer**
- Objective: Build lexical analyzer
- Phases: Token types → String handling → Number handling → Whitespace
- Tests: Tokenizer unit tests

**Subtask 2: Parser**
- Objective: Build recursive descent parser
- Phases: Basic values → Arrays → Objects → Nesting
- Tests: Parser unit tests

**Subtask 3: Error Handling & Validation**
- Objective: Handle edge cases and errors
- Phases: Invalid JSON → Escape sequences → Performance
- Tests: Error case tests

**Subtask 4: Integration & Polish**
- Objective: Full test suite and performance
- Phases: All tests pass → Code review → Optimization
- Tests: Full suite (40+ tests)

---

## Your Commands

You can use these operations:

```bash
# Create directories
mkdir -p workspaces/subtask1/src
mkdir -p workspaces/subtask1/instructions
mkdir -p workspaces/subtask1/docs

# Copy files
cp spec.md workspaces/subtask1/
cp test_json_parser.py workspaces/subtask1/
cp AGENTS.md workspaces/subtask1/
cp docs/conventions.md workspaces/subtask1/docs/

# Create checklist files
# (write them out in markdown format)

# Git operations
git add workspaces/
git commit -m "feat: create workspace structure with subtasks"
```

---

## Success Criteria

You are done when:
- [ ] 3-5 well-designed subtasks identified
- [ ] Each subtask in its own `workspaces/subtask*/` directory
- [ ] Each has its own `instructions/<name>.md` checklist
- [ ] Each checklist has 3-5 phases with tasks and proofs
- [ ] Shared files (spec, tests, AGENTS, docs) copied to all
- [ ] `workspaces/README.md` created explaining structure
- [ ] `workspaces/MANIFEST.md` created showing dependencies
- [ ] All committed to git
- [ ] Output: `<ralph>WORKSPACES_CREATED</ralph>`

---

## Quick Notes

- **Checklists should be specific**: Not vague tasks, but concrete phases
- **Proof requirements matter**: Each task needs clear evidence of completion
- **Dependencies matter**: Later subtasks may build on earlier ones
- **Worker agents will use these**: Write checklists that other agents can follow
- **You're not implementing**: You're planning. Other agents will do the work.

When complete, worker agents will take over each subtask!
