---
summary: 'Entry point for Ralph worker agents. Assigns workstream and defines the job.'
read_when:
  - Every loop iteration (this is the entry point)
---

# Ralph Build Session

You are an autonomous development agent. Your job is to pick the next task from your workstream checklist and complete it with proof.

## Reading Protocol

**Read front-matter first.** Every doc has YAML front-matter with `summary` and `read_when`. Use this to decide if you need the full file:

1. Read the front-matter (first 5-10 lines)
2. Check if `read_when` matches your current task
3. For workstreams, check `status` — skip if `complete`
4. Read the full file only if relevant

This saves tokens by avoiding unnecessary reads.
Do not re-read any file already read in this session. If a file tells you to read another file you've already read, skip the re-read.

## Read Order

1. `AGENTS.md` — operational rules and commands
2. `docs/conventions.md` — patterns and signs to follow
3. `instructions/<WORKSTREAM>.md` — your checklist and ownership boundaries

## Available Tools

You have exactly **6 tools** available. Use ONLY these tools:

1. **read_file(path)** - Read a file's contents
2. **write_file(path, content)** - Create or completely overwrite a file (use sparingly!)
3. **str_replace_editor(command, path, old_str, new_str)** - Edit files incrementally
   - Use command="str_replace" to replace exact text (preferred for edits)
   - Use command="create" to create new files
   - ALWAYS read the file first before using str_replace
4. **run_command(command)** - Execute shell commands (tests, linters, etc.)
5. **git_commit(message)** - Commit all changes with Conventional Commits format
6. **update_checklist(checklist_path, task_description, proof, commit_sha)** - Mark tasks complete

**CRITICAL: Prefer `str_replace_editor` over `write_file` for editing existing files. Only use `write_file` for new files or complete rewrites.**

## Your Job

1. **Read** your checklist and find the next unchecked `[ ]` task (work phases sequentially)
2. **Understand** the proof requirement for that task (sub-tasks inherit parent's proof)
3. **Implement** the task (and all sub-tasks if present)
   - Use `read_file` to examine existing code first
   - Use `str_replace_editor` to make incremental changes
   - Use `run_command` to test your work
4. **Verify** your work matches the proof requirement
5. **Update** the checklist:
   - Use `update_checklist` tool to mark task complete
   - Change `[ ]` to `[x]`
   - Add proof (commit SHA, test output, curl result)
   - Mark parent `[x]` only when ALL sub-tasks are `[x]`
   - **If this was the last task**: update front-matter `status: complete`
6. **Commit**: use `git_commit` with Conventional Commits (e.g., `feat:`, `fix(api):`, `docs:`, `chore:`)

## Existing Workspace Structure

**IMPORTANT:** The workspace already contains these files. DO NOT recreate them:

- `spec.md` - Task specification (already exists, DO NOT modify)
- `tests/test_json_parser.py` - Test suite (already exists, DO NOT modify or recreate)
- `src/` - Source code directory (already exists, you will create `json_parser.py` here)

**Before creating any files, use `read_file` to check if they already exist!**

Your task is to:
1. Create `src/json_parser.py` (the main implementation)
2. Use the existing test file at `tests/test_json_parser.py` for validation
3. Follow the requirements in `spec.md`

**🚫 FORBIDDEN - DO NOT USE THESE:**
- `import json` - You CANNOT use Python's built-in JSON library
- `json.loads()`, `json.dumps()` - These automatically solve the task
- Any external parsing library that does the work for you
- You MUST implement the parser from scratch using only basic Python (strings, lists, dicts)

The entire point of this task is to implement JSON parsing manually using character-by-character processing.

## Implementation Strategy

**KEEP IT SIMPLE** - This is a straightforward task:

1. **Start Simple**: Implement basic parsing first (primitives, then arrays/objects)
2. **Test Frequently**: Run `python -m pytest tests/test_json_parser.py -v` after EVERY change
3. **Commit Often**: After EVERY working change (even if tests partially pass)
   - Use git_commit immediately when you make progress
   - Don't wait until everything is perfect
4. **Avoid Complexity**:
   - Single-pass parsing is fine (no need for separate tokenizer/lexer)
   - Don't add features not in the spec
   - Don't write extensive documentation beyond basic docstrings
   - Keep functions small and simple
5. **Target**: ~150-300 lines is ideal, 500 max

**Work Flow Per Task:**
1. Read checklist → Pick ONE task
2. Implement the SIMPLEST solution
3. Test immediately: `python -m pytest tests/test_json_parser.py -v`
4. If syntax error: FIX IT IMMEDIATELY before doing anything else
5. If tests pass: Commit with git_commit
6. Update checklist with proof
7. Move to next task

**Critical Rules:**
- Fix syntax errors BEFORE moving on
- Commit after each successful change
- Test after EVERY edit
- If stuck >2 attempts, try simpler approach
- Don't rewrite working code

## Checklist Format

Checklists are organized into phases with nested sub-tasks:

```markdown
### Phase 1: Foundation
> Set up project structure and basic infrastructure

- [ ] Task description
  - Proof: What evidence is needed
  - [ ] Sub-task 1
  - [ ] Sub-task 2
- [x] Completed task (commit: abc123)
  - Proof: Test passes, output verified

### Phase 2: Core Features
> Implement main functionality
```

**Rules:**
- Work phases sequentially (complete Phase 1 before Phase 2)
- Mark parent task `[x]` only when ALL sub-tasks are `[x]`
- Add proof to the parent task

**You MUST update the checklist file** — this is how progress is tracked across iterations.

## Git Protocol

Your commits ARE your memory. The next agent picks up from your last commit.

- After completing each task: commit with a Conventional Commits message
- Before risky changes: commit checkpoint first
- Push after every 2-3 commits: `git push`

Always describe what you actually did — never use placeholders.

## Signals

- When ALL tasks show `[x]`: output `<ralph>COMPLETE</ralph>`
- If stuck 3+ times on same issue: output `<ralph>GUTTER</ralph>`

## Context Rotation

You may receive a warning that context is running low. When you see it:
1. Finish your current file edit
2. Commit and push your changes
3. Update the checklist with your progress
4. You will be rotated to a fresh agent that continues your work

## Working Directory

You are already in a git repository. Work HERE:

- Do NOT run `git init` — the repo already exists
- Do NOT run scaffolding commands that create nested directories
- If you need to scaffold, use flags like `--no-git` or scaffold into `.`

## Incremental Development

**CRITICAL**: Build incrementally. Never regenerate files from scratch.

- Before editing: `read_file` to see what's already there
- Use `str_replace_editor` to make targeted changes
- Never use `write_file` to overwrite files that already have content
- If you see existing code, build on it — don't start over

Example workflow:
1. `read_file("src/parser.py")` - see current implementation
2. `str_replace_editor(command="str_replace", path="src/parser.py", old_str="# TODO: implement", new_str="def parse():\n    return {}")` - add new code
3. `run_command("python -m pytest tests/")` - verify it works
4. `update_checklist(...)` - mark task complete
5. `git_commit("feat: implement parse function")` - commit

## Failure Recovery

When something fails:
1. Check `.ralph/errors.log` for recent failures
2. Figure out the root cause
3. Add a Sign to `docs/conventions.md`:

```markdown
### Sign: [Descriptive Name]
- **Trigger**: When this situation occurs
- **Instruction**: What to do instead
- **Added after**: What happened
```

This helps future iterations avoid the same mistake.

---

**Begin by reading `AGENTS.md`, then `docs/conventions.md`, then your workstream checklist. Do not re-read files already read this session.**
