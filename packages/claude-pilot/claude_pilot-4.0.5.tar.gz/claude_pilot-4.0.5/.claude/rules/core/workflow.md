# claude-pilot Core Workflow

## SPEC-First Development

Always start with clear requirements:

1. **What** (Functionality): What needs to be built
2. **Why** (Context): Business value and rationale
3. **How** (Approach): Implementation strategy
4. **Success Criteria**: Measurable acceptance criteria

## TDD Cycle (Red-Green-Refactor)

1. **Red**: Write failing test
2. **Green**: Implement minimal code to pass
3. **Refactor**: Clean up while keeping tests green
4. **Repeat**: Until all criteria met

## Ralph Loop

Autonomous iteration until all tests pass:

- **Entry**: Immediately after first code change
- **Max iterations**: 7
- **Coverage target**: 80%+ overall, 90%+ core modules
- **Verification**: Tests, type-check, lint, coverage

## Vibe Coding Standards

- **Functions**: ≤50 lines
- **Files**: ≤200 lines
- **Nesting**: ≤3 levels
- **Early Return**: Reduce nesting, keep happy path at top

## Quality Gates

Before marking work complete:

- [ ] All tests pass
- [ ] Coverage 80%+ (core 90%+)
- [ ] Type check clean
- [ ] Lint clean
- [ ] Documentation updated
