---
summary: 'Guide for the planner agent to design the checklist structure'
read_when:
  - Planner initialization
---

# Planner Checklist Design

You are designing a checklist that the worker agent will execute. The worker uses `prompt.md` as its system prompt, which defines a specific structure and protocol.

## Checklist Format Requirements

Design the checklist with this structure:

```markdown
---
status: incomplete
---

### Phase N: [Phase Name]
> [One sentence describing the phase's purpose]

- [ ] [Task Description]
  - Proof: [What evidence proves this task is complete - e.g., "File created at src/X, test passes", "Commit SHA", "curl output shows 200", etc.]
  - [ ] Sub-task 1 description
    - Proof: [Sub-task proof requirement]
  - [ ] Sub-task 2 description
    - Proof: [Sub-task proof requirement]

- [ ] [Another Task]
  - Proof: [Evidence requirement]
```

## Key Rules

1. **Phases First**: Organize into logical phases (Foundation, Core Features, Testing, etc.)
2. **Proof Upfront**: Each task must have a clear "Proof" requirement. The worker will add evidence here (commit SHA, test output, etc.)
3. **Sub-tasks Optional**: Only use sub-tasks if a task naturally breaks into smaller pieces
4. **One Sentence Per Phase**: The `>` line explains the phase purpose
5. **Inherit Proof**: Sub-tasks inherit the parent's proof requirement unless overridden
6. **Sequential**: Phases should be completed in order top-to-bottom

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
- Break implementation into 3-5 clear phases max
- Each phase should have 2-4 concrete implementation tasks
- Total should be 10-20 tasks, not 30+

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
