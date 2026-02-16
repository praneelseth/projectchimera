---
summary: 'Guide for the planner agent to design the checklist structure'
read_when:
  - Planner initialization
---

# Planner Checklist Design

You are designing a checklist that the worker agent will execute. The worker uses `prompt.md` as its system prompt, which defines a specific structure and protocol.

## Checklist Format Requirements

Design the checklist as a **flat list** with this structure:

```markdown
---
status: incomplete
---

# Implementation Checklist

- [ ] [Task Description]
  - Proof: [What evidence proves this task is complete - e.g., "Tests X, Y, Z passing", "Commit SHA: abc123", "File exists at path"]

- [ ] [Next Task Description]
  - Proof: [Evidence requirement]
```

## Key Rules

1. **Flat List Only**: NO phases, NO nested sub-tasks. Just a simple numbered list of tasks.
2. **Proof Required**: Each task MUST have a specific "Proof" requirement that can be verified
3. **One Task = One Action**: Each checkbox should be one atomic, testable action
4. **Sequential Order**: Tasks should be completed top-to-bottom
5. **Status Field**: Keep `status: incomplete` until ALL tasks done. Worker will change to `complete` only when finished.

## What to Design

1. Analyze the specification in `spec.md`
2. Break down the work into logical phases
3. For each phase:
   - Choose a clear phase name
   - Write the purpose
   - List concrete tasks with measurable proof requirements
4. Ensure all tasks together fully satisfy the spec

## Important Context

**The workspace already has a proper structure:**
- `src/` directory exists for source code
- `tests/` directory exists with test files
- Git is already initialized
- Test framework is already set up

**DO NOT create tasks for:**
- Creating directory structures (they already exist)
- Initializing git (already done)
- Setting up test frameworks (already configured)
- Creating nested project directories (unnecessary complexity)

**Focus your plan on:**
- Implementing the actual functionality in `src/`
- Running tests to verify implementation
- Making incremental progress with frequent commits
- Fixing bugs and passing all tests

**Keep it simple:**
- This is a small-scale task, not a large project
- Create a flat list of 8-15 specific tasks
- NO phases or grouping - just a simple sequential list
- Each task should be small and testable

## Output

Write the complete checklist to `instructions/plan.md` using the format above.

Start with front-matter:
```
---
status: incomplete
---
```

Then add phases and tasks following the requirements above.

Do NOT include instructions like "implement X" without concrete proof. The worker needs to know what success looks like.

Examples of good proof requirements:
- "Feature implemented in src/parser.py, test passes: `python test_json_parser.py`"
- "Git commit: feat(parser): implement json parsing"
- "All unit tests pass, 0 failures"
- "API endpoint returns 200 on valid input, 400 on invalid"

Examples of weak proof requirements:
- "Code written" (too vague)
- "Feature complete" (not measurable)
- "Tests pass" (which tests? where?)
