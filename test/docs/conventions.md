---
summary: 'Patterns observed during task execution and how to handle them.'
read_when:
  - When a task fails or you encounter an unexpected situation
---

# Conventions & Failure Signs

This document captures patterns (Signs) learned during agent execution. When you encounter an issue, check if a matching Sign exists here. If so, follow the instruction. If not, solve the problem and add a new Sign.

## Checklist Update Format

### Sign: How to properly format checklist updates
- **Trigger**: When updating `instructions/<TASK>.md` to mark tasks complete
- **Instruction**: 
  1. Find the task line: `- [ ] Task description`
  2. Change to: `- [x] Task description (commit: COMMIT_SHA)`
  3. Add proof on next line with proper indent (2 spaces more):
     ```
     - [x] Task name (commit: abc123)
       - Proof: Test output or file created
     ```
  4. When ALL sub-tasks are `[x]`, mark parent `[x]`
  5. Commit with: `git commit -m "chore: mark task complete with proof"`
- **Added after**: Initial agent setup

## LLM Output Format Issues

### Sign: LLM returns multiple action formats
- **Trigger**: LLM outputs actions in inconsistent XML formats (sometimes `<parameter_path>`, sometimes `<path>`, sometimes `<parameter=path>`)
- **Instruction**: Use regex parser that handles all variants:
  - Format 1: `<action type="write_file"><path>...</path><content>...</content></action>`
  - Format 2: `<parameter_path>...</parameter_path><parameter_content>...</parameter_content>`
  - Format 3: `<parameter=path>...</parameter=path><parameter=content>...</parameter=content>`
  - Test parser before deployment
- **Added after**: Progress.md shows actions failing to parse despite valid XML

### Sign: LLM doesn't follow system prompt
- **Trigger**: Model ignores output format instructions in system message
- **Instruction**: Embed format requirements directly in the user prompt, not system message
- **Added after**: Multiple action parsing failures with OpenRouter

### Sign: Context window too small for complex tasks
- **Trigger**: Agent makes progress on simple tasks but fails on complex ones after ~10 steps
- **Instruction**: Increase context threshold:
  - Current default: 8000 tokens
  - For complex tasks: 12000 tokens
  - For simple tasks: 5000 tokens sufficient
  - Adjust via `--context-threshold` CLI flag
- **Added after**: JSON parser task hit rate limits after buffer filled

## Testing & Validation

### Sign: Tests not found during execution
- **Trigger**: `run_command python -m pytest test_json_parser.py -v` fails with "file not found"
- **Instruction**: Pre-create test files in workspace before starting agent
- **Added after**: Initial test framework implementation

### Sign: Test assertions too strict
- **Trigger**: Legitimate implementation fails tests due to strict edge case checks
- **Instruction**: 
  1. Read test file to understand expectations
  2. Implement strictly to match test format (not just "correct")
  3. Example: JSON parser must return exact type (int not float for `1`)
- **Added after**: Parser implementation failures

## File Operations

### Sign: Workspace isolation violations
- **Trigger**: Agent tries to read/write files outside `workspace/json_parser/`
- **Instruction**: All file operations must be within workspace directory:
  - ✓ `workspace/json_parser/src/json_parser.py`
  - ✓ `workspace/json_parser/plan.md`
  - ✗ `agents/ralph_agent.py` (outside workspace)
  - ✗ `core/llm_client.py` (outside workspace)
- **Added after**: Initial design clarification

### Sign: Large files in progress.md cause noise
- **Trigger**: Progress file grows too large with full LLM response bodies
- **Instruction**: Only log action type and result, not full response:
  - Log: `Step 5: write_file -> ✓ File written: src/json_parser.py`
  - Don't log: Full 500-line response content
  - Use separate file for debugging if needed
- **Added after**: Progress.md became unwieldy

## Agent State Management

### Sign: Agent loops without progress
- **Trigger**: Same task attempted repeatedly (3+ times with no change)
- **Instruction**: Output `<ralph>GUTTER</ralph>` to signal stuck state and trigger intervention
- **Added after**: Failure recovery protocol

### Sign: Checklist out of sync with actual work
- **Trigger**: Files created but checklist not updated, or vice versa
- **Instruction**: After each task:
  1. Create/modify files
  2. Verify with test
  3. Update checklist immediately
  4. Commit once
  5. Never commit without updating checklist
- **Added after**: Progress tracking confusion

## API & Rate Limiting

### Sign: OpenRouter rate limiting
- **Trigger**: 429 errors after ~10 API calls within 30 seconds
- **Instruction**: Use NVIDIA free tier instead:
  ```
  NVIDIA_API_KEY=nvapi-...
  --provider nvidia  # Uses https://integrate.api.nvidia.com/v1
  ```
  - No rate limit complaints observed
  - Better model quality
  - Same OpenAI SDK interface
- **Added after**: OpenRouter free tier rate limiting

### Sign: SSL/TLS connection timeouts
- **Trigger**: Hang during API calls to integrate.api.nvidia.com
- **Instruction**: 
  1. Check network connection
  2. Increase timeout (requests timeout=30 is default)
  3. Not a code issue, just network delays
  4. Let it hang for 30+ seconds before cancelling
- **Added after**: Development testing

## Implementation Patterns

### Sign: How to structure a JSON parser
- **Trigger**: Starting JSON parser implementation
- **Instruction**: 
  1. Phase 1: Tokenizer - break string into tokens (STRING, NUMBER, COLON, BRACE, etc.)
  2. Phase 2: Parser - recursive descent functions (parse_value, parse_object, parse_array)
  3. Phase 3: Error handling - track position, report line/column
  4. Phase 4: Testing - verify all edge cases
  5. Keep under 300 lines per spec
- **Added after**: JSON parser specification

---

**Note**: New Signs should be added when patterns emerge during task execution. Document the trigger, instruction, and context in which it was discovered.
