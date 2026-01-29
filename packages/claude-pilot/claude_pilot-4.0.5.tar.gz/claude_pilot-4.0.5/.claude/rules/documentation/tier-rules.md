---
paths:
  - "CLAUDE.md"
  - "**/CONTEXT.md"
  - "docs/**"
---

# 3-Tier Documentation Rules

## Size Limits

| Tier | File | Max Lines | Max Tokens (Est.) |
|------|------|-----------|-------------------|
| **Tier 1** | CLAUDE.md | 300 lines | ~3000 tokens |
| **Tier 2** | Component CONTEXT.md | 200 lines | ~2000 tokens |
| **Tier 3** | Feature CONTEXT.md | 150 lines | ~1500 tokens |

## Auto-Management Triggers

When limit exceeded:

1. **Notify user**: Document exceeds recommended size
2. **Suggest strategy**: Compression or split based on tier
3. **Execute with confirmation**: User must approve changes

## Tier-Specific Actions

### Tier 1 (CLAUDE.md > 300 lines)

1. Move detailed sections to `docs/ai-context/`
2. Keep only quick-reference in CLAUDE.md
3. Use `@imports` for details when needed

### Tier 2 (CONTEXT.md > 200 lines)

1. Archive historical decisions to `{component}/HISTORY.md`
2. Keep only current architecture
3. Compress implementation details

### Tier 3 (CONTEXT.md > 150 lines)

1. Split by feature area
2. Create sub-CONTEXT.md files
3. Link from parent CONTEXT.md

## Documentation Checklist

When completing work (`/03_close`), verify:

- [ ] Tier 1 (CLAUDE.md): Updated if project-level changes
- [ ] Tier 2 (Component CONTEXT.md): Updated for affected components
- [ ] Tier 3 (Feature CONTEXT.md): Updated for specific features
- [ ] Document sizes: Check if any exceed thresholds
- [ ] Auto-management: Apply if thresholds exceeded
